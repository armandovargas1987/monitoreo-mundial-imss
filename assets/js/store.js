const Store = (() => {
  const LS_KEY = 'monitoreo_imss_v1';
  const ALERT_KW = /marcha|manifestaci|bloqueo|protesta|cnte|convocan|concentraci|antorcha|cerrad|plant[oó]n|megamarcha|ayotzinapa/i;

  let cache = null;

  async function init() {
    if (cache) return cache;
    const saved = localStorage.getItem(LS_KEY);
    if (saved) {
      cache = JSON.parse(saved);
      return cache;
    }
    const [meta, marchas, noticias, catalogos] = await Promise.all([
      fetch('data/catalogos_meta.json').then((r) => r.json()),
      fetch('data/marchas.json').then((r) => r.json()),
      fetch('data/noticias.json').then((r) => r.json()),
      fetch('data/catalogos.json').then((r) => r.json()),
    ]);
    let redes = { publicaciones: [] };
    try {
      redes = await fetch('data/redes_sociales.json').then((r) => r.json());
    } catch (e) { /* opcional */ }
    cache = {
      meta,
      marchas: marchas.marchas || [],
      noticias: noticias.noticias || [],
      unidades: catalogos.unidades || [],
      redes: redes.publicaciones || [],
      nextMarchaId: Math.max(0, ...(marchas.marchas || []).map((m) => +m.id)) + 1,
    };
    persist();
    return cache;
  }

  function persist() {
    localStorage.setItem(LS_KEY, JSON.stringify(cache));
    window.dispatchEvent(new CustomEvent('monitoreo:update'));
  }

  async function getMeta() { await init(); return cache.meta; }
  async function getMarchas() { await init(); return cache.marchas.filter((m) => m.activo !== '0'); }
  async function getMarchasAll() { await init(); return cache.marchas; }
  async function getUnidades() { await init(); return cache.unidades; }
  async function getNoticias() { await init(); return cache.noticias; }
  async function getRedes() { await init(); return cache.redes || []; }

  async function refreshRedes() {
    try {
      const r = await fetch('data/redes_sociales.json', { cache: 'no-store' });
      const j = await r.json();
      if (j.publicaciones?.length) {
        await init();
        cache.redes = j.publicaciones;
        persist();
        return { total: j.publicaciones.length, actualizado: j.actualizado };
      }
    } catch (e) { /* ignore */ }
    return { total: (cache?.redes || []).length };
  }

  function linkedUrls() {
    return new Set(
      (cache?.marchas || [])
        .map((m) => m.fuente_url || m.fuente?.u)
        .filter(Boolean)
    );
  }

  function tituloSimilar(a, b) {
    const na = (a || '').toLowerCase().replace(/[^a-záéíóúñ0-9 ]/g, '').slice(0, 40);
    const nb = (b || '').toLowerCase().replace(/[^a-záéíóúñ0-9 ]/g, '').slice(0, 40);
    return na && nb && (na.includes(nb.slice(0, 20)) || nb.includes(na.slice(0, 20)));
  }

  async function getAlertas() {
    await init();
    const urls = linkedUrls();
    return cache.noticias
      .filter((n) => ALERT_KW.test(n.titulo || ''))
      .map((n) => {
        const linked = urls.has(n.url) || (cache.marchas || []).some((m) =>
          tituloSimilar(m.fuente_titulo || m.titulo, n.titulo)
        );
        return { ...n, vinculada: linked, prioridad: /cnte|megamarcha|antorcha|bloqueo/i.test(n.titulo) ? 'alta' : 'media' };
      })
      .sort((a, b) => (a.vinculada === b.vinculada ? 0 : a.vinculada ? 1 : -1));
  }

  async function saveMarcha(data, id) {
    await init();
    const meta = cache.meta;
    const tipo = meta.tipos.find((t) => t.id === String(data.tipo_id));
    const nivel = meta.niveles.find((n) => n.id === String(data.nivel_id));
    const estado = meta.estados.find((e) => e.id === String(data.estado_id));
    const ooad = meta.ooad.find((o) => o.id === String(data.ooad_id));

    const row = {
      id: id ? String(id) : String(cache.nextMarchaId++),
      city: data.ciudad,
      titulo: data.titulo,
      tipo: tipo?.nombre || '',
      tipo_id: String(data.tipo_id),
      nivel: nivel?.clave || 'medio',
      nivel_id: String(data.nivel_id),
      nivel_color: nivel?.color || '#e0a800',
      estado: estado?.clave || 'PROGRAMADA',
      estado_id: String(data.estado_id),
      estado_color: estado?.color || '#a57f2c',
      fecha: data.fecha,
      hora: data.hora,
      aforo: +data.aforo || 0,
      lat: +data.lat,
      lng: +data.lng,
      ruta: data.ruta || '',
      partido: data.partido_n || null,
      fuente_titulo: data.fuente_titulo || null,
      fuente_url: data.fuente_url || null,
      fuente: data.fuente_url ? { t: data.fuente_titulo, u: data.fuente_url } : null,
      ooad: ooad?.nombre || '',
      ooad_id: data.ooad_id || '',
      capturado_por: data.capturado_por || sessionStorage.getItem('monitoreo_user') || '',
      activo: '1',
    };

    const idx = cache.marchas.findIndex((m) => m.id === row.id);
    if (idx >= 0) cache.marchas[idx] = { ...cache.marchas[idx], ...row };
    else cache.marchas.push(row);
    persist();
    return row;
  }

  async function accMarcha(id, accion) {
    await init();
    const idx = cache.marchas.findIndex((m) => m.id === String(id));
    if (idx < 0) return false;
    if (accion === 'baja') cache.marchas[idx].activo = '0';
    else if (accion === 'reactivar') cache.marchas[idx].activo = '1';
    else if (accion === 'eliminar') cache.marchas.splice(idx, 1);
    persist();
    return true;
  }

  async function refreshNoticias(extra) {
    await init();
    if (Array.isArray(extra) && extra.length) {
      const known = new Set(cache.noticias.map((n) => n.url));
      let nuevas = 0;
      extra.forEach((n) => {
        if (!known.has(n.url)) { cache.noticias.unshift(n); nuevas++; }
      });
      persist();
      return { nuevas, total: cache.noticias.length };
    }
    try {
      const r = await fetch('data/noticias.json', { cache: 'no-store' });
      const j = await r.json();
      if (j.noticias?.length) {
        cache.noticias = j.noticias;
        persist();
        return { nuevas: j.noticias.length, total: j.noticias.length };
      }
    } catch (e) { /* ignore */ }
    return { nuevas: 0, total: cache.noticias.length };
  }

  return {
    init, getMeta, getMarchas, getMarchasAll, getUnidades, getNoticias, getRedes,
    getAlertas, saveMarcha, accMarcha, refreshNoticias, refreshRedes,
  };
})();
