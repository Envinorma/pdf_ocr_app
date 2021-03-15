import argparse
import os
import random
import string
import subprocess
from typing import Any, Callable, List, Union

import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
from tqdm import tqdm

from pdf_ocr_app.db.ap import OCRProcessingStep, dump_alto_pages_xml, dump_processing_step, input_pdf_path

_SIMPLE_OCR = 'simple_ocr'
_AP_EXTRACTION = 'ap_extraction'


def _decode(content: Union[str, bytes]) -> str:
    return content.decode() if isinstance(content, bytes) else content


def _tesseract(page: Any) -> str:
    return _decode(pytesseract.image_to_alto_xml(page, lang='fra'))


def _build_tmp_file() -> str:
    return '/tmp/' + ''.join([random.choice(string.ascii_letters) for _ in range(10)])


def _ocr_page(path: str, page_nb: int) -> str:
    page = convert_from_path(path, first_page=page_nb + 1, last_page=page_nb + 1)[0]
    file_ = _build_tmp_file() + '.png'
    page.save(file_)
    page = _tesseract(file_)
    os.remove(file_)
    return page


def _nb_pages_in_pdf(filename: str) -> int:
    return pdfinfo_from_path(filename)['Pages']


def _ocr_step_callback(document_id: str) -> Callable[[OCRProcessingStep], None]:
    def _func(step: OCRProcessingStep) -> None:
        dump_processing_step(step, document_id)

    return _func


def simple_ocr_on_file(document_id: str) -> None:
    _ocr_step_callback(document_id)(OCRProcessingStep(f'Starting OCR.', 0.05, False))
    input_path = input_pdf_path(document_id)
    nb_pages = _nb_pages_in_pdf(input_path)
    result: List[str] = []
    for page_nb in tqdm(range(nb_pages), 'Performing OCR.'):
        result.append(_ocr_page(input_path, page_nb))
        msg = f'Performing OCR on page {page_nb + 2}/{nb_pages}'
        _ocr_step_callback(document_id)(OCRProcessingStep(msg, 0.1 + 0.9 * (page_nb + 1) / nb_pages, False))
    dump_alto_pages_xml(result, document_id)
    _ocr_step_callback(document_id)(OCRProcessingStep(None, 1.0, True))


def _get_src_file() -> str:
    to_replace = '/pdf_ocr_app/process.py'
    if not __file__.endswith(to_replace):
        raise ValueError(f'Expecting __file__ to end with {to_replace}, got {__file__}')
    return __file__.replace(to_replace, '')


_SRC_FILE = _get_src_file()


def _start_process(document_id: str, mode: str) -> None:
    cmd = ['python3', __file__, '--doc', document_id, '--mode', mode]
    env = os.environ.copy()
    env['PYTHONPATH'] = _SRC_FILE + ':' + env['PYTHONPATH']
    subprocess.Popen(cmd, env=env)


def start_simple_ocr_process(document_id: str) -> None:
    _start_process(document_id, _SIMPLE_OCR)


def start_ap_extraction_process(document_id: str) -> None:
    _start_process(document_id, _AP_EXTRACTION)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--doc', required=True)
    parser.add_argument('--mode', required=True)
    args = parser.parse_args()
    if args.mode == _SIMPLE_OCR:
        simple_ocr_on_file(args.doc)
    raise NotImplementedError(args.mode)
