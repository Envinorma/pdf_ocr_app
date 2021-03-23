import argparse
import os
import random
import string
import subprocess
from typing import Any, Callable, List, Union

import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
from tqdm import tqdm

from pdf_ocr_app.compute import OCRProcessingStep
from pdf_ocr_app.config import CONFIG
from pdf_ocr_app.db import dump_alto_pages_xml, dump_processing_step, dump_svg, input_pdf_path
from pdf_ocr_app.utils import safely_replace_path_suffix

_SIMPLE_OCR = 'simple_ocr'


def _decode(content: Union[str, bytes]) -> str:
    return content.decode() if isinstance(content, bytes) else content


def _tesseract(page: Any) -> str:
    return _decode(pytesseract.image_to_alto_xml(page, lang=CONFIG.tesseract.lang))


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
    if not os.path.exists(input_pdf_path(document_id)):
        raise ValueError(f'Input pdf not found at path {input_pdf_path(document_id)}.')
    _ocr_step_callback(document_id)(OCRProcessingStep('OCR en cours.', 0.05, False))
    input_path = input_pdf_path(document_id)
    nb_pages = _nb_pages_in_pdf(input_path)
    result: List[str] = []
    for page_nb in tqdm(range(nb_pages), 'Performing OCR.'):
        result.append(_ocr_page(input_path, page_nb))
        msg = f'OCR en cours de la page {page_nb + 1}/{nb_pages}'
        adv = min(0.1 + 0.9 * (page_nb + 1) / nb_pages, 1.0)
        _ocr_step_callback(document_id)(OCRProcessingStep(msg, adv, False))
    dump_alto_pages_xml(result, document_id)
    dump_svg(result, document_id)
    _ocr_step_callback(document_id)(OCRProcessingStep(None, 1.0, True))


def _get_src_file() -> str:
    return safely_replace_path_suffix(__file__, '/pdf_ocr_app/process.py', '')


def _start_process(document_id: str, mode: str) -> None:
    cmd = ['python3', __file__, '--doc', document_id, '--mode', mode]
    env = os.environ.copy()
    env['PYTHONPATH'] = _get_src_file() + ':' + env['PYTHONPATH']
    subprocess.Popen(cmd, env=env)


def start_simple_ocr_process(document_id: str) -> None:
    _start_process(document_id, _SIMPLE_OCR)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--doc', required=True)
    parser.add_argument('--mode', required=True)
    args = parser.parse_args()
    if args.mode == _SIMPLE_OCR:
        simple_ocr_on_file(args.doc)
    else:
        raise NotImplementedError(args.mode)
