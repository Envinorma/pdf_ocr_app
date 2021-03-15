from typing import List

import pytest

from pdf_ocr_app.compute.table_extraction import (
    Contour,
    DetectedCell,
    LocatedTable,
    _are_close,
    _are_neighbor,
    _build_groups,
    _build_table,
    _extract_col_rank,
    _extract_colspan,
    _extract_row_rank,
    _extract_rowspan,
    _find_fuzzy_rank,
    _get_highest_ascendant,
    _group_ints,
    _left_line,
    _lines_are_neighbor,
    _lower_line,
    _mean,
    _revert_dict,
    _right_line,
    _upper_line,
    group_by_proximity,
)
from pdf_ocr_app.models import Cell, Row, Table


def test_lines_are_neighbor():
    assert _lines_are_neighbor((0, 100, 1), (0, 100, 1))
    assert _lines_are_neighbor((0, 100, 1), (0, 100, 0))
    assert _lines_are_neighbor((0, 100, 1), (0, 100, -1))
    assert _lines_are_neighbor((0, 100, 1), (0, 101, -1))
    assert _lines_are_neighbor((1, 100, 1), (0, 101, -1))
    assert _lines_are_neighbor((-1, 100, 1), (0, 101, -1))
    assert _lines_are_neighbor((0, 100, 5), (40, 60, 2))
    assert not _lines_are_neighbor((-1, 100, 10), (0, 101, -1))
    assert not _lines_are_neighbor((0, 100, 10), (0, 100, -1))
    assert not _lines_are_neighbor((0, 100, 100), (103, 200, 103))


def test_left_line():
    assert _left_line(Contour(100, 200, 0, 100)) == (0, 100, 100)


def test_right_line():
    assert _right_line(Contour(100, 200, 0, 100)) == (0, 100, 200)


def test_upper_line():
    assert _upper_line(Contour(100, 200, 0, 100)) == (100, 200, 100)


def test_lower_line():
    assert _lower_line(Contour(100, 200, 0, 100)) == (100, 200, 0)


def test_are_neighbor():
    contour_1 = Contour(0, 100, 0, 100)
    contour_2 = Contour(100, 200, 0, 100)
    assert _are_neighbor(DetectedCell('', contour_1), DetectedCell('', contour_2))
    contour_1 = Contour(0, 100, 0, 100)
    contour_2 = Contour(102, 200, 0, 100)
    assert _are_neighbor(DetectedCell('', contour_1), DetectedCell('', contour_2))
    contour_1 = Contour(0, 100, 0, 100)
    contour_2 = Contour(102, 200, 0, 400)
    assert _are_neighbor(DetectedCell('', contour_1), DetectedCell('', contour_2))
    contour_1 = Contour(0, 100, 0, 400)
    contour_2 = Contour(102, 200, -2, 100)
    assert _are_neighbor(DetectedCell('', contour_1), DetectedCell('', contour_2))
    contour_1 = Contour(0, 100, 0, 400)
    contour_2 = Contour(1, 99, 401, 700)
    assert _are_neighbor(DetectedCell('', contour_1), DetectedCell('', contour_2))
    contour_1 = Contour(0, 100, 0, 100)
    contour_2 = Contour(200, 300, 0, 100)
    assert not _are_neighbor(DetectedCell('', contour_1), DetectedCell('', contour_2))
    contour_1 = Contour(0, 100, 0, 100)
    contour_2 = Contour(103, 200, 103, 200)
    assert not _are_neighbor(DetectedCell('', contour_1), DetectedCell('', contour_2))
    contour_1 = Contour(0, 100, 0, 100)
    contour_2 = Contour(0, 100, 200, 300)
    assert not _are_neighbor(DetectedCell('', contour_1), DetectedCell('', contour_2))
    cell_1 = DetectedCell(text='', contour=Contour(x_0=259, x_1=373, y_0=1586, y_1=1631))
    cell_2 = DetectedCell(text='', contour=Contour(x_0=259, x_1=373, y_0=1519, y_1=1581))
    assert _are_neighbor(cell_1, cell_2)


