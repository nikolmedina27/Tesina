/* SteelPlan · Mantenimiento de máquinas (v3): listado ejecutivo, ficha, Gantt de máquinas, paradas, órdenes y plan preventivo.
   Usa los helpers de app.js (shell, api, ic, kpi, chart, modal…); se carga antes que app.js y solo se ejecuta al navegar. */
'use strict';
const EDITA_MANT = ['jefe_taller', 'mantenimiento'];
const REPORTA_MANT = ['jefe_taller', 'mantenimiento', 'supervisor', 'calidad'];
const EST_MAQ = { OPERANDO: ['Operando', 'b-ver'], MANTENIMIENTO: ['En mantenimiento', 'b-nar'], PARADA: ['Parada por falla', 'b-roj'] };
const TIPO_OM = { PREVENTIVO: ['Preventivo', 'b-az'], CORRECTIVO: ['Correctivo', 'b-roj'], PREDICTIVO: ['Predictivo', 'b-mor'] };
const EST_OM = [['PENDIENTE', 'Pendiente'], ['EN_CURSO', 'En curso'], ['CERRADA', 'Cerrada']];
const pctDk = x => x == null ? '—' : `${(100 * x).toFixed(1)} %`;
const clsDk = (x, meta = 0.9) => x == null ? '' : x >= meta ? 'ver' : x >= 0.8 ? 'nar' : 'roj';
const horas = h => h == null ? '—' : `${fmtNum(h, h < 10 ? 1 : 0)} h`;
const ahoraLocal = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16);
const migasMant = (...x) => [`${ic('llave', 20)} <a href="#/mant">Mantenimiento</a>`, ...x].join('<span class="sep">/</span>');

/* ---------- reportar falla (crea la orden correctiva; si la máquina quedó parada, arranca en curso) ---------- */
function modalFalla(maquinas, mid, alTerminar) {
  modal('Reportar falla de máquina', `<div class="form">
    <label class="ancho">Máquina<select name="maquina_id">${maquinas.map(m => `<option value="${m.id}" ${m.id === mid ? 'selected' : ''}>${esc(m.nombre)}</option>`).join('')}</select></label>
    <label class="ancho">Qué pasó<input name="titulo" required minlength="3" placeholder="No corta, ruido en el motor, fuga de aceite..."></label>
    <label class="ancho">Detalle<textarea name="descripcion" rows="2"></textarea></label>
    <label class="chk ancho"><input type="checkbox" name="iniciar" checked> La máquina está parada ahora</label>
    <p class="nota ancho">Se abre una orden correctiva. Al cerrarla con su hora de inicio y fin, queda registrada la parada y se recalculan la disponibilidad, el MTBF y el MTTR.</p></div>`,
  async f => {
    await api('/api/mant/ordenes', { method: 'POST', body: { maquina_id: +f.get('maquina_id'), tipo: 'CORRECTIVO', titulo: f.get('titulo'), descripcion: f.get('descripcion') || null, iniciar: !!f.get('iniciar') } });
    toast('Falla reportada'); alTerminar && alTerminar();
  }, 'Reportar');
}

/* =====================================================================  MÁQUINAS (listado ejecutivo) */
async function vMant() {
  const m = shell('mant', migasMant('Máquinas'),
    `${puede(REPORTA_MANT) ? `<button class="btn roj" id="bfalla">${ic('alerta', 15)} Reportar falla</button>` : ''}<a class="btn" href="#/mantgantt">${ic('gantt', 15)} Gantt de máquinas</a>`);
  const d = await api('/api/mant/maquinas');
  const r = d.resumen;
  m.innerHTML = `
  <div class="kpis">
    ${kpi('Disponibilidad promedio · 30 días', pctDk(r.dk_promedio), `meta ${pctDk(d.meta_dk)} (TPM)`, clsDk(r.dk_promedio, d.meta_dk), 'engranaje')}
    ${kpi('Fallas · 30 días', r.fallas_30d, `${horas(r.horas_perdidas_30d)} de máquina perdidas`, r.fallas_30d ? 'nar' : 'ver', 'alerta')}
    ${kpi('Preventivos vencidos', r.preventivos_vencidos, 'pasaron su fecha programada', r.preventivos_vencidos ? 'roj' : 'ver', 'reloj')}
    ${kpi('Máquinas detenidas ahora', r.paradas_ahora, `de ${d.maquinas.length} máquinas de habilitado`, r.paradas_ahora ? 'roj' : 'ver', 'llave')}</div>
  <div class="maqs">${d.maquinas.map(x => tarjetaMaquina(x, d.meta_dk)).join('')}</div>
  <p class="nota">Disponibilidad Dₖ = (tiempo programado − paradas) / tiempo programado, con turnos de lunes a sábado. MTBF: horas operando entre fallas; MTTR: horas promedio para reparar.
    El plan preventivo inicial es una sugerencia con frecuencias típicas de fabricante: ajústalo en <a href="#/mantordenes?tab=plan">Órdenes y plan</a>.</p>`;
  $$('.maq', m).forEach(c => c.onclick = e => { if (!e.target.closest('button')) location.hash = '#/maquina/' + c.dataset.id; });
  $$('[data-falla]', m).forEach(b => b.onclick = () => modalFalla(d.maquinas, +b.dataset.falla, vMant));
  const bf = $('#bfalla'); if (bf) bf.onclick = () => modalFalla(d.maquinas, null, vMant);
}
function tarjetaMaquina(x, meta) {
  const i = x.indicadores_30d, e = EST_MAQ[x.estado], dk = i.dk;
  const prox = x.proximo_preventivo;
  return `<article class="maq" data-id="${x.id}" tabindex="0">
    <header><div class="ico">${ic('engranaje', 22)}</div><div><b>${esc(x.nombre)}</b><div class="nota">${esc(x.centro || '')}${x.criticidad ? ` · criticidad ${esc(x.criticidad)}` : ''}</div></div>
      <i class="sem ${x.semaforo}" role="img" aria-label="estado"></i></header>
    <div class="estado"><span class="badge ${e[1]}">${e[0]}</span>${x.parada_actual ? ` <span class="nota">desde ${esc(x.parada_actual.inicio.slice(11, 16))} · ${esc(x.parada_actual.causa)}</span>` : x.orden_en_curso ? ` <span class="nota">OM-${x.orden_en_curso.id} ${esc(x.orden_en_curso.titulo)}</span>` : ''}</div>
    <div class="dk"><span class="v ${clsDk(dk, meta)}">${pctDk(dk)}</span><span class="nota">disponibilidad 30 días</span>
      <div class="barra dkb"><i style="width:${dk == null ? 0 : 100 * dk}%"></i><s style="left:${100 * meta}%" title="meta"></s></div></div>
    <dl><div><dt>MTBF</dt><dd>${horas(i.mtbf_h)}</dd></div><div><dt>MTTR</dt><dd>${horas(i.mttr_h)}</dd></div><div><dt>Fallas</dt><dd>${i.n_fallas}</dd></div><div><dt>Horas paradas</dt><dd>${horas(i.horas_parada)}</dd></div></dl>
    <footer><div><span class="nota">Último preventivo</span> ${fmtCorta(x.ultimo_preventivo)}</div>
      <div><span class="nota">Próximo</span> ${prox ? `${fmtCorta(prox.programada_para)}${x.preventivos_vencidos ? ' <span class="badge b-roj">vencido</span>' : ''}` : '—'}</div>
      ${puede(REPORTA_MANT) ? `<button class="btn peq" data-falla="${x.id}">${ic('alerta', 13)} Falla</button>` : ''}</footer></article>`;
}

