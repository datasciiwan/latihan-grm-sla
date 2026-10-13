# latihan-grm-sla

Skrip kecil untuk mengecek kepatuhan SLA penanganan aduan (GRM). Batasnya 14 hari kalender.
Semua data di `data/aduan_dummy.csv` fiktif.

## Aturan

- Aduan selesai: lama = `tanggal_selesai - tanggal_masuk`. Lebih dari 14 hari berarti **TERLAMBAT**.
  Selesai tepat di hari ke-14 masih **TEPAT WAKTU**.
- Aduan belum selesai (`tanggal_selesai` kosong): lama = `--acuan - tanggal_masuk`.
  Lebih dari 14 hari berarti **TERLAMBAT**. Kalau belum lewat 14 hari, statusnya **DALAM PROSES**.
  Aduan ini tidak dihitung tepat waktu, karena memang belum selesai.
- Rata-rata hari penyelesaian per kategori hanya memakai aduan yang sudah selesai.
- Status ditentukan dari kolom `tanggal_selesai`. Kolom `status` tidak dipakai dalam perhitungan.

## Cara menjalankan

Butuh Python 3.9 atau lebih baru. Skrip hanya memakai pustaka standar.

```bash
python src/cek_sla.py --acuan 2026-03-31
```

Opsi lain: `--input` (bawaan `data/aduan_dummy.csv`) dan `--output` (bawaan `output/ringkasan.csv`).

Hasilnya berupa tabel per aduan dan ringkasan di terminal. Ringkasan yang sama ditulis ke
`output/ringkasan.csv`, misalnya `terlambat,4 dari 12 aduan`.

## Menjalankan tes

```bash
pip install pytest
python -m pytest
```
