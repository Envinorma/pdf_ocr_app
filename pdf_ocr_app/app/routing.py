from enum import Enum
from typing import Any, Callable, Optional, Tuple

import dash
from werkzeug.routing import Map, MapAdapter, Rule


class Endpoint(Enum):
    AP_IMAGE = 'ap_image'
    INDEX = 'index'
    TMP = 'tmp'

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


class APOperation(Enum):
    EDIT_PRESCRIPTIONS = 'edit_prescriptions'

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value


ROUTER: MapAdapter = Map(
    [
        Rule('/', endpoint=Endpoint.INDEX),
        Rule(f'/{Endpoint.AP_IMAGE}', endpoint=Endpoint.AP_IMAGE),
        Rule(f'/{Endpoint.TMP}', endpoint=Endpoint.TMP),
    ]
).bind('')

CallbacksAdder = Optional[Callable[[dash.Dash], None]]
Page = Tuple[Callable[..., Any], CallbacksAdder]
