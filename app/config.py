import os
from pathlib import Path

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "./tracelens.sqlite3"))
