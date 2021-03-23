import json
import os


def safely_replace_path_suffix(path: str, to_replace: str, with_: str) -> str:
    if not path.endswith(to_replace):
        raise ValueError(f'Expecting path to end with {to_replace}, got {path}')
    return path.replace(to_replace, with_)


def create_folder_if_inexistent(folder: str) -> None:
    if not os.path.exists(folder):
        os.mkdir(folder)


def write_json(obj, filename: str) -> None:
    with open(filename, 'w') as file_:
        json.dump(obj, file_, indent=4)
