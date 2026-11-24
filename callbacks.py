"""Fungsi interaksi dasbor, dikelompokkan per proses DFD level 1.

Semua logika ada di logika.py / grafik.py / peta.py; callback hanya merangkai.
State aktif (kunci, p, kondisi, solusi_id, kel) disimpan di dcc.Store "st-state".
"""
from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate

import config
import grafik
import layout
import logika
import peta


def state_baru(state, pemicu, nilai):
    """Hitung state berikutnya dari satu pemicu (fungsi murni, diuji pytest).

    pemicu: "dd-skenario" | "sl-p" | "rb-kondisi" | "g-pareto" | "geo-kel" | "btn-tutup"
    """
    s = dict(state)
    if pemicu == "dd-skenario" and nilai:
        s.update(kunci=nilai, solusi_id=1)
    elif pemicu == "sl-p" and nilai is not None:
        s.update(p=int(nilai), solusi_id=1)
    elif pemicu == "rb-kondisi" and nilai in config.KONDISI:
        s.update(kondisi=nilai)
    elif pemicu == "g-pareto" and nilai is not None:
        s.update(solusi_id=int(nilai))
    elif pemicu == "geo-kel" and nilai:
        s.update(kel=nilai)
    elif pemicu == "btn-tutup":
        s.update(kel=None)
    return s


def _id_titik_pareto(click):
    try:
        return int(click["points"][0]["customdata"])
    except (TypeError, KeyError, IndexError, ValueError):
        return None


def _kode_kelurahan(klik):
    """Kode dari Store st-klik-kel ({kode, t}) yang diisi assets/peta.js."""
    try:
        return klik["kode"]
    except (TypeError, KeyError):
        return None


