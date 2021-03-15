import os
from typing import Dict, Optional
from urllib.parse import unquote

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.development.base_component import Component
from flask.helpers import send_file

from pdf_ocr_app.app.pages.output import page as output_page
from pdf_ocr_app.app.pages.parse import page as parse_page
from pdf_ocr_app.app.pages.temp_page import page as temp_page
from pdf_ocr_app.app.routing import ROUTER, Endpoint, Page
from pdf_ocr_app.config import CONFIG
from pdf_ocr_app.db import download_document
from pdf_ocr_app.utils import safely_replace_path_suffix

_TESSDATA_URL = CONFIG.tesseract.models_url_template.format(CONFIG.tesseract.lang)
_TESSDATA_PREFIX = CONFIG.tesseract.tessdata_location


def _suffix(text: str) -> str:
    return text.split('/')[-1]


def _download_tessdata_if_inexistent():
    filename = os.path.join(_TESSDATA_PREFIX, _suffix(_TESSDATA_URL))
    if not os.path.exists(filename):
        print(f'Downloading {_TESSDATA_URL} to {filename}')
        download_document(_TESSDATA_URL, filename)


_download_tessdata_if_inexistent()


def _header_link(content: str, href: str, target: Optional[str] = None) -> Component:
    style = {'color': 'grey', 'display': 'inline-block'}
    return html.Span(html.A(content, href=href, className='nav-link', style=style, target=target))


def _get_nav() -> Component:
    nav = html.Span(
        [_header_link('Parse document', href=f'/{Endpoint.PDF}')],
        style={'display': 'inline-block'},
    )
    return nav


def _get_page_heading() -> Component:
    src = f'/assets/logo-envinorma.png'
    sticky_style = {
        'padding': '.2em',
        'border-bottom': '1px solid rgba(0,0,0,.1)',
        'position': 'sticky',
        'top': 0,
        'background-color': '#fff',
        'z-index': '10',
        'margin-bottom': '10px',
    }
    img = html.Img(src=src, style={'width': '30px', 'display': 'inline-block'})
    return html.Div(html.Div([dcc.Link(img, href='/'), _get_nav()], className='container'), style=sticky_style)


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        safely_replace_path_suffix(__file__, 'pdf_ocr_app/app/__init__.py', 'assets/style.css'),
    ],
    suppress_callback_exceptions=True,
    title='PDF parsing',
    update_title=None,
)


app.layout = html.Div(
    [dcc.Location(id='url', refresh=False), _get_page_heading(), html.Div(id='page-content', className='container')],
    id='layout',
)


def _index_layout() -> Component:
    return html.Div()


_ENDPOINT_TO_PAGE: Dict[Endpoint, Page] = {
    Endpoint.INDEX: (_index_layout, None),
    Endpoint.PDF: parse_page,
    Endpoint.OUTPUT: output_page,
    Endpoint.TMP: temp_page,
}


def _route(pathname: str) -> Component:
    endpoint, kwargs = ROUTER.match(pathname)
    return _ENDPOINT_TO_PAGE[endpoint][0](**kwargs)


@app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
def display_page(pathname: str):
    return _route(pathname)


@app.server.route('/download/<path:path>')
def _download(path: str):
    return send_file(unquote(path), as_attachment=True)


for _, _add_callbacks in _ENDPOINT_TO_PAGE.values():
    if _add_callbacks:
        _add_callbacks(app)

APP = app.server  # for gunicorn deployment

if __name__ == '__main__':
    app.run_server(debug=True)
