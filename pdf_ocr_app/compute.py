import random
import string
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


def _generate_id() -> str:
    return ''.join([random.choice(string.ascii_letters) for _ in range(12)])


@dataclass
class Document:
    document_id: str
    ocr_processing_step: OCRProcessingStep

    @classmethod
    def new(cls) -> 'Document':
        return cls(document_id=_generate_id(), ocr_processing_step=OCRProcessingStep(None, 0, False))