def daftarkan_callback(app, data):
    """Daftarkan semua callback ke aplikasi."""

    # ================================================= Proses 3.0 Tampilkan Solusi
    @app.callback(
        Output("st-state", "data"), Output("g-pareto", "clickData"),
        Input("dd-skenario", "value"), Input("sl-p", "value"), Input("rb-kondisi", "value"),
        Input("g-pareto", "clickData"), Input("st-klik-kel", "data"), Input("btn-tutup", "n_clicks"),
        State("st-state", "data"),
        prevent_initial_call=True)
    def perbarui_state(skenario, p, kondisi, klik_pareto, klik_kel, _n_tutup, state):
        pemicu = {"st-klik-kel": "geo-kel"}.get(ctx.triggered_id, ctx.triggered_id)
        nilai = {"dd-skenario": skenario, "sl-p": p, "rb-kondisi": kondisi,
                 "g-pareto": _id_titik_pareto(klik_pareto), "geo-kel": _kode_kelurahan(klik_kel)}.get(pemicu)
        if pemicu == "g-pareto" and nilai is None:
            raise PreventUpdate
        return state_baru(state, pemicu, nilai), None

    @app.callback(
        Output("geo-kel", "hideout"), Output("lap-pos", "children"), Output("kartu-metrik", "children"),
        Output("g-pareto", "figure"), Output("ket-pareto", "children"), Output("nilai-p", "children"),
        Input("st-state", "data"))
    def tampilkan_solusi(state):
        daftar = logika.daftar_solusi(data, state["kunci"], state["p"])
        sol = logika.solusi_aktif(data, state["kunci"], state["p"], state["solusi_id"])
        ring = logika.ringkasan_metrik(sol, state["kondisi"])
        return (peta.hideout_kelurahan(sol, state["kondisi"], state["kel"]),
                peta.lapisan_pos(sol, data),
                layout.kartu_metrik(ring, sol["solusi_id"], len(daftar)),
                grafik.figur_pareto(daftar, sol["solusi_id"]),
                f"p = {state['p']}: {len(daftar)} solusi",
                str(state["p"]))

    @app.callback(Output("lap-kandidat", "children"), Input("st-state", "data"), Input("sw-kandidat", "value"))
    def tampilkan_kandidat(state, sakelar):
        if not sakelar:
            return []
        sol = logika.solusi_aktif(data, state["kunci"], state["p"], state["solusi_id"])
        return peta.lapisan_kandidat(sol, data)

    # ================================================= Proses 4.0 Tampilkan Analisis
    @app.callback(Output("g-kenaikan", "figure"), Output("tbl-terendah", "children"), Input("st-state", "data"))
    def tampilkan_analisis(state):
        sol = logika.solusi_aktif(data, state["kunci"], state["p"], state["solusi_id"])
        kenaikan = data["metrik"][state["kunci"]]["kenaikan_cakupan"]
        return (grafik.figur_kenaikan(kenaikan, state["p"]),
                layout.tabel_terendah(logika.kelurahan_terendah(sol, data, state["kondisi"])))

    @app.callback(Output("lap-inti", "children"), Output("pesan-inti", "children"),
                  Input("st-state", "data"), Input("sw-pos-inti", "value"))
    def tampilkan_pos_inti(state, sakelar):
        if not sakelar:
            return [], ""
        daftar = logika.pos_inti(data, state["kunci"], state["p"])
        return peta.lapisan_pos_inti(daftar, data), logika.pesan_pos_inti(len(daftar), state["p"])

    # ================================================= Kerangka tampilan (bukan proses DFD)
    # Peta dipaskan ke seluruh Kota Bekasi setelah dimuat dan setiap laci dibuka/dilipat.
    # dash-leaflet 1.1.3 hanya menjalankan fitBounds lewat prop `viewport` (bukan `bounds`).
    # Padding = ruang yang tertutup kolom kiri, bilah judul, legenda, dan laci. Angka 340/80/395/110
    # mengikuti --kiri dan --laci di assets/style.css; ubah keduanya bersamaan.
    app.clientside_callback(
        """function(n, kelas, batas) {
            // Ditunda agar peta sudah berukuran penuh dan transisi laci selesai sebelum fitBounds.
            // HP (<= 640 px, lihat @media di style.css): panel tersembunyi, jadi padding kecil saja.
            const hp = window.innerWidth <= 640;
            const bawah = hp ? 60 : ((kelas || "").includes("terbuka") ? 395 : 110);
            const pas = function () {
                window.dash_clientside.set_props("peta", {viewport: {bounds: batas,
                    options: {paddingTopLeft: hp ? [10, 70] : [340, 80], paddingBottomRight: hp ? [10, bawah] : [30, bawah]}}});
            };
            // dua kali: saat muat awal komponen peta dimuat asinkron, jadi panggilan pertama bisa terlalu cepat
            setTimeout(pas, 400);
            setTimeout(pas, 1600);
            return window.dash_clientside.no_update;
        }""",
        Output("peta", "viewport"), Input("peta", "n_loads"), Input("laci", "className"),
        State("st-batas", "data"))

    # Laci: keadaan awal mengikuti lebar layar (HP terlipat, desktop terbuka); setelah itu tiap klik menukar.
    app.clientside_callback(
        """function(n, kelas) {
            if (!n) { return window.innerWidth <= 640 ? "laci" : "laci terbuka"; }
            return (kelas || "").includes("terbuka") ? "laci" : "laci terbuka";
        }""",
        Output("laci", "className"), Input("btn-laci", "n_clicks"), State("laci", "className"))

    # Tombol khusus HP: ⚙ membuka/menutup kartu kontrol, "Legenda" membuka/menutup isi legenda.
    tukar_terbuka = """function(n, kelas) {
        kelas = kelas || "";
        return kelas.includes(" terbuka") ? kelas.replace(" terbuka", "") : kelas + " terbuka";
    }"""
    for tombol, target in (("btn-kontrol", "kolom-kiri"), ("btn-legenda", "legenda")):
        app.clientside_callback(tukar_terbuka, Output(target, "className"), Input(tombol, "n_clicks"),
                                State(target, "className"), prevent_initial_call=True)

    # ================================================= Proses 5.0 Tampilkan Detail Kelurahan
    @app.callback(Output("isi-detail", "children"), Output("panel-detail", "className"),
                  Output("lap-rute", "children"), Input("st-state", "data"))
    def tampilkan_detail(state):
        if not state.get("kel"):
            return [], "kartu panel-detail tersembunyi", []
        sol = logika.solusi_aktif(data, state["kunci"], state["p"], state["solusi_id"])
        d = logika.detail_kelurahan(data, state["kunci"], sol, state["kel"])
        return layout.panel_detail(d, state["kondisi"]), "kartu panel-detail", peta.lapisan_rute(d)
