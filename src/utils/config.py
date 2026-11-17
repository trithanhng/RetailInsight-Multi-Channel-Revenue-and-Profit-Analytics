"""Shared repository paths and fixed-point money scale."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "adventureworks"
RAW = ROOT / "data" / "raw"
SCALE = 10000