def test_get_highest_ascendant():
    assert _get_highest_ascendant(1, {0: 0, 1: 2, 2: 3, 3: 0}) == 0
    assert _get_highest_ascendant(1, {0: 0, 1: 2, 2: 3, 3: 3}) == 3
    assert _get_highest_ascendant(1, {0: 0, 1: 1, 2: 3, 3: 3}) == 1
    assert _get_highest_ascendant(1, {0: 0, 1: 0, 2: 3, 3: 3}) == 0


def test_revert_dict():
    assert _revert_dict({1: 1, 2: 1, 3: 3}) == {1: [1, 2], 3: [3]}
    assert _revert_dict({}) == {}
    assert _revert_dict({1: 1, 2: 2}) == {1: [1], 2: [2]}
    assert _revert_dict({1: 1, 2: 1, 3: 1}) == {1: [1, 2, 3]}


def test_build_groups():
    assert _build_groups({0: 1, 1: 1, 2: 1}) == [[0, 1, 2]]
    assert _build_groups({0: 1, 1: 1, 2: 2}) == [[0, 1], [2]]
    assert _build_groups({0: 1, 1: 1, 2: 0}) == [[0, 1, 2]]
    assert _build_groups({0: 0, 1: 1, 2: 2, 3: 3}) == [[0], [1], [2], [3]]


def _sort(list_: List[List[int]]) -> List[List[int]]:
    return list(sorted([sorted(x) for x in list_], key=lambda x: min(x)))


def test_group_by_proximity():
    res = group_by_proximity([0, 1, 2, 3, 4, 5, 6, 100, 200, 1000, 1001, 1002], _are_close)
    assert res == [[0, 1, 2, 3, 4, 5, 6], [100], [200], [1000, 1001, 1002]]

    res = group_by_proximity([0, 2, 3, 100, 1001, 6, 1000, 4, 1, 5, 1002, 200], _are_close)
    assert _sort(res) == _sort([[0, 1, 2, 3, 4, 5, 6], [100], [200], [1000, 1001, 1002]])

    res = group_by_proximity([5, 0, 200, 1001, 6, 100, 1002, 1000, 1, 2, 4, 3], _are_close)
    assert _sort(res) == _sort([[0, 1, 2, 3, 4, 5, 6], [100], [200], [1000, 1001, 1002]])

    res = group_by_proximity([0, 0, 0, 0], _are_close)
    assert res == [[0, 0, 0, 0]]

    # all ints are neighbors -> one cluster
    assert group_by_proximity(list(range(50)), _are_close) == [list(range(50))]

    # no ints are neighbors -> 50 clusters
    assert group_by_proximity([x * 100 for x in range(50)], _are_close) == [[x * 100] for x in range(50)]


def test_mean():
    assert _mean([1, 2, 3]) == 2
    assert _mean([1, 5, 11]) == 5
    assert _mean([2, 10] * 100) == 6


def test_group_ints():
    assert _group_ints([0, 1, 2, 3, 4, 5, 6, 100, 200, 1000, 1001, 1002]) == [3, 100, 200, 1001]
    assert _group_ints(list(range(51))) == [25]
    assert _group_ints([x * 100 for x in range(50)]) == [x * 100 for x in range(50)]


def test_find_fuzzy_rank():
    assert _find_fuzzy_rank(100, [0, 100, 200, 400]) == 1
    assert _find_fuzzy_rank(100, [0, 101, 200, 400]) == 1
    assert _find_fuzzy_rank(100, [0, 99, 200, 400]) == 1
    assert _find_fuzzy_rank(100, [101]) == 0
    with pytest.raises(ValueError):
        _find_fuzzy_rank(100, [])
        _find_fuzzy_rank(100, [1000])


def test_extract_row_rank():
    assert _extract_row_rank(Contour(100, 300, 0, 100), [0, 100, 200, 300]) == 0
    assert _extract_row_rank(Contour(100, 200, 0, 100), [0, 100, 200, 300]) == 0
    assert _extract_row_rank(Contour(100, 200, 100, 301), [0, 100, 200, 300]) == 1


