import os
from configparser import ConfigParser

from pdf_ocr_app.utils import safely_replace_path_suffix

_CONFIG_FILE = safely_replace_path_suffix(__file__, 'tests/test_config.py', 'config.ini')
_CONFIG_TEMPLATE_FILE = safely_replace_path_suffix(__file__, 'tests/test_config.py', 'config_template.ini')


def test_files_existence():
    assert os.path.exists(_CONFIG_FILE)


def test_config_loads():
    from pdf_ocr_app.config import CONFIG


def assert_no_missing_parameter_in_template():
    config = ConfigParser()
    config.read(_CONFIG_FILE)
    config_template = ConfigParser()
    config_template.read(_CONFIG_TEMPLATE_FILE)
    for section in config.sections():
        for var in config[section]:
            assert var in config_template[section]


def test_config():
    if os.path.exists(_CONFIG_FILE):
        assert_no_missing_parameter_in_template()
