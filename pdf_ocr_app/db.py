import json
import os
import shutil
from typing import List, Union

import alto
import requests
from ocr_utils.alto_to_svg import alto_pages_and_cells_to_svg

from pdf_ocr_app.compute import OCRProcessingStep
from pdf_ocr_app.config import CONFIG
from pdf_ocr_app.utils import create_folder_if_inexistent, safely_replace_path_suffix, write_json

_DOCS_FOLDER = CONFIG.storage.documents_folder


def _document_folder(document_id: str) -> str:
    return os.path.join(_DOCS_FOLDER, document_id)


def _step_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'step.json')


def input_pdf_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'in.pdf')


def alto_xml_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'out.xml')


def svg_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'out.svg')


def _load_json(path: str):
    with open(path, 'r') as file_:
        return json.load(file_)


def load_processing_step(document_id: str) -> OCRProcessingStep:
    return OCRProcessingStep.from_dict(_load_json(_step_path(document_id)))


def has_processing_step(document_id: str) -> bool:
    return os.path.exists(_step_path(document_id))


def dump_processing_step(step: OCRProcessingStep, document_id: str):
    return write_json(step.to_dict(), _step_path(document_id))


def load_alto_pages_xml(document_id: str) -> List[str]:
    return _load_json(alto_xml_path(document_id))


def dump_alto_pages_xml(xml: List[str], document_id: str) -> None:
    write_json(xml, alto_xml_path(document_id))


def dump_svg(xml: List[str], document_id: str) -> None:
    alto_pages_and_cells_to_svg(xml, [[]]).saveas(svg_path(document_id))


def _ensure_one_page_and_get_it(alto_file: alto.Alto) -> alto.Page:
    if len(alto_file.layout.pages) != 1:
        raise ValueError(f'Expecting exactly one page, got {len(alto_file.layout.pages)}')
    return alto_file.layout.pages[0]


def load_alto_pages(document_id: str) -> List[alto.Page]:
    step = load_processing_step(document_id)
    if not step.done:
        raise ValueError(f'Cannot load alto pages: processing not done yet. (OCRProcessingStep={step})')
    pages = load_alto_pages_xml(document_id)
    return [_ensure_one_page_and_get_it(alto.parse(page)) for page in pages]


def download_document(url: str, output_filename: str) -> None:
    req = requests.get(url, stream=True)
    if req.status_code == 200:
        with open(output_filename, 'wb') as f:
            req.raw.decode_content = True
            shutil.copyfileobj(req.raw, f)


def _sample_data_folder_name() -> str:
    res = safely_replace_path_suffix(__file__, 'db.py', 'data')
    if not os.path.exists(res):
        raise ValueError('Sample data folder not found, it should exists.')
    return res


def load_sample_documents() -> List[str]:
    folder = _sample_data_folder_name()
    contents = [os.path.join(folder, x) for x in os.listdir(folder)]
    return [x for x in contents if os.path.isfile(x)]


def write_file(content: Union[bytes, str], path: str) -> None:
    if isinstance(content, str):
        with open(path, 'w') as file_:
            file_.write(content)
        return
    with open(path, 'wb') as file_b_:
        file_b_.write(content)


def save_document(content: Union[bytes, str], document_id: str) -> None:
    create_folder_if_inexistent(_document_folder(document_id))
    path = input_pdf_path(document_id)
    write_file(content, path)


def copy_pdf(input_path: str, document_id: str) -> None:
    create_folder_if_inexistent(_document_folder(document_id))
    dest_path = input_pdf_path(document_id)
    shutil.copyfile(input_path, dest_path)
