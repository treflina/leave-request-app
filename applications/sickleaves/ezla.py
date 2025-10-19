import base64
import glob
from io import BytesIO
import logging
import os
import pyzipper
import re
import xml.etree.ElementTree as ET

from datetime import datetime
from requests import Session
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, SSLError, HTTPError
from zeep import Client, Settings
from zeep.transports import Transport

from django.conf import settings

from .models import EZLAReportGeneration, Sickleave
from .utils import get_text, safe_extract, cleanup_extracted_files

ezlalogger = logging.getLogger("ezla")

URL = getattr(settings, "EZLA_URL", "")
HOST_IP = getattr(settings, "EZLA_SERVICE_IP", "ipcheck")
LOGIN = getattr(settings, "EZLA_LOGIN", "")
PASSWORD = getattr(settings, "EZLA_HASLO", "")
NIP = getattr(settings, "EZLA_NIP", "")
EZLA_EXTRACT_PSWD = getattr(settings, "EZLA_EXTRACT_PSWD", "")
EZLA_SERVICE_USERNAME = getattr(settings, "EZLA_SERVICE_USERNAME", "")
EZLA_SERVICE_PSWD = getattr(settings, "EZLA_SERVICE_PSWD", "")

headers = {
    "SOAPAction": (
        "zus_channel_platnikRaportyZla_wsdlPlatnikRaportyZla_Binder_pobierzRaporty"  # noqa: E501
    )
}
zeep_settings = Settings(extra_http_headers=headers, raw_response=True)


class CustomHostNameCheckingAdapter(HTTPAdapter):
    def cert_verify(self, conn, url, verify, cert):
        if conn.host == HOST_IP:
            conn.assert_hostname = "*.zus.pl"
        return super(CustomHostNameCheckingAdapter, self).cert_verify(
            conn, url, verify, cert
        )


class UnpackingException(Exception):
    pass


