import base64
import glob
import logging
import os
import pyzipper
import re
import xml.etree.ElementTree as ET

from datetime import date, datetime
from requests import Session
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.exceptions import SSLError, HTTPError
from zeep import Client, Settings
from zeep.transports import Transport

from django.conf import settings

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
settings = Settings(extra_http_headers=headers, raw_response=True)
today = date.today()


class CustomHostNameCheckingAdapter(HTTPAdapter):
    def cert_verify(self, conn, url, verify, cert):
        if conn.host == HOST_IP:
            conn.assert_hostname = "*.zus.pl"
        return super(CustomHostNameCheckingAdapter, self).cert_verify(
            conn, url, verify, cert
        )


class UnpackingException(Exception):
    pass


def decode_and_extract(input, filename, pswd=None):
    """Decode input content, save as zip file and extract."""

    altchars = b"+/"
    data = re.sub(rb"[^a-zA-Z0-9%s]+" % altchars, b"", input)  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b"=" * (4 - missing_padding)

    zipped_file = f"{filename}.zip"

    try:
        with open(zipped_file, "wb") as result:
            result.write(base64.b64decode(data))
    except IOError as e:
        ezlalogger.error(f"Błąd podczas zapisywania zapakowanego raportu: {e}")
        raise IOError(f"Błąd podczas zapisywania zapakowanego raportu: {e}")

    with pyzipper.AESZipFile(
        zipped_file,
        "r",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as extracted_zip:
        try:
            extracted_zip.extractall(
                pwd=str.encode(pswd), path=f"extracted_files/{filename}"
            )
        except Exception as e:
            ezlalogger.error(f"Błąd podczas wypakowywania: {e}")
            raise UnpackingException(
                "Błąd podczas wypakowywania raportów pobranych z ZUS"
            )

    # remove unnecesary zip files
    try:
        os.remove(zipped_file)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


def get_data_from_zus(date=today):
    """Connection to ZUS service to get sick leaves reports"""

    session = Session()
    session.auth = HTTPBasicAuth(EZLA_SERVICE_USERNAME, EZLA_SERVICE_PSWD)
    session.mount("https://", CustomHostNameCheckingAdapter())

    try:
        client = Client(
            URL, transport=Transport(session=session), settings=settings
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
            with open("applications/sickleaves/raporty.xml", mode="wb") as f:
                f.write(resp.content)
        except IOError as e:
            ezlalogger.error(f"Błąd podczas zapisywania raportu: {e}")
            return f"Błąd podczas zapisywania raportu: {e}"

        tree = ET.parse("applications/sickleaves/raporty.xml")
        root = tree.getroot()
        code = root.find(".//kod").text

        if code == "0":
            try:
                content_list = root.findall(".//raport")
                for i, item in enumerate(content_list):
                    generated_date = item.find("dataWygenerowania").text

                for i, report in enumerate(content_list):
                    generated_date = report.find("dataWygenerowania").text
                    report_str_content = report.find("zawartosc").text
                    report_binary_content = report_str_content.encode("utf-8")
                    filename = f"{generated_date}-{i}"
                    decode_and_extract(
                        report_binary_content, filename, pswd=EZLA_EXTRACT_PSWD
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

    if date <= today:
        data = get_data_from_zus(date)
        # if data is string not None, return error message
        if isinstance(data, str):
            return data
    else:
        return "Dzisiejszy raport został już pobrany z ZUS."

    sickleaves_list = []
    if not glob.glob("extracted_files/**/*.xml", recursive=True):
        return "Błąd. Brak pobranych raportów."

    for filename in glob.glob("extracted_files/**/*.xml"):
        tree = ET.parse(filename)
        root = tree.getroot()
        pos_num = root.find(".//liczbaDokumentowEzla")
        dirname = os.path.dirname(filename)

        if pos_num is not None and pos_num.text != "0":
            try:
                for doc in root.iter("dokumentyEzla"):
                    empl_identifier = doc.find(".//identyfikator/wartosc").text
                    first_name = doc.find(".//imie").text
                    last_name = doc.find(".//nazwisko").text
                    series = doc.find(".//seria").text
                    number = doc.find(".//numer").text
                    # status = doc[1][1].text
                    issue_date = doc.find(".//dataWystawienia").text
                    period_from = doc.find(".//okresZwolnienia/dataOd").text
                    period_to = doc.find(".//okresZwolnienia/dataDo").text
                    hospital_from = doc.find(".//okresWSzpitalu/dataOd").text
                    hospital_to = doc.find(".//okresWSzpitalu/dataDo").text
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
                    can_walk = doc.find(".//wskazaniaLekarskie").text
                    is_cancelled = doc.find(".//czyAnulowane").text
                    family_member_care = doc.find(".//dataUrodzeniaOsoby").text

                    additional_info = ""

                    if hospital_from is not None:
                        hospital_start = ("-").join(
                            hospital_from.split("-")[:-1]
                        )
                        hospital_end = (
                            ("-").join(hospital_to.split("-")[:-1])
                            if hospital_to is not None
                            else hospital_from
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

                    if is_cancelled.lower() == "tak":
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
                        "issue_date": (
                            datetime.strptime(issue_date, "%Y-%m-%d")
                        ),
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
        try:
            os.remove(filename)
            os.rmdir(dirname)
        except OSError as e:
            ezlalogger.warning(f"Nie udało się usunąć pliku lub katalogu {e}")

    return sickleaves_list
