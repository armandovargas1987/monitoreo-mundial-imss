const ESTADIOS = [
  { id: 'est-cdmx', city: 'CDMX', nombre: 'Estadio Ciudad de México (Azteca)', lat: 19.3030, lng: -99.1504, aforo: 103000 },
  { id: 'est-gdl', city: 'GDL', nombre: 'Estadio Guadalajara (Akron)', lat: 20.6819, lng: -103.4626, aforo: 46000 },
  { id: 'est-mty', city: 'MTY', nombre: 'Estadio Monterrey (BBVA)', lat: 25.6694, lng: -100.2443, aforo: 53000 },
];
const FANFEST = [
  { id: 'ff-zocalo', city: 'CDMX', nombre: 'FIFA Fan Fest · Zócalo', lat: 19.4326, lng: -99.1332, aforo: 60000 },
  { id: 'ff-angel', city: 'CDMX', nombre: 'Punto de celebración · Ángel de la Independencia', lat: 19.4270, lng: -99.1677, aforo: 200000 },
  { id: 'ff-gdl', city: 'GDL', nombre: 'FIFA Fan Fest · Plaza de la Liberación', lat: 20.6767, lng: -103.3401, aforo: 70000 },
  { id: 'ff-mty', city: 'MTY', nombre: 'FIFA Fan Fest · Parque Fundidora', lat: 25.6785, lng: -100.2840, aforo: 51000 },
];
const PARTIDOS = [
  { n: 1, fecha: '2026-06-11', hora: '13:00', city: 'CDMX', partido: 'México vs Sudáfrica', nivel: 'critico' },
  { n: 2, fecha: '2026-06-11', hora: '20:00', city: 'GDL', partido: 'Corea del Sur vs Rep. Checa', nivel: 'medio' },
  { n: 3, fecha: '2026-06-14', hora: '20:00', city: 'MTY', partido: 'Suecia vs Túnez', nivel: 'medio' },
  { n: 4, fecha: '2026-06-17', hora: '19:30', city: 'CDMX', partido: 'Uzbekistán vs Colombia', nivel: 'alto' },
  { n: 5, fecha: '2026-06-18', hora: '19:30', city: 'GDL', partido: 'México vs Corea del Sur', nivel: 'critico' },
  { n: 6, fecha: '2026-06-20', hora: '22:00', city: 'MTY', partido: 'Japón vs Túnez', nivel: 'medio' },
  { n: 7, fecha: '2026-06-23', hora: '20:00', city: 'GDL', partido: 'Colombia vs Rep. Dem. del Congo', nivel: 'alto' },
  { n: 8, fecha: '2026-06-24', hora: '19:30', city: 'CDMX', partido: 'México vs Rep. Checa', nivel: 'critico' },
  { n: 9, fecha: '2026-06-24', hora: '19:00', city: 'MTY', partido: 'Sudáfrica vs Corea del Sur', nivel: 'medio' },
  { n: 10, fecha: '2026-06-26', hora: '18:00', city: 'GDL', partido: 'Uruguay vs España', nivel: 'alto' },
  { n: 11, fecha: '2026-06-29', hora: '19:00', city: 'MTY', partido: 'Dieciseisavos de final', nivel: 'alto' },
  { n: 12, fecha: '2026-06-30', hora: '16:45', city: 'CDMX', partido: 'Dieciseisavos de final', nivel: 'alto' },
  { n: 13, fecha: '2026-07-05', hora: '16:45', city: 'CDMX', partido: 'Octavos de final', nivel: 'critico' },
];

let UNIDADES = [], MARCHAS = [], OOAD = [], UNIT_MK = [];
const CITY_CENTER = { ALL: [23.0, -101.5, 5], CDMX: [19.40, -99.15, 11], GDL: [20.67, -103.40, 11], MTY: [25.67, -100.27, 11] };
const RADIO_KM = 5;
const HEX = { rojo: '#c1121f', naranja: '#d97316', amarillo: '#e0a800', verde: '#1a5c45' };
let CITY = 'ALL', SELDAY = null;
const fmt = (n) => n.toLocaleString('es-MX');

