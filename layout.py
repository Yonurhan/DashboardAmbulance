"""Penyusun tampilan: kerangka halaman dan isi kartu/panel."""
from dash import dcc, html

import config
import peta
from format_angka import angka

KUNCI_DEFAULT = "|".join(config.ID_DEFAULT)


def chip_kategori(kat):
    return html.Span([html.I(className="chip-warna", style={"background": config.WARNA_KATEGORI[kat]}),
                      config.LABEL_KATEGORI[kat]], className="chip")


# ------------------------------------------------------------------ kerangka
def _kartu_kontrol(data):
    return html.Div(className="kartu", children=[
        html.Div("Skenario dan metode", className="label"),
        dcc.Dropdown(id="dd-skenario", options=data["opsi_skenario"], value=KUNCI_DEFAULT,
                     clearable=False, searchable=False, className="dropdown"),
        html.Div(className="baris-p", children=[
            html.Div("Jumlah pos", className="label"),
            html.Div(id="nilai-p", className="nilai-p", children=str(config.P_DEFAULT)),
        ]),
        dcc.Slider(id="sl-p", min=config.P_MIN, max=config.P_MAKS, step=1, value=config.P_DEFAULT,
                   marks={p: str(p) for p in (1, 5, 10, 15, 20)}, className="slider", updatemode="mouseup",
                   allow_direct_input=False),
        html.Div("Kondisi lalu lintas", className="label"),
        dcc.RadioItems(id="rb-kondisi", value=config.KONDISI_DEFAULT, className="segmen",
                       options=[{"label": v, "value": k} for k, v in config.LABEL_KONDISI.items()]),
        dcc.Checklist(id="sw-pos-inti", value=[], className="sakelar",
                      options=[{"label": f"Tampilkan pos inti (≥ {config.AMBANG_POS_INTI:g}%)", "value": "ya"}]),
        dcc.Checklist(id="sw-kandidat", value=[], className="sakelar",
                      options=[{"label": "Tampilkan kandidat lain", "value": "ya"}]),
        html.Div(id="pesan-inti", className="pesan"),
    ])


def _legenda():
    return html.Div(className="kartu legenda", children=[
        html.Div("Waktu ke pos tercepat", className="label"),
        *[html.Div([html.I(className="kotak", style={"background": config.WARNA_KATEGORI[k]}), v],
                   className="legenda-baris") for k, v in config.LABEL_KATEGORI.items()],
        html.Div(className="legenda-sep"),
        html.Div([html.I(className="titik titik-pos"), "Pos terpilih"], className="legenda-baris"),
        html.Div([html.I(className="titik titik-inti"), "Pos inti"], className="legenda-baris"),
        html.Div([html.I(className="titik titik-kandidat"), "Kandidat lain"], className="legenda-baris"),
    ])


def _laci():
    return html.Div(id="laci", className="laci terbuka", children=[
        html.Button("Analisis", id="btn-laci", className="btn-laci", n_clicks=0),
        html.Div(className="laci-isi", children=[
            html.Div(id="kartu-metrik", className="kartu kartu-analisis kartu-metrik"),
            html.Div(className="kartu kartu-analisis", children=[
                html.Div([html.Span("Front Pareto", className="judul-kartu"),
                          html.Span(id="ket-pareto", className="ket")], className="kepala-kartu"),
                dcc.Graph(id="g-pareto", config={"displayModeBar": False}, className="grafik"),
            ]),
            html.Div(className="kartu kartu-analisis", children=[
                html.Div([html.Span("Kenaikan cakupan", className="judul-kartu"),
                          html.Span("Z1 terbaik per jumlah pos", className="ket")], className="kepala-kartu"),
                dcc.Graph(id="g-kenaikan", config={"displayModeBar": False}, className="grafik"),
            ]),
            html.Div(className="kartu kartu-analisis", children=[
                html.Div([html.Span("10 kelurahan cakupan terendah", className="judul-kartu")],
                         className="kepala-kartu"),
                html.Div(id="tbl-terendah", className="tabel-wadah"),
            ]),
        ]),
    ])


def buat_layout(data):
    """Kerangka halaman: peta penuh layar + kartu melayang + laci analisis."""
    batas = peta.batas_wilayah(data["geojson"])
    return html.Div(className="akar", children=[
        dcc.Store(id="st-state", data={"kunci": KUNCI_DEFAULT, "p": config.P_DEFAULT,
                                       "kondisi": config.KONDISI_DEFAULT, "solusi_id": 1, "kel": None}),
        dcc.Store(id="st-batas", data=batas),
        dcc.Store(id="st-klik-kel"),
        peta.peta_dasar(data["geojson"], batas),
        html.Header(className="bilah", children=[
            html.Div([html.Span(className="logo"),
                      html.H1("Dashboard Lokasi Pos Gawat Darurat Kota Bekasi")], className="bilah-judul"),
        ]),
        html.Aside(className="kolom-kiri", children=[_kartu_kontrol(data)]),
        html.Div(id="panel-detail", className="kartu panel-detail tersembunyi", children=[
            html.Button("×", id="btn-tutup", className="btn-tutup", n_clicks=0, title="Tutup panel"),
            html.Div(id="isi-detail"),
        ]),
        _legenda(),
        _laci(),
    ])


