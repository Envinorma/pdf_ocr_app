import json


def generate_id(filename: str, suffix: str) -> str:
    prefix = filename.split('/')[-1].replace('.py', '').replace('_', '-')
    return prefix + '-' + suffix


def write_json(obj, filename: str) -> None:
    with open(filename, 'w') as file_:
        json.dump(obj, file_, indent=4)
