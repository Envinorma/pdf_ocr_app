import os
from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Type, TypeVar


class _ConfigError(Exception):
    pass


def _get_var(section: str, varname: str) -> str:
    env_key = f'{section}_{varname}'
    if env_key in os.environ:
        return os.environ[env_key]
    config = load_config()
    try:
        return config[section][varname]
    except KeyError:
        raise _ConfigError(f'Variable {varname} must either be defined in config.ini or in environment.')


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
    tessdata: str

    @classmethod
    def default_load(cls) -> 'TesseractConfig':
        return _default_load(cls)


class EnvironmentType(Enum):
    PROD = 'prod'
    DEV = 'dev'


@dataclass
class EnvironmentConfig:
    type: EnvironmentType

    @classmethod
    def default_load(cls) -> 'EnvironmentConfig':
        return _default_load(cls)


@dataclass
class Config:
    tesseract: TesseractConfig
    environment: EnvironmentConfig

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
