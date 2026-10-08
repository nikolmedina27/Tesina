/* SteelPlan · aplicación de una sola página (vanilla JS). */
'use strict';
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const S = { me: null, cat: null, charts: [], ultimaCot: null, ultimaSol: null };
const DIAS = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];
const fmtFecha = iso => { if (!iso) return '—'; const [y, m, d] = String(iso).slice(0, 10).split('-').map(Number); const f = new Date(y, m - 1, d); return `${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}/${y} (${DIAS[f.getDay()]})`; };
const fmtCorta = iso => iso ? String(iso).slice(0, 10).split('-').reverse().join('/') : '—';
const fmtNum = (n, d = 0) => n == null ? '—' : Number(n).toLocaleString('es-PE', { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (x, d = 0) => x == null ? '—' : `${(100 * x).toFixed(d)} %`;
const hoyISO = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
const iniciales = n => (n || '?').split(/\s+/).filter(w => /^[A-Za-zÁÉÍÓÚÑ]/.test(w)).slice(0, 2).map(w => w[0]).join('').toUpperCase();
const avatar = (n, c, chico) => `<span class="avatar${chico ? ' chico' : ''}" style="background:${esc(c || '#5b738b')}" title="${esc(n)}">${esc(iniciales(n))}</span>`;

/* ---------- íconos (trazo, 24x24) ---------- */
const P = {
  inicio: '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  proyectos: '<path d="M3 7h6l2 2h10v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M3 7V5a1 1 0 0 1 1-1h5l2 2"/>',
  gantt: '<path d="M4 4v16h16"/><rect x="7" y="6" width="7" height="3" rx="1"/><rect x="10" y="11" width="8" height="3" rx="1"/><rect x="8" y="16" width="5" height="3" rx="1"/>',
  cotizador: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M12 11h2M16 11h0M8 15h2M12 15h2M8 18h8"/>',
  planta3d: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
  planta: '<path d="M3 21V10l6 4V10l6 4V6l6 3v12z"/><path d="M7 18h2M12 18h2M17 18h2"/>',
  tareas: '<rect x="3" y="4" width="5" height="16" rx="1"/><rect x="10" y="4" width="5" height="10" rx="1"/><rect x="17" y="4" width="4" height="13" rx="1"/>',
  usuarios: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.5-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><circle cx="17" cy="9" r="2.6"/><path d="M16 14.6c2.6.1 4.6 1.8 5.3 4.6"/>',
  salir: '<path d="M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4"/><path d="M10 8l-4 4 4 4M6 12h10"/>',
  viga: '<path d="M4 5h16M4 19h16M12 5v14M8 5v2M16 5v2M8 17v2M16 17v2"/>',
  engranaje: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
  alerta: '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>',
  reloj: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  mas: '<path d="M12 5v14M5 12h14"/>',
  buscar: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
  lista: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  chispa: '<path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"/>',
  check: '<path d="M4 12l5 5L20 6"/>',
  rayo: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  cerrar: '<path d="M6 6l12 12M18 6L6 18"/>',
  comentario: '<path d="M4 5h16v11H9l-5 4z"/>',
  importar: '<path d="M12 3v12M7 10l5 5 5-5"/><path d="M4 16v4h16v-4"/>',
  hoja: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16M10 3v18"/>',
  curva: '<path d="M3 20h18"/><path d="M4 18c5 0 6-12 16-13"/>',
  camion: '<path d="M2 6h11v10H2zM13 10h4l3 3v3h-7"/><circle cx="6" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/>',
  bandeja: '<path d="M3 13l3-8h12l3 8v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/><path d="M3 13h5l1 3h6l1-3h5"/>',
  reporte: '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
  semana: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4M7 14h2M11 14h2M15 14h2"/>',
  imprimir: '<path d="M7 9V3h10v6"/><rect x="3" y="9" width="18" height="8" rx="1"/><path d="M7 14h10v7H7z"/>',
};
const ic = (n, s = 18, extra = '') => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" ${extra}>${P[n] || ''}</svg>`;

const ESTADOS = [['BACKLOG', 'Backlog', '#8a96a3'], ['POR_HACER', 'Por hacer', '#5b738b'], ['EN_CURSO', 'En curso', '#0a6ed1'], ['REVISION', 'En revisión', '#e9730c'], ['HECHO', 'Hecho', '#107e3e']];
const PRIO = { 1: ['Urgente', 'var(--rojo)'], 2: ['Alta', 'var(--naranja)'], 3: ['Media', 'var(--azul)'], 4: ['Baja', 'var(--gris)'] };
const TIPOS_T = { TAREA: ['Tarea', 'b-az'], BLOQUEO: ['Bloqueo', 'b-roj'], NO_CONFORMIDAD: ['No conformidad', 'b-nar'], RFI: ['RFI cliente', 'b-mor'], CAMBIO_ALCANCE: ['Cambio de alcance', 'b-gris'], COMPRA: ['Compra', 'b-ver'] };
const CAT = { maquina: ['Máquina', '#8ec5ff'], contratista: ['Contratista', '#ffc58a'], externo: ['Servicio externo', '#d6c4f0'], interno: ['Interno', '#c3ccd5'] };

/* ---------- API ---------- */
async function api(url, opt = {}) {
  const r = await fetch(url, { credentials: 'same-origin', ...opt, headers: { 'Content-Type': 'application/json' },
    body: opt.body && typeof opt.body !== 'string' ? JSON.stringify(opt.body) : opt.body });
  if (r.status === 401 && !url.endsWith('/login')) { S.me = null; renderLogin(); throw new Error('Sesión expirada'); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : (j.detail ? j.detail.map(e => e.msg).join('; ') : r.statusText));
  return j;
}
function toast(msg, err) { const t = document.createElement('div'); t.className = 'toast' + (err ? ' err' : ''); t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 3800); }
const cargando = () => '<div class="cargando"><div class="spin"></div></div>';
function chart(el, option) { const c = echarts.init(el); c.setOption(option); S.charts.push(c); return c; }
window.addEventListener('resize', () => S.charts.forEach(c => c.resize()));

/* ---------- Gantt ---------- */
function gantt(el, tareas, o = {}) {
  if (!tareas || !tareas.length) { el.innerHTML = '<div class="vacio">Sin datos para el Gantt</div>'; return null; }
  el.innerHTML = '<svg></svg>';
  const t = tareas.map(x => ({ id: x.id, name: x.name, start: x.start, end: x.end, progress: x.progress || 0, dependencies: x.dependencies || '', custom_class: 'cat-' + (x.categoria || '') }));
  try {
    return new Gantt(el.querySelector('svg'), t, {
      view_mode: o.modo || 'Week', language: 'es', bar_height: 20, padding: 14, date_format: 'YYYY-MM-DD',
      custom_popup_html: task => {
        const x = tareas.find(y => y.id === task.id) || {};
        return `<div class="pop"><b>${esc(x.name)}</b><br>${fmtCorta(x.start)} → ${fmtCorta(x.end)}${x.hh != null ? `<br>${fmtNum(x.hh)} HH` : ''}${x.progress ? `<br>Avance ${x.progress} %` : ''}${o.extra ? o.extra(x) : ''}</div>`;
      },
      on_click: o.click || (() => {}), on_date_change: () => {}, on_progress_change: () => {},
    });
  } catch (e) { el.innerHTML = `<div class="vacio">No se pudo dibujar el Gantt: ${esc(e.message)}</div>`; return null; }
}
const leyendaCat = () => `<div class="leyenda">${Object.values(CAT).map(([n, c]) => `<span><i style="background:${c}"></i>${n}</span>`).join('')}</div>`;

/* ---------- ilustración metalmecánica (cercha + grúa) ---------- */
function cercha(w = 560, h = 230) {
  const n = 10, x0 = 30, x1 = w - 30, yb = h - 40, yt = 70, dx = (x1 - x0) / n;
  let s = `<svg viewBox="0 0 ${w} ${h}" class="cercha" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round">`;
  s += `<path d="M${x0} ${yb}H${x1}M${x0} ${yb}L${w / 2} ${yt}L${x1} ${yb}"/>`;
  for (let i = 1; i < n; i++) { const x = x0 + i * dx; const yt_ = yb - (yb - yt) * (1 - Math.abs(x - w / 2) / (w / 2 - x0)); s += `<path d="M${x} ${yb}V${yt_}"/>`; if (i < n) s += `<path d="M${x} ${yb}L${x + (x < w / 2 ? dx : -dx)} ${yb - (yb - yt) * (1 - Math.abs(x + (x < w / 2 ? dx : -dx) - w / 2) / (w / 2 - x0))}" stroke-opacity=".7"/>`; }
  s += `<path d="M${x0} ${yb}V${h - 6}M${x1} ${yb}V${h - 6}" stroke-width="4"/><path d="M${w - 150} 20H${w - 40}M${w - 120} 20V${yt + 26}" stroke="#e9730c" stroke-width="3"/><path d="M${w - 126} ${yt + 26}a6 6 0 1 0 12 0" stroke="#e9730c" stroke-width="3"/></svg>`;
  return s;
}

/* ---------- login ---------- */
function renderLogin() {
  S.charts.forEach(c => c.dispose()); S.charts = [];
  $('#app').innerHTML = `
  <div class="login">
    <section class="hero">
      <div><div class="marca" style="margin-bottom:28px"><span class="logo">${ic('viga', 20)}</span>SteelPlan <small>· Steelser S.A.C.</small></div>
        <h1>Fechas de entrega realistas para estructuras metálicas</h1>
        <p>Cotiza con probabilidad de cumplimiento, sigue cada proyecto en Gantt, registra el tareo y las paradas de planta, y coordina al equipo en un solo lugar.</p></div>
      ${cercha()}
      <p class="nota" style="color:#cfe3f7">Prototipo de tesis · UPC Ingeniería Industrial · el modelo usa datos simulados hasta cargar los tareos reales.</p>
    </section>
    <section class="panel"><form class="caja" id="flogin">
      <h2>Iniciar sesión</h2><span class="nota">Cada persona entra con su propia cuenta y rol.</span>
      <label>Usuario<input name="usuario" autocomplete="username" required autofocus></label>
      <label>Clave<input name="clave" type="password" autocomplete="current-password" required></label>
      <div class="error" id="lerr"></div>
      <button class="btn prim" style="justify-content:center">Entrar</button>
      <span class="nota">Cuentas de demostración: ver <code>data/credenciales_demo.txt</code> en la PC del servidor.</span>
    </form></section>
  </div>`;
  $('#flogin').onsubmit = async e => {
    e.preventDefault(); const f = new FormData(e.target);
    try { await api('/api/login', { method: 'POST', body: { usuario: f.get('usuario'), clave: f.get('clave') } }); await arrancar(); }
    catch (err) { $('#lerr').textContent = err.message; }
  };
}

/* ---------- estructura ---------- */
/* El menú agrupa las vistas por lo que hace cada persona: decidir (Cotizar), gestionar (Proyectos), la planta (registro y gemelo 3D) y datos. */
const ROLES = { cotizador: ['cotizador', 'jefe_taller'], planta: ['jefe_taller', 'supervisor', 'calidad'], importar: ['jefe_taller', 'cotizador'], usuarios: ['__solo_gerencia__'] };
const GRUPOS = [
  { k: 'inicio', t: 'Inicio', ic: 'inicio', subs: [['inicio', 'Tablero']] },
  { k: 'cotizador', t: 'Cotizar', ic: 'cotizador', subs: [['cotizador', 'Cotizador de plazos']] },
  { k: 'proyectos', t: 'Proyectos', ic: 'proyectos', subs: [['proyectos', 'Proyectos'], ['gantt', 'Gantt'], ['tareas', 'Tareas'], ['bandeja', 'RFI y NC']] },
  { k: 'planta', t: 'Planta', ic: 'planta3d', subs: [['planta3d', 'Gemelo 3D'], ['planta', 'Registro diario']] },
  { k: 'datos', t: 'Datos', ic: 'engranaje', subs: [['importar', 'Importar formato único'], ['usuarios', 'Usuarios']] },
];
const puede = roles => !roles || S.me.rol === 'gerencia' || roles.includes(S.me.rol);
const puedeVer = k => puede(ROLES[k]);
const subsVisibles = g => g.subs.filter(([k]) => puedeVer(k));
const grupoDe = k => GRUPOS.find(g => g.subs.some(([x]) => x === k));
const MARCAN_PIEZAS = ['jefe_taller', 'supervisor', 'calidad'];
function shell(activo, migas, acciones = '') {
  S.charts.forEach(c => c.dispose()); S.charts = [];
  $$('body > .velo, body > .lateral, body > .modal, body > .paleta').forEach(e => e.remove());   // paneles abiertos de la vista anterior
  $('#app').innerHTML = `
  <header class="shell">
    <div class="marca" onclick="location.hash='#/inicio'"><span class="logo">${ic('viga', 18)}</span>SteelPlan</div>
    <nav class="menu">${GRUPOS.filter(g => subsVisibles(g).length).map(g => `<a href="#/${subsVisibles(g)[0][0]}" class="${g === grupoDe(activo) ? 'activo' : ''}">${ic(g.ic, 17)}${g.t}</a>`).join('')}</nav>
    <button class="kbtn" id="bk" title="Buscar (Ctrl+K)">${ic('buscar', 16)}<span>Buscar</span><kbd>Ctrl K</kbd></button>
    <div class="usuario" id="umenu">${avatar(S.me.nombre, S.me.color)}<div><div>${esc(S.me.nombre)}</div><div class="rol">${esc(S.me.rol_nombre.split(' (')[0])}</div></div>
      <div class="desplegable oculto" id="udrop"><div class="nota" style="padding:8px 10px">${esc(S.me.rol_nombre)}<br>Área: ${esc(S.me.area || '—')}</div>
      <button id="bsalir">${ic('salir', 16)} Cerrar sesión</button></div></div>
  </header>
  ${(() => { const g = grupoDe(activo), v = g ? subsVisibles(g) : []; return v.length > 1 ? `<div class="subnav">${v.map(([k, t]) => `<a href="#/${k}" class="${k === activo ? 'activo' : ''}">${t}</a>`).join('')}</div>` : ''; })()}
  <div class="control"><div class="migas">${migas}</div><div class="acciones">${acciones}</div></div>
  <main class="contenido" id="main">${cargando()}</main>`;
  $('#umenu').onclick = e => { e.stopPropagation(); $('#udrop').classList.toggle('oculto'); };
  document.onclick = () => $('#udrop') && $('#udrop').classList.add('oculto');
  $('#bsalir').onclick = async () => { await api('/api/logout', { method: 'POST' }); S.me = null; renderLogin(); };
  $('#bk').onclick = paleta;
  return $('#main');
}

/* ---------- buscador global (Ctrl+K), estilo Linear ---------- */
function paleta() {
  if ($('.paleta')) return;
  const acciones = [
    ...GRUPOS.flatMap(g => subsVisibles(g).map(([k, t]) => ({ tipo: 'Ir a', titulo: g.subs.length > 1 ? `${g.t} · ${t}` : t, ruta: '#/' + k, icono: k === 'planta3d' ? 'planta3d' : g.ic }))),
    ...(puedeVer('cotizador') ? [{ tipo: 'Acción', titulo: 'Nueva cotización', ruta: '#/cotizador', icono: 'cotizador' }] : []),
    ...(puede(['jefe_taller', 'supervisor']) ? [{ tipo: 'Acción', titulo: 'Registrar tareo de hoy', ruta: '#/planta', icono: 'planta' }] : []),
    ...S.cat.proyectos.map(p => ({ tipo: 'Reporte semanal', titulo: `${p.codigo} · ${p.nombre}`, ruta: `#/reporte/${p.id}`, icono: 'reporte' })),
  ];
  const v = document.createElement('div'); v.className = 'velo';
  const pa = document.createElement('div'); pa.className = 'paleta';
  pa.innerHTML = `<div class="pq">${ic('buscar', 18)}<input id="pq" placeholder="Buscar proyecto, OT, pieza, tarea, cliente... o escribe una acción" autocomplete="off"><kbd>Esc</kbd></div><div class="pres" id="pres"></div>`;
  document.body.append(v, pa);
  const cerrar = () => { v.remove(); pa.remove(); };
  v.onclick = cerrar;
  let items = [], sel = 0, t = null;
  const icoTipo = { 'Proyecto en curso': 'proyectos', Tarea: 'tareas', Pieza: 'viga', 'Histórico': 'reloj' };
  const pintar = () => {
    $('#pres').innerHTML = items.length ? items.map((x, i) => `<div class="pit ${i === sel ? 'sel' : ''}" data-i="${i}">${ic(x.icono || icoTipo[x.tipo] || 'chispa', 16)}
      <div><div>${esc(x.titulo)}</div>${x.detalle ? `<small>${esc(x.detalle)}</small>` : ''}</div><span class="nota">${esc(x.tipo)}</span></div>`).join('') : '<div class="vacio">Sin resultados</div>';
    $$('.pit', pa).forEach(el => { el.onclick = () => ir(+el.dataset.i); el.onmousemove = () => { if (sel !== +el.dataset.i) { sel = +el.dataset.i; pintar(); } }; });
    const s = $('.pit.sel', pa); if (s) s.scrollIntoView({ block: 'nearest' });
  };
  const ir = i => { if (!items[i]) return; cerrar(); location.hash = items[i].ruta; };
  const buscarYa = async q => {
    const ql = q.toLowerCase();
    const loc = acciones.filter(a => !q || a.titulo.toLowerCase().includes(ql)).slice(0, q ? 8 : 12);
    items = loc; sel = 0; pintar();
    if (q.length >= 2) { try { const r = await api('/api/buscar?q=' + encodeURIComponent(q)); if ($('#pq') && $('#pq').value === q) { items = [...r, ...loc]; sel = 0; pintar(); } } catch { } }
  };
  const inp = $('#pq');
  inp.oninput = () => { clearTimeout(t); t = setTimeout(() => buscarYa(inp.value.trim()), 180); };
  inp.onkeydown = e => {
    if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(sel + 1, items.length - 1); pintar(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(sel - 1, 0); pintar(); }
    else if (e.key === 'Enter') { e.preventDefault(); ir(sel); }
    else if (e.key === 'Escape') cerrar();
  };
  inp.focus(); buscarYa('');
}
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k' && S.me) { e.preventDefault(); paleta(); }
});

