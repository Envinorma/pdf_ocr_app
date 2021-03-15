import os
from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Type, TypeVar

from pdf_ocr_app.utils import create_folder_if_inexistent


class _ConfigError(Exception):
    pass


def _get_var(section: str, varname: str) -> str:
    env_key = f'{section}_{varname}'
    if env_key in os.environ:
        return os.environ[env_key]
    config = load_config()
    try:
        res = config[section][varname]
    except KeyError:
        raise _ConfigError(f'Variable {varname} must either be defined in config.ini or in environment.')
    if not res:
        raise _ConfigError(f'Variable {varname} cannot be empty.')
    return res


def _key_to_class_name(key: str) -> str:
    return key[0].upper() + key[1:] + 'Config'


def _class_name_to_key(class_name: str) -> str:
    return class_name.split('Config')[0].lower()


T = TypeVar('T')


def _default_load(cls: Type[T]) -> T:
    name = _class_name_to_key(cls.__name__)
    kwargs = {key: _get_var(name, key) for key in cls.__dataclass_fields__}  # type: ignore
    return cls(**kwargs)  # type: ignore


@dataclass
class TesseractConfig:
    tessdata_location: str
    models_url_template: str
    lang: str

    @classmethod
    def default_load(cls) -> 'TesseractConfig':
        return _default_load(cls)


class EnvironmentType(Enum):
    PROD = 'prod'
    DEV = 'dev'


@dataclass
class EnvironmentConfig:
    type: str

    @classmethod
    def default_load(cls) -> 'EnvironmentConfig':
        res = _default_load(cls)
        values = {x.value for x in EnvironmentType}
        assert res.type in values, f'Unexpecting value {res.type} for environment.type (expecting value in {values})'
        return res


@dataclass
class StorageConfig:
    documents_folder: str

    @classmethod
    def default_load(cls) -> 'StorageConfig':
        return _default_load(cls)


@dataclass
class AppConfig:
    assets_folder: str

    @classmethod
    def default_load(cls) -> 'AppConfig':
        return _default_load(cls)


@dataclass
class Config:
    tesseract: TesseractConfig
    environment: EnvironmentConfig
    storage: StorageConfig
    app: AppConfig

    @classmethod
    def default_load(cls) -> 'Config':
        dict_ = {key: globals()[_key_to_class_name(key)].default_load() for key in cls.__dataclass_fields__}  # type: ignore
        return cls(**dict_)


@lru_cache
def load_config() -> ConfigParser:
    parser = ConfigParser()
    parser.read('config.ini')
    return parser


CONFIG = Config.default_load()


create_folder_if_inexistent(CONFIG.storage.documents_folder)
