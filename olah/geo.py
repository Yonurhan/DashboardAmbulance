"""Data spasial untuk dasbor: daftar faskes dan poligon kelurahan (GeoJSON ringan)."""
import json
import warnings

import pandas as pd
import pyogrio
import shapely

import config

PETA_JENIS = {"Rumah Sakit": "RS", "Puskesmas": "PKM"}
KANDIDAT_TOLERANSI = (0.00005, 0.0001, 0.0002)   # derajat
BATAS_UKURAN_KB = 300.0
BATAS_PERUBAHAN_LUAS = 0.01                      # 1%


def buat_faskes(path_csv, fas):
    """Daftar faskes {kode, nama, jenis, kecamatan, lat, lng} dengan urutan sama seperti model."""
    a = pd.read_csv(path_csv).set_index("id")
    out = []
    for kode in fas:
        r = a.loc[kode]
        if r["kategori"] not in PETA_JENIS:
            raise ValueError(f"kategori faskes tidak dikenal untuk {kode}: {r['kategori']!r}")
        out.append({"kode": kode, "nama": str(r["nama_faskes"]), "jenis": PETA_JENIS[r["kategori"]],
                    "kecamatan": str(r["kecamatan"]), "lat": float(r["latitude"]),
                    "lng": float(r["longitude"])})
    return out


def baca_poligon(path_gdb):
    """Baca poligon kelurahan Kota Bekasi dari GDB BIG, 2D, EPSG:4326."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # peringatan organizePolygons dari GDAL
        g = pyogrio.read_dataframe(path_gdb, layer=config.LAYER_GDB, where=config.FILTER_GDB,
                                   columns=["KDEPUM", "NAMOBJ", "WADMKC", "WADMKK"])  # WADMKK wajib ikut agar filter where berlaku
    # CRS asli EPSG:9518 = WGS84 horizontal + tinggi EGM2008; sumbu Z dibuang.
    g["geometry"] = shapely.force_2d(g.geometry.values)
    return g.set_crs(4326, allow_override=True)


def _ukuran_kb(fc):
    return len(json.dumps(fc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) / 1024


def _ke_fc(g, props):
    fitur = []
    for _, r in g.iterrows():
        fitur.append({"type": "Feature", "properties": props[r["KDEPUM"]],
                      "geometry": json.loads(shapely.to_geojson(shapely.set_precision(r.geometry, 1e-6)))})
    return {"type": "FeatureCollection", "features": fitur}


def _perubahan_luas_maks(asli, sederhana):
    a = asli.to_crs(32748).area.to_numpy()
    b = sederhana.to_crs(32748).area.to_numpy()
    return float(abs(b - a).max() / a.min()) if len(a) else 0.0


def buat_kelurahan(path_gdb, path_centroid, d, toleransi=None):
    """FeatureCollection 56 kelurahan + laporan ukuran.

    toleransi=None: pilih toleransi terbesar dari KANDIDAT_TOLERANSI yang ukurannya
    ≤ BATAS_UKURAN_KB dan perubahan luas tiap kelurahan < BATAS_PERUBAHAN_LUAS.
    """
    g = baca_poligon(path_gdb)
    cen = pd.read_csv(path_centroid).set_index("kode_kelurahan")
    tidak_cocok = sorted(set(d["kel"]) ^ set(g["KDEPUM"]))
    tidak_cocok += sorted(k for k in d["kel"] if k not in cen.index)
    g = g[g["KDEPUM"].isin(d["kel"])].reset_index(drop=True)

    props = {}
    for i, kel in enumerate(d["kel"]):
        r = g[g["KDEPUM"] == kel]
        if r.empty or kel not in cen.index:
            continue
        props[kel] = {"kode": kel, "nama": str(r.iloc[0]["NAMOBJ"]), "kecamatan": str(r.iloc[0]["WADMKC"]),
                      "penduduk": int(d["P"][i]), "lansia": int(d["L"][i]),
                      "centroid_lat": float(cen.loc[kel, "lat"]), "centroid_lng": float(cen.loc[kel, "lon"])}

    ukuran_asli = _ukuran_kb(_ke_fc(g, props))
    calon = [toleransi] if toleransi is not None else list(KANDIDAT_TOLERANSI)
    pilihan = None
    for tol in calon:
        s = g.copy()
        s["geometry"] = g.geometry.simplify(tol, preserve_topology=True)
        fc = _ke_fc(s, props)
        info = (tol, fc, _ukuran_kb(fc), _perubahan_luas_maks(g.geometry, s.geometry))
        if toleransi is not None or (info[2] <= BATAS_UKURAN_KB and info[3] < BATAS_PERUBAHAN_LUAS):
            pilihan = info
    if pilihan is None:          # tidak ada yang memenuhi -> pakai toleransi paling halus
        s = g.copy()
        s["geometry"] = g.geometry.simplify(calon[0], preserve_topology=True)
        fc = _ke_fc(s, props)
        pilihan = (calon[0], fc, _ukuran_kb(fc), _perubahan_luas_maks(g.geometry, s.geometry))
    tol, fc, ukuran, dluas = pilihan
    laporan = {"ukuran_sebelum_kb": round(ukuran_asli, 1), "ukuran_sesudah_kb": round(ukuran, 1),
               "toleransi": tol, "perubahan_luas_maks": round(dluas, 5), "tidak_cocok": tidak_cocok}
    return fc, laporan
