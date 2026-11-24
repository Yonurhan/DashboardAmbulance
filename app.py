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


app = buat_app()
server = app.server  # untuk gunicorn saat deploy (Render): gunicorn app:server

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=False)
