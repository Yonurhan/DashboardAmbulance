"""Titik masuk dasbor. Jalankan:  .venv\\Scripts\\python app.py  lalu buka http://127.0.0.1:8050"""
from dash import Dash

import callbacks
import config
import data_loader
import layout


def buat_app():
    """Buat aplikasi Dash: data olahan dibaca sekali di sini."""
    data = data_loader.muat_semua(config.DIR_OLAHAN)
    app = Dash(__name__, title="Dashboard Lokasi Pos Gawat Darurat Kota Bekasi", update_title=None)
    app.layout = layout.buat_layout(data)
    callbacks.daftarkan_callback(app, data)
    return app


dash_app = buat_app()
app = dash_app.server  # objek WSGI (Flask) yang dicari Vercel: entrypoint app.py, variabel `app`

if __name__ == "__main__":
    dash_app.run(host="127.0.0.1", port=8050, debug=False)
