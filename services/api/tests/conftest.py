import os
import tempfile
from pathlib import Path

ROOT = Path(tempfile.mkdtemp(prefix="frametrace-tests-"))
os.environ["FRAMETRACE_DATA_DIR"] = str(ROOT)
os.environ["FRAMETRACE_DATABASE_URL"] = os.environ.get(
    "FRAMETRACE_TEST_DATABASE_URL", f"sqlite:///{ROOT / 'test.db'}"
)
os.environ["FRAMETRACE_EXECUTION"] = "local"


import importlib.util

import pytest


@pytest.fixture(scope="session")
def media(tmp_path_factory):
    folder = tmp_path_factory.mktemp("footage")
    spec = importlib.util.spec_from_file_location(
        "fixtures", Path(__file__).parents[3] / "scripts/make_fixtures.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.fixtures(folder)
    return folder