# ------------------------------------------------------------------ isi dinamis
def kartu_metrik(ring, kondisi, solusi_id, jumlah):
    """Ringkasan metrik solusi aktif."""
    nama_k = config.LABEL_KONDISI[kondisi].lower()
    return [
        html.Div([html.Span("Solusi aktif", className="label"),
                  html.Span(f"{solusi_id} dari {jumlah}", className="ket")], className="kepala-kartu"),
        html.Div(className="grid-metrik", children=[
            html.Div([html.Div("Z1 · cakupan", className="label"),
                      html.Div(angka(ring["Z1"], 4), className="angka")]),
            html.Div([html.Div("Z2 · waktu", className="label"),
                      html.Div([angka(ring["Z2"], 2), html.Small(" mnt")], className="angka")]),
            html.Div([html.Div("≤ 15 menit", className="label"),
                      html.Div([angka(ring["persen_15"], 1), html.Small("%")], className="angka")]),
            html.Div([html.Div("≤ 40 menit", className="label"),
                      html.Div([angka(ring["persen_40"], 1), html.Small("%")], className="angka")]),
        ]),
        html.P(f"Persentase permintaan berbobot, kondisi {nama_k}.", className="catatan"),
    ]


def tabel_terendah(baris):
    kepala = html.Tr([html.Th("Kelurahan"), html.Th("Kecamatan"), html.Th("Cakupan", className="kanan"),
                      html.Th("Kategori")])
    isi = [html.Tr([html.Td(r["nama"]), html.Td(r["kecamatan"], className="redup"),
                    html.Td(angka(r["cakupan"], 3), className="kanan mono"), html.Td(chip_kategori(r["kategori"]))])
           for r in baris]
    return html.Table([html.Thead(kepala), html.Tbody(isi)], className="tabel")


def _sel_kategori(d, k, kondisi):
    """Satu kolom kondisi: nama kondisi, chip kategori, menit kecil (kolom terpilih ditandai)."""
    isi = [html.Span(config.LABEL_KONDISI[k], className="kondisi"), chip_kategori(d["kategori"][k])]
    if d.get("menit"):
        isi.append(html.Div([html.Span(angka(d["menit"][k]["menit"], 1), className="menit"), html.Small(" mnt")]))
    return html.Div(isi, className="sel-kondisi" + (" terpilih" if k == kondisi else ""))


def _menit_terpilih(d, kondisi):
    """Angka menit besar untuk kondisi lalu lintas yang sedang dipilih."""
    if not d.get("menit"):
        return None
    m = d["menit"][kondisi]
    return html.Div(className="menit-blok", children=[
        html.Div([html.Span(angka(m["menit"], 1), className="menit-besar"), html.Span(" menit", className="satuan")]),
        html.Div(["ke pos tercepat ", html.Span(m["pos"], className="kode"),
                  f" · kondisi {config.LABEL_KONDISI[kondisi].lower()}"], className="menit-ket"),
        # Menit dan rute bisa menunjuk pos berbeda: rute ke pos κ tertinggi, menit ke pos tercepat.
        html.Div(["Pos tercepat ", html.Span(m["pos"], className="kode"), " berbeda dari pos yang melayani ",
                  html.Span(d["pos_kode"], className="kode"), "; rute di peta menuju pos yang melayani."],
                 className="beda-pos") if m["pos"] != d["pos_kode"] else None,
    ])


def panel_detail(d, kondisi):
    """Isi panel detail kelurahan (DFD 5.0): data kelurahan, pos melayani, waktu tempuh."""
    cakupan = (html.Div("Tidak tercakup (κ = 0); ditampilkan pos terdekat", className="peringatan")
               if not d["tercakup"] else html.Div(angka(d["cakupan"], 3), className="angka"))
    return [
        html.Div(className="kepala-detail", children=[
            html.Div(f"Kecamatan {d['kecamatan']}", className="label"), html.H2(d["nama"])]),
        html.Div(className="grid-detail", children=[
            html.Div([html.Div("Penduduk", className="label"), html.Div(angka(d["penduduk"]), className="mono")]),
            html.Div([html.Div("Lansia 65+", className="label"), html.Div(angka(d["lansia"]), className="mono")]),
            html.Div([html.Div("Bobot permintaan", className="label"),
                      html.Div(angka(d["bobot"], 4), className="mono")]),
        ]),
        html.Div(className="blok blok-pos", children=[
            html.Div([html.Div("Pos yang melayani (κ tertinggi)", className="label"),
                      html.Div([html.Span(d["pos_kode"], className="kode"), d["pos_nama"]],
                               className="pos-melayani")]),
            html.Div([html.Div("Cakupan", className="label"), cakupan], className="kanan"),
        ]),
        html.Div(className="blok blok-waktu", children=[
            html.Div("Waktu tempuh ke pos tercepat", className="label"),
            _menit_terpilih(d, kondisi),
            html.Div([_sel_kategori(d, k, kondisi) for k in config.KONDISI], className="grid-kategori"),
        ]),
    ]
