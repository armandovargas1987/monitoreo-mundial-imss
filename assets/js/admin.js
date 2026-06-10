const PARTIDOS = [
  { n: 1, t: '11/jun CDMX · México vs Sudáfrica' }, { n: 2, t: '11/jun GDL · Corea vs Rep. Checa' },
  { n: 3, t: '14/jun MTY · Suecia vs Túnez' }, { n: 4, t: '17/jun CDMX · Uzbekistán vs Colombia' },
  { n: 5, t: '18/jun GDL · México vs Corea' }, { n: 6, t: '20/jun MTY · Japón vs Túnez' },
  { n: 7, t: '23/jun GDL · Colombia vs RD Congo' }, { n: 8, t: '24/jun CDMX · México vs Rep. Checa' },
  { n: 9, t: '24/jun MTY · Sudáfrica vs Corea' }, { n: 10, t: '26/jun GDL · Uruguay vs España' },
  { n: 11, t: '29/jun MTY · Dieciseisavos' }, { n: 12, t: '30/jun CDMX · Dieciseisavos' },
  { n: 13, t: '05/jul CDMX · Octavos' },
];
const CENTER = { CDMX: [19.40, -99.15], GDL: [20.67, -103.40], MTY: [25.67, -100.27] };

let CAT = {}, MAR = [], pickMap = null, pickMk = null;
const $ = (id) => document.getElementById(id);

function toast(msg, err) {
  const t = $('toast');
  t.textContent = msg;
  t.className = 'toast show' + (err ? ' err' : '');
  setTimeout(() => { t.className = 'toast'; }, 2600);
}

function pill(txt, color) { return `<span class="pill" style="background:${color}">${txt}</span>`; }

document.querySelectorAll('.tabbar button').forEach((b) => b.onclick = () => {
  document.querySelectorAll('.tabbar button').forEach((x) => x.classList.remove('on'));
  b.classList.add('on');
  document.querySelectorAll('.tab').forEach((t) => t.classList.remove('on'));
  $('tab-' + b.dataset.tab).classList.add('on');
  if (b.dataset.tab === 'alertas') renderAlertas();
  if (b.dataset.tab === 'redes') renderRedes();
});

async function loadCat() {
  CAT = await Store.getMeta();
  const opt = (arr, val, txt) => arr.map((x) => `<option value="${x[val]}">${x[txt]}</option>`).join('');
  $('m_ooad').innerHTML = '<option value="">— Sin OOAD —</option>' + opt(CAT.ooad.filter((o) => o.activo === '1'), 'id', 'nombre');
  $('m_tipo').innerHTML = opt(CAT.tipos.filter((t) => t.activo === '1'), 'id', 'nombre');
  $('m_nivel').innerHTML = CAT.niveles.map((n) => `<option value="${n.id}">${n.nombre}</option>`).join('');
  $('m_estado').innerHTML = CAT.estados.map((e) => `<option value="${e.id}">${e.nombre}</option>`).join('');
  $('fEstado').innerHTML = '<option value="">Todos los estados</option>' + CAT.estados.map((e) => `<option value="${e.clave}">${e.nombre}</option>`).join('');
  $('m_partido').innerHTML = '<option value="">— Ninguno —</option>' + PARTIDOS.map((p) => `<option value="${p.n}">${p.t}</option>`).join('');
}

async function loadMarchas() {
  MAR = await Store.getMarchasAll();
  renderMarchas();
  updateAlertBadge();
}