function haversine(a, b, c, d) {
  const R = 6371, dLa = (c - a) * Math.PI / 180, dLo = (d - b) * Math.PI / 180;
  const s = Math.sin(dLa / 2) ** 2 + Math.cos(a * Math.PI / 180) * Math.cos(c * Math.PI / 180) * Math.sin(dLo / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(s), Math.sqrt(1 - s));
}
function nivelHex(n) { return n === 'alto' ? HEX.naranja : n === 'medio' ? HEX.amarillo : n === 'critico' ? HEX.rojo : HEX.verde; }
function estadoClass(e) { return e === 'ACTIVA' ? 'activa' : e === 'PROGRAMADA' ? 'prog' : 'concl'; }
function unidadesEnRadio(m) {
  return UNIDADES.map((u) => ({ ...u, dist: haversine(m.lat, m.lng, u.lat, u.lng) }))
    .filter((u) => u.dist <= RADIO_KM).sort((a, b) => a.dist - b.dist);
}
const visC = (i) => CITY === 'ALL' || i.city === CITY;
const visD = (i) => !SELDAY || (i.fecha && i.fecha === SELDAY);

const map = L.map('map').setView([CITY_CENTER.ALL[0], CITY_CENTER.ALL[1]], CITY_CENTER.ALL[2]);
const tileStreet = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 19,
});
const tileSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  attribution: '&copy; Esri, Maxar, Earthstar Geographics', maxZoom: 19,
});
const tileLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
  attribution: '', maxZoom: 19,
});
let mapBase = 'street';
let labelsOnMap = null;
let mapTypeBtn = null;

function syncMapBaseUI() {
  document.querySelectorAll('#mapBaseSeg button').forEach((b) => {
    b.classList.toggle('on', b.dataset.base === mapBase);
  });
  if (mapTypeBtn) {
    const sat = mapBase === 'satellite';
    mapTypeBtn.textContent = sat ? '🗺 Mapa' : '🛰 Satélite';
    mapTypeBtn.classList.toggle('on-sat', sat);
    mapTypeBtn.title = sat ? 'Volver a vista de mapa' : 'Vista satelital';
  }
}

function setMapBase(mode) {
  if (mode === mapBase) return;
  mapBase = mode;
  map.removeLayer(tileStreet);
  map.removeLayer(tileSat);
  if (labelsOnMap) { map.removeLayer(labelsOnMap); labelsOnMap = null; }
  if (mode === 'satellite') {
    tileSat.addTo(map);
    labelsOnMap = tileLabels;
    labelsOnMap.addTo(map);
  } else {
    tileStreet.addTo(map);
  }
  syncMapBaseUI();
}
tileStreet.addTo(map);

const MapTypeControl = L.Control.extend({
  options: { position: 'topright' },
  onAdd() {
    const wrap = L.DomUtil.create('div', 'leaflet-bar map-type-ctl');
    const btn = L.DomUtil.create('button', 'map-type-btn', wrap);
    btn.type = 'button';
    mapTypeBtn = btn;
    btn.onclick = () => setMapBase(mapBase === 'street' ? 'satellite' : 'street');
    L.DomEvent.disableClickPropagation(wrap);
    L.DomEvent.disableScrollPropagation(wrap);
    syncMapBaseUI();
    return wrap;
  },
});
map.addControl(new MapTypeControl());

document.querySelectorAll('#mapBaseSeg button').forEach((b) => {
  b.onclick = () => setMapBase(b.dataset.base);
});

const L_est = L.layerGroup().addTo(map), L_fan = L.layerGroup().addTo(map);
const L_hosp = L.layerGroup().addTo(map), L_umf = L.layerGroup().addTo(map);
const L_march = L.layerGroup().addTo(map), L_ring = L.layerGroup().addTo(map), L_lines = L.layerGroup().addTo(map);

const divIcon = (cls, txt, ex = '') => L.divIcon({
  className: '', html: `<div class="mk ${cls} ${ex}">${txt}</div>`, iconSize: [30, 30], iconAnchor: [15, 15],
});