/* =====================================================================  INICIO */
async function vInicio() {
  const m = shell('inicio', `${ic('inicio', 20)} Tablero`);
  const d = await api('/api/dashboard');
  const apps = [['cotizador', 'Cotizar', '#e9730c'], ['proyectos', 'Proyectos', '#0a6ed1'], ['planta3d', 'Gemelo 3D', '#1a9898'], ['planta', 'Registro diario', '#5b738b'],
    ['tareas', 'Tareas', '#925ace'], ['bandeja', 'RFI y NC', '#bb0000'], ['importar', 'Importar Excel', '#107e3e'], ['usuarios', 'Usuarios', '#c0399f']]
    .filter(a => puedeVer(a[0]));
  const t = d.tareas || {};
  const abiertas = (t.BACKLOG || 0) + (t.POR_HACER || 0) + (t.EN_CURSO || 0) + (t.REVISION || 0);
  m.innerHTML = `
  <section class="banda">${cercha(640, 200)}
    <h1>Hola, ${esc(S.me.nombre.split(' (')[0])}</h1><p>Gestión de proyectos de estructuras metálicas · ${new Date().toLocaleDateString('es-PE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
    <div class="apps">${apps.map(([k, n, c]) => `<div class="app" onclick="location.hash='#/${k}'"><div class="ic" style="background:${c}">${ic(k, 24)}</div><span>${n}</span></div>`).join('')}</div>
  </section>
  <div class="kpis">
    ${kpi('Cumplimiento histórico', d.historico.otd + ' %', `${d.historico.proyectos - d.historico.atrasados} de ${d.historico.proyectos} proyectos 2019-2026`, d.historico.otd >= 85 ? 'ver' : 'nar', 'check')}
    ${kpi('Proyectos con retraso', d.historico.atrasados, `retraso promedio ${d.historico.retraso_prom} días`, 'roj', 'alerta')}
    ${kpi('Proyectos en curso', d.activos.length, 'seguimiento prospectivo', '', 'proyectos')}
    ${kpi('HH registradas (7 días)', fmtNum(d.hh_7d), 'tareo de planta', 'mor', 'reloj')}
    ${kpi('Tareas abiertas', abiertas, `${t.EN_CURSO || 0} en curso · ${t.REVISION || 0} en revisión`, 'nar', 'tareas')}
  </div>
  <div class="grid g2">
    <div class="tarjeta"><h3>Cumplimiento de entregas por año <span class="nota">meta 85 %</span></h3><div class="cuerpo"><div class="grafico bajo" id="gotd"></div></div></div>
    <div class="tarjeta"><h3>Disponibilidad de máquinas · últimos 30 días <span class="nota">registrada en Planta</span></h3><div class="cuerpo"><div class="grafico bajo" id="gdisp"></div></div></div>
    <div class="tarjeta"><h3>Proyectos en curso</h3><div class="cuerpo scroll" id="tact">${cargando()}</div></div>
    <div class="tarjeta"><h3>${ic('alerta', 17)} Atención</h3><div class="cuerpo">${d.criticas.length ? `<table class="tabla">${d.criticas.map(c => `<tr class="clic" onclick="location.hash='#/tareas'"><td><span class="badge ${TIPOS_T[c.tipo][1]}">${TIPOS_T[c.tipo][0]}</span></td><td>${esc(c.titulo)}</td><td class="nota">${esc(c.responsable || '')}</td></tr>`).join('')}</table>` : '<div class="vacio">Sin alertas</div>'}</div></div>
    <div class="tarjeta" style="grid-column:1/-1"><h3>Actividad reciente del equipo</h3><div class="cuerpo"><ul class="feed">${d.actividad.map(a => `<li>${avatar(a.nombre, a.color, 1)}<div>${esc(a.detalle)}<small>${esc(a.nombre || '')} · ${esc(String(a.creado_en).slice(0, 16))}</small></div></li>`).join('') || '<li class="nota">Sin actividad</li>'}</ul></div></div>
  </div>`;
  chart($('#gotd'), { grid: { left: 40, right: 20, top: 20, bottom: 28 }, tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: d.otd_anual.map(r => r.anio) }, yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value} %' } },
    series: [{ type: 'bar', data: d.otd_anual.map(r => ({ value: r.otd_pct, itemStyle: { color: r.otd_pct >= 85 ? '#107e3e' : r.otd_pct >= 70 ? '#0a6ed1' : '#e9730c', borderRadius: [4, 4, 0, 0] } })), barWidth: '55%',
      label: { show: true, position: 'top', formatter: '{c} %' }, markLine: { symbol: 'none', lineStyle: { color: '#107e3e', type: 'dashed' }, data: [{ yAxis: 85 }], label: { formatter: 'meta' } } }] });
  const dk = Object.entries(d.disponibilidad);
  chart($('#gdisp'), { grid: { left: 190, right: 40, top: 10, bottom: 20 }, tooltip: { valueFormatter: v => v + ' %' },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value} %' } }, yAxis: { type: 'category', data: dk.map(x => x[0]) },
    series: [{ type: 'bar', data: dk.map(x => ({ value: +(100 * x[1]).toFixed(1), itemStyle: { color: x[1] >= .9 ? '#107e3e' : x[1] >= .75 ? '#0a6ed1' : '#bb0000', borderRadius: 4 } })), barWidth: 16, label: { show: true, position: 'right', formatter: '{c} %' },
      markLine: { symbol: 'none', data: [{ xAxis: 90 }], lineStyle: { type: 'dashed', color: '#107e3e' }, label: { formatter: 'meta 90 %' } } }] });
  const act = await api('/api/proyectos_activos');
  $('#tact').innerHTML = tablaActivos(act.filter(a => a.estado === 'EN_CURSO'));
}
const kpi = (t, v, s, cls, icono) => `<div class="kpi ${cls}">${ic(icono, 60, 'class="fondo"')}<div class="t">${t}</div><div class="v">${v}</div><div class="s">${s}</div></div>`;
function tablaActivos(act) {
  if (!act.length) return '<div class="vacio">No hay proyectos en curso. Créalos desde el Cotizador.</div>';
  return `<table class="tabla"><tr><th>OT</th><th>Proyecto</th><th>Entrega comprometida</th><th>Avance HH</th><th>Avance físico (kg)</th><th></th></tr>${act.map(a => `
    <tr class="clic" onclick="location.hash='#/proyecto/a/${a.id}'"><td><b>${esc(a.codigo)}</b>${a.es_demo ? ' <span class="badge b-nar">DEMO</span>' : ''}</td>
    <td>${esc(a.nombre)}<div class="nota">${esc(a.cliente || '')} · ${fmtNum(a.ton)} t</div></td><td>${fmtFecha(a.fecha_comprometida)}<div class="nota">${a.prob_cumplir != null ? 'P(cumplir) cotizada ' + pct(a.prob_cumplir) : 'importado del Excel'}</div></td>
    <td style="min-width:130px"><div class="barra"><i style="width:${a.avance}%"></i></div><span class="nota">${a.avance} % · ${fmtNum(a.hh_registradas)} / ${fmtNum(a.hh_p50)} HH</span></td>
    <td style="min-width:130px">${a.avance_fisico != null ? `<div class="barra nar"><i style="width:${a.avance_fisico}%"></i></div><span class="nota">${a.avance_fisico} % ponderado</span>` : '<span class="nota">sin piezas</span>'}</td>
    <td><span class="badge ${a.estado === 'ENTREGADO' ? 'b-ver' : a.estado === 'PERDIDO' ? 'b-gris' : 'b-az'}">${esc(a.estado.replace('_', ' '))}</span></td></tr>`).join('')}</table>`;
}

/* =====================================================================  PROYECTOS */
async function vProyectos(tab = 'curso') {
  const m = shell('proyectos', `${ic('proyectos', 20)} Proyectos`,
    `<div class="buscar">${ic('buscar', 16)}<input id="q" placeholder="Buscar cliente, proyecto, OT..."></div>
     ${puede(['cotizador']) ? `<button class="btn prim" onclick="location.hash='#/cotizador'">${ic('mas', 16)} Nuevo desde cotización</button>` : ''}`);
  const [hist, act] = await Promise.all([api('/api/proyectos'), api('/api/proyectos_activos')]);
  const atr = hist.filter(p => p.dias_retraso > 0).length;
  m.innerHTML = `
    <div class="pestanas"><button data-t="curso" class="${tab === 'curso' ? 'activo' : ''}">En curso (${act.length})</button><button data-t="hist" class="${tab === 'hist' ? 'activo' : ''}">Histórico 2019-2026 (${hist.length})</button></div>
    <div id="pcurso" class="${tab === 'curso' ? '' : 'oculto'}"><div class="tarjeta"><div class="cuerpo" id="lact"></div></div></div>
    <div id="phist" class="${tab === 'hist' ? '' : 'oculto'}">
      <div class="estado-btns" style="margin-bottom:12px">
        <button class="estado-btn" data-f="todos"><b>${hist.length}</b>Todos</button><button class="estado-btn ver" data-f="cumple"><b>${hist.length - atr}</b>Cumplió</button>
        <button class="estado-btn roj" data-f="retraso"><b>${atr}</b>Con retraso</button><button class="estado-btn gris" data-f="muestra"><b>${hist.filter(p => p.en_muestra).length}</b>En muestra de tesis</button></div>
      <div class="tarjeta"><div class="cuerpo scroll" id="lhist" style="max-height:640px"></div></div></div>`;
  let filtro = 'todos';
  const pintar = () => {
    const q = ($('#q').value || '').toLowerCase();
    const okq = p => !q || `${p.cliente} ${p.nombre} ${p.codigo || ''}`.toLowerCase().includes(q);
    $('#lact').innerHTML = tablaActivos(act.filter(okq));
    const h = hist.filter(okq).filter(p => filtro === 'todos' || (filtro === 'cumple' && p.dias_retraso <= 0) || (filtro === 'retraso' && p.dias_retraso > 0) || (filtro === 'muestra' && p.en_muestra));
    $('#lhist').innerHTML = `<table class="tabla"><tr><th>N°</th><th>Año</th><th>Cliente</th><th>Proyecto</th><th>Tipo</th><th class="num">t</th><th>Inicio</th><th>Fin plan</th><th>Fin real</th><th>Estado</th></tr>
      ${h.map(p => `<tr class="clic" onclick="location.hash='#/proyecto/h/${p.id}'"><td>${p.n_registro}</td><td>${p.anio}</td><td>${esc(p.cliente)}</td><td>${esc(p.nombre)}</td>
      <td class="nota">${esc((p.tipo || '—').split(' /')[0])}</td><td class="num">${p.toneladas ? fmtNum(p.toneladas) : '—'}</td><td>${fmtCorta(p.fecha_inicio)}</td><td>${fmtCorta(p.fecha_fin_plan)}</td><td>${fmtCorta(p.fecha_fin_real)}</td>
      <td>${p.dias_retraso > 0 ? `<span class="badge b-roj">Retraso ${p.dias_retraso} d</span>` : '<span class="badge b-ver">Cumplió</span>'}</td></tr>`).join('')}</table>`;
  };
  $('#q').oninput = pintar;
  $$('.pestanas button').forEach(b => b.onclick = () => { $$('.pestanas button').forEach(x => x.classList.toggle('activo', x === b)); $('#pcurso').classList.toggle('oculto', b.dataset.t !== 'curso'); $('#phist').classList.toggle('oculto', b.dataset.t !== 'hist'); });
  $$('[data-f]').forEach(b => b.onclick = () => { filtro = b.dataset.f; pintar(); });
  pintar();
}

async function vProyectoHist(id) {
  const m = shell('proyectos', `<a href="#/proyectos/hist">Proyectos</a><span class="sep">/</span>Histórico`);
  const d = await api('/api/proyectos/' + id);
  const p = d.proyecto;
  $('.migas').innerHTML += `<span class="sep">/</span>${esc(p.nombre)}`;
  m.innerHTML = `
  <div class="kpis">${kpi('Cliente', `<span style="font-size:17px">${esc(p.cliente)}</span>`, `Proyecto N° ${p.n_registro} · ${p.anio}`, '', 'proyectos')}
    ${kpi('Toneladas', p.toneladas ? fmtNum(p.toneladas) : '—', esc(p.tipo || 'fuera de la muestra'), 'mor', 'viga')}
    ${kpi('Plazo planificado', fmtCorta(p.fecha_fin_plan), `inicio ${fmtCorta(p.fecha_inicio)}`, '', 'reloj')}
    ${kpi('Entrega real', fmtCorta(p.fecha_fin_real), p.dias_retraso > 0 ? `${p.dias_retraso} días de retraso · penalidad ≈ ${p.dias_retraso} %` : 'a tiempo', p.dias_retraso > 0 ? 'roj' : 'ver', p.dias_retraso > 0 ? 'alerta' : 'check')}</div>
  ${p.en_muestra ? `
  <div class="tarjeta" style="margin-bottom:16px"><h3>Gantt de procesos <span><div class="vistas"><button data-g="plan" class="activo">Plan con el ratio vigente</button><button data-g="sim">Ejecución (SIMULADA)</button></div></span></h3>
    <div class="cuerpo"><div class="aviso oculto" id="avsim">${ic('alerta', 16)} La ejecución por proceso es SIMULADA (escenario M2) a partir de la duración real del proyecto; no hay registro real por proceso.</div>
    <div class="gantt-wrap" id="gh"></div>${leyendaCat()}</div></div>
  <div class="tarjeta"><h3>Procesos (Excel de la muestra de 25 proyectos)</h3><div class="cuerpo"><table class="tabla"><tr><th>Proceso</th><th class="num">Personas</th><th class="num">Días plan</th><th class="num">HH ratio vigente</th></tr>
    ${d.procesos.map(r => `<tr><td>${esc(r.proceso)}</td><td class="num">${r.personas}</td><td class="num">${r.dias_plan}</td><td class="num">${fmtNum(r.hh_ratio)}</td></tr>`).join('')}</table></div></div>`
    : `<div class="tarjeta"><div class="cuerpo vacio">Este proyecto está fuera de la muestra de 25: no hay detalle por proceso.</div></div>`}`;
  if (p.en_muestra) {
    gantt($('#gh'), d.gantt_plan);
    $$('[data-g]').forEach(b => b.onclick = () => { $$('[data-g]').forEach(x => x.classList.toggle('activo', x === b)); $('#avsim').classList.toggle('oculto', b.dataset.g !== 'sim'); gantt($('#gh'), b.dataset.g === 'sim' ? d.gantt_sim : d.gantt_plan); });
  }
}

async function vProyectoAct(id, qs = '') {
  const prm = new URLSearchParams(qs);
  const m = shell('proyectos', `<a href="#/proyectos">Proyectos</a><span class="sep">/</span>En curso`,
    `<button class="btn" onclick="location.hash='#/reporte/${id}'">${ic('reporte', 16)} Reporte semanal</button>
     <button class="btn" onclick="location.hash='#/tareas?p=${id}'">${ic('tareas', 16)} Tareas</button>
     ${puede(['jefe_taller', 'supervisor']) ? `<button class="btn" onclick="location.hash='#/planta?p=${id}'">${ic('planta', 16)} Registrar tareo</button>` : ''}
     <button class="btn nar" id="bpron">${ic('rayo', 16)} Re-pronosticar entrega</button>`);
  const d = await api('/api/proyectos_activos/' + id);
  const p = d.proyecto;
  $('.migas').innerHTML += `<span class="sep">/</span>${esc(p.codigo)}`;
  const avance = d.procesos.reduce((s, r) => s + Math.min(r.hh_reg, r.hh_p50), 0) / d.procesos.reduce((s, r) => s + r.hh_p50, 0);
  const tareas = await api('/api/tareas?proyecto_id=' + id);
  m.innerHTML = `
  ${p.es_demo ? `<div class="aviso">${ic('alerta', 16)} Proyecto de DEMOSTRACIÓN creado al instalar la plataforma.</div>` : ''}
  <div class="kpis">${kpi(esc(p.codigo), `<span style="font-size:17px">${esc(p.nombre)}</span>`, `${esc(p.cliente || '')} · ${fmtNum(p.ton)} t · ${esc(p.tipo.split(' /')[0])}`, '', 'proyectos')}
    ${kpi('Entrega comprometida', fmtCorta(p.fecha_comprometida), p.prob_cumplir != null ? `cotizada con P(cumplir) ${pct(p.prob_cumplir)}` : 'proyecto importado del Excel', 'mor', 'reloj')}
    ${kpi('Avance por HH', pct(avance), `${fmtNum(d.procesos.reduce((s, r) => s + r.hh_reg, 0))} HH registradas`, 'nar', 'reloj')}
    ${kpi('Tareas abiertas', tareas.filter(t => t.estado !== 'HECHO').length, `${tareas.filter(t => t.tipo === 'BLOQUEO' && t.estado !== 'HECHO').length} bloqueos`, 'roj', 'tareas')}</div>
  <div id="pron"></div>
  <div class="pestanas" id="ptabs"><button class="activo" data-t="res">${ic('gantt', 15)} Resumen y Gantt</button><button data-t="pie">${ic('viga', 15)} Piezas y avance</button>
    <button data-t="cur">${ic('curva', 15)} Curva S</button><button data-t="sem">${ic('semana', 15)} Semanas</button><button data-t="log">${ic('camion', 15)} Compras, servicios y eventos</button></div>
  <div id="t-pie" class="oculto">${cargando()}</div><div id="t-cur" class="oculto">${cargando()}</div><div id="t-sem" class="oculto">${cargando()}</div><div id="t-log" class="oculto">${cargando()}</div>
  <div id="t-res">
  <div class="tarjeta" style="margin-bottom:16px"><h3>Gantt del proyecto · plan P50 con avance real <span class="vistas"><button data-m="Day">Día</button><button data-m="Week" class="activo">Semana</button><button data-m="Month">Mes</button></span></h3>
    <div class="cuerpo"><div class="gantt-wrap" id="ga"></div>${leyendaCat()}</div></div>
  <div class="grid g2">
    <div class="tarjeta"><h3>Avance por proceso</h3><div class="cuerpo"><table class="tabla"><tr><th>Proceso</th>${d.procesos.some(r => r.hh_cotizador != null) ? '<th class="num" title="Estimación del cotizador (hoja COTIZ_PROCESO)">HH cotizador</th>' : ''}<th class="num">HH P50</th><th class="num">HH registradas</th><th>Avance</th></tr>
      ${d.procesos.map(r => `<tr><td><i style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${CAT[r.categoria][1]};margin-right:6px"></i>${esc(r.proceso)}</td>${d.procesos.some(x => x.hh_cotizador != null) ? `<td class="num">${fmtNum(r.hh_cotizador)}</td>` : ''}<td class="num">${fmtNum(r.hh_p50)}</td><td class="num">${fmtNum(r.hh_reg)}</td><td style="min-width:120px"><div class="barra ${r.avance >= 100 ? '' : 'nar'}"><i style="width:${r.avance}%"></i></div><span class="nota">${r.avance} %</span></td></tr>`).join('')}</table></div></div>
    <div class="tarjeta"><h3>Último tareo</h3><div class="cuerpo scroll"><table class="tabla"><tr><th>Fecha</th><th>Proceso</th><th class="num">Personas</th><th class="num">HH</th><th>Registró</th></tr>
      ${d.tareo.map(t => `<tr><td>${fmtCorta(t.fecha)}</td><td>${esc(S.cat.procesos[t.proceso - 1].nombre)}</td><td class="num">${t.n_personas}</td><td class="num">${fmtNum(t.hh)}</td><td class="nota">${esc(t.usuario || '')}</td></tr>`).join('') || '<tr><td colspan="5" class="vacio">Sin tareo</td></tr>'}</table></div></div>
  </div></div>`;
  const cargadas = {};
  $$('#ptabs button').forEach(b => b.onclick = () => {
    $$('#ptabs button').forEach(x => x.classList.toggle('activo', x === b));
    ['res', 'pie', 'cur', 'sem', 'log'].forEach(t => $('#t-' + t).classList.toggle('oculto', t !== b.dataset.t));
    if (!cargadas[b.dataset.t] && b.dataset.t !== 'res') { cargadas[b.dataset.t] = 1; ({ pie: tabPiezas, cur: tabCurva, sem: tabSemanas, log: tabLogistica })[b.dataset.t](id, prm.get('q') || ''); }
    S.charts.forEach(c => c.resize());
  });
  if (prm.get('tab')) { const b = $(`#ptabs [data-t="${prm.get('tab')}"]`); if (b) setTimeout(() => b.click(), 0); }
  let modo = 'Week';
  const dib = () => gantt($('#ga'), d.gantt, { modo });
  dib();
  $$('[data-m]').forEach(b => b.onclick = () => { modo = b.dataset.m; $$('[data-m]').forEach(x => x.classList.toggle('activo', x === b)); dib(); });
  $('#bpron').onclick = async () => {
    const b = $('#bpron'); b.disabled = true; $('#pron').innerHTML = cargando();
    try {
      const r = await api(`/api/proyectos_activos/${id}/pronostico`, { method: 'POST' });
      const txt = { VERDE: 'En camino', AMBAR: 'En riesgo', ROJO: 'Atraso probable' }[r.semaforo];
      $('#pron').innerHTML = `<div class="tarjeta" style="margin-bottom:16px"><h3>${ic('rayo', 17)} Re-pronóstico desde hoy (Monte Carlo sobre el trabajo restante)</h3><div class="cuerpo grid g3">
        <div class="semaforo ${r.semaforo}"><span class="luz"></span><div><b>${txt}</b><br>P(cumplir el ${fmtCorta(r.comprometida)}) = ${pct(r.prob_cumplir)}</div></div>
        <div>Fin probable (P50): <b>${fmtFecha(r.p50)}</b><br>Con 80 %: <b>${fmtFecha(r.p80)}</b><br>Con 90 %: <b>${fmtFecha(r.p90)}</b></div>
        <div>Penalidad esperada si se mantiene la fecha: <b>USD ${fmtNum(r.penalidad)}</b><br><span class="nota">Avance medio por proceso ${r.avance_global} % · usa el tareo y las paradas registradas.</span></div></div></div>`;
    } catch (e) { $('#pron').innerHTML = ''; toast(e.message, 1); } finally { b.disabled = false; }
  };
}