def decode_and_extract(input_data, password=None):
    """
    Decode base64 input and extract ZIP contents into a temp directory.
    Returns a list of extracted XML file paths.
    """
    altchars = b"+/"
    data = re.sub(rb"[^a-zA-Z0-9%s]+" % altchars, b"", input_data)
    missing_padding = len(data) % 4
    if missing_padding:
        data += b"=" * (4 - missing_padding)

    try:
        decoded_data = base64.b64decode(data)
    except Exception as e:
        raise UnpackingException(f"Base64 decode error: {e}")

    temp_dir = os.path.join(
        "extracted_files",
        f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    try:
        os.makedirs(temp_dir, exist_ok=True)
    except Exception as e:
        raise UnpackingException(f"Failed to create temp directory: {e}")

    zip_path = os.path.join(temp_dir, "report.zip")

    try:
        with open(zip_path, "wb") as f:
            f.write(decoded_data)

        with pyzipper.AESZipFile(
            zip_path,
            "r",
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zip_file:
            pwd = password.encode() if password else None
            safe_extract(zip_file, temp_dir, password=pwd)

        extracted_files = [
            os.path.join(root, f)
            for root, _, files in os.walk(temp_dir)
            for f in files if f.lower().endswith(".xml")
        ]

        os.remove(zip_path)

        if not extracted_files:
            raise UnpackingException(
                "ZIP archive did not contain any XML files."
                )

        return extracted_files

    except Exception as e:
        raise UnpackingException(f"Failed to unpack ZIP: {e}")


def get_data_from_zus(date=None):
    """Connection to ZUS service to get sick leaves reports"""

    if date is None:
        date = date.today()

    session = Session()
    session.auth = HTTPBasicAuth(EZLA_SERVICE_USERNAME, EZLA_SERVICE_PSWD)
    session.mount("https://", CustomHostNameCheckingAdapter())

    try:
        client = Client(
            URL, transport=Transport(session=session), settings=zeep_settings
        )
    except ValueError as e:
        ezlalogger.error(f"Błąd połączenia: {e}")
        return (
            "Błąd połączenia. Sprawdź czy w ustawieniach podano "
            "prawidłowy URL."
        )
    except HTTPError as eh:
        ezlalogger.error(
            (
                "Błąd połączenia - sprawdź login, hasło i url do wejścia do "
                f"serwisu ZUS {eh}."
            )
        )
        return (
            "Błąd połączenia - sprawdź login, hasło, url do "
            "wejścia do serwisu ZUS "
        )
    try:
        resp = client.service.pobierzRaporty(
            login=LOGIN,
            haslo=PASSWORD,
            nip=NIP,
            dataOd=date,
        )

        try:
            tree = ET.parse(BytesIO(resp.content))
            root = tree.getroot()
        except ET.ParseError as e:
            ezlalogger.error(f"Błąd podczas parsowania XML z ZUS: {e}")
            return f"Błąd podczas parsowania XML: {e}"

        code = get_text(root, ".//kod")

        if code == "0":
            try:
                content_list = root.findall(".//raport")
                for i, item in enumerate(content_list):
                    generated_date = item.find("dataWygenerowania").text

                reports_dates = []
                for i, report in enumerate(content_list):
                    generated_date = report.find("dataWygenerowania").text
                    generated_date_obj = datetime.strptime(
                        generated_date, "%Y-%m-%d"
                        ) if generated_date is not None else None
                    reports_dates.append(generated_date_obj)
                    report_str_content = report.find("zawartosc").text
                    report_binary_content = report_str_content.encode("utf-8")
                    # filename = f"{generated_date}-{i}"
                    decode_and_extract(
                        report_binary_content, password=EZLA_EXTRACT_PSWD
                    )

                last_report_date = max(reports_dates) if reports_dates and (
                    all(isinstance(x, datetime) for x in reports_dates)
                    ) else None
                if last_report_date:
                    last_date_in_db = EZLAReportGeneration.objects.last()
                    if last_date_in_db:
                        last_date_in_db.last_report_date = last_report_date
                        last_date_in_db.save()
                    else:
                        EZLAReportGeneration.objects.create(
                            last_report_date=last_report_date
                            )

            except KeyError as e:
                ezlalogger.error(
                    f"Sprawdź treść pobranego z ZUS raportu. Błąd: {e}"
                )
                return f"Sprawdź treść pobranego z ZUS raportu. Błąd: {e}"
            except TypeError as et:
                ezlalogger.error(
                    (
                        "Sprawdź treść pobranego z ZUS raportu. "
                        f"Błąd podczas próby przetworzenia danych: {et}"
                    )
                )
                return (
                    "Sprawdź treść pobranego z ZUS raportu. "
                    f"Błąd podczas próby przetworzenia danych: {et}"
                )

        elif code == "200":
            ezlalogger.error("Błąd wewnętrzny serwisu ZUS")
            return "Błąd wewnętrzny serwisu ZUS"
        else:
            description = root.find(".//opis").text
            ezlalogger.error(f"Błąd: {description}")
            return f"Błąd: {description}"

    except ConnectionError as e:
        ezlalogger.error(f"Błąd połączenia: {e}.")
        return "Błąd połączenia"
    except SSLError as es:
        ezlalogger.error(f"Błąd przy weryfikacji ssl: {es}.")
        return "Błąd połączenia - weryfikacja SSL serwisu ZUS"
    except UnpackingException as ex:
        return f"{ex}"


def get_compiled_ezla_data(date):
    """Get and prepare sick leaves data from xml ZUS reports"""

    if date <= date.today():
        data = get_data_from_zus(date)
        # if data is string not None, return error message
        if isinstance(data, str):
            return data
    else:
        return "Ostatni raport wygenerowany przez ZUS został już pobrany."

    sickleaves_list = []
    if not glob.glob("extracted_files/**/*.xml", recursive=True):
        return (
            "Błąd. Brak pobranych raportów. "
            "Sprawdź w ZUS PUE czy raport został wygenerowany."
            )

    for filename in glob.glob("extracted_files/**/*.xml", recursive=True):
        tree = ET.parse(filename)
        root = tree.getroot()
        pos_num = root.find(".//liczbaDokumentowEzla")

        if pos_num is not None and pos_num.text != "0":
            try:
                for doc in root.iter("dokumentyEzla"):
                    # TODO
                    empl_identifier = get_text(doc, ".//identyfikator/wartosc")
                    first_name = get_text(doc, ".//imie")
                    last_name = get_text(doc, ".//nazwisko")
                    # status = doc[1][1].texT
                    issue_date = get_text(doc, ".//dataWystawienia")
                    issue_date_dt = datetime.strptime(
                        issue_date, "%Y-%m-%d").date() if issue_date else None

                    series = get_text(doc, ".//seria")
                    number = get_text(doc, ".//numer")
                    doc_number = f"{series}{number}"

                    # Skip already saved documents
                    if Sickleave.objects.filter(
                        doc_number=doc_number,
                        issue_date=issue_date_dt
                    ).exists():
                        continue

                    period_from = get_text(doc, ".//okresZwolnienia/dataOd")
                    period_to = get_text(doc, ".//okresZwolnienia/dataDo")
                    hospital_from = get_text(doc, ".//okresWSzpitalu/dataOd")
                    hospital_to = get_text(doc, ".//okresWSzpitalu/dataDo")
                    codeA = (
                        "A"
                        if doc.find(".//kodChorobyA").text is not None
                        else None
                    )
                    codeB = (
                        "B"
                        if doc.find(".//kodChorobyB").text is not None
                        else None
                    )
                    codeC = (
                        "C"
                        if doc.find(".//kodChorobyC").text is not None
                        else None
                    )
                    codeD = (
                        "D"
                        if doc.find(".//kodChorobyD").text is not None
                        else None
                    )
                    codeE = (
                        "E"
                        if doc.find(".//kodChorobyE").text is not None
                        else None
                    )
                    can_walk = get_text(doc, ".//wskazaniaLekarskie")
                    is_cancelled = get_text(doc, ".//czyAnulowane")
                    family_member_care = get_text(doc, ".//dataUrodzeniaOsoby")

                    additional_info = ""

                    if hospital_from is not None:
                        hospital_start = (".").join(
                            hospital_from.split("-")[::-1]
                        )
                        hospital_end = (
                            (".").join(hospital_to.split("-")[::-1])
                            if hospital_to is not None
                            else hospital_start
                        )

                        hospital_info = (
                            f"szpital {hospital_start} do {hospital_end}"
                        )
                        additional_info += f"{hospital_info} "

                    codes = list(
                        filter(
                            lambda x: x is not None,
                            [codeA, codeB, codeC, codeD, codeE],
                        )
                    )
                    if codes:
                        codes_info = f'kod {"".join(codes)}'
                        additional_info += f"{codes_info} "

                    if can_walk is not None:
                        additional_info += f"{can_walk} "

                    if is_cancelled and is_cancelled.lower() == "tak":
                        is_cancelled = True
                        cancelled_info = "ANULOWANE"
                        additional_info = cancelled_info
                    else:
                        is_cancelled = False

                    sickleave = {
                        "empl_identifier": empl_identifier,
                        "first_name": first_name.capitalize(),
                        "last_name": (
                            ("-").join(
                                [
                                    word.capitalize()
                                    for word in last_name.split("-")
                                ]
                            )
                        ),
                        "issue_date": issue_date_dt,
                        "doc_number": series + number,
                        "start_date": (
                            datetime.strptime(period_from, "%Y-%m-%d")
                        ),
                        "end_date": datetime.strptime(period_to, "%Y-%m-%d"),
                        "leave_type": (
                            "O" if family_member_care is not None else "C"
                        ),
                        "additional_info": additional_info,
                        "is_cancelled": is_cancelled,
                    }

                    sickleaves_list.append(sickleave)

            except Exception as e:
                ezlalogger.error(f"Błąd podczas parsowania danych: {e}")
                return "Błąd podczas przetwarzania danych."

    cleanup_extracted_files()
    return sickleaves_list
