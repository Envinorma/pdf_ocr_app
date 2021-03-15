import json
import os
import shutil
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import alto
import requests

from pdf_ocr_app.app.utils import write_json
from pdf_ocr_app.config import CONFIG

_DOCS_FOLDER = ''  # CONFIG.storage.ap_data_folder TODO


@dataclass
class OCRProcessingStep:
    messsage: Optional[str]
    advancement: float
    done: bool

    def __post_init__(self) -> None:
        assert 0 <= self.advancement <= 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]) -> 'OCRProcessingStep':
        return cls(**dict_)


def _document_folder(document_id: str) -> str:
    return os.path.join(_DOCS_FOLDER, document_id)


def _step_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'step.json')


def _ap_extraction_step_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'ap_step.json')


def input_pdf_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'in.pdf')


def alto_xml_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'out.xml')


def _get_ap_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'ap.json')


def ap_odt_path(document_id: str) -> str:
    return os.path.join(_document_folder(document_id), 'ap.odt')


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


def _create_folder_if_inexistent(folder: str) -> None:
    if not os.path.exists(folder):
        os.mkdir(folder)


def download_document(url: str, output_filename: str) -> None:
    req = requests.get(url, stream=True)
    if req.status_code == 200:
        with open(output_filename, 'wb') as f:
            req.raw.decode_content = True
            shutil.copyfileobj(req.raw, f)


def _pdf_exists(document_id: str) -> bool:
    return os.path.exists(os.path.join(_DOCS_FOLDER, document_id, 'in.pdf'))


def load_document_ids() -> List[str]:
    return [x for x in os.listdir(_DOCS_FOLDER) if _pdf_exists(x)]


def _ap_exists(document_id: str) -> bool:
    return os.path.exists(os.path.join(_DOCS_FOLDER, document_id, 'ap.json'))


def load_document_ids_having_ap() -> List[str]:
    return [x for x in os.listdir(_DOCS_FOLDER) if _ap_exists(x)]


def save_document(document_id: str, content: bytes) -> None:
    _create_folder_if_inexistent(_document_folder(document_id))
    path = input_pdf_path(document_id)
    with open(path, 'wb') as file_:
        file_.write(content)