/* ---------- pestañas del proyecto en curso (v2) ---------- */
const barraGrupo = (filas, titulo) => `<div class="tarjeta"><h3>${titulo}</h3><div class="cuerpo"><table class="tabla">
  <tr><th></th><th class="num">kg</th><th class="num">Piezas</th><th>Avance ponderado</th></tr>
  ${filas.map(g => `<tr><td>${esc(g.nombre)}</td><td class="num">${fmtNum(g.kg)}</td><td class="num">${g.n}</td>
    <td style="min-width:150px"><div class="barra ${g.avance >= 99.9 ? '' : 'nar'}"><i style="width:${g.avance}%"></i></div><span class="nota">${g.avance} % · ${fmtNum(g.kg_avanzado)} kg</span></td></tr>`).join('')}</table></div></div>`;

async function tabPiezas(id, q0 = '') {
  const el = $('#t-pie');
  const d = await api(`/api/proyectos_activos/${id}/piezas`);
  const edita = puede(MARCAN_PIEZAS);
  const r = d.resumen;
  if (!d.piezas.length) {
    el.innerHTML = `<div class="tarjeta"><div class="cuerpo vacio">${ic('hoja', 36)}<p>Este proyecto aún no tiene piezas.<br>Cárgalas con la hoja PIEZAS del formato único.</p>
      ${puede(['jefe_taller', 'cotizador']) ? `<button class="btn prim" onclick="location.hash='#/importar'">${ic('importar', 16)} Importar Excel</button>` : ''}</div></div>`;
    return;
  }
  el.innerHTML = `
  <div class="kpis">${kpi('Avance físico ponderado', r.avance + ' %', `${fmtNum(r.kg_avanzado)} de ${fmtNum(r.kg_total)} kg`, 'nar', 'viga')}
    ${kpi('Partidas de piezas', r.n_piezas, `${fmtNum(d.piezas.reduce((s, p) => s + (p.cantidad || 0), 0))} unidades`, '', 'hoja')}
    ${kpi('Fierro negro liberado', (r.etapas[3].avance) + ' %', 'kg con liberación de calidad', 'ver', 'check')}
    ${kpi('Despachado', r.etapas[6].avance + ' %', 'kg con fecha de despacho', 'mor', 'camion')}</div>
  <div class="tarjeta" style="margin-bottom:16px"><h3>Avance por etapa <span class="nota">pesos de su hoja REPORTE_DE_HABILITADO (ajustables)</span></h3><div class="cuerpo">
    <div class="etapas">${r.etapas.map(e => `<div class="etapa"><div class="nota">${esc(e.etapa)} · peso ${e.peso} %</div><div class="barra ${e.avance >= 99.9 ? '' : 'nar'}" style="height:12px"><i style="width:${e.avance}%"></i></div><b>${e.avance} %</b> <span class="nota">${fmtNum(e.kg)} kg</span></div>`).join('')}</div></div></div>
  <div class="grid g3" style="margin-bottom:16px">${barraGrupo(r.tipo_elemento, 'Por tipo de elemento')}${barraGrupo(r.contratista, 'Por contratista')}${barraGrupo(r.clase_peso, 'Por clase de peso')}</div>
  <div class="tarjeta"><h3>Piezas <div class="buscar" style="min-width:220px">${ic('buscar', 15)}<input id="qpz" placeholder="Filtrar por marca, perfil, contratista..." value="${esc(q0)}"></div></h3>
    ${edita ? `<div class="accionpz" id="apz"><b id="nsel">0 seleccionadas</b>
      <select id="etpz">${d.etapas.map(e => `<option value="${e.col}" ${e.col === S.etapaPz ? 'selected' : ''}>${esc(e.nombre)}</option>`).join('')}</select>
      <input type="date" id="fepz" value="${hoyISO()}" max="${hoyISO()}">
      <button class="btn prim peq" id="bmarcar">${ic('check', 15)} Marcar etapa</button><button class="btn peq" id="bquitar" title="Corrige una fecha mal registrada">Quitar fecha</button>
      <span class="nota">Selecciona piezas con la casilla. Queda registrado quién y cuándo.</span></div>` : ''}
    <div class="cuerpo scroll" style="max-height:560px" id="lpz"></div></div>`;
  const marca = (f, c) => f ? `<span class="punto si" title="${esc(c)}: ${fmtCorta(f)}">●</span>` : `<span class="punto" title="${esc(c)}: pendiente">○</span>`;
  const sel = new Set();
  const contar = () => { if ($('#nsel')) $('#nsel').textContent = `${sel.size} seleccionada${sel.size === 1 ? '' : 's'}`; };
  const visibles = () => { const q = ($('#qpz').value || '').toLowerCase(); return d.piezas.filter(p => !q || `${p.tipo_elemento} ${p.conjunto} ${p.perfil} ${p.contratista} ${p.orden_fab}`.toLowerCase().includes(q)); };
  const pintar = () => {
    const ps = visibles();
    $('#lpz').innerHTML = `<table class="tabla"><tr>${edita ? `<th><input type="checkbox" id="pztodas" title="Seleccionar las visibles"></th>` : ''}<th>#</th><th>Marca</th><th>Elemento</th><th>Perfil</th><th class="num">Cant.</th><th class="num">kg</th><th>Clase</th><th>Contratista</th><th>O.F.</th>
      ${d.etapas.map(e => `<th title="peso ${e.peso} %">${esc(e.nombre.split(' ')[0].slice(0, 5))}</th>`).join('')}<th>Avance</th></tr>
      ${ps.map(p => `<tr>${edita ? `<td><input type="checkbox" class="pzc" data-id="${p.id}" ${sel.has(p.id) ? 'checked' : ''}></td>` : ''}<td>${p.n_item}</td><td><b>${esc(p.conjunto)}</b></td><td>${esc(p.tipo_elemento)}</td><td class="nota">${esc(p.perfil || '')}</td><td class="num">${p.cantidad}</td>
        <td class="num">${fmtNum(p.peso_total)}</td><td class="nota">${esc((p.clase_peso || '').split(' ')[0])}</td><td class="nota">${esc(p.contratista || '')}</td><td>${esc(p.orden_fab || '')}</td>
        ${d.etapas.map(e => `<td style="text-align:center">${marca(p[e.col], e.nombre)}</td>`).join('')}
        <td style="min-width:90px"><div class="barra ${p.avance >= 99.9 ? '' : 'nar'}"><i style="width:${p.avance}%"></i></div><span class="nota">${p.avance} %</span></td></tr>`).join('')}</table>`;
    if (!edita) return;
    $$('.pzc', el).forEach(c => c.onchange = () => { c.checked ? sel.add(+c.dataset.id) : sel.delete(+c.dataset.id); contar(); });
    $('#pztodas').onchange = e => { ps.forEach(p => e.target.checked ? sel.add(p.id) : sel.delete(p.id)); pintar(); contar(); };
  };
  $('#qpz').oninput = pintar;
  const aplicar = async fecha => {
    if (!sel.size) return toast('Selecciona al menos una pieza', 1);
    const etapa = $('#etpz').value;
    S.etapaPz = etapa;
    try {
      const r = await api('/api/piezas/etapa', { method: 'POST', body: { ids: [...sel], etapa, fecha } });
      toast(`${r.actualizadas} piezas actualizadas${r.errores.length ? ` · ${r.errores.length} rechazadas` : ''}`, r.errores.length && !r.actualizadas);
      if (r.errores.length) modal('Piezas no actualizadas', `<p class="nota">Estas piezas no respetan el orden de fabricación; corrige primero la etapa anterior.</p>
        <table class="tabla"><tr><th>Marca</th><th>Motivo</th></tr>${r.errores.slice(0, 50).map(x => `<tr><td><b>${esc(x.conjunto)}</b></td><td>${esc(x.msg)}</td></tr>`).join('')}</table>`, async () => {}, 'Entendido');
      tabPiezas(id, $('#qpz').value);
    } catch (e) { toast(e.message, 1); }
  };
  if (edita) {
    $('#bmarcar').onclick = () => aplicar($('#fepz').value || hoyISO());
    $('#bquitar').onclick = () => aplicar(null);
  }
  pintar();
}

async function tabSemanas(id) {
  const el = $('#t-sem');
  const [d, hp] = await Promise.all([api(`/api/proyectos_activos/${id}/semanas`), api(`/api/proyectos_activos/${id}/pronosticos`)]);
  const idx = v => v == null ? '<span class="nota">—</span>' : `<span class="badge ${v >= 1 ? 'b-ver' : v >= .9 ? 'b-nar' : 'b-roj'}">${v.toFixed(2)}</span>`;
  el.innerHTML = `
  <div class="tarjeta" style="margin-bottom:16px"><h3>${ic('semana', 17)} Semanas de producción <span class="nota">ciclo lunes–sábado · plan P50 vs. real</span></h3><div class="cuerpo">
    <div class="grafico bajo" id="gsem"></div>
    <div class="scroll" style="max-height:420px"><table class="tabla"><tr><th>Sem.</th><th>Del</th><th>Al</th><th class="num">kg plan</th><th class="num">kg real</th><th class="num">HH plan</th><th class="num">HH real</th><th>Índice kg (acum.)</th><th>Índice HH (acum.)</th><th></th></tr>
    ${d.semanas.map(s => `<tr class="${s.en_curso ? 'actual' : ''}" title="${s.en_curso ? 'Semana en curso: real e índice al ' + fmtCorta(s.al) : ''}"><td><b>S${s.n}</b>${s.en_curso ? ' <span class="nota">en curso</span>' : ''}</td><td>${fmtCorta(s.inicio)}</td><td>${fmtCorta(s.fin)}</td><td class="num">${fmtNum(s.plan_kg)}</td><td class="num">${d.tiene_piezas ? fmtNum(s.real_kg) : '—'}</td>
      <td class="num">${fmtNum(s.plan_hh)}</td><td class="num">${fmtNum(s.real_hh)}</td><td>${d.tiene_piezas ? idx(s.spi_kg) : '—'}</td><td>${idx(s.spi_hh)}</td>
      <td>${s.real_hh_acum != null ? `<a class="btn peq" href="#/reporte/${id}?semana=${s.inicio}">${ic('reporte', 14)} Reporte</a>` : ''}</td></tr>`).join('')}</table></div></div></div>
  <div class="tarjeta"><h3>${ic('rayo', 17)} Historial de re-pronósticos <span class="nota">permite medir con cuánta anticipación se avisó un atraso</span></h3><div class="cuerpo">
    ${hp.length ? `<div class="grafico bajo" id="ghp"></div><table class="tabla"><tr><th>Fecha</th><th>P(cumplir)</th><th>P50</th><th>P80</th><th>Avance HH</th><th>Avance físico</th><th>Semáforo</th><th>Usuario</th></tr>
      ${hp.slice().reverse().map(x => `<tr><td>${fmtCorta(x.fecha)}</td><td><b>${pct(x.prob_cumplir)}</b></td><td>${fmtCorta(x.p50)}</td><td>${fmtCorta(x.p80)}</td><td>${x.avance_hh ?? '—'} %</td><td>${x.avance_fisico ?? '—'}${x.avance_fisico != null ? ' %' : ''}</td>
        <td><span class="badge ${{ VERDE: 'b-ver', AMBAR: 'b-nar', ROJO: 'b-roj' }[x.semaforo]}">${esc(x.semaforo)}</span></td><td class="nota">${esc(x.usuario || '')}</td></tr>`).join('')}</table>`
      : '<div class="vacio">Aún no hay re-pronósticos. Usa el botón «Re-pronosticar entrega» cada semana: queda guardado aquí.</div>'}</div></div>`;
  const s = d.semanas;
  chart($('#gsem'), { grid: { left: 60, right: 50, top: 30, bottom: 40 }, tooltip: { trigger: 'axis' }, legend: { bottom: 0 },
    xAxis: { type: 'category', data: s.map(x => 'S' + x.n) }, yAxis: [{ type: 'value', name: 'kg' }, { type: 'value', name: 'HH', splitLine: { show: false } }],
    series: [{ name: 'kg plan', type: 'bar', data: s.map(x => x.plan_kg), itemStyle: { color: '#c3ccd5' } },
      ...(d.tiene_piezas ? [{ name: 'kg real', type: 'bar', data: s.map(x => x.real_kg), itemStyle: { color: '#0a6ed1' } }] : []),
      { name: 'HH plan', type: 'line', yAxisIndex: 1, data: s.map(x => x.plan_hh), itemStyle: { color: '#5b738b' }, lineStyle: { type: 'dashed', color: '#5b738b' } },
      { name: 'HH real', type: 'line', yAxisIndex: 1, data: s.map(x => x.real_hh), itemStyle: { color: '#e9730c' }, lineStyle: { color: '#e9730c', width: 2 } }] });
  if (hp.length) chart($('#ghp'), { grid: { left: 50, right: 20, top: 20, bottom: 30 }, tooltip: { trigger: 'axis', valueFormatter: v => v + ' %' },
    xAxis: { type: 'category', data: hp.map(x => fmtCorta(x.fecha)) }, yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value} %' } },
    series: [{ type: 'line', data: hp.map(x => ({ value: +(100 * x.prob_cumplir).toFixed(1), itemStyle: { color: { VERDE: '#107e3e', AMBAR: '#e9730c', ROJO: '#bb0000' }[x.semaforo] } })),
      lineStyle: { color: '#0a6ed1' }, symbolSize: 9 }] });
}

