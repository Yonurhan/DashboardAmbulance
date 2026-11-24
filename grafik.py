"""Figur Plotly untuk kartu analisis: front Pareto (DFD 3.0) dan kenaikan cakupan (DFD 4.0)."""
import plotly.graph_objects as go

import config
from format_angka import angka

FONT = "IBM Plex Sans, sans-serif"
FONT_MONO = "IBM Plex Mono, monospace"
WARNA_TITIK = "#8A867E"       # titik non-aktif: tinta sekunder, bukan warna kategori
WARNA_GRID = "#ECE9E3"


def _tata_letak(fig, judul_x, judul_y):
    fig.update_layout(
        margin={"l": 48, "r": 12, "t": 6, "b": 36}, height=222,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT, "size": 11, "color": config.WARNA_TEKS},
        showlegend=False, hovermode="closest",
        hoverlabel={"bgcolor": "#FFFFFF", "bordercolor": config.WARNA_GARIS,
                    "font": {"family": FONT_MONO, "size": 11, "color": config.WARNA_TEKS}},
    )
    sumbu = {"fixedrange": True,  # tanpa zoom/drag; tooltip tetap ada
             "gridcolor": WARNA_GRID, "zeroline": False, "linecolor": config.WARNA_GARIS,
             "tickfont": {"family": FONT_MONO, "size": 10, "color": "#6B675F"},
             "title": {"font": {"size": 11, "color": "#6B675F"}}}
    fig.update_xaxes(title_text=judul_x, **sumbu)
    fig.update_yaxes(title_text=judul_y, **sumbu)
    return fig


def figur_pareto(daftar_solusi, solusi_id_aktif):
    """Scatter X = Z2 (menit), Y = Z1 untuk p terpilih; customdata = solusi_id."""
    fig = go.Figure()
    biasa = [s for s in daftar_solusi if s["solusi_id"] != solusi_id_aktif]
    aktif = [s for s in daftar_solusi if s["solusi_id"] == solusi_id_aktif]
    templat = "Solusi %{customdata}<br>Z1 %{y:.4f}<br>Z2 %{x:.2f} menit<extra></extra>"
    if len(daftar_solusi) > 1:   # garis tipis penghubung front, urut Z2
        urut = sorted(daftar_solusi, key=lambda s: s["Z2"])
        fig.add_trace(go.Scatter(x=[s["Z2"] for s in urut], y=[s["Z1"] for s in urut], mode="lines",
                                 line={"color": WARNA_GRID, "width": 2}, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[s["Z2"] for s in biasa], y=[s["Z1"] for s in biasa], customdata=[s["solusi_id"] for s in biasa],
        mode="markers", hovertemplate=templat,
        marker={"size": 9, "color": WARNA_TITIK, "line": {"color": "#FFFFFF", "width": 2}}))
    fig.add_trace(go.Scatter(
        x=[s["Z2"] for s in aktif], y=[s["Z1"] for s in aktif], customdata=[s["solusi_id"] for s in aktif],
        mode="markers", hovertemplate=templat,
        marker={"size": 14, "color": config.WARNA_AKSEN, "line": {"color": "#FFFFFF", "width": 2}}))
    if len(daftar_solusi) == 1:
        fig.add_annotation(text="Hanya satu solusi Pareto pada p ini", xref="paper", yref="paper",
                           x=0.5, y=0.08, showarrow=False, font={"size": 11, "color": "#6B675F"})
    return _tata_letak(fig, "Z2 · waktu tempuh berbobot (menit)", "Z1 · cakupan")


def figur_kenaikan(kenaikan, p_aktif):
    """Garis Z1 terbaik terhadap p; selisih terhadap p − 1 di tooltip; p aktif ditandai."""
    xs = [r["p"] for r in kenaikan]
    ys = [r["Z1_terbaik"] for r in kenaikan]
    selisih = ["—" if r["selisih"] is None else ("+" if r["selisih"] >= 0 else "−") + angka(abs(r["selisih"]), 4)
               for r in kenaikan]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines+markers", customdata=[[s] for s in selisih],
        line={"color": "#4A4740", "width": 2}, marker={"size": 8, "color": "#4A4740",
                                                     "line": {"color": "#FFFFFF", "width": 2}},
        hovertemplate="p = %{x}<br>Z1 terbaik %{y:.4f}<br>selisih dari p − 1: %{customdata[0]}<extra></extra>"))
    titik = [r for r in kenaikan if r["p"] == int(p_aktif)]
    if titik:
        fig.add_trace(go.Scatter(x=[titik[0]["p"]], y=[titik[0]["Z1_terbaik"]], mode="markers",
                                 marker={"size": 14, "color": config.WARNA_AKSEN,
                                         "line": {"color": "#FFFFFF", "width": 2}},
                                 hoverinfo="skip"))
    fig = _tata_letak(fig, "jumlah pos (p)", "Z1 terbaik")
    fig.update_xaxes(dtick=1 if len(xs) <= 10 else 2)
    return fig
