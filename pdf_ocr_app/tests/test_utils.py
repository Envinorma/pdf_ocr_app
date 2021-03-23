from pdf_ocr_app.utils import safely_replace_path_suffix


def test_safely_replace_path_suffix():
    assert safely_replace_path_suffix('', '', '') == ''
    assert safely_replace_path_suffix('a/b/c', 'c', 'd') == 'a/b/d'