function renderMarchas() {
  const fc = $('fCiudad').value, fe = $('fEstado').value, ft = $('fTexto').value.toLowerCase(), vb = $('fBajas').checked;
  const rows = MAR.filter((m) =>
    (!fc || m.city === fc) && (!fe || m.estado === fe) &&
    (!ft || m.titulo.toLowerCase().includes(ft)) && (vb || m.activo === '1')
  );
  $('tbMarchas').innerHTML = rows.length ? rows.map((m) => `
    <tr class="${m.activo === '1' ? '' : 'baja'}">
      <td>${pill(m.estado, m.estado_color)}</td>
      <td><b>${m.titulo}</b><div style="font-size:11px;color:var(--gray)">${m.ruta || ''}</div>
        ${m.fuente_url ? `<div style="font-size:10px"><a href="${m.fuente_url}" target="_blank" rel="noopener">📰 Nota vinculada</a></div>` : ''}</td>
      <td>${m.city}</td><td>${m.tipo}</td>
      <td>${pill(m.nivel, m.nivel_color)}</td>
      <td>${m.fecha.split('-').reverse().join('/')}<br><span style="color:var(--gray)">${m.hora}</span></td>
      <td>${(+m.aforo).toLocaleString('es-MX')}</td>
      <td style="font-size:11.5px">${m.ooad || '—'}<div style="color:var(--gray)">${m.capturado_por || ''}</div></td>
      <td style="text-align:right;white-space:nowrap">
        <button class="btn btn-o btn-sm" onclick="editMarcha('${m.id}')">Editar</button>
        ${m.activo === '1'
    ? `<button class="btn btn-o btn-sm" onclick="accMarcha('${m.id}','baja')">Baja</button>`
    : `<button class="btn btn-g btn-sm" onclick="accMarcha('${m.id}','reactivar')">Reactivar</button>`}
        <button class="btn btn-r btn-sm" onclick="accMarcha('${m.id}','eliminar')">Eliminar</button>
      </td></tr>`).join('')
    : '<tr><td colspan="9" style="text-align:center;color:var(--gray);padding:24px">Sin registros. Usa “+ Nueva marcha” o registra desde una alerta de noticias.</td></tr>';
}

['fCiudad', 'fEstado', 'fTexto', 'fBajas'].forEach((id) => $(id).addEventListener('input', renderMarchas));

function openForm() {
  $('formCard').classList.add('on');
  setTimeout(initPickMap, 60);
  $('formCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function closeForm() { $('formCard').classList.remove('on'); }

$('btnNueva').onclick = () => {
  $('formTitle').textContent = 'Nueva marcha';
  $('m_id').value = '';
  ['m_titulo', 'm_ruta', 'm_lat', 'm_lng', 'm_cap', 'm_ftit', 'm_furl'].forEach((i) => $(i).value = '');
  $('m_aforo').value = 0;
  $('m_ciudad').value = 'CDMX';
  $('m_partido').value = '';
  $('m_fecha').value = '2026-06-11';
  $('m_hora').value = '12:00';
  $('m_estado').value = '2';
  $('m_nivel').value = '2';
  openForm();
  setPicker(CENTER.CDMX[0], CENTER.CDMX[1], true);
  document.querySelector('.tabbar button[data-tab="marchas"]').click();
};

$('btnCancelar').onclick = closeForm;
$('m_ciudad').onchange = () => {
  const c = CENTER[$('m_ciudad').value];
  if (c && pickMap) pickMap.setView(c, 11);
};

window.editMarcha = function (id) {
  const m = MAR.find((x) => x.id === id);
  if (!m) return;
  $('formTitle').textContent = 'Editar marcha #' + id;
  $('m_id').value = id;
  $('m_titulo').value = m.titulo;
  $('m_ciudad').value = m.city;
  $('m_ooad').value = m.ooad_id || '';
  $('m_tipo').value = m.tipo_id;
  $('m_nivel').value = m.nivel_id;
  $('m_estado').value = m.estado_id;
  $('m_partido').value = m.partido || '';
  $('m_fecha').value = m.fecha;
  $('m_hora').value = m.hora;
  $('m_aforo').value = m.aforo;
  $('m_ruta').value = m.ruta || '';
  $('m_lat').value = m.lat;
  $('m_lng').value = m.lng;
  $('m_cap').value = m.capturado_por || '';
  $('m_ftit').value = m.fuente_titulo || '';
  $('m_furl').value = m.fuente_url || '';
  openForm();
  setPicker(+m.lat, +m.lng, true);
};

$('btnGuardar').onclick = async () => {
  const id = $('m_id').value;
  const body = {
    titulo: $('m_titulo').value,
    ciudad: $('m_ciudad').value,
    ooad_id: $('m_ooad').value,
    tipo_id: $('m_tipo').value,
    nivel_id: $('m_nivel').value,
    estado_id: $('m_estado').value,
    partido_n: $('m_partido').value,
    fecha: $('m_fecha').value,
    hora: $('m_hora').value,
    aforo: $('m_aforo').value,
    ruta: $('m_ruta').value,
    lat: $('m_lat').value,
    lng: $('m_lng').value,
    capturado_por: $('m_cap').value || sessionStorage.getItem('monitoreo_user'),
    fuente_titulo: $('m_ftit').value,
    fuente_url: $('m_furl').value,
  };
  if (!body.titulo || !body.lat || !body.lng) { toast('Título y ubicación son obligatorios', true); return; }
  await Store.saveMarcha(body, id || null);
  toast(id ? 'Marcha actualizada' : 'Marcha registrada');
  closeForm();
  loadMarchas();
};

window.accMarcha = async function (id, accion) {
  if (accion === 'eliminar' && !confirm('¿Eliminar definitivamente esta marcha?')) return;
  await Store.accMarcha(id, accion);
  toast('Listo');
  loadMarchas();
};

function initPickMap() {
  if (pickMap) { pickMap.invalidateSize(); return; }
  pickMap = L.map('pick').setView(CENTER.CDMX, 11);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom: 19, attribution: '© OSM © CARTO' }).addTo(pickMap);
  pickMap.on('click', (e) => setPicker(e.latlng.lat, e.latlng.lng));
}

