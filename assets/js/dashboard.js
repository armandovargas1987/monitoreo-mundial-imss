(function () {
  const data = window.MONITOREO_DATA;
  if (!data || !window.L) return;

  const { estadio, umfs } = data;
  const map = L.map('map', { scrollWheelZoom: true }).setView(
    [estadio.lat, estadio.lon],
    13
  );

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap',
    maxZoom: 18,
  }).addTo(map);

  L.circle([estadio.lat, estadio.lon], {
    color: '#a57f2c',
    fillColor: '#a57f2c',
    fillOpacity: 0.06,
    weight: 2,
    radius: 10000,
  }).addTo(map);

  const estadioIcon = L.divIcon({
    className: 'marker-estadio',
    html: '<div style="background:#611232;color:#fff;font-weight:800;font-size:11px;padding:6px 8px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.25);white-space:nowrap">⚽ ' +
      estadio.nombre.replace('Estadio ', '') + '</div>',
    iconSize: [120, 30],
    iconAnchor: [60, 15],
  });

  L.marker([estadio.lat, estadio.lon], { icon: estadioIcon, zIndexOffset: 1000 })
    .addTo(map)
    .bindPopup('<strong>' + estadio.nombre + '</strong><br>Sede Mundial 2026');

  const umfMarkers = [];

  umfs.forEach(function (umf) {
    const marker = L.circleMarker([umf.lat, umf.lon], {
      radius: 7,
      color: '#13795c',
      fillColor: '#1a5c45',
      fillOpacity: 0.85,
      weight: 2,
    }).addTo(map);

    marker.bindPopup(
      '<strong>' + umf.nombre + '</strong><br>' +
      'Distancia al estadio: <b>' + umf.dist_km + ' km</b><br>' +
      'Hospital: ' + (umf.hospital || '—') + '<br>' +
      'Consultorios MF: ' + (umf.cons_mf || '—')
    );

    umfMarkers.push({ marker, umf });
  });

  if (umfs.length) {
    const bounds = L.latLngBounds(
      umfs.map((u) => [u.lat, u.lon]).concat([[estadio.lat, estadio.lon]])
    );
    map.fitBounds(bounds.pad(0.12));
  }

  const rows = document.querySelectorAll('tbody tr[data-lat]');
  rows.forEach(function (row) {
    row.addEventListener('click', function () {
      const lat = parseFloat(row.dataset.lat);
      const lon = parseFloat(row.dataset.lon);
      rows.forEach((r) => r.classList.remove('active-row'));
      row.classList.add('active-row');
      map.setView([lat, lon], 15, { animate: true });
      const match = umfMarkers.find(
        (m) => m.umf.lat === lat && m.umf.lon === lon
      );
      if (match) match.marker.openPopup();
    });
  });
})();
