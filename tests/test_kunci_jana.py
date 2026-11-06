"""`jana` tidak pernah menulis semula KUNCI.json yang wujud: cincangan ujian lain = BERHENTI (ADR-003)."""
import json

import pytest

from mypii.jana.jana import jana


def test_jana_berhenti_bila_split_ujian_berbeza_dengan_kunci(tmp_path):
    kunci = tmp_path / "KUNCI.json"
    asal = json.dumps({"ujian": {"dokumen": 1000, "sha256": "0" * 64}})
    kunci.write_text(asal)
    with pytest.raises(SystemExit, match="BERUBAH"):
        jana(tmp_path)
    assert kunci.read_text() == asal


def test_jana_mencipta_kunci_ujian_sahaja_bila_tiada(tmp_path):
    r = jana(tmp_path)
    assert json.loads((tmp_path / "KUNCI.json").read_text()) == {"ujian": r["ujian"]}
    assert set(json.loads((tmp_path / "CINCANGAN.json").read_text())) == {"latih", "dev"}
