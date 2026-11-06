"""PELAN-V2 P16: pecahan kategori laporan v2 (recall (b)–(d) span tepat; (e) = ramalan bertindih kawasan negatif)."""

from mypii.nilai.bandingan_v2 import kategori


def test_kategori_recall_dan_fp_negatif():
    dok = [{"spans": [{"mula": 0, "tamat": 12, "entiti": "MY_SSM"}, {"mula": 20, "tamat": 30, "entiti": "MY_PHONE"}],
            "kategori": [{"kategori": "b", "mula": 0, "tamat": 12}, {"kategori": "d", "mula": 20, "tamat": 30},
                         {"kategori": "e", "mula": 40, "tamat": 52}]}]
    ram = [[{"mula": 0, "tamat": 12, "entiti": "MY_SSM"}, {"mula": 21, "tamat": 30, "entiti": "MY_PHONE"},
            {"mula": 40, "tamat": 52, "entiti": "MY_NRIC"}]]
    c = kategori(dok, ram)
    assert c["b"]["recall"] == 1.0 and c["d"]["recall"] == 0.0   # span separa ≠ tepat
    assert c["e"] == {"emas": 0, "betul": 0, "kawasan": 1, "fp": 1, "recall": None}
    assert list(c) == ["b", "d", "e"]
