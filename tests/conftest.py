# Standard Library
from pathlib import Path

# Third Party
import pytest


@pytest.fixture
def sample_data_path():
    return Path(__file__).parent.parent / "samples"


@pytest.fixture
def samples(sample_data_path):
    return [d for d in sample_data_path.glob("sample-*") if d.is_dir()]