async function tabCurva(id) {
  const el = $('#t-cur');
  const c = await api(`/api/proyectos_activos/${id}/curva_s`);
  const lectura = s => s == null ? '—' : s >= 1 ? 'adelantado o al día' : s >= 0.9 ? 'ligeramente atrasado' : 'atrasado';
  el.innerHTML = `
  <div class="kpis">${kpi('Índice de avance (kg)', c.spi_kg ?? '—', c.spi_kg == null ? 'sin piezas importadas' : `real / plan al ${fmtCorta(c.hoy)} · ${lectura(c.spi_kg)}`, c.spi_kg == null ? '' : c.spi_kg >= 1 ? 'ver' : c.spi_kg >= .9 ? 'nar' : 'roj', 'curva')}
    ${kpi('Índice de avance (HH)', c.spi_hh ?? '—', `real / plan al ${fmtCorta(c.hoy)} · ${lectura(c.spi_hh)}`, c.spi_hh == null ? '' : c.spi_hh >= 1 ? 'ver' : c.spi_hh >= .9 ? 'nar' : 'roj', 'reloj')}
    ${kpi('Fin del plan P50', fmtCorta(c.fin_plan), `comprometida ${fmtCorta(c.comprometida)}`, 'mor', 'gantt')}
    ${kpi('Peso del plan', fmtNum(c.kg_total_plan) + ' kg', esc(c.fuente_kg), '', 'viga')}</div>
  <div class="tarjeta" style="margin-bottom:16px"><h3>Curva S · kg ponderados (planificado vs. real)</h3><div class="cuerpo"><div class="grafico" id="gcs"></div>
    <p class="nota">Plan: el programa P50 de la cotización repartido por etapas (habilitado, armado, soldeo, liberación, granallado, pintura, despacho) con sus pesos. Real: cada pieza suma su peso × peso de la etapa en la fecha en que se completó.</p></div></div>
  <div class="tarjeta"><h3>Curva S · horas-hombre (P50 cotizado vs. tareo)</h3><div class="cuerpo"><div class="grafico bajo" id="gch"></div></div></div>`;
  const x = c.fechas.map(f => f.slice(5).split('-').reverse().join('/'));
  const marcas = [{ name: 'hoy', xAxis: c.hoy.slice(5).split('-').reverse().join('/'), lineStyle: { color: '#e9730c' } }];
  if (c.comprometida && c.fechas.includes(c.comprometida)) marcas.push({ name: 'comprometida', xAxis: c.comprometida.slice(5).split('-').reverse().join('/'), lineStyle: { color: '#bb0000' } });
  const op = (plan, real, unidad) => ({ grid: { left: 60, right: 20, top: 30, bottom: 40 }, tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '—' : fmtNum(v) + ' ' + unidad },
    legend: { bottom: 0 }, xAxis: { type: 'category', data: x, boundaryGap: false }, yAxis: { type: 'value', name: unidad },
    series: [{ name: 'Planificado (P50)', type: 'line', data: plan, showSymbol: false, itemStyle: { color: '#5b738b' }, lineStyle: { type: 'dashed', width: 2, color: '#5b738b' } },
      { name: 'Real', type: 'line', data: real, showSymbol: false, connectNulls: false, itemStyle: { color: '#0a6ed1' }, lineStyle: { width: 3, color: '#0a6ed1' }, areaStyle: { color: 'rgba(27,144,255,.15)' },
        markLine: { symbol: 'none', label: { formatter: p => p.name }, data: marcas } }] });
  chart($('#gcs'), op(c.plan_kg, c.real_kg, 'kg'));
  chart($('#gch'), op(c.plan_hh, c.real_hh, 'HH'));
}

async function tabLogistica(id) {
  const el = $('#t-log');
  const d = await api(`/api/proyectos_activos/${id}/piezas`);
  const dias = (a, b) => a && b ? Math.round((new Date(b) - new Date(a)) / 864e5) : null;
  el.innerHTML = `<div class="grid g2">
    <div class="tarjeta"><h3>${ic('camion', 16)} Compras de material</h3><div class="cuerpo scroll"><table class="tabla"><tr><th>OC</th><th>Material</th><th class="num">kg</th><th>Pedido</th><th>Prometida</th><th>Recibida</th><th>Atraso</th></tr>
      ${d.compras.map(c => { const at = dias(c.fecha_prometida, c.fecha_recepcion); return `<tr><td>${esc(c.n_oc)}</td><td>${esc(c.material)}</td><td class="num">${fmtNum(c.kg)}</td><td>${fmtCorta(c.fecha_pedido)}</td><td>${fmtCorta(c.fecha_prometida)}</td><td>${fmtCorta(c.fecha_recepcion)}</td>
        <td>${at == null ? '<span class="badge b-gris">pendiente</span>' : at > 0 ? `<span class="badge b-roj">${at} d</span>` : '<span class="badge b-ver">a tiempo</span>'}</td></tr>`; }).join('') || '<tr><td colspan="7" class="vacio">Sin compras registradas</td></tr>'}</table></div></div>
    <div class="tarjeta"><h3>Servicios externos</h3><div class="cuerpo scroll"><table class="tabla"><tr><th>Servicio</th><th>Proveedor</th><th>Envío</th><th>Retorno</th><th class="num">Días</th></tr>
      ${d.servicios.map(s => `<tr><td>${esc(s.servicio)}</td><td>${esc(s.proveedor || '')}</td><td>${fmtCorta(s.fecha_envio)}</td><td>${s.fecha_retorno ? fmtCorta(s.fecha_retorno) : '<span class="badge b-az">en proveedor</span>'}</td><td class="num">${dias(s.fecha_envio, s.fecha_retorno) ?? '—'}</td></tr>`).join('') || '<tr><td colspan="5" class="vacio">Sin servicios</td></tr>'}</table></div></div>
    <div class="tarjeta" style="grid-column:1/-1"><h3>${ic('alerta', 16)} Eventos que afectan el plazo</h3><div class="cuerpo"><table class="tabla"><tr><th>Fecha</th><th>Tipo</th><th>Imputable a</th><th class="num">Días</th><th>Ampliación</th><th>Descripción</th></tr>
      ${d.eventos.map(e => `<tr><td>${fmtCorta(e.fecha)}</td><td>${esc(e.tipo)}</td><td><span class="badge ${e.imputable === 'Cliente' ? 'b-mor' : e.imputable === 'Steelser' ? 'b-roj' : 'b-gris'}">${esc(e.imputable || '—')}</span></td>
        <td class="num">${e.dias_impacto ?? '—'}</td><td>${e.pidio_ampliacion ? 'Sí' : 'No'}</td><td>${esc(e.descripcion)}</td></tr>`).join('') || '<tr><td colspan="6" class="vacio">Sin eventos</td></tr>'}</table>
      <p class="nota">Los días imputables al cliente justifican ampliaciones de plazo y no deberían contar como incumplimiento de la planta.</p></div></div></div>`;
}

/* =====================================================================  IMPORTAR (formato único) */
async function vImportar() {
  const m = shell('importar', `${ic('importar', 20)} Importar formato único`,
    `<a class="btn" href="/api/plantilla">${ic('hoja', 16)} Descargar plantilla vacía</a>`);
  const hist = await api('/api/importaciones');
  m.innerHTML = `
  <div class="grid cotz">
    <div class="tarjeta"><h3>${ic('hoja', 17)} Archivo Excel (.xlsx)</h3><div class="cuerpo" style="display:grid;gap:12px">
      <label class="soltar" id="zona">${ic('importar', 34)}<span>Arrastra aquí el formato único<br>o haz clic para elegirlo</span><input type="file" id="farch" accept=".xlsx" hidden></label>
      <div id="nomarch" class="nota"></div>
      <div style="display:flex;gap:8px"><button class="btn" id="bval" disabled>${ic('check', 16)} 1. Validar</button><button class="btn prim" id="bimp" disabled>${ic('importar', 16)} 2. Importar</button></div>
      <ol class="nota" style="margin:0;padding-left:18px"><li>Validar revisa todas las filas y no guarda nada.</li><li>Importar guarda; volver a importar el mismo archivo actualiza y no duplica.</li>
        <li>Las filas con error se omiten y se listan con su número de fila para corregirlas en el Excel.</li></ol>
    </div></div>
    <div id="rep"><div class="tarjeta"><div class="cuerpo vacio">${ic('hoja', 40)}<p>Elige un archivo para ver el reporte de validación.</p></div></div></div>
  </div>
  <div class="tarjeta" style="margin-top:16px"><h3>Historial de importaciones</h3><div class="cuerpo"><table class="tabla"><tr><th>Fecha</th><th>Archivo</th><th>Usuario</th><th class="num">Filas</th><th class="num">Cambios</th><th class="num">Errores</th><th>OT</th></tr>
    ${hist.map(h => `<tr><td>${esc(String(h.creado_en).slice(0, 16))}</td><td>${esc(h.archivo)}</td><td class="nota">${esc(h.usuario || '')}</td><td class="num">${h.filas}</td><td class="num">${h.cambios}</td>
      <td class="num">${h.errores ? `<span class="badge b-roj">${h.errores}</span>` : '<span class="badge b-ver">0</span>'}</td><td>${h.ots.map(esc).join(', ')}</td></tr>`).join('') || '<tr><td colspan="7" class="vacio">Sin importaciones</td></tr>'}</table></div></div>`;
  let archivo = null;
  const elegir = f => { if (!f) return; if (!f.name.toLowerCase().endsWith('.xlsx')) return toast('Solo archivos .xlsx', 1);
    archivo = f; $('#nomarch').innerHTML = `${ic('hoja', 14)} <b>${esc(f.name)}</b> · ${fmtNum(f.size / 1024, 1)} KB`; $('#bval').disabled = false; $('#bimp').disabled = false; };
  $('#farch').onchange = e => elegir(e.target.files[0]);
  const z = $('#zona');
  z.ondragover = e => { e.preventDefault(); z.classList.add('sobre'); };
  z.ondragleave = () => z.classList.remove('sobre');
  z.ondrop = e => { e.preventDefault(); z.classList.remove('sobre'); elegir(e.dataTransfer.files[0]); };
  const enviar = async modo => {
    if (!archivo) return;
    $$('#bval, #bimp').forEach(b => b.disabled = true); $('#rep').innerHTML = `<div class="tarjeta">${cargando()}</div>`;
    try {
      const r = await fetch(`/api/importar?modo=${modo}&archivo=${encodeURIComponent(archivo.name)}`, { method: 'POST', body: archivo, credentials: 'same-origin',
        headers: { 'Content-Type': 'application/octet-stream' } });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : r.statusText);
      reporteImportacion(j);
      if (modo === 'importar') { toast(`Importado: ${j.cambios} registros`); S.cat = await api('/api/catalogos'); setTimeout(() => vImportar(), 2500); }
    } catch (e) { $('#rep').innerHTML = `<div class="tarjeta"><div class="cuerpo vacio">${ic('alerta', 30)}<p>${esc(e.message)}</p></div></div>`; }
    finally { $$('#bval, #bimp').forEach(b => b.disabled = false); }
  };
  $('#bval').onclick = () => enviar('validar');
  $('#bimp').onclick = () => enviar('importar');
}

function reporteImportacion(j) {
  const hojas = Object.entries(j.hojas);
  const errores = hojas.flatMap(([h, r]) => r.errores.map(e => ({ hoja: h, ...e })));
  $('#rep').innerHTML = `
  <div class="semaforo ${j.errores ? 'AMBAR' : 'VERDE'}" style="margin-bottom:12px"><span class="luz"></span><div><b>${j.aplicado ? 'Importación aplicada' : 'Validación (no se guardó nada)'}</b>:
    ${j.filas} filas leídas, ${j.cambios} ${j.aplicado ? 'registros guardados' : 'registros se guardarían'}, ${j.errores} filas con error. OT: ${j.ots.map(esc).join(', ') || '—'}</div></div>
  <div class="tarjeta" style="margin-bottom:12px"><h3>Por hoja</h3><div class="cuerpo"><table class="tabla"><tr><th>Hoja</th><th class="num">Leídas</th><th class="num">Nuevas</th><th class="num">Actualizadas</th><th class="num">Ya existían</th><th class="num">Errores</th></tr>
    ${hojas.map(([h, r]) => `<tr><td><b>${esc(h)}</b></td><td class="num">${r.leidas}</td><td class="num">${r.nuevas}</td><td class="num">${r.actualizadas}</td><td class="num">${r.omitidas}</td>
      <td class="num">${r.errores.length ? `<span class="badge b-roj">${r.errores.length}</span>` : '<span class="badge b-ver">0</span>'}</td></tr>`).join('')}</table></div></div>
  ${errores.length ? `<div class="tarjeta"><h3>${ic('alerta', 16)} Filas a corregir en el Excel</h3><div class="cuerpo scroll"><table class="tabla"><tr><th>Hoja</th><th class="num">Fila</th><th>Problema</th></tr>
    ${errores.slice(0, 300).map(e => `<tr><td>${esc(e.hoja)}</td><td class="num">${e.fila}</td><td>${esc(e.msg)}</td></tr>`).join('')}</table></div></div>` : ''}`;
}

/* =====================================================================  GANTT DEL TALLER */
async function vGantt() {
  const m = shell('gantt', `${ic('gantt', 20)} Gantt de proyectos`,
    `<select id="gan"><option value="activos">En curso</option></select>
     <div class="vistas"><button data-m="Week">Semana</button><button data-m="Month" class="activo">Mes</button></div>`);
  const d = await api('/api/gantt/taller');
  const anios = [...new Set(d.historico.map(r => r.anio))].sort((a, b) => b - a);
  $('#gan').innerHTML += anios.map(a => `<option value="${a}">${a}</option>`).join('');
  $('#gan').value = d.activos.length ? 'activos' : String(anios[0]);
  m.innerHTML = `<div class="tarjeta"><h3>Proyectos en el tiempo <span class="leyenda" style="margin:0"><span><i style="background:#9bd3ae"></i>Cumplió</span><span><i style="background:#f2a3a3"></i>Con retraso</span><span><i style="background:#1b90ff"></i>En curso</span></span></h3>
    <div class="cuerpo"><div class="gantt-wrap" id="gt"></div><p class="nota">Barra = inicio → entrega real (histórico) o → entrega comprometida (en curso). Clic en una barra para abrir el proyecto.</p></div></div>`;
  let modo = 'Month';
  const dib = () => {
    const v = $('#gan').value;
    const t = v === 'activos' ? d.activos : d.historico.filter(r => String(r.anio) === v);
    gantt($('#gt'), t, { modo, extra: x => x.plan_fin ? `<br>Fin plan ${fmtCorta(x.plan_fin)}${x.retraso > 0 ? `<br><b style="color:var(--rojo)">Retraso ${x.retraso} días</b>` : ''}` : '',
      click: task => location.hash = task.id[0] === 'h' ? `#/proyecto/h/${task.id.slice(1)}` : `#/proyecto/a/${task.id.slice(1)}` });
  };
  $('#gan').onchange = dib;
  $$('[data-m]').forEach(b => b.onclick = () => { modo = b.dataset.m; $$('[data-m]').forEach(x => x.classList.toggle('activo', x === b)); dib(); });
  dib();
}

