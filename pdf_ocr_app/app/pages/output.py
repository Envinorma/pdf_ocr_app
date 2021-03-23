from typing import List

import alto
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate
from flask.helpers import send_file

from pdf_ocr_app.app.alto_to_html import (
    alto_page_to_grouped_lines,
    alto_page_to_grouped_paragraphs,
    alto_page_to_html,
    alto_pages_to_paragraphs,
)
from pdf_ocr_app.app.common_ids import DOCUMENT_ID
from pdf_ocr_app.app.routing import Page
from pdf_ocr_app.app.utils import generate_id
from pdf_ocr_app.db import load_alto_pages, svg_path

_OCR_OUTPUT = generate_id(__file__, 'ocr-output')


def _explain_word_confidence() -> Component:
    return html.P('L\'intensité de surlignage des mots est inversement proportionnelle à la confiance de détection.')


def _word_confidence_tab(pages: List[alto.Page]) -> Component:
    return html.Div(
        [_explain_word_confidence(), *[html.Div(alto_page_to_html(page, False), className='mb-3') for page in pages]]
    )


def _explain_grouping() -> Component:
    return html.P(
        'Les lignes sont surlignées en bleu, les textes (groupes de lig'
        'nes) en vert et les blocs composés (groupes de textes) en rouge.'
    )


def _groups_tab(pages: List[alto.Page]) -> Component:
    return html.Div(
        [_explain_grouping()] + [html.Div(alto_page_to_html(page, True), className='mb-3') for page in pages]
    )


def _grouped_by_lines(pages: List[alto.Page]) -> Component:
    return html.Div([html.Div(alto_page_to_grouped_lines(page), className='mb-3') for page in pages])


def _grouped_by_paragraphs(pages: List[alto.Page]) -> Component:
    return html.Div([html.Div(alto_page_to_grouped_paragraphs(page), className='mb-3') for page in pages])


def _raw_text(pages: List[alto.Page]) -> Component:
    return alto_pages_to_paragraphs(pages)


def _top_margin(component: Component) -> Component:
    return html.Div(component, style={'margin-top': '15px'})


def _tabs(pages: List[alto.Page]) -> Component:
    return dbc.Tabs(
        [
            dbc.Tab(_top_margin(_word_confidence_tab(pages)), label='Mots détectés'),
            dbc.Tab(_top_margin(_groups_tab(pages)), label='Mots et groupes détectés'),
            dbc.Tab(_top_margin(_grouped_by_lines(pages)), label='Regroupement par lignes'),
            dbc.Tab(_top_margin(_grouped_by_paragraphs(pages)), label='Regroupement par paragraphes'),
            dbc.Tab(_top_margin(_raw_text(pages)), label='Texte extrait'),
        ],
        style={'margin-top': '5px'},
    )


def _buttons(document_id: str) -> Component:
    button = html.Button('Télécharger au format SVG', className='btn btn-link')
    return html.A(button, href=f'/download_svg/{document_id}')


def _load_and_display_alto(document_id: str) -> Component:
    pages = load_alto_pages(document_id)
    children = []
    children.append(_buttons(document_id))
    children.append(_tabs(pages))
    return html.Div(children)


def _add_callbacks(app: dash.Dash):
    @app.callback(Output(_OCR_OUTPUT, 'children'), Input(DOCUMENT_ID, 'data'))
    def load_result(document_id: str) -> Component:
        if not document_id:
            raise PreventUpdate
        return _load_and_display_alto(document_id)

    @app.server.route('/download_svg/<document_id>')
    def _download(document_id: str):
        return send_file(svg_path(document_id), as_attachment=True)


def _page() -> Component:
    return html.Div([html.H1('PDF'), html.Div(id=_OCR_OUTPUT)])


page: Page = (_page, _add_callbacks)
