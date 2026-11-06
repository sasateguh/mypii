import hashlib
import json

from mypii import konfig

BENCH = konfig.AKAR / "data/bench"


def test_kunci_ujian_sepadan():
    """Split ujian tidak boleh berubah tanpa sengaja (gelung automatik dilarang menyentuhnya)."""
    kunci = json.loads((BENCH / "KUNCI.json").read_text())
    sebenar = hashlib.sha256((BENCH / "ujian.jsonl").read_bytes()).hexdigest()
    assert sebenar == kunci["ujian"]["sha256"]


def test_span_dalam_teks():
    for split in ("latih", "dev"):
        for baris in (BENCH / f"{split}.jsonl").read_text(encoding="utf-8").splitlines():
            d = json.loads(baris)
            for s in d["spans"]:
                assert 0 <= s["mula"] < s["tamat"] <= len(d["teks"])
                assert d["teks"][s["mula"]:s["tamat"]].strip() == d["teks"][s["mula"]:s["tamat"]]