/* =====================================================================  COTIZADOR */
async function vCotizador() {
  const m = shell('cotizador', `${ic('cotizador', 20)} Cotizador de plazos`);
  const def = S.ultimaSol || { tipo: S.cat.tipos[1], ton: 47, pct_planchas: 0.17, piezas_por_t: 8, m2_pint_t: 14, montaje: false, presupuesto: 150000,
    inicio: hoyISO(), fecha_pedida: '', penalidad: 0.01, pierde_por_dia: 0.005, margen: 0.16, carga_extra: 0, replicas: 1000 };
  m.innerHTML = `
  <div class="aviso">${ic('alerta', 16)} Modelo de horas entrenado con datos SIMULADOS (25 proyectos, escenario M2) hasta cargar los tareos reales. Úsalo para probar el flujo, no para ofertar.</div>
  <div class="grid cotz">
    <form class="tarjeta" id="fcot"><h3>${ic('viga', 17)} Proyecto a cotizar</h3><div class="cuerpo form">
      <label class="ancho">Tipo de estructura<select name="tipo">${S.cat.tipos.map(t => `<option ${t === def.tipo ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select></label>
      <label>Toneladas (metrado)<input name="ton" type="number" step="0.5" min="1" value="${def.ton}"></label>
      <label>% planchas<input name="pct_planchas" type="number" step="1" min="0" max="80" value="${Math.round(def.pct_planchas * 100)}"></label>
      <label>Piezas por t<input name="piezas_por_t" type="number" step="0.5" min="1" value="${def.piezas_por_t}"></label>
      <label>m² pintura por t<input name="m2_pint_t" type="number" step="1" min="1" value="${def.m2_pint_t}"></label>
      <label>Presupuesto (USD)<input name="presupuesto" type="number" step="1000" min="1000" value="${def.presupuesto}"></label>
      <label>Día 1 (planos + OC)<input name="inicio" type="date" value="${def.inicio}"></label>
      <label>Fecha que pide el cliente<input name="fecha_pedida" type="date" value="${def.fecha_pedida || ''}"></label>
      <label class="chk ancho"><input type="checkbox" name="montaje" ${def.montaje ? 'checked' : ''}> Incluye montaje</label>
      <details class="ancho"><summary class="nota" style="cursor:pointer">Riesgo, competitividad y simulación</summary><div class="form" style="margin-top:10px">
        <label>Penalidad por día (%)<input name="penalidad" type="number" step="0.1" value="${def.penalidad * 100}"></label>
        <label>Pierde oferta por día extra (pts %)<input name="pierde_por_dia" type="number" step="0.1" value="${def.pierde_por_dia * 100}"></label>
        <label>Margen (%)<input name="margen" type="number" step="1" value="${def.margen * 100}"></label>
        <label>Carga extra de máquinas (%)<input name="carga_extra" type="number" step="5" min="0" max="80" value="${def.carga_extra * 100}"></label>
        <label>Réplicas Monte Carlo<select name="replicas">${[500, 1000, 2000].map(r => `<option ${r === def.replicas ? 'selected' : ''}>${r}</option>`).join('')}</select></label>
      </div></details>
      <button class="btn prim ancho" style="justify-content:center" id="bcot">${ic('rayo', 16)} Calcular fecha realista</button>
    </div></form>
    <div id="rcot"><div class="tarjeta"><div class="cuerpo vacio">${ic('cotizador', 40)}<p>Completa los datos y calcula.<br>El sistema simula 1 000 futuros del taller (horas, paradas de las 4 máquinas, carga, proveedores).</p></div></div></div>
  </div>`;
  $('#fcot').onsubmit = async e => {
    e.preventDefault(); const f = new FormData(e.target); const b = $('#bcot'); b.disabled = true;
    const s = { tipo: f.get('tipo'), ton: +f.get('ton'), pct_planchas: f.get('pct_planchas') / 100, piezas_por_t: +f.get('piezas_por_t'), m2_pint_t: +f.get('m2_pint_t'),
      montaje: !!f.get('montaje'), presupuesto: +f.get('presupuesto'), inicio: f.get('inicio'), fecha_pedida: f.get('fecha_pedida') || null,
      penalidad: f.get('penalidad') / 100, pierde_por_dia: f.get('pierde_por_dia') / 100, margen: f.get('margen') / 100, carga_extra: f.get('carga_extra') / 100, replicas: +f.get('replicas') };
    $('#rcot').innerHTML = `<div class="tarjeta">${cargando()}<p class="nota" style="text-align:center;padding-bottom:20px">Simulando ${s.replicas} futuros del taller…</p></div>`;
    try { const r = await api('/api/cotizar', { method: 'POST', body: s }); S.ultimaCot = r; S.ultimaSol = s; resultadoCot(r, s); }
    catch (err) { $('#rcot').innerHTML = ''; toast(err.message, 1); } finally { b.disabled = false; }
  };
  if (S.ultimaCot) resultadoCot(S.ultimaCot, S.ultimaSol);
}

function resultadoCot(r, s) {
  S.charts.forEach(c => c.dispose()); S.charts = [];
  const sem = r.pedida ? (r.pedida.prob >= r.alpha ? 'VERDE' : r.pedida.prob >= .5 ? 'AMBAR' : 'ROJO') : null;
  $('#rcot').innerHTML = `
  <div class="kpis">
    ${kpi('Fecha recomendada', fmtCorta(r.fecha_recomendada), `${r.plazo} días calendario · confianza ${pct(r.alpha)}`, 'ver', 'check')}
    ${kpi('Probabilidad de cumplir', pct(r.prob), `P50 ${fmtCorta(r.p50)} · P90 ${fmtCorta(r.p90)}`, '', 'chispa')}
    ${kpi('Penalidad esperada', 'USD ' + fmtNum(r.penalidad), `${(100 * r.penalidad / s.presupuesto).toFixed(2)} % del presupuesto`, 'nar', 'alerta')}
    ${kpi('Método actual (ratio)', fmtCorta(r.fecha_metodo_actual), `solo ${pct(r.prob_metodo_actual)} de probabilidad de cumplir`, 'roj', 'reloj')}
  </div>
  ${sem ? `<div class="semaforo ${sem}" style="margin-bottom:16px"><span class="luz"></span><div><b>${{ VERDE: 'Viable', AMBAR: 'Riesgoso', ROJO: 'No recomendable' }[sem]}:</b> el cliente pide el ${fmtFecha(r.pedida.fecha)} → probabilidad de cumplir ${pct(r.pedida.prob)}, penalidad esperada USD ${fmtNum(r.pedida.penalidad)}.</div></div>` : ''}
  <div class="tarjeta" style="margin-bottom:16px"><h3>Plazo vs. riesgo y competitividad
    ${puede(['cotizador']) ? `<button class="btn prim peq" id="bcrear">${ic('mas', 15)} Crear proyecto con esta fecha</button>` : ''}</h3>
    <div class="cuerpo"><div class="grafico" id="gcurva"></div><p class="nota">La curva naranja suma la penalidad esperada y el costo de ofertar un plazo largo (perder la oferta). Su mínimo es la fecha económicamente óptima. ${esc(r.modelo.entrenado_con)} · MTBF: ${esc(r.modelo.fuente_mtbf)}.</p></div></div>
  <div class="tarjeta" style="margin-bottom:16px"><h3>Programa probable (réplica mediana)</h3><div class="cuerpo"><div class="gantt-wrap" id="gcot"></div>${leyendaCat()}</div></div>
  <div class="grid g2">
    <div class="tarjeta"><h3>Horas-hombre por proceso <span class="nota">ratio actual ${fmtNum(r.hh_ratio_total)} HH · P50 ${fmtNum(r.hh_total_p50)} HH</span></h3><div class="cuerpo"><table class="tabla"><tr><th>Proceso</th><th class="num">P10</th><th class="num">P50</th><th class="num">P90</th></tr>
      ${r.hh.map(h => `<tr><td><i style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${CAT[h.categoria][1]};margin-right:6px"></i>${esc(h.proceso)}</td><td class="num">${fmtNum(h.p10)}</td><td class="num"><b>${fmtNum(h.p50)}</b></td><td class="num">${fmtNum(h.p90)}</td></tr>`).join('')}</table></div></div>
    <div class="tarjeta"><h3>Distribución de la fecha de fin</h3><div class="cuerpo"><div class="grafico" id="ghist"></div></div></div>
  </div>`;
  const c = r.curva;
  chart($('#gcurva'), {
    grid: { left: 50, right: 70, top: 30, bottom: 50 }, tooltip: { trigger: 'axis' }, legend: { bottom: 0 },
    xAxis: { type: 'category', data: c.map(x => x.fecha.slice(5).split('-').reverse().join('/')) },
    yAxis: [{ type: 'value', max: 100, name: 'P(cumplir) %', axisLabel: { formatter: '{value}' } }, { type: 'value', name: 'USD', splitLine: { show: false } }],
    series: [
      { name: 'Probabilidad de cumplir', type: 'line', smooth: true, showSymbol: false, data: c.map(x => +(100 * x.prob).toFixed(1)), itemStyle: { color: '#0a6ed1' }, lineStyle: { width: 3, color: '#0a6ed1' }, areaStyle: { color: 'rgba(27,144,255,.12)' },
        markLine: { symbol: 'none', label: { formatter: p => p.name }, data: [
          { name: 'recomendada', xAxis: r.fecha_recomendada.slice(5).split('-').reverse().join('/'), lineStyle: { color: '#107e3e' } },
          { name: 'método actual', xAxis: r.fecha_metodo_actual.slice(5).split('-').reverse().join('/'), lineStyle: { color: '#bb0000' } },
          ...(r.pedida ? [{ name: 'pedida', xAxis: r.pedida.fecha.slice(5).split('-').reverse().join('/'), lineStyle: { color: '#925ace' } }] : [])].filter(x => c.some(y => y.fecha.slice(5).split('-').reverse().join('/') === x.xAxis)) } },
      { name: 'Penalidad esperada', type: 'line', yAxisIndex: 1, showSymbol: false, data: c.map(x => x.pen), itemStyle: { color: '#bb0000' }, lineStyle: { type: 'dashed', color: '#bb0000' } },
      { name: 'Costo total (penalidad + plazo largo)', type: 'line', yAxisIndex: 1, showSymbol: false, data: c.map(x => x.costo), itemStyle: { color: '#e9730c' }, lineStyle: { color: '#e9730c', width: 2 } },
    ] });
  chart($('#ghist'), { grid: { left: 40, right: 10, top: 10, bottom: 40 }, tooltip: {}, xAxis: { type: 'category', data: r.histograma_fechas.map(f => f.slice(5).split('-').reverse().join('/')) },
    yAxis: { type: 'value', name: 'réplicas' }, series: [{ type: 'bar', data: r.histograma, itemStyle: { color: '#1b90ff', borderRadius: [3, 3, 0, 0] } }] });
  gantt($('#gcot'), r.gantt);
  const bc = $('#bcrear');
  if (bc) bc.onclick = () => modalProyecto(r, s);
}

function modal(titulo, cuerpo, onok, txtok = 'Guardar') {
  const v = document.createElement('div'); v.className = 'velo';
  const mo = document.createElement('div'); mo.className = 'modal';
  mo.innerHTML = `<header>${titulo}</header><form><div class="cuerpo">${cuerpo}<div class="error" id="merr"></div></div><footer><button type="button" class="btn" id="mcan">Cancelar</button><button class="btn prim">${txtok}</button></footer></form>`;
  document.body.append(v, mo);
  const cerrar = () => { v.remove(); mo.remove(); };
  v.onclick = cerrar; $('#mcan', mo).onclick = cerrar;
  $('form', mo).onsubmit = async e => { e.preventDefault(); try { await onok(new FormData(e.target)); cerrar(); } catch (err) { $('#merr', mo).textContent = err.message; } };
  return mo;
}
function modalProyecto(r, s) {
  modal('Crear proyecto desde la cotización', `<div class="form">
    <label>Código OT<input name="codigo" required placeholder="OT-2026-001"></label><label>Cliente<input name="cliente"></label>
    <label class="ancho">Nombre del proyecto<input name="nombre" required></label>
    <label>Entrega comprometida<input name="fecha" type="date" value="${r.fecha_recomendada}" required></label>
    <p class="nota ancho">Fecha recomendada ${fmtFecha(r.fecha_recomendada)} con ${pct(r.prob)} de probabilidad. Si cambias la fecha, la probabilidad cotizada se recalcula en el re-pronóstico.</p></div>`,
  async f => {
    const fecha = f.get('fecha');
    const prob = r.curva.find(x => x.fecha === fecha)?.prob ?? r.prob;
    const j = await api('/api/proyectos_activos', { method: 'POST', body: { codigo: f.get('codigo'), cliente: f.get('cliente'), nombre: f.get('nombre'), cotizacion: s,
      fecha_comprometida: fecha, alpha: r.alpha, prob_cumplir: prob, programa: r.programa, hh_p50: r.hh.map(h => h.p50) } });
    S.cat = await api('/api/catalogos'); toast('Proyecto creado'); location.hash = '#/proyecto/a/' + j.id;
  }, 'Crear proyecto');
}

/* =====================================================================  PLANTA (registro prospectivo) */
async function vPlanta(qs) {
  const m = shell('planta', `${ic('planta', 20)} Registro de planta`);
  const pSel = new URLSearchParams(qs).get('p');
  const [tar, par] = await Promise.all([api('/api/tareo'), api('/api/paradas')]);
  const opProy = S.cat.proyectos.map(p => `<option value="${p.id}" ${String(p.id) === pSel ? 'selected' : ''}>${esc(p.codigo)} · ${esc(p.nombre)}</option>`).join('');
  m.innerHTML = `
  <div class="aviso" style="background:var(--celeste-cl);border-color:var(--celeste-med);color:var(--azul-osc)">${ic('chispa', 16)} Este registro diario es lo que convierte el análisis en prospectivo: alimenta el avance real, la disponibilidad de las 4 máquinas y el re-entrenamiento del modelo.</div>
  <div class="pestanas"><button class="activo" data-t="tareo">Tareo diario (HH)</button><button data-t="paradas">Paradas de máquina</button></div>
  <div id="ptareo" class="grid cotz">
    <form class="tarjeta" id="ftar"><h3>Nuevo tareo</h3><div class="cuerpo form">
      <label>Fecha<input name="fecha" type="date" value="${hoyISO()}" max="${hoyISO()}" required></label>
      <label class="ancho">Proyecto<select name="proyecto_id" required>${opProy}</select></label>
      <label class="ancho">Proceso<select name="proceso">${S.cat.procesos.map(p => `<option value="${p.id}">${p.id}. ${esc(p.nombre)}</option>`).join('')}</select></label>
      <label class="ancho">Contratista / cuadrilla<select name="contratista"><option value="">Personal propio</option>${S.cat.contratistas.map(c => `<option>${esc(c)}</option>`).join('')}</select></label>
      <label>Personas<input name="n_personas" type="number" min="1" max="60" value="4" required></label>
      <label>Horas por persona<input name="horas_persona" type="number" step="0.5" min="0.5" max="12" value="8" required></label>
      <label>Kg avanzados<input name="kg_avanzados" type="number" step="1" min="0"></label>
      <label class="ancho">Observación<textarea name="observacion" rows="2" placeholder="Falta de material, retrabajo, lluvia..."></textarea></label>
      <button class="btn prim ancho" style="justify-content:center">${ic('check', 16)} Registrar tareo</button></div></form>
    <div class="tarjeta"><h3>Últimos registros</h3><div class="cuerpo scroll"><table class="tabla"><tr><th>Fecha</th><th>OT</th><th>Proceso</th><th>Cuadrilla</th><th class="num">HH</th><th>Registró</th></tr>
      ${tar.map(t => `<tr><td>${fmtCorta(t.fecha)}</td><td>${esc(t.codigo)}</td><td>${esc(S.cat.procesos[t.proceso - 1].nombre)}</td><td class="nota">${esc(t.contratista || 'Propio')}</td><td class="num">${t.n_personas} × ${t.horas_persona} = <b>${fmtNum(t.hh)}</b></td><td class="nota">${esc(t.usuario || '')}</td></tr>`).join('') || '<tr><td colspan="6" class="vacio">Sin registros</td></tr>'}</table></div></div>
  </div>
  <div id="pparadas" class="grid cotz oculto">
    <form class="tarjeta" id="fpar"><h3>Nueva parada</h3><div class="cuerpo form">
      <label class="ancho">Máquina<select name="maquina">${S.cat.maquinas.map(x => `<option>${esc(x)}</option>`).join('')}</select></label>
      <label>Inicio<input name="inicio" type="datetime-local" required></label><label>Fin<input name="fin" type="datetime-local" required></label>
      <label class="ancho">Causa<select name="causa">${S.cat.causas.map(x => `<option>${esc(x)}</option>`).join('')}</select></label>
      <label class="chk ancho"><input type="checkbox" name="planificada"> Fue planificada (mantenimiento preventivo, setup programado)</label>
      <label class="ancho">Proyecto afectado<select name="proyecto_id"><option value="">—</option>${opProy}</select></label>
      <label class="ancho">Observación<textarea name="observacion" rows="2"></textarea></label>
      <button class="btn prim ancho" style="justify-content:center">${ic('check', 16)} Registrar parada</button></div></form>
    <div class="tarjeta"><h3>Paradas registradas</h3><div class="cuerpo scroll"><table class="tabla"><tr><th>Máquina</th><th>Inicio</th><th class="num">Horas</th><th>Causa</th><th>Tipo</th><th>Registró</th></tr>
      ${par.map(p => `<tr><td>${esc(p.maquina)}</td><td>${esc(String(p.inicio).replace('T', ' '))}</td><td class="num">${p.horas}</td><td>${esc(p.causa)}</td><td>${p.planificada ? '<span class="badge b-az">Planificada</span>' : '<span class="badge b-roj">Falla</span>'}</td><td class="nota">${esc(p.usuario || '')}</td></tr>`).join('') || '<tr><td colspan="6" class="vacio">Sin paradas</td></tr>'}</table></div></div>
  </div>`;
  $$('.pestanas button').forEach(b => b.onclick = () => { $$('.pestanas button').forEach(x => x.classList.toggle('activo', x === b)); $('#ptareo').classList.toggle('oculto', b.dataset.t !== 'tareo'); $('#pparadas').classList.toggle('oculto', b.dataset.t !== 'paradas'); });
  $('#ftar').onsubmit = async e => { e.preventDefault(); const f = new FormData(e.target);
    try { await api('/api/tareo', { method: 'POST', body: { fecha: f.get('fecha'), proyecto_id: +f.get('proyecto_id'), proceso: +f.get('proceso'), contratista: f.get('contratista') || null,
      n_personas: +f.get('n_personas'), horas_persona: +f.get('horas_persona'), kg_avanzados: f.get('kg_avanzados') ? +f.get('kg_avanzados') : null, observacion: f.get('observacion') || null } });
      toast('Tareo registrado'); vPlanta(qs); } catch (err) { toast(err.message, 1); } };
  $('#fpar').onsubmit = async e => { e.preventDefault(); const f = new FormData(e.target);
    try { await api('/api/paradas', { method: 'POST', body: { maquina: f.get('maquina'), inicio: f.get('inicio').replace('T', ' '), fin: f.get('fin').replace('T', ' '),
      planificada: !!f.get('planificada'), causa: f.get('causa'), proyecto_id: f.get('proyecto_id') ? +f.get('proyecto_id') : null, observacion: f.get('observacion') || null } });
      toast('Parada registrada'); vPlanta(qs); } catch (err) { toast(err.message, 1); } };
}

/* =====================================================================  TAREAS (estilo Linear) */
async function vTareas(qs) {
  const pSel = new URLSearchParams(qs).get('p') || '';
  const m = shell('tareas', `${ic('tareas', 20)} Tareas del equipo`,
    `<select id="fproy"><option value="">Todos los proyectos</option>${S.cat.proyectos.map(p => `<option value="${p.id}" ${String(p.id) === pSel ? 'selected' : ''}>${esc(p.codigo)}</option>`).join('')}</select>
     <select id="fresp"><option value="">Todos los responsables</option><option value="${S.me.id}">Mis tareas</option>${S.cat.usuarios.map(u => `<option value="${u.id}">${esc(u.nombre)}</option>`).join('')}</select>
     <button class="btn prim" id="bnueva">${ic('mas', 16)} Nueva tarea</button>`);
  const cargar = async () => {
    const ts = await api('/api/tareas' + ($('#fproy').value ? '?proyecto_id=' + $('#fproy').value : ''));
    const fr = $('#fresp').value;
    const vis = ts.filter(t => !fr || String(t.responsable_id) === fr);
    m.innerHTML = `<div class="kanban">${ESTADOS.map(([k, n, c]) => { const col = vis.filter(t => t.estado === k); return `
      <div class="col" data-e="${k}"><h4><i style="width:10px;height:10px;border-radius:50%;background:${c};display:inline-block"></i>${n}<span class="n">${col.length}</span></h4>
      ${col.map(t => `<div class="ficha p${t.prioridad}" draggable="true" data-id="${t.id}"><div class="id">STL-${t.id}${t.proyecto ? ' · ' + esc(t.proyecto) : ''}</div>
        <div class="tit">${esc(t.titulo)}</div><div class="pie"><span class="badge ${TIPOS_T[t.tipo][1]}">${TIPOS_T[t.tipo][0]}</span>
        <span class="prio" style="color:${PRIO[t.prioridad][1]}">● ${PRIO[t.prioridad][0]}</span>${t.fecha_limite ? `<span>${ic('reloj', 13)} ${fmtCorta(t.fecha_limite)}</span>` : ''}
        ${t.n_comentarios ? `<span>${ic('comentario', 13)} ${t.n_comentarios}</span>` : ''}<span style="flex:1"></span>${t.responsable ? avatar(t.responsable, t.color, 1) : ''}</div></div>`).join('')}
      </div>`; }).join('')}</div><p class="nota">Arrastra las fichas entre columnas. Clic para ver detalle y comentarios.</p>`;
    $$('.ficha', m).forEach(f => { f.ondragstart = e => e.dataTransfer.setData('text/plain', f.dataset.id); f.onclick = () => panelTarea(+f.dataset.id, ts, cargar); });
    $$('.col', m).forEach(c => {
      c.ondragover = e => { e.preventDefault(); c.classList.add('sobre'); };
      c.ondragleave = () => c.classList.remove('sobre');
      c.ondrop = async e => { e.preventDefault(); c.classList.remove('sobre'); const id = e.dataTransfer.getData('text/plain');
        try { await api('/api/tareas/' + id, { method: 'PATCH', body: { estado: c.dataset.e } }); cargar(); } catch (err) { toast(err.message, 1); } };
    });
  };
  $('#fproy').onchange = cargar; $('#fresp').onchange = cargar;
  $('#bnueva').onclick = () => modal('Nueva tarea', `<div class="form">
      <label class="ancho">Título<input name="titulo" required minlength="3"></label>
      <label>Tipo<select name="tipo">${Object.entries(TIPOS_T).map(([k, v]) => `<option value="${k}">${v[0]}</option>`).join('')}</select></label>
      <label>Prioridad<select name="prioridad">${Object.entries(PRIO).map(([k, v]) => `<option value="${k}" ${k === '3' ? 'selected' : ''}>${v[0]}</option>`).join('')}</select></label>
      <label>Proyecto<select name="proyecto_id"><option value="">—</option>${S.cat.proyectos.map(p => `<option value="${p.id}" ${String(p.id) === $('#fproy').value ? 'selected' : ''}>${esc(p.codigo)}</option>`).join('')}</select></label>
      <label>Proceso<select name="proceso"><option value="">—</option>${S.cat.procesos.map(p => `<option value="${p.id}">${esc(p.nombre)}</option>`).join('')}</select></label>
      <label>Responsable<select name="responsable_id"><option value="">Sin asignar</option>${S.cat.usuarios.map(u => `<option value="${u.id}">${esc(u.nombre)}</option>`).join('')}</select></label>
      <label>Fecha límite<input name="fecha_limite" type="date"></label>
      <details class="ancho"><summary class="nota" style="cursor:pointer">Si es RFI, no conformidad, bloqueo o cambio de alcance</summary><div class="form" style="margin-top:10px">${camposIncidencia()}</div></details>
      <label class="ancho">Descripción<textarea name="descripcion" rows="3"></textarea></label></div>`,
  async f => { await api('/api/tareas', { method: 'POST', body: { titulo: f.get('titulo'), tipo: f.get('tipo'), prioridad: +f.get('prioridad'), proyecto_id: f.get('proyecto_id') ? +f.get('proyecto_id') : null,
    proceso: f.get('proceso') ? +f.get('proceso') : null, responsable_id: f.get('responsable_id') ? +f.get('responsable_id') : null, fecha_limite: f.get('fecha_limite') || null, descripcion: f.get('descripcion') || null, ...leerIncidencia(f) } });
    toast('Tarea creada'); cargar(); }, 'Crear tarea');
  await cargar();
  const tAbrir = new URLSearchParams(qs).get('t');
  if (tAbrir) { const ts = await api('/api/tareas'); if (ts.find(x => x.id === +tAbrir)) panelTarea(+tAbrir, ts, cargar); }
}

async function panelTarea(id, ts, recargar) {
  const t = ts.find(x => x.id === id);
  const v = document.createElement('div'); v.className = 'velo';
  const p = document.createElement('aside'); p.className = 'lateral';
  const pintar = async () => {
    const cs = await api(`/api/tareas/${id}/comentarios`);
    p.innerHTML = `<header><div><div class="nota">STL-${t.id}${t.proyecto ? ' · ' + esc(t.proyecto) : ''}</div><b style="font-size:16px">${esc(t.titulo)}</b></div><button class="btn peq" id="pcerrar">${ic('cerrar', 16)}</button></header>
    <div class="cuerpo"><div class="form">
      <label>Estado<select id="pe">${ESTADOS.map(([k, n]) => `<option value="${k}" ${k === t.estado ? 'selected' : ''}>${n}</option>`).join('')}</select></label>
      <label>Prioridad<select id="pp">${Object.entries(PRIO).map(([k, x]) => `<option value="${k}" ${+k === t.prioridad ? 'selected' : ''}>${x[0]}</option>`).join('')}</select></label>
      <label>Responsable<select id="pr"><option value="">Sin asignar</option>${S.cat.usuarios.map(u => `<option value="${u.id}" ${u.id === t.responsable_id ? 'selected' : ''}>${esc(u.nombre)}</option>`).join('')}</select></label>
      <label>Fecha límite<input id="pf" type="date" value="${t.fecha_limite || ''}"></label></div>
      <div><span class="badge ${TIPOS_T[t.tipo][1]}">${TIPOS_T[t.tipo][0]}</span> ${t.proceso ? `<span class="badge b-gris">${esc(S.cat.procesos[t.proceso - 1].nombre)}</span>` : ''}${t.fecha_cierre ? ` <span class="badge b-ver">cerrada ${fmtCorta(t.fecha_cierre)}</span>` : ''}</div>
      ${TIPOS_BANDEJA.includes(t.tipo) ? `<form class="form" id="finc">${camposIncidencia(t)}</form>` : ''}
      ${t.descripcion ? `<p>${esc(t.descripcion)}</p>` : ''}
      <h4 style="margin:6px 0 0">Comentarios</h4>
      ${cs.map(c => `<div class="comentario">${avatar(c.nombre, c.color, 1)}<div class="burbuja"><small>${esc(c.nombre)} · ${esc(String(c.creado_en).slice(0, 16))}</small><div>${esc(c.texto)}</div></div></div>`).join('') || '<p class="nota">Sin comentarios</p>'}
      <form id="fcom" style="display:grid;gap:8px"><textarea name="texto" rows="3" placeholder="Escribe un comentario para el equipo..." required></textarea><button class="btn prim">${ic('comentario', 15)} Comentar</button></form></div>`;
    $('#pcerrar', p).onclick = cerrar;
    const cambiar = async body => { try { await api('/api/tareas/' + id, { method: 'PATCH', body }); Object.assign(t, body); toast('Tarea actualizada'); } catch (e) { toast(e.message, 1); } };
    $('#pe', p).onchange = e => cambiar({ estado: e.target.value });
    $('#pp', p).onchange = e => cambiar({ prioridad: +e.target.value });
    $('#pr', p).onchange = e => e.target.value && cambiar({ responsable_id: +e.target.value });
    $('#pf', p).onchange = e => e.target.value && cambiar({ fecha_limite: e.target.value });
    if ($('#finc', p)) $('#finc', p).onchange = () => { const x = leerIncidencia(new FormData($('#finc', p))); const b = Object.fromEntries(Object.entries(x).filter(([, v]) => v != null)); if (Object.keys(b).length) cambiar(b); };
    $('#fcom', p).onsubmit = async e => { e.preventDefault(); const tx = new FormData(e.target).get('texto'); await api(`/api/tareas/${id}/comentarios`, { method: 'POST', body: { texto: tx } }); pintar(); };
  };
  const cerrar = () => { v.remove(); p.remove(); recargar(); };
  v.onclick = cerrar;
  document.body.append(v, p);
  pintar();
}

/* =====================================================================  BANDEJA RFI / NC */
const TIPOS_BANDEJA = ['RFI', 'NO_CONFORMIDAD', 'CAMBIO_ALCANCE', 'BLOQUEO'];
const camposIncidencia = (t = {}) => `
  <label>Imputable a<select name="imputable"><option value="">—</option>${S.cat.imputable.map(x => `<option ${x === t.imputable ? 'selected' : ''}>${esc(x)}</option>`).join('')}</select></label>
  <label>Días de impacto en el plazo<input name="dias_impacto" type="number" min="0" step="0.5" value="${t.dias_impacto ?? ''}"></label>
  <label class="ancho">Marca de la pieza afectada<input name="conjunto" placeholder="V-3, T-1..." value="${esc(t.conjunto || '')}"></label>`;
const leerIncidencia = f => ({ imputable: f.get('imputable') || null, dias_impacto: f.get('dias_impacto') ? +f.get('dias_impacto') : null, conjunto: f.get('conjunto') || null });

async function vBandeja() {
  const m = shell('bandeja', `${ic('bandeja', 20)} RFI, no conformidades y bloqueos`,
    `<select id="bfiltro"><option value="abiertas">Abiertas</option><option value="vencidas">Vencidas</option><option value="todas">Todas</option></select>
     <select id="btipo"><option value="">Todos los tipos</option>${TIPOS_BANDEJA.map(t => `<option value="${t}">${TIPOS_T[t][0]}</option>`).join('')}</select>
     <button class="btn prim" id="bnueva">${ic('mas', 16)} Registrar</button>`);
  const d = await api('/api/bandeja');
  const r = d.resumen;
  m.innerHTML = `
  <div class="kpis">${kpi('Abiertas', r.abiertas, TIPOS_BANDEJA.map(t => `${r.por_tipo[t]} ${TIPOS_T[t][0].toLowerCase()}`).join(' · '), 'nar', 'bandeja')}
    ${kpi('Vencidas', r.vencidas, 'pasaron su fecha límite', r.vencidas ? 'roj' : 'ver', 'alerta')}
    ${kpi('Días promedio para cerrar', r.dias_cierre ?? '—', 'de las ya cerradas', '', 'reloj')}
    ${kpi('Días imputables al cliente', fmtNum(r.dias_cliente, 1), `Steelser: ${fmtNum(r.dias_steelser, 1)} días · sustentan ampliaciones`, 'mor', 'check')}</div>
  <div class="tarjeta"><div class="cuerpo scroll" id="lband" style="max-height:640px"></div>
    <p class="nota" style="padding:0 16px 14px">Los días imputables al cliente (RFI sin respuesta, cambios de alcance) justifican pedir ampliación de plazo; los imputables a Steelser son incumplimiento propio. Esta separación es la que falta en el histórico.</p></div>`;
  const pintar = () => {
    const f = $('#bfiltro').value, tp = $('#btipo').value;
    const fs = d.filas.filter(x => (f === 'todas' || (f === 'abiertas' && x.estado !== 'HECHO') || (f === 'vencidas' && x.vencida)) && (!tp || x.tipo === tp));
    $('#lband').innerHTML = fs.length ? `<table class="tabla"><tr><th>ID</th><th>Tipo</th><th>Título</th><th>OT</th><th>Pieza</th><th>Estado</th><th>Responsable</th><th>Límite</th><th class="num">Días abierta</th><th>Imputable</th><th class="num">Días impacto</th></tr>
      ${fs.map(x => `<tr class="clic" data-id="${x.id}"><td class="nota">STL-${x.id}</td><td><span class="badge ${TIPOS_T[x.tipo][1]}">${TIPOS_T[x.tipo][0]}</span></td><td><b>${esc(x.titulo)}</b>${x.n_comentarios ? ` <span class="nota">${ic('comentario', 12)} ${x.n_comentarios}</span>` : ''}</td>
        <td>${esc(x.proyecto || '—')}</td><td>${esc(x.conjunto || '')}</td><td>${esc((ESTADOS.find(e => e[0] === x.estado) || [, x.estado])[1])}</td><td>${x.responsable ? avatar(x.responsable, x.color, 1) + ' ' + esc(x.responsable) : '<span class="nota">sin asignar</span>'}</td>
        <td>${x.vencida ? `<span class="badge b-roj">${fmtCorta(x.fecha_limite)}</span>` : fmtCorta(x.fecha_limite)}</td><td class="num">${x.dias_abierta ?? '—'}</td>
        <td>${x.imputable ? `<span class="badge ${x.imputable === 'Cliente' ? 'b-mor' : x.imputable === 'Steelser' ? 'b-roj' : 'b-gris'}">${esc(x.imputable)}</span>` : '<span class="nota">por definir</span>'}</td><td class="num">${x.dias_impacto ?? '—'}</td></tr>`).join('')}</table>`
      : '<div class="vacio">Nada pendiente con este filtro</div>';
    $$('#lband tr[data-id]').forEach(tr => tr.onclick = () => panelTarea(+tr.dataset.id, d.filas, vBandeja));
  };
  $('#bfiltro').onchange = pintar; $('#btipo').onchange = pintar;
  $('#bnueva').onclick = () => modal('Registrar RFI, no conformidad o bloqueo', `<div class="form">
      <label>Tipo<select name="tipo">${TIPOS_BANDEJA.map(t => `<option value="${t}">${TIPOS_T[t][0]}</option>`).join('')}</select></label>
      <label>Prioridad<select name="prioridad">${Object.entries(PRIO).map(([k, v]) => `<option value="${k}" ${k === '2' ? 'selected' : ''}>${v[0]}</option>`).join('')}</select></label>
      <label class="ancho">Título<input name="titulo" required minlength="3"></label>
      <label>Proyecto<select name="proyecto_id"><option value="">—</option>${S.cat.proyectos.map(p => `<option value="${p.id}">${esc(p.codigo)}</option>`).join('')}</select></label>
      <label>Responsable<select name="responsable_id"><option value="">Sin asignar</option>${S.cat.usuarios.map(u => `<option value="${u.id}">${esc(u.nombre)}</option>`).join('')}</select></label>
      <label>Fecha límite de respuesta<input name="fecha_limite" type="date"></label>
      ${camposIncidencia()}
      <label class="ancho">Descripción<textarea name="descripcion" rows="3"></textarea></label></div>`,
  async f => { await api('/api/tareas', { method: 'POST', body: { titulo: f.get('titulo'), tipo: f.get('tipo'), prioridad: +f.get('prioridad'), proyecto_id: f.get('proyecto_id') ? +f.get('proyecto_id') : null,
    responsable_id: f.get('responsable_id') ? +f.get('responsable_id') : null, fecha_limite: f.get('fecha_limite') || null, descripcion: f.get('descripcion') || null, ...leerIncidencia(f) } });
    toast('Registrado'); vBandeja(); }, 'Registrar');
  pintar();
}

/* =====================================================================  REPORTE SEMANAL (imprimible → PDF) */
async function vReporte(id, qs = '') {
  const sem = new URLSearchParams(qs).get('semana') || '';
  const m = shell('proyectos', `<a href="#/proyectos">Proyectos</a><span class="sep">/</span><a href="#/proyecto/a/${id}">Proyecto</a><span class="sep">/</span>Reporte semanal`,
    `<select id="rsem"></select><button class="btn prim" id="bimp">${ic('imprimir', 16)} Imprimir / guardar PDF</button>`);
  const d = await api(`/api/proyectos_activos/${id}/reporte${sem ? '?semana=' + sem : ''}`);
  const p = d.proyecto, f = d.fila || {}, pr = d.pronostico;
  $('#rsem').innerHTML = d.semanas.filter(s => s.inicio <= hoyISO()).map(s => `<option value="${s.inicio}" ${s.inicio === d.semana.inicio ? 'selected' : ''}>Semana ${s.n} · ${fmtCorta(s.inicio)}</option>`).join('')
    || `<option>${fmtCorta(d.semana.inicio)}</option>`;
  $('#rsem').onchange = e => location.hash = `#/reporte/${id}?semana=${e.target.value}`;
  $('#bimp').onclick = () => window.print();
  const tabla = (cab, filas, vacio) => filas.length ? `<table class="tabla"><tr>${cab.map(c => `<th>${c}</th>`).join('')}</tr>${filas.join('')}</table>` : `<p class="nota">${vacio}</p>`;
  const sem_ = { VERDE: 'En camino', AMBAR: 'En riesgo', ROJO: 'Atraso probable' };
  m.innerHTML = `<article class="reporte">
  <header class="rcab"><div class="marca"><span class="logo">${ic('viga', 18)}</span>SteelPlan <small>· Steelser S.A.C.</small></div>
    <div><h1>Actualización semanal · ${esc(p.codigo)}</h1><div>${esc(p.nombre)} · ${esc(p.cliente || '')} · ${fmtNum(p.ton)} t</div>
    <div class="nota">Semana ${d.semana.n ?? '—'} de producción · del ${fmtFecha(d.semana.inicio)} al ${fmtFecha(d.semana.fin)} · emitido ${esc(d.generado)} por ${esc(d.generado_por)}</div></div></header>
  ${p.es_demo ? `<div class="aviso">${ic('alerta', 16)} Proyecto de DEMOSTRACIÓN.</div>` : ''}
  <div class="kpis">
    ${kpi('Entrega comprometida', fmtCorta(p.fecha_comprometida), pr ? `P(cumplir) ${pct(pr.prob_cumplir)} al ${fmtCorta(pr.fecha)}` : 'sin re-pronóstico', pr ? { VERDE: 'ver', AMBAR: 'nar', ROJO: 'roj' }[pr.semaforo] : '', 'reloj')}
    ${kpi('Avance físico', d.avance_fisico != null ? d.avance_fisico + ' %' : '—', d.avance_fisico != null ? 'kg ponderados por etapa' : 'sin piezas importadas', 'nar', 'viga')}
    ${kpi('Avance por HH', d.avance_hh + ' %', 'contra HH P50 cotizadas', '', 'reloj')}
    ${kpi('Índice de avance', f.spi_kg ?? f.spi_hh ?? '—', f.spi_kg != null ? `kg · HH ${f.spi_hh ?? '—'}` : 'por HH', (f.spi_kg ?? f.spi_hh ?? 1) >= 1 ? 'ver' : 'roj', 'curva')}</div>
  ${pr ? `<div class="semaforo ${pr.semaforo}" style="margin-bottom:14px"><span class="luz"></span><div><b>${sem_[pr.semaforo]}</b> · último re-pronóstico (${fmtCorta(pr.fecha)}): fin probable ${fmtFecha(pr.p50)}, con 80 % ${fmtFecha(pr.p80)}; penalidad esperada USD ${fmtNum(pr.penalidad)}.</div></div>` : ''}
  <div class="grid g2">
    <section class="tarjeta"><h3>1. Logrado esta semana</h3><div class="cuerpo">
      ${tabla(['Etapa', 'Piezas', 'kg', 'Marcas'], d.logros.map(l => `<tr><td>${esc(l.etapa)}</td><td class="num">${l.piezas}</td><td class="num">${fmtNum(l.kg)}</td><td class="nota">${l.marcas.map(esc).join(', ')}</td></tr>`), 'Sin etapas de pieza completadas en la semana.')}
      <p class="nota">kg = peso de las piezas que completaron la etapa. Avance ponderado de la semana (peso × peso de etapa): plan ${fmtNum(f.plan_kg)} kg, real ${fmtNum(f.real_kg)} kg · HH: plan ${fmtNum(f.plan_hh)}, real ${fmtNum(f.real_hh)}${f.en_curso ? ` (al ${fmtCorta(f.al)})` : ''}.</p></div></section>
    <section class="tarjeta"><h3>2. Horas-hombre por proceso</h3><div class="cuerpo">
      ${tabla(['Proceso', 'Días', 'Personas prom.', 'HH'], d.hh_semana.map(h => `<tr><td>${esc(h.proceso)}</td><td class="num">${h.dias}</td><td class="num">${h.personas}</td><td class="num">${fmtNum(h.hh)}</td></tr>`), 'Sin tareo registrado en la semana.')}</div></section>
    <section class="tarjeta"><h3>3. Plan de la próxima semana (P50)</h3><div class="cuerpo">
      ${tabla(['Proceso', 'Desde', 'Hasta', 'HH P50'], d.proxima.map(x => `<tr><td>${esc(x.proceso)}</td><td>${fmtCorta(x.inicio)}</td><td>${fmtCorta(x.fin)}</td><td class="num">${fmtNum(x.hh_p50)}</td></tr>`), 'El plan no tiene procesos activos la próxima semana.')}</div></section>
    <section class="tarjeta"><h3>4. RFI, no conformidades y bloqueos abiertos</h3><div class="cuerpo">
      ${tabla(['Incidencia', 'Responsable', 'Límite', 'Imputable'], d.incidencias.map(x => `<tr><td><span class="badge ${TIPOS_T[x.tipo][1]}">${TIPOS_T[x.tipo][0]}</span> ${esc(x.titulo)} <span class="nota">STL-${x.id}</span></td><td>${esc(x.responsable || '—')}</td><td>${fmtCorta(x.fecha_limite)}</td><td>${esc(x.imputable || '—')}</td></tr>`), 'Ninguno abierto.')}</div></section>
    <section class="tarjeta"><h3>5. Material y servicios pendientes</h3><div class="cuerpo">
      ${tabla(['OC', 'Material', 'kg', 'Prometida'], d.compras_pendientes.map(c => `<tr><td>${esc(c.n_oc)}</td><td>${esc(c.material)}</td><td class="num">${fmtNum(c.kg)}</td><td>${c.fecha_prometida && c.fecha_prometida < hoyISO() ? `<span class="badge b-roj">${fmtCorta(c.fecha_prometida)}</span>` : fmtCorta(c.fecha_prometida)}</td></tr>`), 'Sin compras pendientes.')}
      ${d.servicios_en_proveedor.length ? `<p class="nota" style="margin-top:8px">En proveedor: ${d.servicios_en_proveedor.map(s => `${esc(s.servicio)} (${esc(s.proveedor || '')}, desde ${fmtCorta(s.fecha_envio)})`).join('; ')}</p>` : ''}</div></section>
    <section class="tarjeta"><h3>6. Eventos y paradas de la semana</h3><div class="cuerpo">
      ${tabla(['Evento', 'Imputable', 'Días'], d.eventos.map(e => `<tr><td>${esc(e.tipo)}: ${esc(e.descripcion || '')}</td><td>${esc(e.imputable || '—')}</td><td class="num">${e.dias_impacto ?? '—'}</td></tr>`), 'Sin eventos.')}
      ${tabla(['Máquina', 'Causa', 'Horas'], d.paradas.map(x => `<tr><td>${esc(x.maquina)}</td><td>${esc(x.causa)}${x.planificada ? ' (planificada)' : ''}</td><td class="num">${x.horas}</td></tr>`), 'Sin paradas de máquina.')}</div></section>
  </div>
  <section class="tarjeta" style="margin-top:16px"><h3>Avance acumulado por semana</h3><div class="cuerpo"><div class="grafico bajo" id="grep"></div></div></section>
  <p class="nota">El modelo de horas usa datos simulados hasta cargar tareos reales. Plan = programa P50 de la cotización; real = fechas de etapa por pieza y tareo registrados en SteelPlan.</p>
  </article>`;
  const s = d.semanas;
  chart($('#grep'), { animation: false, grid: { left: 60, right: 20, top: 20, bottom: 40 }, legend: { bottom: 0 }, tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: s.map(x => 'S' + x.n) }, yAxis: { type: 'value', name: d.avance_fisico != null ? 'kg' : 'HH' },
    series: d.avance_fisico != null
      ? [{ name: 'Plan kg', type: 'line', data: s.map(x => x.plan_kg_acum), itemStyle: { color: '#5b738b' }, lineStyle: { type: 'dashed', color: '#5b738b' } },
        { name: 'Real kg', type: 'line', data: s.map(x => x.real_kg_acum), itemStyle: { color: '#0a6ed1' }, lineStyle: { width: 3, color: '#0a6ed1' } }]
      : [{ name: 'Plan HH', type: 'line', data: s.map(x => x.plan_hh_acum), itemStyle: { color: '#5b738b' }, lineStyle: { type: 'dashed', color: '#5b738b' } },
        { name: 'Real HH', type: 'line', data: s.map(x => x.real_hh_acum), itemStyle: { color: '#0a6ed1' }, lineStyle: { width: 3, color: '#0a6ed1' } }] });
}

