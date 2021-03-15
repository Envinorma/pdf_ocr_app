from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Tuple, TypeVar, Union

import cv2
import numpy as np
import pytesseract
from tqdm import tqdm

from pdf_ocr_app.models import Cell, Row, Table


def _invert_image(img: np.ndarray) -> np.ndarray:
    _, img_bin = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)  # | cv2.THRESH_OTSU)
    img_bin = 255 - img_bin
    return img_bin


@dataclass(unsafe_hash=True)
class Contour:
    x_0: int
    x_1: int
    y_0: int
    y_1: int

    def __post_init__(self):
        if self.x_0 > self.x_1 + 1:
            raise ValueError(f'{self} is not correct')
        if self.y_0 > self.y_1 + 1:
            raise ValueError(f'{self} is not correct')


def _build_contour(contour) -> Contour:
    x, y, w, h = cv2.boundingRect(contour)
    return Contour(x, x + w, y, y + h)


def _get_vertical_lines(img: np.ndarray):
    kernel_len = np.array(img).shape[0] // 300
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
    image_1 = cv2.erode(img, ver_kernel, iterations=3)
    return cv2.dilate(image_1, ver_kernel, iterations=3)


def _get_horizontal_lines(img: np.ndarray):
    kernel_len = np.array(img).shape[1] // 300
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    image_2 = cv2.erode(img, hor_kernel, iterations=3)
    return cv2.dilate(image_2, hor_kernel, iterations=3)


def _is_empty(contour: Contour) -> bool:
    return (
        abs(contour.x_0 - contour.x_1) <= 4 * _PROXIMITY_THRESHOLD
        or abs(contour.y_0 - contour.y_1) <= 4 * _PROXIMITY_THRESHOLD
    )


