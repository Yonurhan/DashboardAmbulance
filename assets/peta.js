/* Fungsi gaya dan tooltip poligon kelurahan untuk dash-leaflet 1.x.
 * Dipanggil lewat dash_extensions.javascript.Namespace("dasbor", "peta").
 * hideout = {warna: {kode: hex}, kategori: {kode: label}, terpilih: kode|null, aksen: hex}
 */
window.dasbor = Object.assign({}, window.dasbor, {
  peta: {
    gaya: function (feature, context) {
      const h = (context && context.hideout) || {};
      window.dasbor._hideout = h;   // disimpan untuk tooltip (dibaca saat tooltip dibuka)
      const kode = feature.properties.kode;
      const pilih = h.terpilih === kode;
      return {
        fillColor: (h.warna || {})[kode] || "#BDB8AE",
        fillOpacity: pilih ? 0.78 : 0.58,
        color: pilih ? h.aksen : "#FFFFFF",
        weight: pilih ? 3.5 : 1.2,
        opacity: 1,
      };
    },
    tooltip: function (feature, layer) {
      layer.bindTooltip(function () {
        const h = window.dasbor._hideout || {};
        const p = feature.properties;
        const kat = (h.kategori || {})[p.kode] || "";
        return '<div class="tt-nama">' + p.nama + '</div>' +
               '<div class="tt-sub">' + p.kecamatan + ' · ' + kat + '</div>';
      }, {sticky: true, direction: "top", className: "tt-kel", opacity: 1});
      // clickData GeoJSON di dash-leaflet 1.1.3 tidak membawa fitur, jadi kode kelurahan
      // dikirim ke Store "st-klik-kel" (t = waktu, agar klik ulang pada kelurahan sama tetap terbaca).
      layer.on("click", function () {
        window.dash_clientside.set_props("st-klik-kel", {data: {kode: feature.properties.kode, t: Date.now()}});
      });
    },
  },
});
