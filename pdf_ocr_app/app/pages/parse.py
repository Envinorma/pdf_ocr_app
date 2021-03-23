import base64
import traceback
from typing import Any, Dict, List, Optional, Union

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate

from pdf_ocr_app.app.common_ids import DOCUMENT_ID
from pdf_ocr_app.app.components.upload_row import upload_row
from pdf_ocr_app.app.routing import Endpoint, Page
from pdf_ocr_app.app.utils import generate_id
from pdf_ocr_app.compute import Document, OCRProcessingStep
from pdf_ocr_app.db import (
    copy_pdf,
    dump_processing_step,
    has_processing_step,
    load_processing_step,
    load_sample_documents,
    save_document,
)
from pdf_ocr_app.process import start_simple_ocr_process

_UPLOAD = generate_id(__file__, 'upload-data')
_PROCESSING_DONE = generate_id(__file__, 'processing-done')
_INTERVAL = generate_id(__file__, 'interval')
_DOCUMENT_ID = generate_id(__file__, 'document-id')
_PROGRESS_BAR = generate_id(__file__, 'progress-bar')
_PROGRESS_BAR_WRAPPER = generate_id(__file__, 'progress-bar-wrapper')
_LOADER = generate_id(__file__, 'loader')
_DROPDOWN = generate_id(__file__, 'dropdown')
_OCR_OUTPUT = generate_id(__file__, 'ocr-output')


def _progress() -> Component:
    progress = dbc.Progress(value=5, id=_PROGRESS_BAR, striped=True, animated=True, style={'height': '25px'})
    return html.Div(progress, hidden=True, id=_PROGRESS_BAR_WRAPPER, className='mt-3 mb-3')


def _page() -> Component:
    return html.Div(
        [
            html.H1('Convertisseur'),
            upload_row(_UPLOAD, _DROPDOWN, load_sample_documents()),
            _progress(),
            dcc.Store(id=_DOCUMENT_ID),
            dcc.Store(id=_PROCESSING_DONE),
            dcc.Interval(id=_INTERVAL, interval=2000),
            html.Div('', id=_OCR_OUTPUT),
            html.Div(dbc.Spinner(html.Div(), id=_LOADER)),
        ]
    )


def _generate_document_id_and_save_document(content: Union[str, bytes]) -> str:
    document_id = Document.new().document_id
    save_document(content, document_id)
    return document_id


def _copy_and_generate_document(input_path: str) -> str:
    document_id = Document.new().document_id
    copy_pdf(input_path, document_id)
    return document_id


def _handle_uploaded_file(contents: str) -> str:
    _, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return _generate_document_id_and_save_document(decoded)


def _load_or_init_step(document_id: str) -> OCRProcessingStep:
    if has_processing_step(document_id):
        return load_processing_step(document_id)
    step = OCRProcessingStep('OCR en cours.', 0.05, False)
    dump_processing_step(step, document_id)
    return step


def _job_is_done(document_id: str) -> bool:
    return _load_or_init_step(document_id).done


def _add_callbacks(app: dash.Dash):
    @app.callback(
        Output(_DOCUMENT_ID, 'data'),
        Input(_UPLOAD, 'contents'),
        Input(_DROPDOWN, 'value'),
        prevent_initial_call=True,
    )
    def save_file(contents, dropdown_value) -> Optional[str]:
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == _UPLOAD:
            if contents:
                return _handle_uploaded_file(contents)
        elif trigger_id == _DROPDOWN:
            return _copy_and_generate_document(dropdown_value)
        raise ValueError(f'Unknown trigger {trigger_id}')

    def _filename_trigger(triggered: List[Dict[str, Any]]) -> bool:
        if len(triggered) == 0:
            raise ValueError(f'Expecting at least one trigger, got {len(triggered)}')
        return any([_DOCUMENT_ID in (trig.get('prop_id') or '') for trig in triggered])

    @app.callback(
        Output(_PROCESSING_DONE, 'data'),
        Output(_PROGRESS_BAR, 'children'),
        Output(_PROGRESS_BAR, 'value'),
        Output(_PROGRESS_BAR_WRAPPER, 'hidden'),
        Input(_INTERVAL, 'n_intervals'),
        Input(_DOCUMENT_ID, 'data'),
        State(_PROGRESS_BAR_WRAPPER, 'hidden'),
        prevent_initial_call=True,
    )
    def _process_file(_, filename, progress_is_hidden):
        ctx = dash.callback_context
        filename_trigger = _filename_trigger(ctx.triggered)
        if filename_trigger and progress_is_hidden:
            if not _job_is_done(filename):
                start_simple_ocr_process(filename)
            return dash.no_update, 'OCR en cours....', 5, False
        if not filename_trigger and not progress_is_hidden:
            step = _load_or_init_step(filename)
            if step.done:
                return filename, 'Done.', 100, True
            return dash.no_update, step.messsage, int(step.advancement * 100), False
        raise PreventUpdate

    @app.callback(
        Output(_LOADER, 'children'),
        Output(DOCUMENT_ID, 'data'),
        Output(_OCR_OUTPUT, 'children'),
        Input(_PROCESSING_DONE, 'data'),
    )
    def handle_new_pdf_filename(filename):
        if filename:
            try:
                return dcc.Location(id='redirect-to-pdf-result', pathname=f'{Endpoint.OUTPUT}'), filename, html.Div()
            except Exception:
                print(traceback.format_exc())
                return html.Div(), dash.no_update, dbc.Alert(traceback.format_exc(), color='danger')
        raise PreventUpdate


page: Page = (_page, _add_callbacks)