function setPicker(lat, lng, recenter) {
  $('m_lat').value = (+lat).toFixed(7);
  $('m_lng').value = (+lng).toFixed(7);
  if (!pickMap) return;
  if (!pickMk) {
    pickMk = L.marker([lat, lng], { draggable: true }).addTo(pickMap);
    pickMk.on('dragend', (ev) => {
      const p = ev.target.getLatLng();
      $('m_lat').value = p.lat.toFixed(7);
      $('m_lng').value = p.lng.toFixed(7);
    });
  } else pickMk.setLatLng([lat, lng]);
  if (recenter) pickMap.setView([lat, lng], 13);
}

['m_lat', 'm_lng'].forEach((id) => $(id).addEventListener('change', () => {
  const la = parseFloat($('m_lat').value), ln = parseFloat($('m_lng').value);
  if (!isNaN(la) && !isNaN(ln)) setPicker(la, ln, true);
}));

/* ---------- ALERTAS / NOTICIAS ---------- */
async function updateAlertBadge() {
  const alertas = await Store.getAlertas();
  const nuevas = alertas.filter((a) => !a.vinculada).length;
  const el = $('alertBadge');
  if (el) {
    el.textContent = nuevas;
    el.style.display = nuevas ? 'inline' : 'none';
  }
}

async function renderAlertas() {
  const alertas = await Store.getAlertas();
  const fc = $('fAlertCiudad')?.value || '';
  const soloNuevas = $('fSoloNuevas')?.checked ?? true;
  const ft = ($('fAlertTexto')?.value || '').toLowerCase();

  let list = alertas;
  if (fc) list = list.filter((a) => a.ciudad === fc);
  if (soloNuevas) list = list.filter((a) => !a.vinculada);
  if (ft) list = list.filter((a) => (a.titulo || '').toLowerCase().includes(ft));

  const nuevas = alertas.filter((a) => !a.vinculada).length;
  $('alertSummary').innerHTML = `
    <strong>${alertas.length}</strong> noticias sobre marchas/manifestaciones ·
    <strong style="color:var(--rojo)">${nuevas}</strong> sin registrar en el monitor`;

  $('alertList').innerHTML = list.length ? list.map((a, i) => `
    <div class="alert-card ${a.vinculada ? 'vinc' : 'nueva'}">
      <h4>${a.titulo}</h4>
      <div class="meta">
        ${a.vinculada ? pill('Ya registrada', '#1a5c45') : pill('Posible marcha · sin registrar', '#c1121f')}
        ${a.prioridad === 'alta' ? pill('Prioridad alta', '#d97316') : ''}
        · ${a.fuente || 'Web'} · ${a.ciudad || '—'} · ${a.pub || ''}
      </div>
      <div class="actions">
        <a class="btn btn-o btn-sm" href="${a.url}" target="_blank" rel="noopener">Abrir nota</a>
        ${!a.vinculada ? `<button class="btn btn-guinda btn-sm" onclick="registrarDesdeNoticia(${i})">+ Registrar como marcha</button>` : ''}
      </div>
    </div>`).join('')
    : '<p class="hint" style="padding:20px;text-align:center">No hay alertas con los filtros actuales.</p>';

  window._alertasFiltradas = list;
}

