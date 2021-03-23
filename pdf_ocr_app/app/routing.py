from enum import Enum
from typing import Any, Callable, Optional, Tuple

import dash
from werkzeug.routing import Map, MapAdapter, Rule


class Endpoint(Enum):
    PDF = 'pdf'
    OUTPUT = 'output'
    INDEX = 'index'
    TMP = 'tmp'

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


ROUTER: MapAdapter = Map(
    [
        Rule('/', endpoint=Endpoint.INDEX),
        Rule(f'/{Endpoint.PDF}', endpoint=Endpoint.PDF),
        Rule(f'/{Endpoint.TMP}', endpoint=Endpoint.TMP),
        Rule(f'/{Endpoint.OUTPUT}', endpoint=Endpoint.OUTPUT),
    ]
).bind('')

CallbacksAdder = Optional[Callable[[dash.Dash], None]]
Page = Tuple[Callable[..., Any], CallbacksAdder]