def test_extract_col_rank():
    assert _extract_col_rank(Contour(100, 300, 0, 100), [0, 100, 201, 303, 400]) == 1
    assert _extract_col_rank(Contour(100, 200, 0, 100), [0, 100, 201, 303, 400]) == 1
    assert _extract_col_rank(Contour(100, 200, 100, 301), [0, 100, 201, 303, 400]) == 1


def test_extract_colspan():
    assert _extract_colspan(Contour(100, 300, 0, 100), [0, 100, 201, 303, 400]) == 2
    assert _extract_colspan(Contour(100, 200, 0, 100), [0, 100, 201, 303, 400]) == 1
    assert _extract_colspan(Contour(100, 200, 100, 301), [0, 100, 201, 303, 400]) == 1


def test_extract_rowspan():
    assert _extract_rowspan(Contour(100, 300, 0, 100), [0, 100, 200, 300]) == 1
    assert _extract_rowspan(Contour(100, 200, 0, 100), [0, 100, 200, 300]) == 1
    assert _extract_rowspan(Contour(100, 200, 100, 301), [0, 100, 200, 300]) == 2


def test_build_table():
    cell = Cell('a', 1, 1)
    row = Row([cell], False)
    assert _build_table([DetectedCell('a', Contour(100, 200, 0, 100))]).table == Table([row])

    cells = [
        DetectedCell('a', Contour(0, 100, 0, 100)),
        DetectedCell('b', Contour(0, 100, 100, 200)),
        DetectedCell('c', Contour(100, 200, 0, 100)),
        DetectedCell('d', Contour(100, 200, 100, 200)),
    ]
    rows = [
        Row([Cell('a', 1, 1), Cell('c', 1, 1)], False),
        Row([Cell('b', 1, 1), Cell('d', 1, 1)], False),
    ]
    assert _build_table(cells) == LocatedTable(Table(rows), 0, 0, 200, 200)

    cells = [
        DetectedCell('a', Contour(0, 101, 0, 100)),
        DetectedCell('b', Contour(0, 99, 100, 200)),
        DetectedCell('c', Contour(100, 200, 3, 100)),
        DetectedCell('d', Contour(100, 200, 101, 200)),
    ]
    rows = [
        Row([Cell('a', 1, 1), Cell('c', 1, 1)], False),
        Row([Cell('b', 1, 1), Cell('d', 1, 1)], False),
    ]
    assert _build_table(cells).table == Table(rows)

    cells = [
        DetectedCell('a', Contour(0, 101, 0, 100)),
        DetectedCell('b', Contour(0, 199, 100, 200)),
        DetectedCell('c', Contour(100, 200, 3, 100)),
    ]
    rows = [
        Row([Cell('a', 1, 1), Cell('c', 1, 1)], False),
        Row([Cell('b', 2, 1)], False),
    ]
    assert _build_table(cells).table == Table(rows)


