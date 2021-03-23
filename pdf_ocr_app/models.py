from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Cell:
    content: str
    colspan: int = 1
    rowspan: int = 1

    @classmethod
    def from_dict(cls, dict_: Dict) -> 'Cell':
        dict_ = dict_.copy()
        return cls(**dict_)


@dataclass
class Row:
    cells: List[Cell]
    is_header: bool
    text_in_inspection_sheet: Optional[str] = None

    @classmethod
    def from_dict(cls, dict_: Dict) -> 'Row':
        dict_ = dict_.copy()
        dict_['cells'] = [Cell.from_dict(cell) for cell in dict_['cells']]
        return cls(**dict_)


@dataclass
class Table:
    rows: List[Row]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dict_: Dict) -> 'Table':
        return cls([Row.from_dict(row) for row in dict_['rows']])