/* =====================================================================  FICHA DE MÁQUINA */
async function vMaquina(id) {
  const m = shell('mant', migasMant('Máquina'));
  const d = await api('/api/mant/maquinas/' + id);
  const x = d.maquina, I = d.indicadores;
  $('.migas').innerHTML = migasMant(`<a href="#/mant">Máquinas</a>`, esc(x.nombre));
  $('.acciones').innerHTML = `${puede(REPORTA_MANT) ? `<button class="btn roj" id="bfalla">${ic('alerta', 15)} Reportar falla</button>` : ''}
    ${puede(EDITA_MANT) ? `<button class="btn" id="bom">${ic('mas', 15)} Nueva orden</button>` : ''}`;
  const e = EST_MAQ[x.estado];
  m.innerHTML = `
  <div class="kpis">
    ${kpi(esc(x.nombre), `<span class="badge ${e[1]}" style="font-size:13px">${e[0]}</span>`, `${esc(x.marca || 'marca por completar')}${x.modelo ? ' ' + esc(x.modelo) : ''}${x.anio ? ' · ' + x.anio : ''}`, '', 'engranaje')}
    ${kpi('Disponibilidad 30 días', pctDk(I['30d'].dk), `90 días ${pctDk(I['90d'].dk)} · 12 meses ${pctDk(I['365d'].dk)}`, clsDk(I['30d'].dk, d.meta_dk), 'check')}
    ${kpi('MTBF · 12 meses', horas(I['365d'].mtbf_h), `${I['365d'].n_fallas} fallas desde ${fmtCorta(I['365d'].desde)}`, '', 'reloj')}
    ${kpi('MTTR · 12 meses', horas(I['365d'].mttr_h), `preventivo ${I['365d'].pct_preventivo == null ? '—' : pct(I['365d'].pct_preventivo)} de las horas paradas`, 'mor', 'llave')}</div>
  <div class="grid g2" style="margin-bottom:14px">
    <div class="tarjeta"><h3>Disponibilidad por mes <span class="nota">meta ${pctDk(d.meta_dk)}${d.inicio_registro ? ` · registro desde ${fmtCorta(d.inicio_registro)}` : ' · sin paradas registradas aún'}</span></h3><div class="cuerpo"><div class="grafico bajo" id="gdk"></div></div></div>
    <div class="tarjeta"><h3>Causas de parada · 12 meses <span class="nota">horas</span></h3><div class="cuerpo">${I['365d'].causas.length ? '<div class="grafico bajo" id="gca"></div>' : '<div class="vacio">Sin paradas registradas</div>'}</div></div></div>
  <div class="pestanas" id="mtabs"><button class="activo" data-t="his">${ic('lista', 15)} Historial</button><button data-t="pla">${ic('reloj', 15)} Plan preventivo (${d.planes.filter(p => p.activo).length})</button><button data-t="dat">${ic('hoja', 15)} Datos técnicos</button></div>
  <div id="t-his">${historialMaquina(d)}</div>
  <div id="t-pla" class="oculto"><div class="tarjeta"><div class="cuerpo">${tablaPlanes(d.planes, false)}</div></div></div>
  <div id="t-dat" class="oculto"><form class="tarjeta" id="fficha"><div class="cuerpo form">
    ${[['centro', 'Centro de trabajo'], ['marca', 'Marca'], ['modelo', 'Modelo']].map(([k, t]) => `<label>${t}<input name="${k}" value="${esc(x[k] || '')}"></label>`).join('')}
    <label>Año<input name="anio" type="number" min="1950" max="2100" value="${x.anio || ''}"></label>
    <label>Criticidad<select name="criticidad">${['A', 'B', 'C'].map(c => `<option ${c === x.criticidad ? 'selected' : ''}>${c}</option>`).join('')}</select></label>
    <label>Horas por turno<input name="horas_turno" type="number" step="0.5" min="1" max="24" value="${x.horas_turno || 8}"></label>
    <label>Turnos por día<input name="turnos" type="number" min="1" max="3" value="${x.turnos || 1}"></label>
    <label class="ancho">Descripción<textarea name="descripcion" rows="2">${esc(x.descripcion || '')}</textarea></label>
    ${puede(EDITA_MANT) ? `<button class="btn prim ancho" style="justify-content:center">${ic('check', 15)} Guardar ficha</button>` : '<p class="nota ancho">Solo el jefe de taller o mantenimiento editan la ficha.</p>'}</div></form></div>`;
  $$('#mtabs button').forEach(b => b.onclick = () => { $$('#mtabs button').forEach(z => z.classList.toggle('activo', z === b)); ['his', 'pla', 'dat'].forEach(t => $('#t-' + t).classList.toggle('oculto', t !== b.dataset.t)); });
  chart($('#gdk'), { grid: { left: 46, right: 16, top: 16, bottom: 26 }, tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '—' : v + ' %' },
    xAxis: { type: 'category', data: d.dk_mensual.map(z => z.mes.slice(5) + '/' + z.mes.slice(2, 4)) }, yAxis: { type: 'value', min: v => Math.max(0, Math.floor(v.min / 10) * 10 - 10), max: 100, axisLabel: { formatter: '{value} %' } },
    series: [{ type: 'bar', barWidth: '55%', data: d.dk_mensual.map(z => ({ value: z.dk == null ? null : +(100 * z.dk).toFixed(1), itemStyle: { color: z.dk == null ? C.borde : z.dk >= d.meta_dk ? C.verde : z.dk >= 0.8 ? C.ambar : C.rojo } })),
      markLine: { symbol: 'none', data: [{ yAxis: 100 * d.meta_dk }], lineStyle: { color: C.verde, type: 'dashed' }, label: { formatter: 'meta' } } }] });
  if ($('#gca')) { const ca = I['365d'].causas.slice().reverse();
    chart($('#gca'), { grid: { left: 170, right: 40, top: 8, bottom: 20 }, tooltip: { valueFormatter: v => v + ' h' }, xAxis: { type: 'value' }, yAxis: { type: 'category', data: ca.map(z => z.causa) },
      series: [{ type: 'bar', barWidth: 14, data: ca.map(z => ({ value: z.horas, itemStyle: { color: /preventivo/i.test(z.causa) ? C.acento : C.rojo } })), label: { show: true, position: 'right', formatter: '{c} h' } }] }); }
  const ff = $('#fficha');
  if (ff && puede(EDITA_MANT)) ff.onsubmit = async ev => { ev.preventDefault(); const f = new FormData(ff); const b = Object.fromEntries([...f].filter(([, v]) => v !== ''));
    ['anio', 'horas_turno', 'turnos'].forEach(k => { if (b[k] != null) b[k] = +b[k]; });
    try { await api('/api/mant/maquinas/' + id, { method: 'PATCH', body: b }); toast('Ficha guardada'); vMaquina(id); } catch (err) { toast(err.message, 1); } };
  const bf = $('#bfalla'); if (bf) bf.onclick = () => modalFalla([x], x.id, () => vMaquina(id));
  const bo = $('#bom'); if (bo) bo.onclick = () => modalOrden(x, () => vMaquina(id));
}
function historialMaquina(d) {
  const ev = [...d.paradas.map(p => ({ f: p.inicio, tipo: p.planificada ? 'Parada planificada' : 'Falla', cls: p.planificada ? 'b-az' : 'b-roj', tit: p.causa, det: p.observacion || '', h: p.horas, ref: p.orden_id ? `OM-${p.orden_id}` : '' })),
    ...d.ordenes.filter(o => o.estado !== 'CERRADA' || !o.parada_id).map(o => ({ f: o.fin || o.inicio || o.programada_para || o.creado_en, tipo: `Orden ${TIPO_OM[o.tipo][0].toLowerCase()}`, cls: TIPO_OM[o.tipo][1], tit: o.titulo,
      det: `${o.estado.replace('_', ' ').toLowerCase()}${o.tecnico ? ' · ' + o.tecnico : ''}${o.repuestos ? ' · repuestos: ' + o.repuestos : ''}`, h: null, ref: `OM-${o.id}` }))]
    .sort((a, b) => String(b.f).localeCompare(String(a.f)));
  return `<div class="tarjeta"><div class="cuerpo scroll" style="max-height:520px">${ev.length ? `<table class="tabla"><tr><th>Fecha</th><th>Tipo</th><th>Qué</th><th class="num">Horas</th><th>Detalle</th><th>Orden</th></tr>
    ${ev.map(z => `<tr><td>${esc(String(z.f).slice(0, 16).replace('T', ' '))}</td><td><span class="badge ${z.cls}">${z.tipo}</span></td><td>${esc(z.tit)}</td><td class="num">${z.h == null ? '—' : fmtNum(z.h, 1)}</td><td class="nota">${esc(z.det)}</td><td class="nota">${z.ref}</td></tr>`).join('')}</table>`
    : '<div class="vacio">Sin historial todavía. Las paradas registradas en Planta y las órdenes cerradas aparecen aquí.</div>'}</div></div>`;
}