def _extract_contours(img: np.ndarray) -> List[Contour]:
    img_bin = _invert_image(img)
    img_vh = cv2.addWeighted(_get_vertical_lines(img_bin), 0.5, _get_horizontal_lines(img_bin), 0.5, 0.0)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    img_vh_2 = cv2.erode(~img_vh, kernel, iterations=2)
    _, img_vh_3 = cv2.threshold(img_vh_2, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(img_vh_3, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # img_debug = cv2.drawContours(img.copy(), contours, -1, (0, 0, 0), 4)
    # concat = cv2.vconcat([img, img_bin, img_vh, img_vh_2, img_vh_3, img_debug])
    # cv2.imwrite('test3.png', concat)
    built_contours = [_build_contour(contour) for contour in contours if len(contour) == 4]
    return [ct for ct in built_contours if not _is_empty(ct) and not _is_full_page(ct, img)]


@dataclass(unsafe_hash=True)
class DetectedCell:
    text: str
    contour: Contour


def _str(text: Union[str, bytes]) -> str:
    if isinstance(text, bytes):
        return text.decode()
    return text


def _extract_string(img, contour: Contour) -> str:
    try:
        return _str(pytesseract.image_to_string(img[contour.y_0 : contour.y_1, contour.x_0 : contour.x_1], lang='fra'))
    except:
        print(contour)
        print(img.shape)
        raise


def _area(contour: Contour) -> float:
    return (contour.x_1 - contour.x_0) * (contour.y_1 - contour.y_0)


def _image_area(img: np.ndarray) -> float:
    assert len(img.shape) == 2
    return img.shape[0] * img.shape[1]


def _is_full_page(contour: Contour, img: np.ndarray) -> bool:
    return (_area(contour) / _image_area(img)) >= 0.95


def _extract_cells(img: np.ndarray) -> List[DetectedCell]:
    contours = _extract_contours(img)
    strings = [_extract_string(img, ct) for ct in tqdm(contours, leave=False, desc='Parsing table cells.')]
    return [DetectedCell(text, contour) for text, contour in list(zip(strings, contours))]


_PROXIMITY_THRESHOLD = 10


def _lines_are_neighbor(line: Tuple[int, int, int], line_: Tuple[int, int, int]) -> bool:
    x_0, x_1, y = line
    x_0_, x_1_, y_ = line_
    if abs(y - y_) >= _PROXIMITY_THRESHOLD:
        return False
    return any(
        [
            x_0 - 1 <= x_0_ <= x_1 + 1,
            x_0 - 1 <= x_1_ <= x_1 + 1,
            x_0_ - 1 <= x_0 <= x_1_ + 1,
            x_0_ - 1 <= x_1 <= x_1_ + 1,
        ]
    )


def _left_line(contour: Contour) -> Tuple[int, int, int]:
    return (contour.y_0, contour.y_1, contour.x_0)


def _right_line(contour: Contour) -> Tuple[int, int, int]:
    return (contour.y_0, contour.y_1, contour.x_1)


def _upper_line(contour: Contour) -> Tuple[int, int, int]:
    return (contour.x_0, contour.x_1, contour.y_1)


def _lower_line(contour: Contour) -> Tuple[int, int, int]:
    return (contour.x_0, contour.x_1, contour.y_0)


def _are_neighbor(cell: DetectedCell, cell_: DetectedCell) -> bool:
    return any(
        [
            _lines_are_neighbor(_left_line(cell.contour), _right_line(cell_.contour)),
            _lines_are_neighbor(_left_line(cell_.contour), _right_line(cell.contour)),
            _lines_are_neighbor(_upper_line(cell.contour), _lower_line(cell_.contour)),
            _lines_are_neighbor(_upper_line(cell_.contour), _lower_line(cell.contour)),
        ]
    )


T = TypeVar('T')


def _get_highest_ascendant(element: T, element_to_parent: Dict[T, T]) -> T:
    parent = element_to_parent[element]
    previous_parent = element
    while parent != previous_parent:
        previous_parent = parent
        parent = element_to_parent[parent]
    return parent


def _revert_dict(input_dict: Dict[T, T]) -> Dict[T, List[T]]:
    group_to_elements: Dict[T, List[T]] = {}
    for element, group in input_dict.items():
        if group not in group_to_elements:
            group_to_elements[group] = []
        group_to_elements[group].append(element)
    return group_to_elements


def _build_groups(element_to_parent: Dict[int, int]) -> List[List[int]]:
    element_to_group = {element: _get_highest_ascendant(element, element_to_parent) for element in element_to_parent}
    return list(_revert_dict(element_to_group).values())


def group_by_proximity(elements: List[T], are_neighbors: Callable[[T, T], bool]) -> List[List[T]]:
    if not elements:
        return []
    element_to_group: Dict[int, int] = {}
    for rank, element in enumerate(elements):
        for rank_, element_ in enumerate(elements[:rank]):
            if are_neighbors(element, element_):
                if rank not in element_to_group:
                    element_to_group[rank] = rank_
                else:
                    element_to_group[_get_highest_ascendant(rank_, element_to_group)] = _get_highest_ascendant(
                        rank, element_to_group
                    )
        if rank not in element_to_group:
            element_to_group[rank] = rank
    groups = _build_groups(element_to_group)
    return [[elements[i] for i in group] for group in groups]


def _are_close(x: int, y: int) -> bool:
    return abs(x - y) <= _PROXIMITY_THRESHOLD


def _mean(ints: List[int]) -> int:
    if not ints:
        raise ValueError('Cannot compute mean on empty list.')
    return int(sum(ints) / len(ints))


def _group_ints(ints: List[int]) -> List[int]:
    groups = group_by_proximity(ints, _are_close)
    return [int(_mean(group)) for group in groups]


def _detect_horizontal_border_levels(cells: List[DetectedCell]) -> List[int]:
    all_levels = [level for cell in cells for level in (cell.contour.y_0, cell.contour.y_1)]
    return sorted(_group_ints(all_levels))


def _detect_vertical_border_levels(cells: List[DetectedCell]) -> List[int]:
    all_levels = [level for cell in cells for level in (cell.contour.x_0, cell.contour.x_1)]
    return sorted(_group_ints(all_levels))


def _assert_positive(int_: int) -> int:
    if int_ < 0:
        raise ValueError(f'Int {int_} is not positive')
    return int_


def _find_fuzzy_rank(candidate: int, borders: List[int]) -> int:
    for rank, border in enumerate(borders):
        if _are_close(border, candidate):
            return rank
    raise ValueError(f'No close border was found for the candidate:\ncandidate={candidate}\nborders={borders}')


def _extract_row_rank(cell_contour: Contour, horizontal_borders: List[int]) -> int:
    return _find_fuzzy_rank(cell_contour.y_0, horizontal_borders)


def _extract_col_rank(cell_contour: Contour, vertical_borders: List[int]) -> int:
    return _find_fuzzy_rank(cell_contour.x_0, vertical_borders)


def _extract_colspan(cell_contour: Contour, vertical_borders: List[int]) -> int:
    x_0_rank = _find_fuzzy_rank(cell_contour.x_0, vertical_borders)
    x_1_rank = _find_fuzzy_rank(cell_contour.x_1, vertical_borders)
    return _assert_positive(x_1_rank - x_0_rank)


def _extract_rowspan(cell_contour: Contour, horizontal_borders: List[int]) -> int:
    y_0_rank = _find_fuzzy_rank(cell_contour.y_0, horizontal_borders)
    y_1_rank = _find_fuzzy_rank(cell_contour.y_1, horizontal_borders)
    return _assert_positive(y_1_rank - y_0_rank)


@dataclass
class LocatedTable:
    table: Table
    h_pos: int
    v_pos: int
    height: int
    width: int

    def to_dict(self) -> Dict[str, Any]:
        dict_ = asdict(self)
        dict_['table'] = self.table.to_dict()
        return dict_

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]) -> 'LocatedTable':
        dict_ = dict_.copy()
        dict_['table'] = Table.from_dict(dict_['table'])
        return cls(**dict_)


