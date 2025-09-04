import sys
import os, re, json, hashlib, time
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))   # rende importabile `tools/` e il resto del progetto

FIX = ROOT / "tests" / "fixtures"

@pytest.fixture(scope="session")
def fixtures_dir():
    return FIX

@pytest.fixture(autouse=True)
def freeze_time(monkeypatch):
    class _time: 
        @staticmethod
        def time(): return 1_725_000_000  # fisso
    monkeypatch.setattr(time, "time", _time.time)
