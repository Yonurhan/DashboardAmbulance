"""Format angka gaya Indonesia, dipakai tampilan (layout.py) dan grafik (grafik.py)."""


def angka(x, d=0):
    """1234.5 -> '1.234,5' (pemisah ribuan titik, desimal koma)."""
    s = f"{x:,.{d}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")
