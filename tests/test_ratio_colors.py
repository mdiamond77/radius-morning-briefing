import os
import sys

os.environ.setdefault("SMTP_USER", "x")
os.environ.setdefault("SMTP_PASSWORD", "x")
os.environ.setdefault("REPORT_RECIPIENTS", "x@example.com")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from send import ratio_cell_colors  # noqa: E402


def bg(students, instructors):
    return ratio_cell_colors(students, instructors)[0]


def test_under_2_25_is_green():
    assert bg(2, 1) == "#86efac"
    assert bg(4, 2) == "#86efac"


def test_2_25_to_under_2_75_is_yellow():
    assert bg(9, 4) == "#fde047"   # 2.25 exactly
    assert bg(5, 2) == "#fde047"   # 2.5


def test_2_75_up_to_3_0_is_light_red():
    assert bg(11, 4) == "#fca5a5"  # 2.75 exactly
    assert bg(3, 1) == "#fca5a5"   # 3.0 exactly


def test_over_3_0_is_bright_red():
    assert bg(7, 2) == "#ef4444"   # 3.5


def test_uses_exact_ratio_not_rounded():
    # 61/20 = 3.05 displays as 3.0 once rounded, but is over 3.0 on the heatmap
    assert bg(61, 20) == "#ef4444"


def test_no_instructors_is_gray():
    assert bg(4, 0) == "#d1d5db"


def test_no_students_is_light_gray():
    assert bg(0, 2) == "#f0f0f0"


def test_bright_red_uses_white_text_others_dark():
    assert ratio_cell_colors(7, 2)[1] == "#ffffff"
    assert ratio_cell_colors(2, 1)[1] == "#1a1a1a"
