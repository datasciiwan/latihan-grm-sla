"""Cek kepatuhan SLA penanganan aduan (batas 14 hari kalender).

Hanya memakai pustaka standar Python.

Contoh:
    python src/cek_sla.py --acuan 2026-03-31
"""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

BATAS_SLA_HARI = 14

TEPAT_WAKTU = "TEPAT WAKTU"
TERLAMBAT = "TERLAMBAT"
DALAM_PROSES = "DALAM PROSES"  # belum selesai, tapi umurnya masih <= 14 hari

FORMAT_TANGGAL = "%Y-%m-%d"


def parse_tanggal(teks):
    """Ubah 'YYYY-MM-DD' jadi date. String kosong dikembalikan sebagai None."""
    teks = (teks or "").strip()
    if not teks:
        return None
    return date.fromisoformat(teks)


def nilai_aduan(tanggal_masuk, tanggal_selesai, acuan):
    """Kembalikan (lama_hari, status_sla, sudah_selesai) untuk satu aduan.

    - Sudah selesai: lama = selesai - masuk. Lebih dari 14 hari -> TERLAMBAT.
      Tepat 14 hari masih TEPAT WAKTU.
    - Belum selesai: lama = acuan - masuk. Lebih dari 14 hari -> TERLAMBAT,
      selain itu DALAM PROSES.
    """
    if tanggal_selesai is not None:
        lama = (tanggal_selesai - tanggal_masuk).days
        if lama < 0:
            raise ValueError("tanggal_selesai lebih awal dari tanggal_masuk")
        status = TERLAMBAT if lama > BATAS_SLA_HARI else TEPAT_WAKTU
        return lama, status, True

    if acuan is None:
        raise ValueError("aduan belum selesai butuh tanggal acuan (--acuan)")
    lama = (acuan - tanggal_masuk).days
    if lama < 0:
        raise ValueError("tanggal acuan lebih awal dari tanggal_masuk")
    status = TERLAMBAT if lama > BATAS_SLA_HARI else DALAM_PROSES
    return lama, status, False


def baca_aduan(path_csv, acuan):
    """Baca CSV aduan dan tambahkan kolom lama_hari, status_sla, sudah_selesai."""
    hasil = []
    with open(path_csv, newline="", encoding="utf-8") as f:
        for baris in csv.DictReader(f):
            try:
                masuk = parse_tanggal(baris["tanggal_masuk"])
                if masuk is None:
                    raise ValueError("tanggal_masuk kosong")
                selesai = parse_tanggal(baris["tanggal_selesai"])
                lama, status, sudah_selesai = nilai_aduan(masuk, selesai, acuan)
            except ValueError as e:
                raise ValueError(f"Aduan {baris.get('id_aduan')}: {e}") from e
            hasil.append(
                {
                    **baris,
                    "lama_hari": lama,
                    "status_sla": status,
                    "sudah_selesai": sudah_selesai,
                }
            )
    return hasil


def dari(n, total):
    return f"{n} dari {total} aduan"


def ringkas(aduan):
    """Hitung ringkasan. Rata-rata per kategori hanya dari aduan yang sudah selesai."""
    total = len(aduan)
    hitung = defaultdict(int)
    hari_per_kategori = defaultdict(list)
    for a in aduan:
        hitung[a["status_sla"]] += 1
        if a["sudah_selesai"]:
            hari_per_kategori[a["kategori"]].append(a["lama_hari"])

    rata_rata = {
        kategori: sum(daftar) / len(daftar)
        for kategori, daftar in sorted(hari_per_kategori.items())
    }
    return {
        "jumlah_aduan": total,
        "tepat_waktu": hitung[TEPAT_WAKTU],
        "terlambat": hitung[TERLAMBAT],
        "dalam_proses": hitung[DALAM_PROSES],
        "rata_rata_per_kategori": rata_rata,
        "jumlah_selesai_per_kategori": {
            k: len(v) for k, v in hari_per_kategori.items()
        },
    }


def baris_ringkasan(r):
    """Ubah ringkasan jadi daftar (metrik, nilai) siap ditulis/dicetak."""
    total = r["jumlah_aduan"]
    baris = [
        ("jumlah_aduan", str(total)),
        ("tepat_waktu", dari(r["tepat_waktu"], total)),
        ("terlambat", dari(r["terlambat"], total)),
        ("dalam_proses", dari(r["dalam_proses"], total)),
    ]
    for kategori, rata in r["rata_rata_per_kategori"].items():
        n = r["jumlah_selesai_per_kategori"][kategori]
        baris.append(
            (
                f"rata_rata_hari_penyelesaian: {kategori}",
                f"{rata:.2f} hari (dari {n} aduan selesai)",
            )
        )
    return baris


def tulis_csv(path_output, baris):
    path_output = Path(path_output)
    path_output.parent.mkdir(parents=True, exist_ok=True)
    with open(path_output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metrik", "nilai"])
        w.writerows(baris)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cek SLA aduan (batas 14 hari).")
    parser.add_argument(
        "--acuan",
        required=True,
        help="Tanggal acuan untuk aduan yang belum selesai (YYYY-MM-DD).",
    )
    parser.add_argument("--input", default="data/aduan_dummy.csv")
    parser.add_argument("--output", default="output/ringkasan.csv")
    args = parser.parse_args(argv)

    try:
        acuan = date.fromisoformat(args.acuan)
    except ValueError:
        parser.error("--acuan harus berformat YYYY-MM-DD")

    try:
        aduan = baca_aduan(args.input, acuan)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Tanggal acuan: {acuan.isoformat()}  |  Batas SLA: {BATAS_SLA_HARI} hari\n")
    print(f"{'ID':<10}{'Kategori':<18}{'Hari':>5}  Status")
    for a in aduan:
        print(f"{a['id_aduan']:<10}{a['kategori']:<18}{a['lama_hari']:>5}  {a['status_sla']}")

    baris = baris_ringkasan(ringkas(aduan))
    print("\nRingkasan:")
    for metrik, nilai in baris:
        print(f"- {metrik}: {nilai}")

    tulis_csv(args.output, baris)
    print(f"\nRingkasan disimpan ke {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
