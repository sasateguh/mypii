# Halaman semakan IAA (PELAN-IAA P5, ADR-015) — Python stdlib + PyYAML sahaja.
# Bina dari `git archive` (deploy/iaa/deploy.sh): hanya fail yang dikomit; .dockerignore = senarai benar.
# TIADA mypii/__init__.py dalam imej: `mypii` jadi pakej ruang nama, jadi `from mypii import konfig` tidak
# menarik presidio (pengecam). Data (bundel, SQLite, token) = bind ~/ops/mypii/iaa → /data, bukan dalam imej.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MYPII_IAA_FOLDER=/data
# Versi sama uv.lock (stdlib selain ini; tiada kebergantungan baharu).
RUN pip install --no-cache-dir pyyaml==6.0.3 \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin iaa
WORKDIR /app
COPY config/mypii.yaml config/mypii.yaml
COPY mypii/konfig.py mypii/konfig.py
COPY mypii/iaa/ mypii/iaa/
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-m", "mypii.iaa.operasi", "sihat"]
CMD ["python", "-m", "mypii.iaa.pelayan"]
