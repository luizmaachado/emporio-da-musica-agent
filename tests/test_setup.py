"""Smoke test: the package is importable and the data files are in place."""
from pathlib import Path

import emporio

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_package_is_importable():
    assert emporio.__doc__


def test_data_files_exist():
    assert len(list(DATA_DIR.glob("*.csv"))) == 6
    assert (DATA_DIR / "políticas_da_loja.pdf").exists()