def test_group_cells_2():
    res = [
        DetectedCell(text='55 000\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=2124, y_1=2169)),
        DetectedCell(text='17\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=2124, y_1=2169)),
        DetectedCell(text='L80 -250 rejet ventilateur\n\x0c', contour=Contour(x_0=377, x_1=865, y_0=2124, y_1=2169)),
        DetectedCell(text='55 000\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=2074, y_1=2120)),
        DetectedCell(text='17\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=2074, y_1=2120)),
        DetectedCell(text='\x0c', contour=Contour(x_0=869, x_1=871, y_0=2074, y_1=2120)),
        DetectedCell(text='L80 —150 rejet ventilateur\n\x0c', contour=Contour(x_0=377, x_1=865, y_0=2074, y_1=2120)),
        DetectedCell(text='Dith8\n\nDith 9\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=2074, y_1=2169)),
        DetectedCell(text='L80\n\x0c', contour=Contour(x_0=97, x_1=254, y_0=2074, y_1=2169)),
        DetectedCell(text='1 400\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=1976, y_1=2070)),
        DetectedCell(text='25\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=1976, y_1=2070)),
        DetectedCell(
            text='Poussières de Dithane\n+\nHS et CS,\n\x0c', contour=Contour(x_0=869, x_1=1180, y_0=1976, y_1=2070)
        ),
        DetectedCell(text='Rejets ventilateur\n\x0c', contour=Contour(x_0=377, x_1=865, y_0=1976, y_1=2070)),
        DetectedCell(text='Dith 7\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=1976, y_1=2070)),
        DetectedCell(text='11 000\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=1877, y_1=1971)),
        DetectedCell(text='35\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=1877, y_1=1971)),
        DetectedCell(
            text='Poussières de Dithane\n+\n\nHS et CS,\n\x0c', contour=Contour(x_0=869, x_1=1180, y_0=1877, y_1=1971)
        ),
        DetectedCell(
            text='Rejets communs atomiseur et lit fixe après\ndernier lavage fluidisé\n\x0c',
            contour=Contour(x_0=377, x_1=865, y_0=1877, y_1=1971),
        ),
        DetectedCell(text='Dith 6\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=1877, y_1=1971)),
        DetectedCell(text='L38\n\nPilote DG\n\x0c', contour=Contour(x_0=97, x_1=254, y_0=1877, y_1=2070)),
        DetectedCell(text='21 000\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=1771, y_1=1872)),
        DetectedCell(text='27\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=1771, y_1=1872)),
        DetectedCell(
            text='Poussières de Dithane\n+\nHS et CS;\n\x0c', contour=Contour(x_0=869, x_1=1180, y_0=1771, y_1=1872)
        ),
        DetectedCell(text='Rejets atomiseur et scrubber\n\x0c', contour=Contour(x_0=377, x_1=865, y_0=1771, y_1=1872)),
        DetectedCell(text='DithS\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=1771, y_1=1872)),
        DetectedCell(text='7000\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=1734, y_1=1767)),
        DetectedCell(text='36\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=1734, y_1=1767)),
        DetectedCell(text='HS et CS,\n\x0c', contour=Contour(x_0=869, x_1=1180, y_0=1734, y_1=1767)),
        DetectedCell(text='Rejets cheminée Convex\n\x0c', contour=Contour(x_0=377, x_1=865, y_0=1734, y_1=1767)),
        DetectedCell(text='Dith 4\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=1734, y_1=1767)),
        DetectedCell(text='L25\n\x0c', contour=Contour(x_0=97, x_1=254, y_0=1734, y_1=1872)),
        DetectedCell(text='25 000\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=1635, y_1=1730)),
        DetectedCell(text='27\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=1635, y_1=1730)),
        DetectedCell(
            text='Poussières de Dithane\n+\nHS et CS,\n\x0c', contour=Contour(x_0=869, x_1=1180, y_0=1635, y_1=1730)
        ),
        DetectedCell(text='Rejets atomiseur et scrubber\n\x0c', contour=Contour(x_0=377, x_1=865, y_0=1635, y_1=1730)),
        DetectedCell(text='Dith 3\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=1635, y_1=1730)),
        DetectedCell(text='7700\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=1586, y_1=1631)),
        DetectedCell(text='36\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=1586, y_1=1631)),
        DetectedCell(text='HS et CS,\n\x0c', contour=Contour(x_0=869, x_1=1180, y_0=1586, y_1=1631)),
        DetectedCell(
            text='Rejets après traitement bioway\n\x0c', contour=Contour(x_0=377, x_1=865, y_0=1586, y_1=1631)
        ),
        DetectedCell(text='Dith2\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=1586, y_1=1631)),
        DetectedCell(text='L11\n\x0c', contour=Contour(x_0=97, x_1=254, y_0=1586, y_1=1730)),
        DetectedCell(text='17 500\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=1519, y_1=1581)),
        DetectedCell(text='26.5\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=1519, y_1=1581)),
        DetectedCell(text='so,\n\x0c', contour=Contour(x_0=869, x_1=1180, y_0=1519, y_1=1581)),
        DetectedCell(
            text='Rejets sortie laveur des effluents des cuves\nde sulfitation\n\x0c',
            contour=Contour(x_0=377, x_1=865, y_0=1519, y_1=1581),
        ),
        DetectedCell(text='Dith 1\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=1519, y_1=1581)),
        DetectedCell(text='L10\n\x0c', contour=Contour(x_0=97, x_1=254, y_0=1519, y_1=1581)),
        DetectedCell(text='DEBIT\nm°/h\n\x0c', contour=Contour(x_0=1342, x_1=1534, y_0=1453, y_1=1515)),
        DetectedCell(text='HAUTEUR\nmètres\n\x0c', contour=Contour(x_0=1184, x_1=1337, y_0=1453, y_1=1515)),
        DetectedCell(text='COMPOSES\n\x0c', contour=Contour(x_0=869, x_1=1180, y_0=1453, y_1=1515)),
        DetectedCell(text='CHEMINEES D’EMISSION\n\x0c', contour=Contour(x_0=377, x_1=865, y_0=1453, y_1=1515)),
        DetectedCell(text='Rp.\nusine\n\x0c', contour=Contour(x_0=259, x_1=373, y_0=1453, y_1=1515)),
        DetectedCell(text='BATIMENT\n\x0c', contour=Contour(x_0=97, x_1=254, y_0=1453, y_1=1515)),
        DetectedCell(
            text='L10,L11,L12,\nL25, L 31,L38,\nL80\n\x0c', contour=Contour(x_0=1322, x_1=1534, y_0=1008, y_1=1165)
        ),
        DetectedCell(
            text='150 t/j de Manèbe et\nMancozèbe (2200 t\nprésentes)\n\x0c',
            contour=Contour(x_0=1066, x_1=1317, y_0=1008, y_1=1165),
        ),
        DetectedCell(text='AS\n\n4 km\n\x0c', contour=Contour(x_0=909, x_1=1061, y_0=1008, y_1=1165)),
        DetectedCell(
            text='Fabrication industrielle de telles substances\n\x0c',
            contour=Contour(x_0=279, x_1=904, y_0=1008, y_1=1165),
        ),
        DetectedCell(text='AS\n\n3 km\n\x0c', contour=Contour(x_0=909, x_1=1061, y_0=829, y_1=1002)),
        DetectedCell(
            text="Stockage et emploi de Substances ou préparations\ndangereuses pour l'environnement - À -, très toxiques pour\nles organismes aquatiques, telles que définies à la rubrique\n1000, à l'exclusion de celles visées nominativement ou par\nfamille par d'autres rubriques\n\x0c",
            contour=Contour(x_0=279, x_1=904, y_0=829, y_1=1002),
        ),
        DetectedCell(text='\x0c', contour=Contour(x_0=1322, x_1=1534, y_0=242, y_1=680)),
        DetectedCell(
            text='Annexe 1.5:\n\nPuissance totale de 7\nMW\n\x0c', contour=Contour(x_0=1066, x_1=1317, y_0=242, y_1=680)
        ),
        DetectedCell(text='\x0c', contour=Contour(x_0=909, x_1=1061, y_0=242, y_1=680)),
        DetectedCell(
            text='Combustion à l’exclusion des installations visées par les\nrubriques 167C et 322 B4.\n\nLa puissance thermique maximale est définie comme la\nquantité maximale de combustible, exprimée en PCI,\nsusceptible d’être consommée par seconde.\n\nA) Lorsque l’installation consomme exclusivement, seuls\nou en mélange du gaz naturel, des gaz de pétrole liquéfiés,\ndu fioul domestique, du charbon, des fiouls lourds ou la\nbiomasse, à l’exclusion des installations visées par d’autres\nrubriques de la nomenclature pour lesquelles la combustion\nparticipe à la fusion, la cuisson ou au traitement, en\nmélange avec les gaz de combustion, des matières entrantes,\nsi la puissance thermique maximale de l’installation est :\n\n2. — supérieure à 2 MW, mais inférieure à 20 MW\n\x0c',
            contour=Contour(x_0=279, x_1=904, y_0=242, y_1=680),
        ),
    ]
    groups = group_by_proximity(res, _are_neighbor)
    for cell in res:
        for group in groups:
            if cell in group:
                continue
            for other_cell in group:
                assert not _are_neighbor(cell, other_cell)
