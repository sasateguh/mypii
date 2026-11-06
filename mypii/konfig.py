"""Muat config/*.yaml. Laluan boleh ditindih dengan MYPII_KONFIG (folder)."""

import os
from functools import lru_cache
from pathlib import Path

import yaml

AKAR = Path(__file__).resolve().parent.parent
# Wheel (`pip install mypii`): config/ + model/ dibawa DALAM pakej di sini (pyproject `force-include`). Klon repo: folder ini tiada.
DATA_PAKEJ = Path(__file__).resolve().parent / "_data"


def akar_data() -> Path:
    """Folder yang memegang config/ dan model/: salinan dalam pakej bila dipasang dari wheel, jika tidak akar klon (AKAR)."""
    return DATA_PAKEJ if (DATA_PAKEJ / "config" / "mypii.yaml").is_file() else AKAR


def folder_konfig() -> Path:
    return Path(os.environ.get("MYPII_KONFIG", akar_data() / "config"))


@lru_cache
def muat(nama: str) -> dict:
    laluan = folder_konfig() / f"{nama}.yaml"
    with open(laluan, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def utama() -> dict:
    return muat("mypii")


def kod_pb_sah() -> set[str]:
    """Kod tempat lahir MyKad yang diterima (semua kod dalam kod_pb.yaml, disahkan atau belum)."""
    return set(muat("kod_pb").get("kod", {}))


def fail_split(split: str) -> str:
    """Laluan relatif fail split: `nilai.split_fail.<split>.fail` (v3, PELAN-V2 P4) atau `data/bench/<split>.jsonl` (v1)."""
    return utama()["nilai"].get("split_fail", {}).get(split, {}).get("fail", f"data/bench/{split}.jsonl")


def fail_cincangan(split: str) -> str:
    """Fail cincangan/kunci yang memuat `<split>.sha256`: v3 dari `nilai.split_fail`, v1 = `data/bench/CINCANGAN.json`."""
    return utama()["nilai"].get("split_fail", {}).get(split, {}).get("cincangan", "data/bench/CINCANGAN.json")
