import glob
import logging
import os
import shutil

ezlalogger = logging.getLogger("ezla")


def get_text(node, path):
    element = node.find(path)
    return element.text.strip() if element is not None and element.text else ""


def safe_extract(zip_file, path, password=None):
    for member in zip_file.namelist():
        member_path = os.path.realpath(os.path.join(path, member))
        if not member_path.startswith(os.path.realpath(path)):
            raise Exception("Zip file contains unsafe paths.")
    zip_file.extractall(path=path, pwd=password)


def cleanup_extracted_files():
    dirs_to_remove = set()
    for filename in glob.glob("extracted_files/**/*.xml", recursive=True):
        dirs_to_remove.add(os.path.dirname(filename))
        try:
            os.remove(filename)
        except OSError as e:
            ezlalogger.warning(f"Nie udało się usunąć pliku {filename}: {e}")
    for dirname in dirs_to_remove:
        try:
            shutil.rmtree(dirname)
        except OSError as e:
            ezlalogger.warning(f"Nie udało się usunąć katalogu {dirname}: {e}")
