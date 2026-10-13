import csv
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cek_sla  # noqa: E402

ACUAN = date(2026, 3, 31)


def test_selesai_tepat_hari_ke_14_masih_tepat_waktu():
    lama, status, selesai = cek_sla.nilai_aduan(date(2026, 1, 8), date(2026, 1, 22), ACUAN)
    assert lama == 14
    assert status == cek_sla.TEPAT_WAKTU
    assert selesai is True


def test_selesai_hari_ke_15_terlambat():
    lama, status, _ = cek_sla.nilai_aduan(date(2026, 2, 3), date(2026, 2, 18), ACUAN)
    assert lama == 15
    assert status == cek_sla.TERLAMBAT


def test_belum_selesai_lewat_14_hari_terlambat():
    lama, status, selesai = cek_sla.nilai_aduan(date(2026, 3, 1), None, ACUAN)
    assert lama == 30
    assert status == cek_sla.TERLAMBAT
    assert selesai is False


def test_belum_selesai_masih_dalam_batas_dalam_proses():
    lama, status, _ = cek_sla.nilai_aduan(date(2026, 3, 25), None, ACUAN)
    assert lama == 6
    assert status == cek_sla.DALAM_PROSES


def test_belum_selesai_tepat_14_hari_belum_terlambat():
    lama, status, _ = cek_sla.nilai_aduan(date(2026, 3, 17), None, ACUAN)
    assert lama == 14
    assert status == cek_sla.DALAM_PROSES


def test_tanggal_selesai_sebelum_masuk_ditolak():
    with pytest.raises(ValueError):
        cek_sla.nilai_aduan(date(2026, 1, 10), date(2026, 1, 5), ACUAN)


def test_ringkasan_data_dummy(tmp_path):
    root = Path(__file__).resolve().parent.parent
    output = tmp_path / "ringkasan.csv"
    kode = cek_sla.main(
        ["--acuan", "2026-03-31", "--input", str(root / "data/aduan_dummy.csv"),
         "--output", str(output)]
    )
    assert kode == 0

    with open(output, newline="", encoding="utf-8") as f:
        hasil = dict(csv.reader(f))
    assert hasil["jumlah_aduan"] == "12"
    assert hasil["tepat_waktu"] == "7 dari 12 aduan"
    assert hasil["terlambat"] == "4 dari 12 aduan"
    assert hasil["dalam_proses"] == "1 dari 12 aduan"
    assert hasil["rata_rata_hari_penyelesaian: Lahan"] == "14.67 hari (dari 3 aduan selesai)"
    assert hasil["rata_rata_hari_penyelesaian: Sosial"] == "8.00 hari (dari 2 aduan selesai)"