function drawAll() {
  [L_est, L_fan, L_hosp, L_umf, L_march, L_ring, L_lines].forEach((g) => g.clearLayers());
  ESTADIOS.filter(visC).forEach((e) => L.marker([e.lat, e.lng], { icon: divIcon('mk-est', '⚽') })
    .bindPopup(`<span class="poptag" style="background:var(--guinda)">Estadio</span><br><b>${e.nombre}</b><br>Aforo: ${fmt(e.aforo)}`).addTo(L_est));
  FANFEST.filter(visC).forEach((f) => L.marker([f.lat, f.lng], { icon: divIcon('mk-fan', '★') })
    .bindPopup(`<span class="poptag" style="background:var(--gold)">Fan Fest</span><br><b>${f.nombre}</b><br>Aforo: ${fmt(f.aforo)}`).addTo(L_fan));

  UNIT_MK = [];
  UNIDADES.filter(visC).forEach((u) => {
    const grp = u.tipo === 'HOSP' ? L_hosp : L_umf;
    const oo = OOAD.find((o) => o.ciudad === u.city);
    const dir = u.direccion ? `<br>📍 ${u.direccion}${u.cp ? (' · C.P. ' + u.cp) : ''}` : '';
    const extra = u.hospital_ref ? `<br>🏥 Refiere: ${u.hospital_ref}` : '';
    const deleg = u.delegacion ? `<br><span style="color:var(--gray)">${u.delegacion}</span>` : '';
    const ood = oo ? `<br><span style="color:var(--gray)">OOAD: ${oo.nombre}</span>` : '';
    const mk = L.marker([u.lat, u.lng], { icon: divIcon(u.tipo === 'HOSP' ? 'mk-hosp' : 'mk-umf', '✚') })
      .bindPopup(`<span class="poptag">${u.tipo === 'HOSP' ? 'Hospital IMSS' : 'UMF'}${u.clave ? (' · ' + u.clave) : ''}</span><br><b>${u.nombre}</b>${dir}${extra}${deleg}${ood}`, { maxWidth: 320 })
      .bindTooltip((u.clave || u.nombre), { direction: 'top', offset: [0, -10] });
    mk.addTo(grp);
    UNIT_MK.push(mk);
  });

  MARCHAS.filter(visC).filter(visD).forEach((m) => {
    if (document.getElementById('lyRing').checked) {
      L.circle([m.lat, m.lng], { radius: RADIO_KM * 1000, color: nivelHex(m.nivel), weight: 1, fillColor: nivelHex(m.nivel), fillOpacity: 0.07, dashArray: '4 5' }).addTo(L_ring);
    }
    const col = m.estado === 'ACTIVA' ? 'var(--rojo)' : m.estado === 'PROGRAMADA' ? 'var(--gold)' : 'var(--gray)';
    const mk = L.marker([m.lat, m.lng], { icon: divIcon('mk-march', '⚐', estadoClass(m.estado)) })
      .bindPopup(`<span class="poptag" style="background:${col}">${m.estado}</span><br><b>${m.titulo}</b><br>${m.tipo} · ${m.hora} hrs<br>Aforo: ${fmt(m.aforo)}`).addTo(L_march);
    mk.on('click', () => selectMarch(m.id));
  });
  toggleLayers();
  updateUnitLabels();
}

function toggleLayers() {
  const set = (g, on) => (on ? map.addLayer(g) : map.removeLayer(g));
  set(L_march, lyMarch.checked); set(L_ring, lyRing.checked); set(L_est, lyEst.checked);
  set(L_fan, lyFan.checked); set(L_hosp, lyHosp.checked); set(L_umf, lyUmf.checked);
}
function updateUnitLabels() {
  const z = map.getZoom();
  UNIT_MK.forEach((m) => { try { if (z >= 14 && map.hasLayer(m)) m.openTooltip(); else m.closeTooltip(); } catch (e) {} });
}
map.on('zoomend', updateUnitLabels);

