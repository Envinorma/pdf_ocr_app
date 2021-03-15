from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class OCRProcessingStep:
    messsage: Optional[str]
    advancement: float
    done: bool

    def __post_init__(self) -> None:
        assert 0 <= self.advancement <= 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]) -> 'OCRProcessingStep':
        return cls(**dict_)
