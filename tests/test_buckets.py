import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parse import buckets_for_session, half_hour_buckets, to_minutes  # noqa: E402


def b(start, end):
    return [x // 60 * 100 + x % 60 for x in buckets_for_session(to_minutes(start), to_minutes(end))]


def test_under_75_minutes_is_two_buckets_with_most_time():
    assert b("5:14 PM", "6:26 PM") == [1730, 1800]


def test_75_to_104_minutes_is_three_buckets():
    assert b("4:50 PM", "6:20 PM") == [1700, 1730, 1800]   # 90 min; 4:30 only has 10


def test_105_plus_minutes_is_four_buckets():
    assert b("4:00 PM", "6:00 PM") == [1600, 1630, 1700, 1730]


def test_tie_goes_to_earlier_buckets():
    assert b("5:15 PM", "6:15 PM") == [1700, 1730]


def test_short_session_only_counts_buckets_it_touches():
    assert b("5:00 PM", "5:30 PM") == [1700]


def sess(name, start, end, inst):
    return {"name": name, "instructor": inst,
            "start_min": to_minutes(start), "end_min": to_minutes(end)}


def test_excluded_instructors_not_counted_and_presence_bridged():
    out = half_hour_buckets([
        sess("A", "4:00 PM", "5:00 PM", "Ann"),
        sess("B", "4:00 PM", "5:00 PM", "Matthew Diamond, Elizabeth Anacleto"),
        sess("C", "5:30 PM", "6:30 PM", "Ann"),
    ])
    by = {x["label"].split(" ")[0] + x["label"].split(" ")[1]: x for x in out}
    assert by["4:00PM"]["count"] == 2 and by["4:00PM"]["instructors"] == 1
    assert "5:00PM" not in by            # no students, so no row
    assert by["5:30PM"]["instructors"] == 1
