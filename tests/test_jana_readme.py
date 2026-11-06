"""PELAN-SEDIA-TERBIT P1: blok jadual dev README = keluaran `scripts/jana_readme.py`; penjana deterministik; blok Python README
boleh diurai. Fixture `hasil` tiruan dalam `tmp_path` mengunci BENTUK jadual, bukan angka sebenar."""

import ast
import importlib.util
import json
import re
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("jana_readme", AKAR / "scripts" / "jana_readme.py")
jr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jr)


def _hasil_tiruan(d: Path) -> Path:
    d.mkdir()  # statistik SAHAJA: dev-<sistem>.json diabaikan git, jadi penjana tidak boleh bergantung padanya
    st = {
        "split": "dev", "dokumen": 7, "unit": "dokumen", "kunci_utama": "semua|*", "rujukan": "mypii",
        "config": {"aras": 0.95, "ulangan": 50, "benih": 1, "kaedah": "holm"},
        "eksplorasi": ["llm:x/eks"],
        "sistem": {
            "llm:x/eks": {"semua|*": {"f1": 0.6, "bawah": 0.5, "atas": 0.7, "n_sah": 7}},
            "mypii": {"semua|*": {"f1": 0.8, "bawah": 0.75, "atas": 0.85, "n_sah": 7}},
            "pesaing": {"semua|*": {"f1": 0.9, "bawah": 0.88, "atas": 0.92, "n_sah": 7}},
        },
        "banding": {
            "llm:x/eks": {"semua|*": {"delta": 0.2, "bawah": 0.1, "atas": 0.3, "eksplorasi": True}},
            "pesaing": {"semua|*": {"delta": -0.1, "bawah": -0.15, "atas": -0.05}},
        },
    }
    (d / "dev-statistik.json").write_text(json.dumps(st))
    return d


def test_jadual_tiruan(tmp_path):
    blok = jr.jadual(_hasil_tiruan(tmp_path / "hasil"))
    baris = [b for b in blok.splitlines() if b.startswith("| `")]
    assert [re.match(r"\| `([^`]+)`", b).group(1) for b in baris] == ["mypii", "x/eks", "pesaing"]
    assert baris[0] == "| `mypii` | **0.8000** | [0.7500, 0.8500] | rujukan / reference |"
    assert "(eksplorasi / exploratory)" in baris[1] and "+0.2000 [0.1000, 0.3000]" in baris[1]
    assert "(eksplorasi" not in baris[2] and "-0.1000 [-0.1500, -0.0500]" in baris[2]
    assert "7 dokumen" in blok and "bootstrap 95% (50 ulangan" in blok


def test_deterministik_dan_ganti(tmp_path):
    h = _hasil_tiruan(tmp_path / "hasil")
    readme = tmp_path / "README.md"
    readme.write_text(f"awal\n{jr.MULA}\nlama\n{jr.TAMAT}\nakhir\n")
    assert jr.main(["--readme", str(readme), "--hasil", str(h), "--semak"]) == 1
    assert jr.main(["--readme", str(readme), "--hasil", str(h)]) == 0
    sekali = readme.read_text()
    assert jr.main(["--readme", str(readme), "--hasil", str(h)]) == 0
    assert readme.read_text() == sekali
    assert sekali.startswith("awal\n") and sekali.endswith(f"{jr.TAMAT}\nakhir\n") and "lama" not in sekali
    assert jr.main(["--readme", str(readme), "--hasil", str(h), "--semak"]) == 0


@pytest.mark.parametrize("teks", ["tiada penanda", f"{jr.TAMAT}\n{jr.MULA}", f"{jr.MULA}{jr.MULA}{jr.TAMAT}"])
def test_penanda_rosak(teks):
    with pytest.raises(ValueError):
        jr.ganti(teks, "x\n")


def test_readme_blok_sama_keluaran():
    readme = (AKAR / "README.md").read_text(encoding="utf-8")
    assert jr.ganti(readme, jr.jadual(AKAR / "hasil")) == readme, "README basi: jalankan `make readme`"


def test_readme_blok_python_boleh_diurai():
    blok = re.findall(r"```python\n(.*?)```", (AKAR / "README.md").read_text(encoding="utf-8"), re.DOTALL)
    assert blok
    for b in blok:
        ast.parse(b)
