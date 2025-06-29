# Our Libraries
from injinja.injinja import reduce_confs


def test_reduce_confs():
    confs = [
        {"a": 1, "b": 2},
        {"b": 3, "c": 4},
        {"c": 5, "d": 6},
    ]
    assert reduce_confs(confs) == {"a": 1, "b": 3, "c": 5, "d": 6}


def test_reading_confs(sample_data_path):
    files = list(sample_data_path.glob("**/*.yml"))
    assert len(files) == 14
