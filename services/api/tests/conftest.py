import os
import tempfile
from pathlib import Path

ROOT = Path(tempfile.mkdtemp(prefix="frametrace-tests-"))
os.environ["FRAMETRACE_DATA_DIR"] = str(ROOT)
os.environ["FRAMETRACE_DATABASE_URL"] = f"sqlite:///{ROOT / 'test.db'}"
os.environ["FRAMETRACE_EXECUTION"] = "local"
