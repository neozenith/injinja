# Third Party
import pytest
from conftest import sample_data_path, samples

# Our Libraries
from injinja.injinja import merge

SAMPLES = samples(sample_data_path())


@pytest.mark.parametrize("sample", SAMPLES)
def test_main(sample):
    configs = [str(f) for f in (sample / "config").rglob("**/*")]
    expectations = [str(f) for f in (sample / "expectations").rglob("**/*")]
    functions = [str(f) for f in (sample / "functions").rglob("**/*.py")]
    templates = [str(f) for f in (sample / "templates").rglob("**/*")]

    for template in templates:
        for expectation in expectations:
            merged_template, diff = merge(config=configs, validate=expectation, functions=functions, template=template)
            assert diff == ""