/* =====================================================================  GANTT DE MÁQUINAS (Hoy · 2 días · Semana · Mes) */
const COL_G = () => ({ proyecto: [C.acentoM, C.acento], falla: [C.rojo, C.rojo], planificada: [C.ambar, C.ambar], orden_preventivo: [C.morado, C.morado], orden_correctivo: [C.rojo, C.rojo], orden_predictivo: [C.morado, C.morado] });
const NOM_G = { proyecto: 'Trabajo de proyectos (plan P50)', falla: 'Falla', planificada: 'Parada planificada', orden_preventivo: 'Preventivo programado', orden_correctivo: 'Correctivo abierto', orden_predictivo: 'Predictivo' };
async function vMantGantt() {
  const zoom = PREFS.get('mant_zoom', '2d');
  const m = shell('mantgantt', migasMant('Gantt de máquinas'),
    `<div class="vistas" id="gz">${[['hoy', 'Hoy'], ['2d', '2 días'], ['sem', 'Semana'], ['mes', 'Mes']].map(([k, t]) => `<button data-z="${k}" class="${k === zoom ? 'activo' : ''}">${t}</button>`).join('')}</div>`);
  const hoy = hoyISO(), desde = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
  const d = await api(`/api/mant/gantt?desde=${desde}&dias=75`);
  m.innerHTML = `
  <div class="tarjeta" style="margin-bottom:14px"><h3>Máquinas en el tiempo <span class="leyenda" style="margin:0">${Object.entries(NOM_G).filter(([k]) => k !== 'orden_predictivo').map(([k, t]) => `<span><i style="background:${COL_G()[k][0]}"></i>${t}</span>`).join('')}</span></h3>
    <div class="cuerpo"><div id="gm" style="height:${120 + 74 * d.maquinas.length}px"></div><p class="nota">Arrastra o usa la barra de abajo para moverte en el tiempo. Clic en una barra para ver el detalle; clic en el nombre de una máquina para abrir su ficha.</p></div></div>
  <div class="grid g2">
    <div class="tarjeta"><h3>${ic('reloj', 16)} Agenda de hoy y los próximos 2 días</h3><div class="cuerpo scroll" style="max-height:360px" id="agenda"></div></div>
    <div class="tarjeta"><h3>${ic('lista', 16)} Detalle</h3><div class="cuerpo" id="gdet"><div class="vacio">Selecciona una barra del Gantt</div></div></div></div>`;
  const ms = d.maquinas, cols = COL_G();
  const t = s => new Date(String(s).replace(' ', 'T')).getTime();
  const data = d.items.map((x, i) => ({ value: [ms.indexOf(x.maquina), t(x.inicio), t(x.fin), i], itemStyle: { color: cols[x.tipo]?.[0] || C.gris } })).filter(z => z.value[0] >= 0);
  const ventana = z => { const h0 = new Date(hoy + 'T00:00').getTime(), H = 36e5;
    return { hoy: [h0 + 6 * H, h0 + 22 * H], '2d': [h0, h0 + 72 * H], sem: [h0 - 24 * H, h0 + 7 * 24 * H], mes: [h0 - 7 * 24 * H, h0 + 30 * 24 * H] }[z]; };
  const [a0, b0] = ventana(zoom);
  const ch = chart($('#gm'), {
    grid: { left: 190, right: 24, top: 18, bottom: 64 },
    tooltip: { formatter: p => { const x = d.items[p.value[3]]; return `<b>${esc(x.titulo)}</b><br>${esc(NOM_G[x.tipo] || x.tipo)}<br>${esc(x.inicio)} → ${esc(x.fin)}${x.detalle ? '<br>' + esc(x.detalle) : ''}${x.vencida ? '<br><b>Vencido</b>' : ''}`; } },
    xAxis: { type: 'time', position: 'top', splitLine: { show: true }, axisLabel: { hideOverlap: true, formatter: { year: '{yyyy}', month: '{dd}/{MM}', day: '{dd}/{MM}', hour: '{HH}:{mm}', minute: '{HH}:{mm}' } } },
    yAxis: { type: 'category', data: ms, inverse: true, triggerEvent: true, axisTick: { show: false }, axisLabel: { fontWeight: 600, color: C.acento, width: 175, overflow: 'truncate' } },
    dataZoom: [{ type: 'slider', xAxisIndex: 0, filterMode: 'weakFilter', startValue: a0, endValue: b0, height: 18, bottom: 16, labelFormatter: v => new Date(v).toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit' }) },
      { type: 'inside', xAxisIndex: 0, filterMode: 'weakFilter' }],
    series: [{ type: 'custom', encode: { x: [1, 2], y: 0 }, data,
      renderItem: (params, api_) => {
        const fila = api_.value(0), x = d.items[api_.value(3)], ini = api_.coord([api_.value(1), fila]), fin = api_.coord([api_.value(2), fila]);
        const alto = api_.size([0, 1])[1], esProy = x.tipo === 'proyecto';
        const h = esProy ? alto * 0.34 : alto * 0.3, y = esProy ? ini[1] - alto * 0.38 : ini[1] + alto * 0.06;
        const r = echarts.graphic.clipRectByRect({ x: ini[0], y, width: Math.max(fin[0] - ini[0], 3), height: h },
          { x: params.coordSys.x, y: params.coordSys.y, width: params.coordSys.width, height: params.coordSys.height });
        if (!r) return;
        const pendiente = x.tipo.startsWith('orden_');
        const hijos = [{ type: 'rect', shape: r, style: { fill: pendiente ? 'transparent' : api_.visual('color'), stroke: cols[x.tipo]?.[1], lineWidth: pendiente ? 1.5 : 0, lineDash: x.vencida ? [4, 3] : null, opacity: esProy ? 0.85 : 1 } }];
        if (r.width > 70) hijos.push({ type: 'text', style: { x: r.x + 5, y: r.y + r.height / 2, text: x.titulo, fill: esProy ? C.acento : pendiente ? cols[x.tipo][1] : '#fff', fontSize: 10.5, verticalAlign: 'middle', width: r.width - 8, overflow: 'truncate' } });
        return { type: 'group', children: hijos };
      } },
    { type: 'line', data: [], markLine: { symbol: 'none', silent: true, label: { formatter: 'ahora', position: 'insideEndTop' }, lineStyle: { color: C.ambar, width: 1.5 }, data: [{ xAxis: t(d.ahora) }] } }],
  });
  ch.on('click', p => {
    if (p.componentType === 'yAxis') { const i = ms.indexOf(p.value); location.hash = '#/maquina/' + (S.maqIds?.[p.value] || i + 1); return; }
    if (p.seriesType !== 'custom') return;
    const x = d.items[p.value[3]], [tipo, rid] = String(x.ref).split(':');
    $('#gdet').innerHTML = `<div class="detg"><span class="badge" style="background:${cols[x.tipo][0]};color:#fff">${esc(NOM_G[x.tipo] || x.tipo)}</span><h4>${esc(x.titulo)}</h4>
      <p><b>${esc(x.maquina)}</b><br>${esc(x.inicio)} → ${esc(x.fin)}</p>${x.detalle ? `<p class="nota">${esc(x.detalle)}</p>` : ''}${x.proyecto ? `<p class="nota">Proyecto ${esc(x.proyecto)}</p>` : ''}
      ${tipo === 'proyecto' ? `<a class="btn peq" href="#/proyecto/a/${rid}">${ic('proyectos', 14)} Abrir proyecto</a>` : tipo === 'orden' ? `<a class="btn peq" href="#/mantordenes?o=${rid}">${ic('llave', 14)} Abrir orden OM-${rid}</a>` : ''}</div>`;
  });
  $$('#gz button').forEach(b => b.onclick = () => { $$('#gz button').forEach(z => z.classList.toggle('activo', z === b)); PREFS.set('mant_zoom', b.dataset.z); const [a, c] = ventana(b.dataset.z); ch.dispatchAction({ type: 'dataZoom', startValue: a, endValue: c }); });
  // agenda: todo lo que toca hoy, mañana y pasado mañana
  const lim = new Date(new Date(hoy + 'T00:00').getTime() + 3 * 864e5).toISOString().slice(0, 10);
  const ag = d.items.filter(x => x.fin.slice(0, 10) >= hoy && x.inicio.slice(0, 10) < lim).sort((a, b) => a.inicio.localeCompare(b.inicio));
  $('#agenda').innerHTML = ag.length ? `<table class="tabla"><tr><th>Cuándo</th><th>Máquina</th><th>Qué</th><th></th></tr>${ag.map(x => `<tr><td>${esc(x.inicio.slice(8, 10) + '/' + x.inicio.slice(5, 7) + ' ' + x.inicio.slice(11, 16))} → ${esc(x.fin.slice(8, 10) + '/' + x.fin.slice(5, 7) + ' ' + x.fin.slice(11, 16))}</td>
    <td>${esc(x.maquina)}</td><td>${esc(x.titulo)}</td><td><span class="badge" style="background:${cols[x.tipo][0]};color:#fff">${esc((NOM_G[x.tipo] || '').split(' (')[0])}</span>${x.vencida ? ' <span class="badge b-roj">vencido</span>' : ''}</td></tr>`).join('')}</table>`
    : '<div class="vacio">Nada programado en las máquinas para estos 3 días</div>';
  try { S.maqIds = Object.fromEntries((await api('/api/mant/maquinas')).maquinas.map(z => [z.nombre, z.id])); } catch (e) { }
}

/* =====================================================================  PARADAS (todas) */
async function vMantParadas(qs = '') {
  const prm = new URLSearchParams(qs);
  const f0 = { desde: prm.get('desde') || new Date(Date.now() - 90 * 864e5).toISOString().slice(0, 10), hasta: prm.get('hasta') || hoyISO(),
    maquina: prm.get('maquina') || '', causa: prm.get('causa') || '', tipo: prm.get('tipo') || '', proyecto_id: prm.get('proyecto_id') || '' };
  const m = shell('mantparadas', migasMant('Paradas'),
    `${puede(REPORTA_MANT) ? `<button class="btn" id="bpar">${ic('mas', 15)} Registrar parada</button>` : ''}<a class="btn" id="bxls" href="#">${ic('hoja', 15)} Exportar a Excel</a>`);
  const q = new URLSearchParams(Object.entries(f0).filter(([, v]) => v)).toString();
  const d = await api('/api/mant/paradas?' + q);
  $('#bxls').href = '/api/mant/paradas/excel?' + q;
  m.innerHTML = `
  <form class="filtros" id="fpar">
    <label>Desde<input type="date" name="desde" value="${f0.desde}"></label><label>Hasta<input type="date" name="hasta" value="${f0.hasta}"></label>
    <label>Máquina<select name="maquina"><option value="">Todas</option>${S.cat.maquinas.map(x => `<option ${x === f0.maquina ? 'selected' : ''}>${esc(x)}</option>`).join('')}</select></label>
    <label>Causa<select name="causa"><option value="">Todas</option>${S.cat.causas.map(x => `<option ${x === f0.causa ? 'selected' : ''}>${esc(x)}</option>`).join('')}</select></label>
    <label>Tipo<select name="tipo"><option value="">Fallas y planificadas</option><option value="falla" ${f0.tipo === 'falla' ? 'selected' : ''}>Solo fallas</option><option value="planificada" ${f0.tipo === 'planificada' ? 'selected' : ''}>Solo planificadas</option></select></label>
    <label>Proyecto<select name="proyecto_id"><option value="">Todos</option>${S.cat.proyectos.map(p => `<option value="${p.id}" ${String(p.id) === f0.proyecto_id ? 'selected' : ''}>${esc(p.codigo)}</option>`).join('')}</select></label>
    <button class="btn prim">${ic('buscar', 14)} Filtrar</button></form>
  <div class="kpis">${kpi('Paradas', d.n, `${d.n_fallas} fallas · ${d.n - d.n_fallas} planificadas`, '', 'alerta')}
    ${kpi('Horas de máquina perdidas', horas(d.total_horas), `${fmtCorta(f0.desde)} → ${fmtCorta(f0.hasta)}`, d.total_horas ? 'nar' : 'ver', 'reloj')}
    ${kpi('Máquina más afectada', d.por_maquina[0] ? `<span style="font-size:15px">${esc(d.por_maquina[0].clave)}</span>` : '—', d.por_maquina[0] ? horas(d.por_maquina[0].horas) : '', 'roj', 'engranaje')}
    ${kpi('Causa principal', d.por_causa[0] ? `<span style="font-size:15px">${esc(d.por_causa[0].clave)}</span>` : '—', d.por_causa[0] ? `${horas(d.por_causa[0].horas)} · ${d.por_causa[0].n} veces` : '', 'mor', 'llave')}</div>
  ${d.n ? `<div class="tarjeta" style="margin-bottom:14px"><h3>Calendario de paradas <span class="nota">horas perdidas por día</span></h3><div class="cuerpo"><div id="gcal" style="height:${Math.max(170, 150 * Math.ceil(((new Date(f0.hasta) - new Date(f0.desde)) / 864e5 + 1) / 190))}px"></div></div></div>
  <div class="grid g2" style="margin-bottom:14px">
    <div class="tarjeta"><h3>Horas por máquina</h3><div class="cuerpo"><div class="grafico bajo" id="gpm"></div></div></div>
    <div class="tarjeta"><h3>Horas por causa (Pareto)</h3><div class="cuerpo"><div class="grafico bajo" id="gpc"></div></div></div></div>` : ''}
  <div class="tarjeta"><h3>Todas las paradas <span class="nota">${d.n} registros</span></h3><div class="cuerpo scroll" style="max-height:560px">${d.n ? `<table class="tabla"><tr><th>Máquina</th><th>Inicio</th><th>Fin</th><th class="num">Horas</th><th>Tipo</th><th>Causa</th><th>OT</th><th>Observación</th><th>Registró</th><th>Orden</th></tr>
    ${d.filas.map(p => `<tr><td>${esc(p.maquina)}</td><td>${esc(p.inicio)}</td><td>${esc(p.fin)}</td><td class="num">${fmtNum(p.horas, 1)}</td><td>${p.planificada ? '<span class="badge b-az">Planificada</span>' : '<span class="badge b-roj">Falla</span>'}</td>
      <td>${esc(p.causa)}</td><td>${esc(p.proyecto || '—')}</td><td class="nota">${esc(p.observacion || '')}</td><td class="nota">${esc(p.usuario || '')}</td>
      <td>${p.orden_id ? `<a href="#/mantordenes?o=${p.orden_id}">OM-${p.orden_id}</a>` : !p.planificada && puede(REPORTA_MANT) ? `<button class="btn peq" data-om="${p.id}">Crear orden</button>` : '—'}</td></tr>`).join('')}</table>`
    : '<div class="vacio">No hay paradas con estos filtros</div>'}</div></div>`;
  $('#fpar').onsubmit = e => { e.preventDefault(); location.hash = '#/mantparadas?' + new URLSearchParams([...new FormData(e.target)].filter(([, v]) => v)).toString(); };
  if (d.n) {
    const porDia = {}; d.filas.forEach(p => { const k = p.inicio.slice(0, 10); porDia[k] = (porDia[k] || 0) + (p.horas || 0); });
    const anchoCal = Math.ceil(((new Date(f0.hasta) - new Date(f0.desde)) / 864e5 + 1));
    chart($('#gcal'), { tooltip: { formatter: p => `${fmtCorta(p.value[0])}: ${fmtNum(p.value[1], 1)} h` },
      visualMap: { min: 0, max: Math.max(4, ...Object.values(porDia)), orient: 'horizontal', left: 'center', bottom: 0, itemHeight: 120, calculable: true, inRange: { color: [C.acentoM, C.ambar, C.rojo] }, textStyle: { color: C.gris } },
      calendar: { range: [f0.desde, f0.hasta], top: 26, left: 40, right: 20, cellSize: ['auto', anchoCal > 200 ? 13 : 18], yearLabel: { show: false }, dayLabel: { firstDay: 1, nameMap: ['D', 'L', 'M', 'M', 'J', 'V', 'S'], color: C.gris },
        monthLabel: { nameMap: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'], color: C.gris }, itemStyle: { color: css('--hover'), borderColor: css('--panel'), borderWidth: 2 }, splitLine: { show: false } },
      series: [{ type: 'heatmap', coordinateSystem: 'calendar', data: Object.entries(porDia).map(([k, v]) => [k, +v.toFixed(1)]) }] });
    chart($('#gpm'), { grid: { left: 190, right: 40, top: 8, bottom: 20 }, tooltip: { valueFormatter: v => v + ' h' }, xAxis: { type: 'value' }, yAxis: { type: 'category', data: d.por_maquina.map(z => z.clave).reverse() },
      series: [{ type: 'bar', barWidth: 14, data: d.por_maquina.map(z => z.horas).reverse(), itemStyle: { color: C.acento }, label: { show: true, position: 'right', formatter: '{c} h' } }] });
    let acum = 0; const tot = d.total_horas || 1;
    chart($('#gpc'), { grid: { left: 46, right: 46, top: 20, bottom: 60 }, tooltip: { trigger: 'axis' }, xAxis: { type: 'category', data: d.por_causa.map(z => z.clave), axisLabel: { rotate: 30, interval: 0, fontSize: 10 } },
      yAxis: [{ type: 'value', name: 'h' }, { type: 'value', max: 100, axisLabel: { formatter: '{value} %' }, splitLine: { show: false } }],
      series: [{ type: 'bar', name: 'Horas', data: d.por_causa.map(z => ({ value: z.horas, itemStyle: { color: /preventivo/i.test(z.clave) ? C.acento : C.rojo } })), barWidth: '50%' },
        { type: 'line', name: '% acumulado', yAxisIndex: 1, data: d.por_causa.map(z => +((acum += z.horas) / tot * 100).toFixed(1)), itemStyle: { color: C.ambar }, lineStyle: { color: C.ambar } }] });
  }
  $$('[data-om]', m).forEach(b => b.onclick = async () => {
    const p = d.filas.find(z => z.id === +b.dataset.om);
    const mq = (await api('/api/mant/maquinas')).maquinas.find(z => z.nombre === p.maquina);
    modal(`Orden correctiva para la parada de ${esc(p.maquina)}`, `<div class="form"><label class="ancho">Qué se debe reparar<input name="titulo" required minlength="3" value="${esc(p.causa)}"></label>
      <label class="ancho">Detalle<textarea name="descripcion" rows="2">${esc(p.observacion || '')}</textarea></label><p class="nota ancho">La orden queda enlazada a esta parada; al cerrarla no se duplica la parada.</p></div>`,
    async f => { await api('/api/mant/ordenes', { method: 'POST', body: { maquina_id: mq.id, tipo: 'CORRECTIVO', titulo: f.get('titulo'), descripcion: f.get('descripcion') || null, parada_id: p.id } }); toast('Orden creada'); vMantParadas(qs); }, 'Crear orden');
  });
  const bp = $('#bpar'); if (bp) bp.onclick = () => modal('Registrar parada de máquina', `<div class="form">
      <label class="ancho">Máquina<select name="maquina">${S.cat.maquinas.map(x => `<option>${esc(x)}</option>`).join('')}</select></label>
      <label>Inicio<input name="inicio" type="datetime-local" max="${ahoraLocal()}" required></label><label>Fin<input name="fin" type="datetime-local" max="${ahoraLocal()}" required></label>
      <label class="ancho">Causa<select name="causa">${S.cat.causas.map(x => `<option>${esc(x)}</option>`).join('')}</select></label>
      <label class="chk ancho"><input type="checkbox" name="planificada"> Fue planificada (preventivo, setup programado)</label>
      <label class="ancho">Proyecto afectado<select name="proyecto_id"><option value="">—</option>${S.cat.proyectos.map(p => `<option value="${p.id}">${esc(p.codigo)}</option>`).join('')}</select></label>
      <label class="ancho">Observación<textarea name="observacion" rows="2"></textarea></label></div>`,
  async f => { await api('/api/paradas', { method: 'POST', body: { maquina: f.get('maquina'), inicio: f.get('inicio').replace('T', ' '), fin: f.get('fin').replace('T', ' '), planificada: !!f.get('planificada'),
    causa: f.get('causa'), proyecto_id: f.get('proyecto_id') ? +f.get('proyecto_id') : null, observacion: f.get('observacion') || null } }); toast('Parada registrada'); vMantParadas(qs); }, 'Registrar');
}

/* =====================================================================  ÓRDENES Y PLAN PREVENTIVO */
async function vMantOrdenes(qs = '') {
  const prm = new URLSearchParams(qs);
  const tab = prm.get('tab') === 'plan' ? 'plan' : 'om';
  const m = shell('mantordenes', migasMant('Órdenes y plan preventivo'),
    `${puede(REPORTA_MANT) ? `<button class="btn roj" id="bfalla">${ic('alerta', 15)} Reportar falla</button>` : ''}${puede(EDITA_MANT) ? `<button class="btn prim" id="bnuevo">${ic('mas', 15)} ${tab === 'plan' ? 'Agregar tarea preventiva' : 'Nueva orden'}</button>` : ''}`);
  const [os, pls, mq] = await Promise.all([api('/api/mant/ordenes'), api('/api/mant/planes'), api('/api/mant/maquinas')]);
  const maqs = mq.maquinas;
  m.innerHTML = `
  <div class="pestanas"><a class="${tab === 'om' ? 'activo' : ''}" href="#/mantordenes">${ic('llave', 15)} Órdenes de mantenimiento (${os.filter(o => o.estado === 'PENDIENTE' || o.estado === 'EN_CURSO').length} abiertas)</a>
    <a class="${tab === 'plan' ? 'activo' : ''}" href="#/mantordenes?tab=plan">${ic('reloj', 15)} Plan preventivo (${pls.filter(p => p.activo).length})</a></div>
  ${tab === 'om' ? `<div class="kanban">${EST_OM.map(([k, t]) => { const col = os.filter(o => o.estado === k).slice(0, k === 'CERRADA' ? 25 : 999); return `
    <div class="col"><h4>${t}<span class="n">${os.filter(o => o.estado === k).length}</span></h4>${col.map(o => `
      <div class="ficha ${o.tipo === 'CORRECTIVO' ? 'p1' : o.vencida ? 'p2' : 'p3'}" data-o="${o.id}" style="cursor:pointer"><div class="id">OM-${o.id} · ${esc(o.maquina)}</div><div class="tit">${esc(o.titulo)}</div>
        <div class="pie"><span class="badge ${TIPO_OM[o.tipo][1]}">${TIPO_OM[o.tipo][0]}</span>${o.programada_para ? `<span>${ic('reloj', 12)} ${fmtCorta(o.programada_para)}</span>` : ''}${o.vencida ? '<span class="badge b-roj">vencida</span>' : ''}
        ${o.estado === 'CERRADA' && o.inicio && o.fin ? `<span>${fmtNum((new Date(o.fin.replace(' ', 'T')) - new Date(o.inicio.replace(' ', 'T'))) / 36e5, 1)} h</span>` : ''}${o.tecnico ? `<span class="nota">${esc(o.tecnico)}</span>` : ''}</div></div>`).join('') || '<p class="nota" style="padding:6px">Nada aquí</p>'}</div>`; }).join('')}</div>
    <p class="nota">Las órdenes preventivas se crean solas cuando una tarea del plan vence en los próximos 10 días laborables. Al cerrar una orden queda registrada su parada y se programa la siguiente.</p>`
  : `<div class="tarjeta"><div class="cuerpo">${tablaPlanes(pls, true)}</div></div>
    <p class="nota">Plan inicial <span class="badge b-gris">sugerido</span>: frecuencias típicas de fabricante, para validar con el jefe de taller. La frecuencia en horas se convierte a días con el turno completo hasta tener horómetro.</p>`}`;
  $$('[data-o]', m).forEach(c => c.onclick = () => panelOrden(os.find(o => o.id === +c.dataset.o), () => vMantOrdenes(qs)));
  if (prm.get('o')) { const o = os.find(z => z.id === +prm.get('o')); if (o) panelOrden(o, () => vMantOrdenes(tab === 'plan' ? 'tab=plan' : '')); }
  $$('[data-plan]', m).forEach(b => b.onclick = () => modalPlan(maqs, pls.find(p => p.id === +b.dataset.plan), () => vMantOrdenes('tab=plan')));
  $$('[data-act]', m).forEach(b => b.onclick = async () => { try { await api('/api/mant/planes/' + b.dataset.act, { method: 'PATCH', body: { activo: b.dataset.v === '1' } }); vMantOrdenes('tab=plan'); } catch (e) { toast(e.message, 1); } });
  const bf = $('#bfalla'); if (bf) bf.onclick = () => modalFalla(maqs, null, () => vMantOrdenes(qs));
  const bn = $('#bnuevo'); if (bn) bn.onclick = () => tab === 'plan' ? modalPlan(maqs, null, () => vMantOrdenes('tab=plan')) : modalOrden(null, () => vMantOrdenes(qs), maqs);
}
function tablaPlanes(pls, acciones) {
  if (!pls.length) return '<div class="vacio">Sin tareas preventivas</div>';
  const vence = p => p.dias_para_vencer == null ? '—' : p.dias_para_vencer < 0 ? `<span class="badge b-roj">vencida hace ${-p.dias_para_vencer} d</span>` : p.dias_para_vencer <= 3 ? `<span class="badge b-nar">en ${p.dias_para_vencer} d</span>` : `en ${p.dias_para_vencer} d`;
  return `<table class="tabla"><tr>${acciones ? '<th>Máquina</th>' : ''}<th>Tarea</th><th>Frecuencia</th><th class="num">Duración</th><th>Última vez</th><th>Próxima</th><th>Falta</th><th>Estado</th>${acciones && puede(EDITA_MANT) ? '<th></th>' : ''}</tr>
    ${pls.map(p => `<tr class="${p.activo ? '' : 'inactivo'}">${acciones ? `<td>${esc(p.maquina)}</td>` : ''}<td style="min-width:240px">${esc(p.tarea)}${p.origen === 'sugerido' ? ' <span class="badge b-gris">sugerido</span>' : ''}</td>
      <td>${p.frecuencia_dias ? `cada ${p.frecuencia_dias} días` : `cada ${fmtNum(p.frecuencia_horas)} h de uso`}</td><td class="num">${horas(p.duracion_h)}</td><td>${fmtCorta(p.ultima)}</td><td>${p.activo ? fmtCorta(p.vence) : '—'}</td><td>${p.activo ? vence(p) : '—'}</td>
      <td>${p.activo ? '<span class="badge b-ver">Activa</span>' : '<span class="badge b-gris">Inactiva</span>'}</td>
      ${acciones && puede(EDITA_MANT) ? `<td style="white-space:nowrap"><button class="btn peq" data-plan="${p.id}">Editar</button> <button class="btn peq" data-act="${p.id}" data-v="${p.activo ? 0 : 1}">${p.activo ? 'Desactivar' : 'Activar'}</button></td>` : ''}</tr>`).join('')}</table>`;
}
function modalPlan(maqs, p, alTerminar) {
  const enHoras = p && !p.frecuencia_dias && p.frecuencia_horas;
  modal(p ? 'Editar tarea preventiva' : 'Agregar tarea preventiva', `<div class="form">
    ${p ? `<p class="ancho"><b>${esc(p.maquina)}</b></p>` : `<label class="ancho">Máquina<select name="maquina_id">${maqs.map(x => `<option value="${x.id}">${esc(x.nombre)}</option>`).join('')}</select></label>`}
    <label class="ancho">Tarea<input name="tarea" required minlength="3" value="${esc(p?.tarea || '')}" placeholder="Lubricación, cambio de hoja, calibración..."></label>
    <label>Frecuencia<input name="frec" type="number" min="1" step="1" required value="${p ? (p.frecuencia_dias || p.frecuencia_horas) : 6}"></label>
    <label>Unidad<select name="unidad"><option value="dias">días laborables</option><option value="horas" ${enHoras ? 'selected' : ''}>horas de uso</option></select></label>
    <label>Duración (h)<input name="duracion_h" type="number" min="0.25" step="0.25" required value="${p?.duracion_h || 1}"></label>
    <label>Responsable<input name="responsable" value="${esc(p?.responsable || '')}"></label></div>`,
  async f => {
    const fr = +f.get('frec'), dias = f.get('unidad') === 'dias';
    const b = { tarea: f.get('tarea'), duracion_h: +f.get('duracion_h'), responsable: f.get('responsable') || null, frecuencia_dias: dias ? fr : null, frecuencia_horas: dias ? null : fr };
    if (p) await api('/api/mant/planes/' + p.id, { method: 'PATCH', body: b });
    else await api('/api/mant/planes', { method: 'POST', body: { ...b, maquina_id: +f.get('maquina_id') } });
    toast('Plan guardado'); alTerminar();
  }, 'Guardar');
}
function modalOrden(x, alTerminar, maqs) {
  modal('Nueva orden de mantenimiento', `<div class="form">
    ${x ? `<input type="hidden" name="maquina_id" value="${x.id}"><p class="ancho"><b>${esc(x.nombre)}</b></p>` : `<label class="ancho">Máquina<select name="maquina_id">${maqs.map(z => `<option value="${z.id}">${esc(z.nombre)}</option>`).join('')}</select></label>`}
    <label>Tipo<select name="tipo">${Object.entries(TIPO_OM).map(([k, v]) => `<option value="${k}">${v[0]}</option>`).join('')}</select></label>
    <label>Programada para<input name="programada_para" type="date" value="${hoyISO()}"></label>
    <label class="ancho">Título<input name="titulo" required minlength="3"></label>
    <label>Duración estimada (h)<input name="duracion_h" type="number" min="0.25" step="0.25" value="1"></label><label>Técnico<input name="tecnico"></label>
    <label class="ancho">Detalle<textarea name="descripcion" rows="2"></textarea></label></div>`,
  async f => { await api('/api/mant/ordenes', { method: 'POST', body: { maquina_id: +f.get('maquina_id'), tipo: f.get('tipo'), titulo: f.get('titulo'), programada_para: f.get('programada_para') || null,
    duracion_h: f.get('duracion_h') ? +f.get('duracion_h') : null, tecnico: f.get('tecnico') || null, descripcion: f.get('descripcion') || null } }); toast('Orden creada'); alTerminar(); }, 'Crear orden');
}
function panelOrden(o, recargar) {
  const v = document.createElement('div'); v.className = 'velo';
  const p = document.createElement('aside'); p.className = 'lateral';
  const edita = puede(EDITA_MANT), abierta = o.estado === 'PENDIENTE' || o.estado === 'EN_CURSO';
  p.innerHTML = `<header><div><div class="nota">OM-${o.id} · ${esc(o.maquina)}</div><b style="font-size:15px">${esc(o.titulo)}</b></div><button class="icono-btn" id="pcerrar">${ic('cerrar', 16)}</button></header>
  <div class="cuerpo">
    <div><span class="badge ${TIPO_OM[o.tipo][1]}">${TIPO_OM[o.tipo][0]}</span> <span class="badge b-gris">${esc(o.estado.replace('_', ' ').toLowerCase())}</span>${o.vencida ? ' <span class="badge b-roj">vencida</span>' : ''}${o.parada_id ? ` <span class="nota">parada #${o.parada_id}</span>` : ''}</div>
    ${o.descripcion ? `<p>${esc(o.descripcion)}</p>` : ''}
    <form class="form" id="fom">
      <label>Programada para<input name="programada_para" type="date" value="${(o.programada_para || '').slice(0, 10)}" ${abierta && edita ? '' : 'disabled'}></label>
      <label>Duración estimada (h)<input name="duracion_h" type="number" step="0.25" min="0.25" value="${o.duracion_h || ''}" ${abierta && edita ? '' : 'disabled'}></label>
      <label>Inicio real<input name="inicio" type="datetime-local" max="${ahoraLocal()}" value="${(o.inicio || '').replace(' ', 'T')}" ${abierta && edita ? '' : 'disabled'}></label>
      <label>Fin real<input name="fin" type="datetime-local" max="${ahoraLocal()}" value="${(o.fin || '').replace(' ', 'T')}" ${abierta && edita ? '' : 'disabled'}></label>
      <label>Técnico<input name="tecnico" value="${esc(o.tecnico || '')}" ${edita ? '' : 'disabled'}></label>
      <label>Costo (S/)<input name="costo" type="number" min="0" step="0.01" value="${o.costo ?? ''}" ${edita ? '' : 'disabled'}></label>
      <label class="ancho">Repuestos usados<input name="repuestos" value="${esc(o.repuestos || '')}" ${edita ? '' : 'disabled'}></label>
      ${o.tipo === 'CORRECTIVO' && abierta && !o.parada_id ? `<label class="ancho">Causa de la falla<select name="causa">${S.cat.causas.filter(c => !/preventivo/i.test(c)).map(c => `<option>${esc(c)}</option>`).join('')}</select></label>` : ''}
    </form>
    ${edita ? `<div class="botones">${abierta ? `<button class="btn" id="bguardar">${ic('check', 14)} Guardar</button>
      ${o.estado === 'PENDIENTE' ? `<button class="btn" id="biniciar">${ic('rayo', 14)} Iniciar ahora</button>` : ''}
      <button class="btn prim" id="bcerrar">${ic('check', 14)} Cerrar orden</button><button class="btn" id="banular">Anular</button>` : `<button class="btn" id="bguardar">${ic('check', 14)} Guardar datos</button>`}</div>
      ${abierta ? '<p class="nota">Para cerrar, indica cuándo empezó y terminó la intervención (si falta el fin, se usa la hora actual). Queda registrada como parada de la máquina.</p>' : ''}`
    : '<p class="nota">Solo el jefe de taller o mantenimiento actualizan las órdenes.</p>'}
  </div>`;
  document.body.append(v, p);
  const cerrar = () => { v.remove(); p.remove(); };
  v.onclick = cerrar; $('#pcerrar', p).onclick = cerrar;
  const leer = () => { const f = new FormData($('#fom', p)); const b = {};
    for (const [k, x] of f) if (x !== '') b[k] = ['duracion_h', 'costo'].includes(k) ? +x : k === 'inicio' || k === 'fin' ? x.replace('T', ' ') : x;
    return b; };
  const enviar = async extra => { try { await api('/api/mant/ordenes/' + o.id, { method: 'PATCH', body: { ...leer(), ...extra } }); toast('Orden actualizada'); cerrar(); recargar(); } catch (e) { toast(e.message, 1); } };
  const b = id => $(id, p);
  if (b('#bguardar')) b('#bguardar').onclick = () => enviar({});
  if (b('#biniciar')) b('#biniciar').onclick = () => enviar({ estado: 'EN_CURSO', inicio: ahoraLocal().replace('T', ' ') });
  if (b('#bcerrar')) b('#bcerrar').onclick = () => enviar({ estado: 'CERRADA' });
  if (b('#banular')) b('#banular').onclick = () => { if (confirm('¿Anular esta orden? No se registra ninguna parada.')) enviar({ estado: 'ANULADA' }); };
}