/* =====================================================================  USUARIOS */
async function vUsuarios() {
  const m = shell('usuarios', `${ic('usuarios', 20)} Usuarios y roles`, `<button class="btn prim" id="bnu">${ic('mas', 16)} Nuevo usuario</button>`);
  const us = await api('/api/usuarios');
  m.innerHTML = `<div class="tarjeta"><div class="cuerpo"><table class="tabla"><tr><th></th><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Área</th><th>Estado</th><th>Creado</th></tr>
    ${us.map(u => `<tr><td>${avatar(u.nombre, u.color)}</td><td><b>${esc(u.usuario)}</b></td><td>${esc(u.nombre)}</td><td>${esc(S.cat.roles[u.rol])}</td><td>${esc(u.area || '')}</td>
    <td>${u.activo ? '<span class="badge b-ver">Activo</span>' : '<span class="badge b-gris">Inactivo</span>'}</td><td class="nota">${esc(String(u.creado_en).slice(0, 10))}</td></tr>`).join('')}</table></div></div>`;
  $('#bnu').onclick = () => modal('Nuevo usuario', `<div class="form">
    <label>Usuario<input name="usuario" required pattern="[a-z0-9._-]{3,30}" placeholder="jperez"></label><label>Nombre<input name="nombre" required></label>
    <label>Rol<select name="rol">${Object.entries(S.cat.roles).map(([k, v]) => `<option value="${k}">${esc(v)}</option>`).join('')}</select></label>
    <label>Área<input name="area"></label><label class="ancho">Clave inicial (mín. 8 caracteres)<input name="clave" type="password" minlength="8" required autocomplete="new-password"></label></div>`,
  async f => { await api('/api/usuarios', { method: 'POST', body: Object.fromEntries(f) }); toast('Usuario creado'); vUsuarios(); }, 'Crear usuario');
}

