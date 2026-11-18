"""Metrik analisis per skenario: kenaikan cakupan dan frekuensi pos inti."""
from collections import defaultdict


def kenaikan_cakupan(solusi):
    """Z1 terbaik per p dan selisihnya terhadap p sebelumnya (None untuk p pertama)."""
    terbaik = {}
    for s in solusi:
        terbaik[s["p"]] = max(terbaik.get(s["p"], float("-inf")), s["Z1"])
    out, sebelum = [], None
    for p in sorted(terbaik):
        z = terbaik[p]
        out.append({"p": p, "Z1_terbaik": z, "selisih": None if sebelum is None else z - sebelum})
        sebelum = z
    return out


def frekuensi_faskes(solusi, kode_faskes):
    """Frekuensi pos inti untuk setiap p awal.

    Untuk p_awal, frekuensi faskes = rata-rata (p = p_awal..p maks) dari persentase
    solusi Pareto di p itu yang memuat faskes; setiap p berbobot sama.
    Hasil: {str(p_awal): {kode: persen}}.
    """
    per_p = defaultdict(list)
    for s in solusi:
        per_p[s["p"]].append(set(s["pos"]))
    daftar_p = sorted(per_p)
    persen_p = {p: {k: 100.0 * sum(k in pos for pos in per_p[p]) / len(per_p[p]) for k in kode_faskes}
                for p in daftar_p}
    out = {}
    for i, p_awal in enumerate(daftar_p):
        rentang = daftar_p[i:]
        out[str(p_awal)] = {k: sum(persen_p[p][k] for p in rentang) / len(rentang) for k in kode_faskes}
    return out
