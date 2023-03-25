import os
import zipfile

import requests

from aluminum.exceptions import CorruptedOnlineMetaError, NetworkError


def download_file(file_url: str, name: str, path: str):
    """Download a file from the Internet.

    Args:
        file_url (str): The URL of target file.
        name (str): The path to save the file.
    """

    try:
        path = os.path.join(path, name)
        r = requests.get(file_url, stream=True)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except requests.RequestException as e:
        raise NetworkError(e)


def unzip(file, path):
    try:
        with zipfile.ZipFile(file) as zip:
            if zip.testzip():
                raise CorruptedOnlineMetaError(f'File {file} is broken')
            zip.extractall(path)
    except Exception as e:
        raise CorruptedOnlineMetaError(e)


def touch_dir(path):
    """Create dictionary if not exists."""
    if not os.path.isdir(path):
        os.makedirs(path)
    return path
