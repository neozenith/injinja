# Standard Library
from pathlib import Path

# Third Party
import pytest


@pytest.fixture
def sample_data_path():
    return Path(__file__).parent / "samples"
