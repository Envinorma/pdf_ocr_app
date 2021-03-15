from typing import Any, Dict, List, Optional

import alto
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.development.base_component import Component

from pdf_ocr_app.app.alto_to_html import (
    alto_page_to_grouped_lines,
    alto_page_to_grouped_paragraphs,
    alto_page_to_html,
    alto_pages_to_paragraphs,
)
from pdf_ocr_app.app.routing import Page
from pdf_ocr_app.app.utils import generate_id
from pdf_ocr_app.db import load_alto_pages

_OCR_OUTPUT = generate_id(__file__, 'ocr-output')


def _page(document_id: str) -> Component:
    return html.Div(
        [
            html.H1('PDF'),
            html.Div(_load_and_display_alto(document_id), id=_OCR_OUTPUT),
        ]
    )


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
            dbc.Tab(_top_margin(_word_confidence_tab(pages)), label='Output 1'),
            dbc.Tab(_top_margin(_groups_tab(pages)), label='Output 2'),
            dbc.Tab(_top_margin(_grouped_by_lines(pages)), label='Regroupement par lignes'),
            dbc.Tab(_top_margin(_grouped_by_paragraphs(pages)), label='Regroupement par paragraphes'),
            dbc.Tab(_top_margin(_raw_text(pages)), label='Texte extrait'),
        ],
        style={'margin-top': '5px'},
    )


def _load_and_display_alto(document_id: str) -> Component:
    pages = load_alto_pages(document_id)
    children = []
    children.append(_tabs(pages))
    return html.Div(children)


def _add_callbacks(app: dash.Dash):
    pass


page: Page = (_page, _add_callbacks)
