from configparser import ConfigParser

from pdf_ocr_app.config import Config
from pdf_ocr_app.utils import safely_replace_path_suffix

_CONFIG_TEMPLATE_FILE = safely_replace_path_suffix(__file__, 'pdf_ocr_app/tests/test_config.py', 'config_template.ini')


def test_config_loads():
    from pdf_ocr_app.config import CONFIG  # noqa: F401


def assert_no_missing_parameter_in_template():
    config_template = ConfigParser()
    config_template.read(_CONFIG_TEMPLATE_FILE)
    for section_name, class_ in Config.__dataclass_fields__.items():
        for var in class_.type.__dataclass_fields__:
            assert var in config_template[section_name]


def test_config():
    assert_no_missing_parameter_in_template()
