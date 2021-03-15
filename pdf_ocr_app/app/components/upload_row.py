from typing import Any, Dict, List

import dash_core_components as dcc
import dash_html_components as html
from dash.development.base_component import Component


def _upload_component(id_: str) -> Component:
    style = {
        'width': '100%',
        'height': '35px',
        'lineHeight': '35px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin-bottom': '10px',
        'cursor': 'pointer',
    }
    return dcc.Upload(id=id_, children=html.Div(['Drag and drop or select file']), style=style, multiple=False)


def _options(options: List[str]) -> List[Dict[str, Any]]:
    return [{'value': file_, 'label': file_} for file_ in options]


def _dropdown(options: List[str], dropdown_id: str) -> Component:
    return dcc.Dropdown(options=_options(options), id=dropdown_id)


def _card(content: Component, title: str) -> Component:
    return html.Div(
        html.Div([html.H5(title, className='card-title'), content], className='card-body'), className='card'
    )


def upload_row(upload_id: str, dropdown_id: str, dropdown_options: List[str]) -> Component:
    col1 = html.Div([html.P('Upload document'), _upload_component(upload_id)])
    col2 = html.Div([html.P('Or choose a sample document'), _dropdown(dropdown_options, dropdown_id)])
    cols = [html.Div(col1, className='col-6'), html.Div(col2, className='col-6')]
    return _card(html.Div(cols, className='row'), 'Choose file')