function selectMarch(id) {
  const m = MARCHAS.find((x) => x.id === id);
  if (!m) return;
  const ues = unidadesEnRadio(m);
  L_lines.clearLayers();
  ues.forEach((u) => L.polyline([[m.lat, m.lng], [u.lat, u.lng]], { color: nivelHex(m.nivel), weight: 2, opacity: 0.7, dashArray: '3 4' }).addTo(L_lines));
  map.setView([m.lat, m.lng], 13, { animate: true });
  const estB = m.estado === 'ACTIVA' ? 'b-activa' : m.estado === 'PROGRAMADA' ? 'b-prog' : 'b-concl';
  const fuente = m.fuente ? `<a href="${m.fuente.u}" target="_blank" rel="noopener">📰 ${m.fuente.t}</a>` : '<span style="color:var(--gray)">Sin nota vinculada</span>';
  const part = m.partido ? PARTIDOS.find((p) => p.n === m.partido) : null;
  const rows = ues.length ? ues.map((u) => `<div class="unit-row"><div class="unit-ic ${u.tipo === 'HOSP' ? 'hosp' : 'umf'}">✚</div><div><div class="nm">${u.nombre}</div><div class="ds">${u.tipo === 'HOSP' ? 'Hospital' : 'UMF'} · ${u.city}${u.delegacion ? ' · ' + u.delegacion : ''}</div></div><div class="dist">${u.dist.toFixed(2)} km</div></div>`).join('')
    : '<div class="note">Sin unidades IMSS dentro de 5 km. Cobertura por <b>red ampliada</b> y respuesta prehospitalaria (CVOED–CPES).</div>';
  document.getElementById('detail').innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px">
      <span class="badge ${estB}">${m.estado}</span>
      <span style="font-size:11px;font-weight:800;color:${nivelHex(m.nivel)};text-transform:uppercase">Nivel ${m.nivel}</span></div>
    <h4>${m.titulo}</h4>
    <div style="color:var(--gray);font-size:12px;margin-bottom:8px">${m.tipo} · ${m.city}${m.ooad ? ' · ' + m.ooad : ''}</div>
    <div class="kv"><span class="k">Fecha y hora</span><span class="v">${m.fecha.split('-').reverse().join('/')} · ${m.hora}</span></div>
    <div class="kv"><span class="k">Aforo estimado</span><span class="v">${fmt(m.aforo)}</span></div>
    <div class="kv"><span class="k">Ruta / ubicación</span><span class="v">${m.ruta || '—'}</span></div>
    ${part ? `<div class="kv"><span class="k">Partido asociado</span><span class="v">${part.partido}<br><span style="font-weight:400;color:var(--gray)">${part.fecha.split('-').reverse().join('/')} · ${part.hora}</span></span></div>` : ''}
    <div style="margin:10px 0 6px;font-weight:800;font-size:12px;text-transform:uppercase;color:var(--guinda)">Unidades IMSS en radio (${ues.length})</div>
    ${rows}
    <div style="margin-top:10px;font-weight:700;font-size:12px;color:var(--guinda)">Nota vinculada</div>
    <div style="margin-top:4px">${fuente}</div>
    <div style="display:flex;gap:8px;margin-top:12px">
      <button class="btn btn-o" onclick="clearSel()">Limpiar</button>
      <button class="btn btn-g" onclick="loadNews()">Actualizar noticias</button></div>`;
}
function clearSel() {
  L_lines.clearLayers();
  document.getElementById('detail').innerHTML = '<div class="empty">Selecciona una marcha en el mapa para ver el <b>análisis de proximidad</b> con las unidades médicas del IMSS.</div>';
}

function refreshKPIs() {
  const ms = MARCHAS.filter(visC).filter(visD);
  document.getElementById('kpiActivas').textContent = ms.filter((m) => m.estado === 'ACTIVA').length;
  const setU = new Set();
  ms.filter((m) => m.estado !== 'CONCLUIDA').forEach((m) => unidadesEnRadio(m).forEach((u) => setU.add(u.id)));
  document.getElementById('kpiUnidades').textContent = setU.size;
  document.getElementById('kpiPartidos').textContent = PARTIDOS.filter(visC).filter((p) => !SELDAY || p.fecha === SELDAY).length;
  document.getElementById('kpiAforo').textContent = fmt(ms.reduce((s, m) => s + m.aforo, 0));
  const box = document.getElementById('riskBox');
  box.innerHTML = '';
  ['CDMX', 'GDL', 'MTY'].forEach((c) => {
    const cm = MARCHAS.filter((m) => m.city === c && m.estado !== 'CONCLUIDA');
    let sc = 0;
    cm.forEach((m) => sc += (m.nivel === 'alto' ? 40 : m.nivel === 'medio' ? 22 : 10) + Math.min(m.aforo / 1000, 30));
    sc = Math.min(Math.round(sc), 100);
    const lvl = sc >= 70 ? { t: 'ROJO', c: HEX.rojo } : sc >= 40 ? { t: 'AMARILLO', c: HEX.amarillo } : { t: 'VERDE', c: HEX.verde };
    box.insertAdjacentHTML('beforeend', `<div class="risk"><span class="city">${c}</span><span class="bar"><i style="width:${sc}%;background:${lvl.c}"></i></span><span class="lvl" style="color:${lvl.c}">${lvl.t}</span></div>`);
  });
}

function buildDateStrip() {
  const s = document.getElementById('dateStrip');
  s.innerHTML = '';
  const all = document.createElement('div');
  all.className = 'daychip' + (SELDAY === null ? ' on' : '');
  all.innerHTML = '<div class="dd">∞</div><div class="mm">Todos</div>';
  all.onclick = () => { SELDAY = null; render(); };
  s.appendChild(all);
  const M = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];
  PARTIDOS.filter(visC).forEach((p) => {
    const d = p.fecha.split('-');
    const col = p.nivel === 'critico' ? HEX.rojo : p.nivel === 'alto' ? HEX.naranja : HEX.amarillo;
    const ch = document.createElement('div');
    ch.className = 'daychip' + (SELDAY === p.fecha ? ' on' : '');
    ch.innerHTML = `<div class="dd">${d[2]}</div><div class="mm">${M[+d[1] - 1]}</div><div class="mt" style="background:${SELDAY === p.fecha ? 'rgba(255,255,255,.25)' : col};color:#fff">${p.city}</div>`;
    ch.title = `${p.partido} · ${p.hora}`;
    ch.onclick = () => { SELDAY = (SELDAY === p.fecha ? null : p.fecha); render(); };
    s.appendChild(ch);
  });
}

let NEWS = [];
let REDES = [];

async function loadRedes() {
  try {
    REDES = await Store.getRedes();
    const box = document.getElementById('redesBox');
    if (!box) return;
    const top = REDES.slice(0, 5);
    box.innerHTML = top.length ? top.map((p) => `
      <div style="padding:8px 0;border-bottom:1px dashed var(--line)">
        <div style="font-weight:800;color:var(--verde);font-size:10px;text-transform:uppercase">${p.handle}</div>
        <div style="line-height:1.35;margin:4px 0">${p.texto.slice(0, 140)}${p.texto.length > 140 ? '…' : ''}</div>
        <a href="${p.url}" target="_blank" rel="noopener" style="font-size:10px">Ver publicación →</a>
      </div>`).join('')
      : '<span style="color:var(--gray)">Sin publicaciones recientes.</span>';
  } catch (e) { /* ignore */ }
}

async function loadNews() {
  const box = document.getElementById('newsBox');
  if (!NEWS.length) box.innerHTML = '<div class="news-loading"><span class="spin"></span> Cargando noticias…</div>';
  try {
    NEWS = await Store.getNoticias();
    if (!NEWS.length) throw new Error('sin noticias');
  } catch (e) {
    NEWS = [{ titulo: 'Sin conexión a noticias', fuente: 'Local', url: '#', pub: '' }];
  }
  const redesAsNews = REDES.slice(0, 6).map((p) => ({
    titulo: `${p.handle}: ${p.texto.slice(0, 100)}${p.texto.length > 100 ? '…' : ''}`,
    fuente: p.fuente || 'X',
    url: p.url,
    pub: p.fecha || '',
  }));
  const merged = [...redesAsNews, ...NEWS].slice(0, 14);
  box.innerHTML = merged.map((n) => `<a class="news-item" href="${n.url}" target="_blank" rel="noopener"><div class="ti">${n.titulo}</div><div class="me"><span class="tag live">${n.fuente?.includes('X') ? 'Redes' : 'Noticia'}</span> ${n.fuente || ''} ${n.pub ? ('· ' + n.pub) : ''}</div></a>`).join('');
  buildTicker();
}
function buildTicker() {
  const tr = document.getElementById('tkTrack');
  const tickerItems = [
    ...REDES.slice(0, 8).map((p) => ({ titulo: `${p.handle}: ${p.texto.slice(0, 90)}…`, url: p.url, fuente: 'Redes IMSS', pub: p.fecha })),
    ...NEWS,
  ];
  if (!tickerItems.length) { tr.textContent = 'Sin noticias por ahora.'; return; }
  const items = tickerItems.map((n) => `<span class="it"><a href="${n.url}" target="_blank" rel="noopener">${n.titulo}</a> <span class="src">${n.fuente || ''}${n.pub ? (' · ' + n.pub) : ''}</span></span>`).join('');
  tr.innerHTML = items + items;
  const secs = Math.max(90, tickerItems.length * 21);
  tr.style.animation = 'none'; void tr.offsetWidth; tr.style.animation = `tk ${secs}s linear infinite`;
}

function tick() {
  const n = new Date();
  document.getElementById('clk').textContent = n.toLocaleTimeString('es-MX');
  document.getElementById('clkd').textContent = n.toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' });
  let d = new Date('2026-06-11T13:00:00-06:00').getTime() - n.getTime();
  if (d < 0) d = 0;
  document.getElementById('cd-d').textContent = String(Math.floor(d / 86400000)).padStart(2, '0');
  document.getElementById('cd-h').textContent = String(Math.floor(d / 3600000 % 24)).padStart(2, '0');
  document.getElementById('cd-m').textContent = String(Math.floor(d / 60000 % 60)).padStart(2, '0');
  document.getElementById('cd-s').textContent = String(Math.floor(d / 1000 % 60)).padStart(2, '0');
  document.getElementById('tkClock').textContent = n.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
}

function render() { drawAll(); refreshKPIs(); buildDateStrip(); }

function mapMarcha(m) {
  return {
    id: +m.id, city: m.city, titulo: m.titulo, tipo: m.tipo,
    lat: +m.lat, lng: +m.lng, fecha: m.fecha, hora: m.hora,
    aforo: +m.aforo, nivel: m.nivel, estado: m.estado, ruta: m.ruta,
    partido: m.partido ? +m.partido : null, ooad: m.ooad,
    fuente: m.fuente || (m.fuente_url ? { t: m.fuente_titulo, u: m.fuente_url } : null),
  };
}

function mapUnidad(u) {
  return {
    id: +u.id, city: u.city, tipo: u.tipo, clave: u.clave, nombre: u.nombre,
    direccion: u.direccion, cp: u.cp, telefono: u.telefono, horario: u.horario,
    director: u.director, lat: +u.lat, lng: +u.lng,
    delegacion: u.delegacion, hospital_ref: u.hospital_ref,
    cons_mf: u.cons_mf, pamf: u.pamf,
  };
}

async function cargarDatos() {
  let origen = 'Regionalización IMSS · CUUMSP Feb 2026';
  try {
    await Store.init();
    const meta = await Store.getMeta();
    OOAD = meta.ooad || [];
    UNIDADES = (await Store.getUnidades()).map(mapUnidad);
    MARCHAS = (await Store.getMarchas()).map(mapMarcha);
  } catch (e) { /* respaldo vacío */ }
  document.getElementById('srcPill').textContent = 'Origen: ' + origen + ' · ' + UNIDADES.length + ' UMF · ' + MARCHAS.length + ' marchas';
  render();
}

window.addEventListener('monitoreo:update', () => cargarDatos());

function checkAuth() {
  const a = document.getElementById('authBox');
  if (!a) return;
  const user = sessionStorage.getItem('monitoreo_user');
  if (sessionStorage.getItem('monitoreo_auth') && user) {
    a.textContent = '🚪 Salir · ' + user;
    a.href = 'acceso.html';
    a.onclick = (e) => { e.preventDefault(); sessionStorage.clear(); location.href = 'monitor.html'; };
  } else {
    a.textContent = '⚙ Administración';
    a.href = 'acceso.html';
    a.onclick = null;
  }
}

document.querySelectorAll('#citySeg button').forEach((b) => b.onclick = () => {
  document.querySelectorAll('#citySeg button').forEach((x) => x.classList.remove('on'));
  b.classList.add('on');
  CITY = b.dataset.city;
  const c = CITY_CENTER[CITY];
  map.setView([c[0], c[1]], c[2], { animate: true });
  clearSel();
  render();
  loadNews();
});
['lyMarch', 'lyRing', 'lyEst', 'lyFan', 'lyHosp', 'lyUmf'].forEach((id) => document.getElementById(id).addEventListener('change', drawAll));
document.getElementById('newsRefresh').onclick = () => loadNews();
document.getElementById('btnFs').onclick = () => {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
  else document.exitFullscreen?.();
};
let rotTimer = null;
const ROT = ['ALL', 'CDMX', 'GDL', 'MTY'];
let rotIdx = 0;
document.getElementById('autoRot').addEventListener('change', (e) => {
  if (rotTimer) { clearInterval(rotTimer); rotTimer = null; }
  if (e.target.checked) {
    rotTimer = setInterval(() => {
      rotIdx = (rotIdx + 1) % ROT.length;
      const b = document.querySelector('#citySeg button[data-city="' + ROT[rotIdx] + '"]');
      if (b) b.click();
    }, 18000);
  }
});

checkAuth();
tick();
setInterval(tick, 1000);
cargarDatos();
loadRedes().then(loadNews);
