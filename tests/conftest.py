"""Satu tempat masuk suite: buang `GIT_*` dari env (perangkap rumah — dari cangkuk pre-commit/pre-push ia menunjuk ke repo
SEBENAR, jadi ujian yang menjalankan git dalam folder sementara akan menulis ke repo ini)."""

import os


def pytest_configure(config):
    for k in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[k]