/* =====================================================================  GEMELO 3D DE LA PLANTA (datos SIMULADOS) */
const P3 = { escena: null, timer: null, charts: [] };
function limpiarP3() { if (P3.timer) { clearInterval(P3.timer); P3.timer = null; } if (P3.escena) { P3.escena.destruir(); P3.escena = null; } P3.charts.forEach(c => c.dispose()); P3.charts = []; }
const EP = Date.UTC(2019, 0, 1);
const fT = t => new Date(EP + t * 3600e3);
const horaTxt = t => { const d = fT(t); return `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()} ${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`; };
const tDeFecha = (iso, h = 7) => (Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) - EP) / 3600e3 + h;
const ETAPAS_G = [['HABILITADO', 'Habilitado', ['HABILITADO']], ['DOBLEZ', 'Doblez', ['DOBLEZ']], ['ARMADO', 'Armado', ['ARMADO']], ['SOLDEO', 'Soldeo', ['SOLDEO', 'RETRABAJO']], ['LIMPIEZA', 'Limpieza', ['LIMPIEZA']], ['PINTURA', 'Pintura', ['LISTO_PINTURA', 'PINTURA', 'PINTADO']], ['ENTREGADO', 'Entregado', ['ENTREGADO']]];
const NOM_POL = { A0: 'Como se hizo', B1: 'Regla del jefe de taller', C1: 'Colchón fijo', D0: 'Monitoreo', D1: 'DSS fecha α = 0.80', D2: 'DSS fecha α*', D3: 'DSS gestión', D4: 'DSS sistema completo' };