window.registrarDesdeNoticia = function (idx) {
  const n = window._alertasFiltradas[idx];
  if (!n) return;
  const ciudad = n.ciudad === 'GDL' || n.ciudad === 'MTY' ? n.ciudad : 'CDMX';
  const coords = CENTER[ciudad] || CENTER.CDMX;
  $('formTitle').textContent = 'Nueva marcha desde noticia';
  $('m_id').value = '';
  $('m_titulo').value = (n.titulo || '').replace(/\s*-\s*[^-]+$/, '').slice(0, 120);
  $('m_ciudad').value = ciudad;
  $('m_ftit').value = n.titulo;
  $('m_furl').value = n.url;
  $('m_cap').value = 'Alerta noticias · ' + (sessionStorage.getItem('monitoreo_user') || '');
  $('m_estado').value = /hoy|activa|bloqueo/i.test(n.titulo) ? '1' : '2';
  $('m_nivel').value = /megamarcha|cnte|6 mil|colapsar/i.test(n.titulo) ? '1' : '2';
  $('m_tipo').value = /bloqueo/i.test(n.titulo) ? '3' : /plant[oó]n|protesta/i.test(n.titulo) ? '4' : /concentraci/i.test(n.titulo) ? '5' : '2';
  $('m_fecha').value = '2026-06-11';
  $('m_hora').value = '09:00';
  $('m_aforo').value = /6 mil|6000/i.test(n.titulo) ? 6000 : /megamarcha/i.test(n.titulo) ? 15000 : 2000;
  $('m_ruta').value = 'Por confirmar — ver nota periodística';
  document.querySelector('.tabbar button[data-tab="marchas"]').click();
  openForm();
  setPicker(coords[0], coords[1], true);
};

['fAlertCiudad', 'fSoloNuevas', 'fAlertTexto'].forEach((id) => {
  const el = $(id);
  if (el) el.addEventListener('input', renderAlertas);
  if (el && el.type === 'checkbox') el.addEventListener('change', renderAlertas);
});

async function renderRedes() {
  const posts = await Store.getRedes();
  const fc = $('fRedesCuenta')?.value || '';
  const ft = ($('fRedesTexto')?.value || '').toLowerCase();
  let list = posts;
  if (fc) list = list.filter((p) => p.cuenta === fc);
  if (ft) list = list.filter((p) => (p.texto || '').toLowerCase().includes(ft));

  const alta = posts.filter((p) => p.relevancia === 'alta').length;
  $('redesSummary').innerHTML = `<strong>${posts.length}</strong> publicaciones filtradas · <strong>${alta}</strong> de alta relevancia · @zoerobledo + @Tu_IMSS`;
  const badge = $('redesBadge');
  if (badge) { badge.textContent = posts.length; badge.style.display = posts.length ? 'inline' : 'none'; }

  $('redesList').innerHTML = list.length ? list.map((p) => `
    <div class="redes-card ${p.relevancia === 'alta' ? 'alta' : 'media'}">
      <div class="who">${p.handle} · ${p.nombre}</div>
      <div class="txt">${p.texto}</div>
      <div class="meta">
        ${pill(p.relevancia === 'alta' ? 'Alta relevancia IMSS' : 'Relevancia media', p.relevancia === 'alta' ? '#611232' : '#a57f2c')}
        · ${p.fuente || 'X'} · ${p.fecha || ''}
      </div>
      <div class="actions" style="margin-top:8px">
        <a class="btn btn-o btn-sm" href="${p.url}" target="_blank" rel="noopener">Ver en X / fuente</a>
      </div>
    </div>`).join('')
    : '<p class="hint" style="padding:20px;text-align:center">Sin publicaciones con los filtros actuales. Ejecuta «Actualizar» o corre <code>python3 scripts/sync_redes.py</code>.</p>';
}

['fRedesCuenta', 'fRedesTexto'].forEach((id) => {
  const el = $(id);
  if (el) el.addEventListener('input', renderRedes);
});

$('btnRedes').onclick = async () => {
  $('btnRedes').textContent = '⟳ Sincronizando…';
  await Store.refreshRedes();
  toast('Redes sociales actualizadas');
  $('btnRedes').textContent = '⟳ Actualizar @zoerobledo y @Tu_IMSS';
  renderRedes();
};

$('btnNoticias').onclick = async () => {
  $('btnNoticias').textContent = '⟳ Buscando…';
  const r = await Store.refreshNoticias();
  toast(`Noticias actualizadas: ${r.total} en total`);
  $('btnNoticias').textContent = '⟳ Actualizar noticias';
  renderAlertas();
  updateAlertBadge();
};

(async () => {
  const user = sessionStorage.getItem('monitoreo_user') || 'marvin.ortiz';
  $('elNombre').textContent = user.replace(/\./g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  await Store.init();
  await loadCat();
  await loadMarchas();
  await renderAlertas();
  await renderRedes();
})();
