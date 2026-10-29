from parsing.layout import Page, Word, find_gutter, group_lines, lines_to_text, normalize, split_columns


def _w(x0: float, top: float, text: str, width: float = 40, height: float = 10) -> Word:
    return Word(x0, top, x0 + width, top + height, text)


def test_group_lines_orders_words_left_to_right() -> None:
    words = [_w(120, 100.5, "dünya"), _w(50, 100, "Merhaba"), _w(50, 130, "ikinci")]
    assert [[w.text for w in line] for line in group_lines(words)] == [["Merhaba", "dünya"], ["ikinci"]]


def test_large_vertical_gap_becomes_blank_line() -> None:
    words = [_w(50, 100, "BİR"), _w(50, 112, "iki"), _w(50, 160, "ÜÇ")]
    assert lines_to_text(words) == "BİR\niki\n\nÜÇ"


def test_no_gutter_for_few_words() -> None:
    words = [_w(50, 100 + i * 15, f"k{i}") for i in range(5)] + [_w(400, 100 + i * 15, f"s{i}") for i in range(5)]
    assert find_gutter(words, 595) is None


def test_full_width_lines_prevent_columns() -> None:
    # Her satır sayfanın iki yanına uzanıyor: sütun yok.
    words = [_w(50, 100 + i * 15, f"a{i}", width=250) for i in range(15)]
    words += [_w(310, 100 + i * 15, f"b{i}", width=230) for i in range(15)]
    words += [_w(280, 100 + i * 15, "orta", width=40) for i in range(15)]
    assert find_gutter(words, 595) is None


def test_header_spanning_gutter_is_read_first() -> None:
    header = [_w(50, 40, "[AD SOYAD] — çok uzun başlık satırı", width=480, height=14)]
    left = [_w(40, 100 + i * 13, f"sol{i}") for i in range(12)]
    right = [_w(260, 104 + i * 21, f"sag{i}", width=200) for i in range(12)]
    regions = split_columns(Page(595, 842, header + left + right))
    assert [[w.text for w in r][:1] for r in regions] == [["[AD SOYAD] — çok uzun başlık satırı"], ["sol0"], ["sag0"]]


def test_normalize() -> None:
    assert normalize("  ﬁrma­  adı \n\n\n\nİstanbul  ") == "firma adı\n\nİstanbul"