async function vPlanta3D() {
  const m = shell('planta3d', `${ic('planta3d', 20)} Gemelo 3D de la planta <span class="badge b-nar" style="font-size:12px">datos simulados · eventos discretos hora a hora</span>`);
  const meta = await api('/api/gemelo/meta').catch(e => { m.innerHTML = `<div class="tarjeta"><div class="cuerpo vacio">${ic('alerta', 30)}<p>${esc(e.message)}</p><p class="nota">Ejecute <code>py scripts/exp6_gemelo.py</code> para crear el gemelo.</p></div></div>`; return null; });
  if (!meta) return;
  const proy = meta.proyectos, pols = meta.politicas;
  const res = (pol, pid) => meta.resultados.find(r => r.politica.startsWith(pol) && r.pid === pid);
  const atraso = p => { const r = res('A0', p.pid); return r ? r.tarde : 0; };
  const inicial = proy.filter(p => p.en_muestra).sort((a, b) => atraso(b) - atraso(a))[0] || proy[0];
  const st = { pid: inicial.pid, pol: pols[0], t: 0, estado: null, sel: null, pestana: 'objeto', play: false, vel: 3, pedido: 0 };
  const P = () => proy.find(x => x.pid === st.pid);
  const nombrePol = k => NOM_POL[k.slice(0, 2)] || k;
  m.innerHTML = `
  <div class="p3d">
    <div class="p3d-izq">
      <div class="p3d-lienzo" id="p3l"></div>
      <div class="p3d-kpis" id="p3k"></div>
      <select class="p3d-vistas" id="p3v" title="Ir a una zona de la planta"><option value="" disabled selected>Ir a…</option><option value="general">Vista general</option><option value="navea">Nave A · habilitado</option><option value="maquinas">Máquinas</option><option value="naveb">Nave B · armado y soldeo</option><option value="patio">Patio de acopio</option><option value="muelles">Muelles</option><option value="oficina">Oficinas</option></select>
      <div class="p3d-abajo"><div class="p3d-seguim" id="p3s"></div>
      <div class="p3d-ctl">
        <select id="p3pol" title="Política (cómo se gestionó)">${pols.map(k => `<option value="${k}">${k} · ${nombrePol(k)}</option>`).join('')}</select>
        <select id="p3p" title="Proyecto">${proy.map(x => `<option value="${x.pid}">${x.cod ? 'OT ' + x.cod : 'P' + x.pid} · ${x.ton.toFixed(0)} t · ${x.nombre.slice(0, 22)}${atraso(x) > 0 ? ' · +' + atraso(x) + ' d' : ''}</option>`).join('')}</select>
        <button class="btn peq" id="p3ant" title="−1 hora">‹</button><button class="btn peq prim" id="p3play" title="Reproducir">▶</button><button class="btn peq" id="p3sig" title="+1 hora">›</button>
        <input type="range" id="p3r" min="0" max="100" value="0" step="1">
        <b id="p3f" style="min-width:150px;text-align:right"></b>
        <select id="p3vel" title="Velocidad"><option value="1">1 h/s</option><option value="3" selected>3 h/s</option><option value="8">8 h/s</option><option value="24">1 día/s</option><option value="72">3 días/s</option></select>
        <label class="p3-chk"><input type="checkbox" id="p3t" checked> Techos</label><label class="p3-chk"><input type="checkbox" id="p3e" checked> Etiquetas</label><label class="p3-chk" title="Oculta paneles e indicadores; al hacer clic en un objeto vuelven"><input type="checkbox" id="p3lim"> Modo limpio</label>
      </div></div>
    </div>
    <aside class="p3d-der tarjeta">
      <div class="p3d-tabs"><button data-t="objeto" class="activo">Objeto</button><button data-t="proyecto">Proyecto</button><button data-t="resultados">Resultados</button></div>
      <div class="p3d-panel" id="p3panel"></div>
    </aside>
  </div>`;
  try {
    P3.escena = (await import('/static/gemelo3d.js?v=1')).crearGemelo($('#p3l'), meta, { alSeleccionar: (ref, obj) => { st.sel = ref; st.obj = obj; st.pestana = 'objeto'; if (ref && $('#p3lim').checked) { $('#p3lim').checked = false; $('.p3d').classList.remove('limpio'); } pestanas(); panel(); } });
  } catch (e) { $('#p3l').innerHTML = `<div class="vacio" style="padding:40px">${ic('alerta', 30)}<p>No se pudo iniciar la escena 3D: ${esc(e.message)}</p></div>`; return; }
  const pestanas = () => $$('.p3d-tabs button').forEach(b => b.classList.toggle('activo', b.dataset.t === st.pestana));

  /* ----- tiempo y estado ----- */
  const rango = () => { const p = P(), r = res(st.pol, p.pid) || res('A0', p.pid); return [tDeFecha(p.ini, 0) - 24, tDeFecha(r ? r.fin : p.fr, 24) + 48]; };
  const ajustarSlider = () => { const [a, b] = rango(); const r = $('#p3r'); r.min = a; r.max = b; r.step = 1; };
  async function cargar(t) {
    st.t = t; const n = ++st.pedido; $('#p3r').value = t; $('#p3f').textContent = horaTxt(t); P3.escena && P3.escena.setT(t);
    const e = await api(`/api/gemelo/estado?t=${t}&politica=${st.pol}`); if (n !== st.pedido) return;
    st.estado = e; P3.escena.actualizar(e, { pid: st.pid }); kpis(); seguimiento(); if (st.pestana === 'objeto') panel();
  }
  const turno = h => h >= 7 && h < 15 ? 'Turno normal' : h >= 15 && h < 17 ? 'Horas extra' : h >= 17 || h < 6 ? 'Noche' : 'Antes del turno';
  function kpis() {
    const k = st.estado.kpi, h = st.estado.hora;
    $('#p3k').innerHTML = [['Proyectos en planta', k.proyectos, 'azul'], ['Personas ahora', k.personas, ''], ['kg en proceso', fmtNum(k.kg_en_proceso), ''], ['kg en cola', fmtNum(k.kg_en_cola), k.kg_en_cola > 20000 ? 'nar' : ''], ['Stock (kg)', fmtNum(k.stock_kg), ''], [turno(h), `${String(Math.floor(h)).padStart(2, '0')}:${String(Math.round((h % 1) * 60)).padStart(2, '0')}`, h >= 15 || h < 7 ? 'nar' : '']]
      .map(([t, v, c]) => `<div class="p3-kpi ${c}"><span>${t}</span><b>${v}</b></div>`).join('');
  }
  function seguimiento() {
    const x = P(), e = st.estado, ls = e.lotes.filter(l => l.pid === st.pid), pr = e.proyectos.find(p => p.pid === st.pid);
    const r = res(st.pol, x.pid);
    const et = ETAPAS_G.map(([k, n, set]) => { const a = ls.filter(l => set.includes(l.etapa) && l.estado === 'proceso').length, c = ls.filter(l => set.includes(l.etapa) && l.estado !== 'proceso' && l.estado !== 'entregado').length; const ent = k === 'ENTREGADO' ? (pr ? pr.entregados : 0) : null;
      return `<div class="p3-et ${a ? 'on' : c ? 'cola' : ''}"><i></i><b>${n}</b><small>${ent != null ? ent + ' lotes' : a ? a + ' en proceso' : c ? c + ' en cola' : '—'}</small></div>`; }).join('<span class="p3-lin"></span>');
    $('#p3s').innerHTML = `<div class="p3-seg-t"><b>${x.cod ? 'OT ' + x.cod : 'Proyecto ' + x.pid}</b> · ${esc(x.nombre.slice(0, 40))} · ${x.ton.toFixed(0)} t · ${esc(x.contratista)} <span class="nota">inicio ${fmtCorta(x.ini)} · compromiso ${r ? fmtCorta(r.compromiso) : fmtCorta(x.fp)} · terminó ${r ? fmtCorta(r.fin) : '—'}</span> ${r && r.tarde > 0 ? `<span class="badge b-roj">${r.tarde} d tarde</span>` : '<span class="badge b-ver">a tiempo</span>'}${r && r.costo > 0 ? ` <span class="badge b-nar">palancas ${fmtNum(r.costo, 1)} %</span>` : ''}
      <span class="p3-av"><i style="width:${pr ? Math.round(100 * pr.entregados / Math.max(pr.lotes_total, 1)) : 0}%"></i></span><small>${pr ? Math.round(100 * pr.entregados / Math.max(pr.lotes_total, 1)) : 0} % entregado</small></div><div class="p3-etapas">${et}</div>`;
  }

  /* ----- panel derecho ----- */
  const fila = (k, v) => `<div class="p3-f"><span>${k}</span><b>${v}</b></div>`;
  const dur = h => h < 1 ? `${Math.round(h * 60)} min` : h < 48 ? `${h.toFixed(1)} h` : `${(h / 24).toFixed(1)} d`;
  async function detalle(ref) {
    if (!ref) return `<div class="p3-vacio">${ic('planta3d', 34)}<p>Haz clic en una máquina, mesa, puesto, lote de piezas, camión, persona o grúa. Doble clic para acercarte.</p><p class="nota">Arrastra para rotar, rueda para acercar, clic derecho para mover. ${esc(meta.aviso)}</p></div>`;
    const e = st.estado;
    if (ref.tipo === 'maquina') {
      const op = e.ops.find(o => o.recurso === 'maq' + ref.k), par = e.paradas.find(p => p.maquina === ref.k), L = op && e.lotes.find(l => l.id === op.lote_id);
      const cola = e.lotes.filter(l => l.etapa === 'HABILITADO' && l.estado === 'cola').length;
      let h = `<h4>${esc(ref.etiqueta)}</h4><span class="badge ${par ? 'b-roj' : op ? 'b-ver' : 'b-gris'}">${par ? 'EN FALLA' : op ? 'operando' : 'libre'}</span><div class="p3-fs">`;
      if (par) h += fila('Causa', esc(par.causa)) + fila('Parada desde', horaTxt(par.t_ini)) + fila('Vuelve', horaTxt(par.t_fin));
      if (op && L) h += fila('Trabajando', `${esc(L.elemento)} ${esc(L.perfil)}`) + fila('Lote', `${fmtNum(L.kg)} kg · ${L.n_piezas} piezas`) + fila('Termina', horaTxt(op.t_fin)) + fila('Operación', esc(op.tipo));
      h += fila('Lotes esperando habilitado', cola) + '</div><h5>Últimos 14 días</h5><div id="p3ch" style="height:170px"></div><div id="p3pm"></div>';
      setTimeout(async () => { const d = await api(`/api/gemelo/maquina/${ref.k}?t=${st.t}&politica=${st.pol}`); if (!$('#p3ch')) return;
        const c = chart($('#p3ch'), { grid: { left: 36, right: 8, top: 14, bottom: 22 }, tooltip: { trigger: 'axis' }, legend: { top: 0, right: 0, itemWidth: 10, textStyle: { fontSize: 10 } }, xAxis: { type: 'category', data: d.dias.map(x => x.fecha.slice(5)), axisLabel: { fontSize: 9 } }, yAxis: { type: 'value', max: 24, axisLabel: { fontSize: 9 } },
          series: [{ name: 'Horas trabajadas', type: 'bar', stack: 'a', data: d.dias.map(x => x.uso_h), itemStyle: { color: '#1b90ff' } }, { name: 'Horas en parada', type: 'bar', stack: 'a', data: d.dias.map(x => x.parada_h), itemStyle: { color: '#e74c3c' } }] }); P3.charts.push(c);
        const uso = d.dias.reduce((a, x) => a + x.uso_h, 0), disp = d.dias.reduce((a, x) => a + 8 - Math.min(8, x.parada_h), 0);
        $('#p3pm').innerHTML = `<div class="p3-fs">${fila('Utilización (14 d, turno de 8 h)', pct(Math.min(1, uso / (8 * 14))))}${fila('Disponibilidad (14 d)', pct(disp / (8 * 14)))}${fila('Operaciones hasta hoy', fmtNum(d.operaciones))}</div>` + (d.paradas.length ? `<h5>Paradas recientes</h5>${d.paradas.slice(-5).map(p => `<div class="p3-i"><span style="color:var(--gris)">${horaTxt(p.t_ini)}</span><b>${esc(p.causa)}</b><span>${dur(p.horas)} de trabajo</span></div>`).join('')}` : ''); }, 30);
      return h;
    }
    if (ref.tipo === 'estacion') {
      const clase = ref.clase, ops = e.ops.filter(o => o.recurso === (clase === 'mesa' ? 'armado' : clase === 'puesto' ? 'soldeo' : 'limpieza') && (clase === 'limpieza' ? Math.ceil(o.estacion / 4) === ref.n : o.estacion === ref.n));
      let h = `<h4>${esc(ref.etiqueta)}</h4><span class="badge ${ops.length ? 'b-ver' : 'b-gris'}">${ops.length ? 'en uso' : 'libre'}</span><div class="p3-fs">`;
      ops.forEach(o => { const L = e.lotes.find(l => l.id === o.lote_id); h += fila('Trabajando', L ? `${esc(L.elemento)} ${esc(L.perfil)} · ${fmtNum(L.kg)} kg` : '—') + fila('Personas', o.personas) + fila('Termina', horaTxt(o.t_fin)) + fila('Operación', esc(o.tipo)); });
      return h + '</div>';
    }
    if (ref.tipo === 'lote') {
      const l = ref.lote; const d = await api(`/api/gemelo/lote/${l.id}?politica=${st.pol}`);
      const t = d.estados; let tiempos = '';
      const agr = {}; t.forEach(x => { agr[x.etapa] = (agr[x.etapa] || 0) + (x.dur_h || 0); });
      tiempos = Object.entries(agr).filter(([k, v]) => v > 0.05 && k !== 'ENTREGADO').map(([k, v]) => `<div class="p3-i"><span>${esc(ETAPA_TXT[k] || k)}</span><b>${dur(v)}</b></div>`).join('');
      return `<h4>${esc(d.lote.elemento)} ${esc(d.lote.perfil)}</h4><span class="badge b-az">${esc(ETAPA_TXT[l.etapa] || l.etapa)}</span> <span class="badge ${l.estado === 'cola' ? 'b-nar' : 'b-ver'}">${esc(l.estado === 'proceso' ? 'en proceso' : l.estado === 'cola' ? 'en cola' : l.estado === 'grua' ? 'en grúa' : l.estado)}</span>${l.nc ? ' <span class="badge b-roj">no conformidad</span>' : ''}${l.adicional ? ' <span class="badge b-mor">cambio de alcance</span>' : ''}
        <div class="p3-fs">${fila('Proyecto', (d.proyecto.cod ? 'OT ' + d.proyecto.cod : 'P') + ' · ' + esc(d.proyecto.nombre.slice(0, 30)))}${fila('Lote', '#' + d.lote.indice + ' · paquete ' + (d.lote.paquete + 1))}${fila('Peso', fmtNum(d.lote.kg) + ' kg')}${fila('Piezas', d.lote.n_piezas)}${fila('Longitud mayor', d.lote.largo + ' m')}${fila('Pasa por doblez', d.lote.doblez ? 'sí' : 'no')}</div>
        <h5>Contiene (${d.piezas.length} piezas)</h5><table class="tabla p3-t"><tr><th>Marca</th><th>Perfil</th><th>kg</th><th>Long. (m)</th><th>Agujeros</th></tr>${d.piezas.slice(0, 14).map(p => `<tr><td>${esc(p.marca)}</td><td>${esc(p.perfil)}</td><td>${fmtNum(p.kg, 1)}</td><td>${p.largo}</td><td>${p.agujeros}</td></tr>`).join('')}</table>${d.piezas.length > 14 ? `<p class="nota">y ${d.piezas.length - 14} piezas más</p>` : ''}
        <h5>Tiempo en cada etapa</h5>${tiempos || '<p class="nota">Sin historial todavía.</p>'}<h5>Operaciones</h5>${d.ops.map(o => `<div class="p3-i"><span>${esc(o.tipo)}${o.personas ? ' · ' + o.personas + ' pers.' : ''}</span><b>${dur(o.t_fin - o.t_ini)}</b></div>`).join('')}`;
    }
    if (ref.tipo === 'persona') { const g = ref.persona; return `<h4>${esc(g.nombre)}</h4><span class="badge b-gris">${esc(g.grupo)}</span><div class="p3-fs">${fila('Rol', esc(g.rol || '—'))}${fila('Ubicación', esc(ref.estacion))}${fila('Haciendo', esc(ref.trabajo))}</div><p class="nota">Persona anónima simulada, ubicada según el plan y el tareo del gemelo.</p>`; }
    if (ref.tipo === 'camion') { const c = ref.camion; return `<h4>Camión de ${esc(c.tipo)}</h4><div class="p3-fs">${fila('Proyecto', c.pid)}${fila('Carga', fmtNum(c.kg) + ' kg · ' + c.n_lotes + ' lotes')}${fila('Sale', horaTxt(c.t_ini))}${fila('Vuelve', c.tipo === 'obra' ? '—' : horaTxt(c.t_fin))}${c.tipo !== 'obra' ? fila('Ida y vuelta', dur(c.t_fin - c.t_ini)) : ''}</div>`; }
    if (ref.tipo === 'grua') { const g = ref.g; const mv = e.movs.find(x => x.grua === g); const L = mv && e.lotes.find(l => l.id === mv.lote_id); return `<h4>${esc(ref.etiqueta)}</h4><span class="badge ${mv ? 'b-ver' : 'b-gris'}">${mv ? 'izando' : 'libre'}</span><div class="p3-fs">${mv && L ? fila('Lleva', `${esc(L.elemento)} · ${fmtNum(L.kg)} kg`) + fila('Destino', esc(mv.destino)) + fila('Llega', horaTxt(mv.t_fin)) : ''}${fila('Capacidad', '10 t')}</div><p class="nota">Cada traslado ocupa la grúa; si está ocupada los lotes esperan en cola.</p>`; }
    if (ref.tipo === 'material' || ref.tipo === 'rack') { return `<h4>${esc(ref.etiqueta)}</h4><div class="p3-fs">${fila('Stock total en planta', fmtNum(e.kpi.stock_kg) + ' kg')}</div><h5>Por proyecto</h5>${e.proyectos.map(p => `<div class="p3-i"><b>${p.cod ? 'OT ' + p.cod : 'P' + p.pid}</b><span>${fmtNum(p.stock_kg)} kg</span></div>`).join('')}<h5>Pedidos recientes</h5>${e.material.length ? e.material.map(x => `<div class="p3-i"><span>P${x.pid} · paquete ${x.paquete + 1}</span><span>${fmtNum(x.kg)} kg · ${x.llegado ? 'llegó' : 'llega ' + horaTxt(x.llegada)}</span></div>`).join('') : '<p class="nota">Sin pedidos en curso.</p>'}`; }
    return `<h4>${esc(ref.nombre || ref.etiqueta || '')}</h4>`;
  }
  const ETAPA_TXT = { ESPERA: 'Esperando material', HABILITADO: 'Habilitado', MOVIMIENTO: 'Traslado con grúa', DOBLEZ: 'Doblez (externo)', ARMADO: 'Armado', SOLDEO: 'Soldeo', RETRABAJO: 'Retrabajo de soldeo', LIMPIEZA: 'Limpieza e inspección', LISTO_PINTURA: 'Listo para pintura', PINTURA: 'Granallado y pintura (externo)', PINTADO: 'Pintado, esperando despacho', ENTREGADO: 'Entregado a obra' };
  async function proyectoTab() {
    const d = await api('/api/gemelo/proyecto/' + st.pid); const x = d.proyecto;
    let h = `<h4>${x.cod ? 'OT ' + x.cod : 'Proyecto ' + x.pid} · ${esc(x.nombre.slice(0, 44))}</h4><div class="p3-fs">${fila('Tipo', esc(x.tipo.split('/')[0]))}${fila('Peso', x.ton.toFixed(0) + ' t · ' + x.n_lotes + ' lotes')}${fila('Contratista', esc(x.contratista))}${fila('Paquetes de ingeniería', x.paquetes + ' (' + x.rfis + ' RFI, ' + x.cambios + ' cambios de alcance)')}${fila('Presupuesto (simulado)', 'S/ ' + fmtNum(x.presupuesto))}</div>
      <h5>Cómo habría terminado con cada política</h5><table class="tabla p3-t"><tr><th>Política</th><th>Compromiso</th><th>Terminó</th><th>Tarde</th><th>Palancas</th></tr>${d.politicas.map(r => `<tr><td>${esc(r.politica.slice(0, 2))} ${esc(NOM_POL[r.politica.slice(0, 2)] || '')}</td><td>${fmtCorta(r.compromiso)}</td><td>${fmtCorta(r.fin)}</td><td style="color:${r.tarde > 0 ? 'var(--rojo)' : 'var(--verde)'}">${r.tarde}</td><td>${r.costo ? fmtNum(r.costo, 1) + ' %' : '—'}</td></tr>`).join('')}</table>
      <h5>Avance acumulado entregado (kg)</h5><div id="p3cu" style="height:210px"></div>`;
    if (d.palancas.length) h += `<h5>Palancas aplicadas (DSS y regla)</h5>${d.palancas.slice(0, 12).map(p => `<div class="p3-i"><span>${esc(p.politica.slice(0, 2))} · ${horaTxt(p.t).slice(0, 10)}</span><b>${esc(p.tipo)} ${esc(NOMBRE_PROC_G[p.proceso] || p.proceso)}</b><span>${fmtNum(p.costo, 1)} %</span></div>`).join('')}`;
    setTimeout(() => { if (!$('#p3cu')) return; const cols = { A0: '#5b738b', B1: '#e9730c', D3: '#925ace', D4: '#107e3e' }; const c = chart($('#p3cu'), { grid: { left: 48, right: 10, top: 24, bottom: 24 }, tooltip: { trigger: 'axis' }, legend: { top: 0, textStyle: { fontSize: 10 } }, xAxis: { type: 'value', min: 'dataMin', axisLabel: { fontSize: 9, formatter: v => horaTxt(v).slice(0, 5) } }, yAxis: { type: 'value', axisLabel: { fontSize: 9 } },
      series: Object.entries(d.curvas).map(([k, v]) => ({ name: k + ' ' + (NOM_POL[k] || ''), type: 'line', step: 'end', showSymbol: false, data: v.t.map((t, i) => [t, v.kg[i]]), lineStyle: { color: cols[k], width: 2 }, itemStyle: { color: cols[k] } })) }); P3.charts.push(c); }, 30);
    return h + `<p class="nota">${esc(d.aviso)}</p>`;
  }
  const NOMBRE_PROC_G = ['Ingeniería', 'Compra', 'Sierra', 'Cizalla', 'CNC', 'Roscado', 'Doblez', 'Armado', 'Soldeo', 'Limpieza', 'Desp. pintura', 'Pintura', 'Desp. obra'];
  function resultadosTab() {
    const r = meta.resumen; if (!r) return '<p class="nota">Aún no se corrió <code>py scripts/exp6_gemelo.py</code>.</p>';
    let h = `<h4>Historia 2019-2026 con cada política</h4><p class="nota">25 proyectos de la muestra, mismo azar para todas. Penalidad: 1 % del presupuesto por día. «Ajustado» suma el costo comercial del plazo extra (0.08 % por día, supuesto).</p><table class="tabla p3-t"><tr><th>Política</th><th>OTD</th><th>Retraso (d)</th><th>Palancas (%)</th><th>Total ajust. (%)</th><th>Plazo (d)</th></tr>${r.map(x => `<tr><td>${esc(x.politica.slice(0, 2))} ${esc(NOM_POL[x.politica.slice(0, 2)] || '')}</td><td>${x.OTD} %</td><td>${x.retraso_dias}</td><td>${x.costo_palancas}</td><td><b>${x.total_ajustado}</b></td><td>${x.plazo}</td></tr>`).join('')}</table>`;
    if (meta.alerta) h += `<h5>Alerta temprana del DSS (re-pronóstico cada 12 días, sin actuar)</h5><table class="tabla p3-t"><tr><th>Tramo del plazo</th><th>AUC</th><th>Brier</th><th>vs. base</th><th>Error de fecha (d)</th></tr>${meta.alerta.map(x => `<tr><td>${esc(x.tramo)}</td><td>${x.AUC}</td><td>${x.Brier}</td><td>${x.Brier_base}</td><td>${x.MAE_fecha_dias}</td></tr>`).join('')}</table><p class="nota">AUC 0.5 = sin señal; 1 = perfecta. El Brier debe ser menor que el de la base.</p>`;
    return h + `<p class="nota">${esc(meta.aviso)}</p>`;
  }
  async function panel() {
    const c = $('#p3panel'); c.innerHTML = cargando();
    try { c.innerHTML = st.pestana === 'objeto' ? await detalle(st.sel) : st.pestana === 'proyecto' ? await proyectoTab() : resultadosTab(); } catch (e) { c.innerHTML = `<p class="nota" style="color:var(--rojo)">${esc(e.message)}</p>`; }
  }

  /* ----- controles ----- */
  $$('.p3d-tabs button').forEach(b => b.onclick = () => { st.pestana = b.dataset.t; pestanas(); panel(); });
  $('#p3v').onchange = e => { P3.escena.vista(e.target.value); e.target.selectedIndex = 0; };
  $('#p3lim').onchange = e => $('.p3d').classList.toggle('limpio', e.target.checked);
  $('#p3s').onclick = () => $('#p3s').classList.toggle('abierto');
  $('#p3pol').onchange = e => { st.pol = e.target.value; ajustarSlider(); cargar(st.t); if (st.pestana !== 'objeto') panel(); };
  $('#p3p').onchange = e => { st.pid = +e.target.value; ajustarSlider(); cargar(Math.floor(tDeFecha(P().ini, 9) + 24 * 12)); if (st.pestana !== 'objeto') panel(); };
  $('#p3r').oninput = e => cargar(+e.target.value);
  const paso = d => cargar(Math.max(+$('#p3r').min, Math.min(+$('#p3r').max, Math.floor(st.t) + d)));
  $('#p3ant').onclick = () => paso(-1); $('#p3sig').onclick = () => paso(1);
  $('#p3vel').onchange = e => { st.vel = +e.target.value; };
  $('#p3play').onclick = () => {
    st.play = !st.play; $('#p3play').textContent = st.play ? '❚❚' : '▶'; clearInterval(P3.timer);
    if (st.play) { let ult = performance.now(); P3.timer = setInterval(() => { const ahora = performance.now(); const dt = (ahora - ult) / 1000; ult = ahora; st.tl = (st.tl ?? st.t) + st.vel * dt; if (st.tl > +$('#p3r').max) { st.play = false; $('#p3play').textContent = '▶'; clearInterval(P3.timer); return; } P3.escena.setT(st.tl); $('#p3f').textContent = horaTxt(st.tl); if (Math.abs(st.tl - st.t) >= 1 && !st.ocupado) { st.ocupado = true; cargar(Math.floor(st.tl)).finally(() => { st.ocupado = false; }); } }, 60); }
    else st.tl = null;
  };
  $('#p3t').onchange = e => P3.escena.techos(e.target.checked); $('#p3e').onchange = e => P3.escena.etiquetas(e.target.checked);
  $('#p3pol').value = st.pol; $('#p3p').value = st.pid; ajustarSlider();
  await cargar(Math.floor(tDeFecha(P().ini, 9) + 24 * 12)); panel();
}

/* =====================================================================  ruteo */
async function ruta() {
  if (!S.me) return renderLogin();
  limpiarP3();
  const [path, qs = ''] = (location.hash.slice(2) || 'inicio').split('?');
  const [v, a, b] = path.split('/');
  try {
    if (v === 'proyecto' && a === 'h') return await vProyectoHist(b);
    if (v === 'proyecto' && a === 'a') return await vProyectoAct(b, qs);
    if (v === 'proyectos') return await vProyectos(a === 'hist' ? 'hist' : 'curso');
    if (v === 'gantt') return await vGantt();
    if (v === 'reporte') return await vReporte(a, qs);
    if (v === 'cotizador' && puedeVer('cotizador')) return await vCotizador();
    if (v === 'planta3d') return await vPlanta3D();
    if (v === 'planta' && puedeVer('planta')) return await vPlanta(qs);
    if (v === 'tareas') return await vTareas(qs);
    if (v === 'bandeja') return await vBandeja();
    if (v === 'importar' && puedeVer('importar')) return await vImportar();
    if (v === 'usuarios' && S.me.rol === 'gerencia') return await vUsuarios();
    return await vInicio();
  } catch (e) { if (e.message !== 'Sesión expirada') { const m = $('#main'); if (m) m.innerHTML = `<div class="tarjeta"><div class="cuerpo vacio">${ic('alerta', 30)}<p>${esc(e.message)}</p></div></div>`; } }
}
async function arrancar() {
  try { S.me = await api('/api/me'); S.cat = await api('/api/catalogos'); } catch { S.me = null; }
  ruta();
}
window.addEventListener('hashchange', ruta);
arrancar();
