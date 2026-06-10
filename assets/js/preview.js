const META = {
  'Estadio Azteca': { ciudad: 'Ciudad de México', delegacion: 'CD México Sur', lat: 19.3029, lon: -99.1506, capacidad: 87523 },
  'Estadio Akron': { ciudad: 'Guadalajara, Jal.', delegacion: 'Jalisco', lat: 20.6819, lon: -103.4616, capacidad: 49850 },
  'Estadio BBVA': { ciudad: 'Monterrey, N.L.', delegacion: 'Nuevo León', lat: 25.6866, lon: -100.2451, capacidad: 53500 },
};

let allData = {};
let activeSede = 'Estadio Azteca';
let map;

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function render() {
  const meta = META[activeSede];
  const umfs = allData[activeSede] || [];
  const distProm = umfs.length
    ? (umfs.reduce((a, u) => a + u.dist_km, 0) / umfs.length).toFixed(1)
    : '0';
  const conContinua = umfs.filter((u) => u.atencion_continua !== '0').length;
  const consTotal = umfs.reduce((a, u) => a + (parseInt(u.cons_mf, 10) || 0), 0);

  document.getElementById('sedes-nav').innerHTML = Object.entries(META).map(([name, info]) =>
    `<a class="sede-tab ${name === activeSede ? 'active' : ''}" href="#" data-sede="${esc(name)}">
      <span class="sede-name">${esc(name)}</span>
      <span class="sede-city">${esc(info.ciudad)}</span>
    </a>`
  ).join('');

  document.getElementById('app').innerHTML = `
    <section class="panel stats">
      <h2>${esc(activeSede)}</h2>
      <p class="delegacion">Delegación IMSS: ${esc(meta.delegacion)}</p>
      <div class="kpi-grid">
        <article class="kpi"><span class="kpi-val">${umfs.length}</span><span class="kpi-label">UMF ≤ 10 km</span></article>
        <article class="kpi"><span class="kpi-val">${distProm} km</span><span class="kpi-label">Distancia promedio</span></article>
        <article class="kpi"><span class="kpi-val">${conContinua}</span><span class="kpi-label">Atención continua</span></article>
        <article class="kpi"><span class="kpi-val">${meta.capacidad.toLocaleString()}</span><span class="kpi-label">Capacidad estadio</span></article>
      </div>
      <div class="fuente"><strong>Fuente cruzada:</strong> Sistema de Regionalización IMSS · CUUMSP Feb 2026</div>
    </section>
    <section class="panel map-panel"><div id="map"></div>
      <div class="map-legend">
        <span><i class="dot estadio"></i> Estadio</span>
        <span><i class="dot umf"></i> UMF cercana</span>
        <span><i class="dot radio"></i> Radio 10 km</span>
      </div>
    </section>
    <section class="panel table-panel">
      <div class="panel-head"><h3>UMF cercanas al estadio</h3><span class="badge">${umfs.length} unidades</span></div>
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>Unidad</th><th>Delegación</th><th>Dist. estadio</th><th>Hospital refiere</th><th>Dist. hospital</th><th>Cons. MF</th><th>PAMF</th><th>Servicios</th></tr></thead>
        <tbody>${umfs.map((u, i) => `
          <tr data-lat="${u.lat}" data-lon="${u.lon}">
            <td>${i + 1}</td>
            <td><strong>${esc(u.nombre)}</strong><small>${esc(u.cve)}</small></td>
            <td>${esc(u.delegacion)}</td>
            <td><span class="pill">${u.dist_km} km</span></td>
            <td>${esc(u.hospital || '—')}</td>
            <td>${esc(u.dist_hosp || '—')}</td>
            <td>${esc(u.cons_mf || '—')}</td>
            <td>${esc(u.pamf || '—')}</td>
            <td>
              ${u.atencion_continua !== '0' ? '<span class="tag tag-green">Continua</span>' : ''}
              ${u.urgencias !== '0' ? '<span class="tag tag-red">Urgencias</span>' : ''}
            </td>
          </tr>`).join('') || '<tr><td colspan="9" class="empty">Sin unidades.</td></tr>'}
        </tbody>
      </table></div>
    </section>
    <section class="panel alert-panel">
      <div class="panel-head"><h3>Monitoreo de entorno · Zona sede</h3><span class="live">● En línea</span></div>
      <div class="alert-grid">
        <article class="alert-card nivel-bajo"><h4>Rutas de acceso</h4><p>UMF más cercana: <strong>${esc(umfs[0]?.nombre || 'N/D')}</strong> (${esc(umfs[0]?.dist_km ?? '—')} km)</p></article>
        <article class="alert-card nivel-medio"><h4>Capacidad instalada</h4><p>${consTotal} consultorios MF en radio de 10 km.</p></article>
        <article class="alert-card nivel-info"><h4>Regionalización</h4><p>Datos sincronizados desde catálogos delegacionales (${esc(meta.delegacion)}).</p></article>
      </div>
    </section>`;

  document.querySelectorAll('.sede-tab').forEach((tab) => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      activeSede = tab.dataset.sede;
      render();
    });
  });

  initMap(meta, umfs);
  bindRows();
}

function initMap(meta, umfs) {
  if (map) map.remove();
  map = L.map('map').setView([meta.lat, meta.lon], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OSM' }).addTo(map);
  L.circle([meta.lat, meta.lon], { color: '#a57f2c', fillOpacity: 0.06, radius: 10000 }).addTo(map);
  const icon = L.divIcon({
    html: `<div style="background:#611232;color:#fff;font-weight:800;font-size:11px;padding:6px 8px;border-radius:8px">⚽ ${activeSede.replace('Estadio ', '')}</div>`,
    iconSize: [120, 30], iconAnchor: [60, 15],
  });
  L.marker([meta.lat, meta.lon], { icon, zIndexOffset: 1000 }).addTo(map);
  window._umfMarkers = [];
  umfs.forEach((u) => {
    const m = L.circleMarker([u.lat, u.lon], { radius: 7, color: '#13795c', fillColor: '#1a5c45', fillOpacity: 0.85 }).addTo(map);
    m.bindPopup(`<strong>${esc(u.nombre)}</strong><br>${u.dist_km} km al estadio`);
    window._umfMarkers.push({ m, u });
  });
  if (umfs.length) {
    const bounds = L.latLngBounds(umfs.map((u) => [u.lat, u.lon]).concat([[meta.lat, meta.lon]]));
    map.fitBounds(bounds.pad(0.12));
  }
}

function bindRows() {
  document.querySelectorAll('tbody tr[data-lat]').forEach((row) => {
    row.addEventListener('click', () => {
      const lat = parseFloat(row.dataset.lat);
      const lon = parseFloat(row.dataset.lon);
      document.querySelectorAll('tbody tr').forEach((r) => r.classList.remove('active-row'));
      row.classList.add('active-row');
      map.setView([lat, lon], 15);
      const hit = (window._umfMarkers || []).find((x) => x.u.lat === lat && x.u.lon === lon);
      if (hit) hit.m.openPopup();
    });
  });
}

fetch('data/estadios_umf.json')
  .then((r) => r.json())
  .then((data) => { allData = data; render(); })
  .catch((err) => {
    document.getElementById('app').innerHTML = `<section class="panel stats"><p>Error cargando datos: ${esc(err.message)}</p></section>`;
  });

if (!sessionStorage.getItem('monitoreo_auth')) location.href = 'index.html';