def _radius(ints: List[int]) -> int:
    return max(ints) - min(ints)


def _build_table(cells: List[DetectedCell]) -> LocatedTable:
    horizontal_borders = _detect_horizontal_border_levels(cells)
    vertical_borders = _detect_vertical_border_levels(cells)
    rows: List[List[Tuple[int, Cell]]] = [[] for _ in range(len(horizontal_borders))]
    for cell in cells:
        row_index = _extract_row_rank(cell.contour, horizontal_borders)
        col_index = _extract_col_rank(cell.contour, vertical_borders)
        rowspan = _extract_rowspan(cell.contour, horizontal_borders)
        colspan = _extract_colspan(cell.contour, vertical_borders)
        rows[row_index].append((col_index, Cell(cell.text, rowspan=rowspan, colspan=colspan)))
    final_rows = [
        Row(is_header=False, cells=[cell for _, cell in sorted(row, key=lambda x: x[0])]) for row in rows if row
    ]
    return LocatedTable(
        Table(rows=final_rows),
        v_pos=min(horizontal_borders),
        h_pos=min(vertical_borders),
        width=_radius(vertical_borders),
        height=_radius(horizontal_borders),
    )


def _hide_tables(image: np.ndarray, tables: List[LocatedTable]) -> np.ndarray:
    color = (255, 255, 255)
    for table in tables:
        cv2.rectangle(
            image, (table.h_pos, table.v_pos), (table.h_pos + table.width, table.v_pos + table.height), color, -1
        )
    return image


def extract_and_remove_tables(image: np.ndarray) -> Tuple[np.ndarray, List[LocatedTable]]:
    cells = _extract_cells(image)
    grouped_cells = group_by_proximity(cells, _are_neighbor)
    tables = [_build_table(group) for group in grouped_cells]
    return _hide_tables(image, tables), tables


if __name__ == '__main__':
    _RAW_FILENAME = (
        '/Users/remidelbouys/EnviNorma/ap_sample/pdf_image_workspace/Z_7_8a8d18be65e763f00165e76dcb250007/in.pdf'
    )
    from pdf2image import convert_from_path

    page = convert_from_path(_RAW_FILENAME, first_page=2, last_page=2)[0]
    file_ = 'tmp.png'
    page.save(file_)
    img = cv2.imread(file_, 0)
    img_without_tables, tables = extract_and_remove_tables(img)
    cv2.imwrite('tmp2.png', img_without_tables)

    # _save_image(_RAW_FILENAME, _FILENAME)
    # _FILENAME = 'tmpimage.png'
    # input_image = _load_image(_FILENAME)
    # image, tables = extract_and_remove_tables(input_image)

    # cv2.imwrite('test.png', image)
    # input_image = _load_image(_FILENAME)

    # for table in tables:
    #     input_image = cv2.rectangle(
    #         input_image,
    #         (table.v_pos, table.h_pos),
    #         (table.v_pos + table.width, table.h_pos + table.height),
    #         (0, 0, 0),
    #         4,
    #     )
    # cv2.imwrite('test2.png', input_image)
