/* SteelPlan · Programación automática de la cartera (v3.1): plan aprobado vs. propuesto, aprobación, simulador
   "¿cabe un proyecto nuevo?" y Gantt maestro (proyectos arriba, carga de las 4 máquinas abajo).
   Usa los helpers de app.js; se carga antes que app.js y solo se ejecuta al navegar. */
'use strict';
const PROPONEN_P = ['jefe_taller', 'cotizador', 'mantenimiento'];
const APRUEBAN_P = ['jefe_taller'];
const REGLA_T = { penalidad: 'Penalidad en riesgo (recomendada)', edd: 'Fecha comprometida más cercana' };
const probBadge = (p, a = 0.8) => p == null ? '<span class="nota">sin fecha</span>' : `<span class="badge ${p >= a ? 'b-ver' : p >= 0.6 ? 'b-nar' : 'b-roj'}">${pct(p)}</span>`;
const holgura = x => { if (!x.compromiso) return '—'; const d = Math.round((new Date(x.compromiso) - new Date(x.p80)) / 864e5); return d >= 0 ? `${d} d` : `<b style="color:var(--rojo)">${d} d</b>`; };

async function vProgramacion(qs = '') {
  const prm = new URLSearchParams(qs);
  const m = shell('programacion', `${ic('gantt', 20)} <a href="#/proyectos">Proyectos</a><span class="sep">/</span>Programación de la cartera`,
    `${puede(PROPONEN_P) ? `<select id="regla">${Object.entries(REGLA_T).map(([k, t]) => `<option value="${k}">${t}</option>`).join('')}</select>
      <button class="btn" id="bsim">${ic('chispa', 15)} ¿Cabe un proyecto nuevo?</button><button class="btn prim" id="bprop">${ic('rayo', 15)} Recalcular propuesta</button>` : ''}`);
  const d = await api('/api/programacion');
  const ap = d.aprobado, pr = d.propuesto;
  const ver = prm.get('ver') || (pr && (!ap || pr.id > ap.id) ? 'prop' : 'apr');
  const plan = ver === 'prop' && pr ? pr : ap || pr;
  if ($('#regla')) $('#regla').value = (plan && plan.regla) || 'penalidad';
  if (!plan) {
    m.innerHTML = `<div class="tarjeta"><div class="cuerpo vacio">${ic('gantt', 36)}<p>Todavía no hay un plan de la cartera.<br>El sistema programa juntos todos los proyectos en curso sobre las 4 máquinas, con los preventivos y las fallas registradas.</p>
      ${puede(PROPONEN_P) ? `<button class="btn prim" id="bprop2">${ic('rayo', 15)} Calcular el primer plan</button>` : '<p class="nota">Lo calcula el jefe de taller, el cotizador o mantenimiento.</p>'}</div></div>`;
    enlazarProg(d); return;
  }
  const r = plan.resultado, P = r.proyectos;
  const riesgo = P.filter(x => x.prob_cumplir != null && x.prob_cumplir < x.alpha);
  const pen = P.reduce((s, x) => s + (x.penalidad || 0), 0);
  const finCartera = P.reduce((s, x) => x.p80 > s ? x.p80 : s, '');
  const propNueva = pr && (!ap || pr.id > ap.id);
  m.innerHTML = `
  ${ap && d.vigencia.desactualizado ? `<div class="aviso">${ic('alerta', 16)} El plan aprobado #${ap.id} quedó desactualizado: cambiaron ${esc(d.vigencia.cambios.join(', '))}. ${propNueva ? 'Hay una propuesta nueva abajo.' : 'Se recalculará solo en unos minutos, o pulsa «Recalcular propuesta».'}</div>` : ''}
  ${propNueva ? tarjetaPropuesta(pr, ap) : ''}
  <div class="pestanas"><a class="${plan === ap ? 'activo' : ''}" href="#/programacion?ver=apr" ${ap ? '' : 'style="pointer-events:none;opacity:.5"'}>${ic('check', 15)} Plan aprobado${ap ? ` #${ap.id}` : ' (ninguno)'}</a>
    ${pr ? `<a class="${plan === pr ? 'activo' : ''}" href="#/programacion?ver=prop">${ic('rayo', 15)} Propuesta #${pr.id}</a>` : ''}</div>
  <div class="kpis">
    ${kpi('Proyectos programados', P.length, `regla: ${esc((REGLA_T[plan.regla] || plan.regla).split(' (')[0].toLowerCase())}`, '', 'proyectos')}
    ${kpi('En riesgo', riesgo.length, riesgo.length ? riesgo.map(x => esc(x.codigo)).join(', ') : 'todos cumplen con su confianza', riesgo.length ? 'roj' : 'ver', 'alerta')}
    ${kpi('Penalidad esperada total', 'USD ' + fmtNum(pen), 'suma de la cartera con este plan', pen > 0 ? 'nar' : 'ver', 'reloj')}
    ${kpi('Fin de la cartera (P80)', fmtCorta(finCartera), `${d.reprogramaciones} reprogramaciones aprobadas`, 'mor', 'gantt')}</div>
  <div class="tarjeta" style="margin-bottom:14px"><h3>Cartera en orden de prioridad <span class="nota">${esc(plan.estado === 'APROBADO' ? `aprobado ${String(plan.aprobado_en || '').slice(0, 16)}` : `propuesto ${String(plan.creado_en).slice(0, 16)} · ${plan.motivo}`)}</span></h3>
    <div class="cuerpo"><table class="tabla"><tr><th>#</th><th>OT</th><th>Comprometida</th><th>Fin probable (P50)</th><th>Fin con 80 % (P80)</th><th>Holgura</th><th>P(cumplir)</th><th class="num">Penalidad esperada</th><th></th></tr>
      ${P.map(x => `<tr class="clic" data-cod="${esc(x.codigo)}"><td><b>${x.prioridad}</b></td><td><b>${esc(x.codigo)}</b></td><td>${fmtCorta(x.compromiso)}</td><td>${fmtFecha(x.p50)}</td><td>${fmtFecha(x.p80)}</td><td>${holgura(x)}</td>
        <td>${probBadge(x.prob_cumplir, x.alpha)}</td><td class="num">${fmtNum(x.penalidad)}</td><td>${x.id ? `<a href="#/proyecto/a/${x.id}" class="nota">abrir</a>` : ''}</td></tr>`).join('')}</table>
      <p class="nota">Holgura = fecha comprometida − fin P80, en días calendario. La prioridad la decide la regla, igual para todos los proyectos. Clic en una fila para ver sus procesos.</p></div></div>
  <div class="tarjeta" style="margin-bottom:14px"><h3>Gantt maestro <span class="leyenda" style="margin:0"><span><i style="background:${C.acento}"></i>Hasta el fin P50</span><span><i style="background:${C.acentoM}"></i>P50 → P80</span><span><i style="background:${C.rojo};transform:rotate(45deg)"></i>Fecha comprometida</span><span><i style="background:${C.verde}"></i>Carga &lt; 70 %</span><span><i style="background:${C.ambar}"></i>70–95 %</span><span><i style="background:${C.rojo}"></i>Saturada</span><span><i style="background:${C.gris}"></i>Sin capacidad</span></span></h3>
    <div class="cuerpo"><div id="gmaestro" style="height:${140 + 44 * P.length + 40 * r.carga.length}px"></div><div id="gproc"></div></div></div>
  <div class="tarjeta"><h3>Historial de planes <span class="nota">se guardan todos: sirven para medir cuánto se reprograma</span></h3><div class="cuerpo scroll" style="max-height:300px"><table class="tabla"><tr><th>#</th><th>Fecha</th><th>Motivo</th><th>Regla</th><th>Estado</th><th class="num">Cambios</th><th class="num">Avisos</th><th>Aprobó</th></tr>
    ${d.historial.map(h => `<tr><td>${h.id}</td><td>${esc(String(h.creado_en).slice(0, 16))}</td><td>${esc(h.motivo)}</td><td class="nota">${esc((REGLA_T[h.regla] || h.regla).split(' (')[0])}</td>
      <td><span class="badge ${{ APROBADO: 'b-ver', PROPUESTO: 'b-az', DESCARTADO: 'b-gris', REEMPLAZADO: 'b-gris' }[h.estado]}">${h.estado.toLowerCase()}</span></td><td class="num">${h.n_cambios}</td><td class="num">${h.n_avisos ? `<span class="badge b-roj">${h.n_avisos}</span>` : 0}</td><td class="nota">${esc(h.aprobado_por || '')}</td></tr>`).join('')}</table></div></div>`;
  ganttMaestro(r);
  $$('tr[data-cod]', m).forEach(tr => tr.onclick = e => { if (!e.target.closest('a')) detalleProcesos(P.find(x => x.codigo === tr.dataset.cod)); });
  enlazarProg(d);
}

function tarjetaPropuesta(pr, ap) {
  const r = pr.resultado;
  return `<div class="tarjeta propuesta" style="margin-bottom:14px"><h3>${ic('rayo', 16)} Propuesta #${pr.id} para aprobar <span class="nota">${esc(String(pr.creado_en).slice(0, 16))} · ${esc(pr.motivo)}</span></h3><div class="cuerpo">
    ${pr.avisos.length ? `<div class="semaforo ROJO" style="margin-bottom:10px"><span class="luz"></span><div><b>Atención:</b> ${pr.avisos.map(a => esc(a.texto)).join(' · ')}</div></div>` : ''}
    ${!ap ? '<p>Es el primer plan de la cartera.</p>' : pr.cambios.length ? `<table class="tabla"><tr><th>OT</th><th>Fin P80 aprobado</th><th>Fin P80 propuesto</th><th class="num">Días</th><th>Prioridad</th><th>P(cumplir)</th></tr>
      ${pr.cambios.map(c => c.cambio ? `<tr><td><b>${esc(c.codigo)}</b></td><td colspan="5">${esc(c.cambio)}</td></tr>` : `<tr><td><b>${esc(c.codigo)}</b></td><td>${fmtCorta(c.p80_antes)}</td><td>${fmtCorta(c.p80_despues)}</td>
        <td class="num">${c.dias > 0 ? `<b style="color:var(--rojo)">+${c.dias}</b>` : c.dias}</td><td>${c.prioridad_antes} → ${c.prioridad_despues}</td><td>${c.prob_antes == null ? '—' : pct(c.prob_antes)} → ${c.prob_despues == null ? '—' : pct(c.prob_despues)}</td></tr>`).join('')}</table>`
      : '<p class="nota">Sin cambios relevantes respecto del plan aprobado (ninguna fecha P80 se mueve ni cambia la prioridad).</p>'}
    ${r.sugerencias.length ? `<h4 style="margin:12px 0 6px">Preventivos que conviene mover</h4><table class="tabla"><tr><th></th><th>Orden</th><th>Máquina</th><th>De</th><th>A</th><th>Para salvar</th><th>P(cumplir)</th></tr>
      ${r.sugerencias.map(s => `<tr><td><input type="checkbox" class="smov" value="${s.orden_id}"></td><td>OM-${s.orden_id} ${esc(s.titulo || '')}</td><td>${esc(s.maquina)}</td><td>${fmtCorta(s.de)}</td><td>${fmtCorta(s.a)}</td><td>${esc(s.proyecto)}</td><td>${pct(s.prob_antes)} → <b>${pct(s.prob_despues)}</b></td></tr>`).join('')}</table>
      <p class="nota">Marca los que aceptas: se reprograman al aprobar. Mover un preventivo aumenta el riesgo de falla de esa máquina.</p>` : ''}
    ${puede(APRUEBAN_P) ? `<div style="display:flex;gap:8px;margin-top:12px"><button class="btn prim" id="baprobar">${ic('check', 15)} Aprobar plan #${pr.id}</button><button class="btn" id="bdescartar">Descartar</button>
      <a class="btn" href="#/programacion?ver=prop">${ic('gantt', 15)} Ver en el Gantt</a></div>` : '<p class="nota">El jefe de taller aprueba los planes.</p>'}</div></div>`;
}

function enlazarProg(d) {
  const recalc = async () => { const b = $('#bprop') || $('#bprop2'); if (b) b.disabled = true;
    try { await api('/api/programacion/proponer', { method: 'POST', body: { regla: ($('#regla') || {}).value || 'penalidad', motivo: 'manual' } }); toast('Propuesta calculada'); location.hash = '#/programacion?ver=prop'; vProgramacion('ver=prop'); }
    catch (e) { toast(e.message, 1); } finally { if (b) b.disabled = false; } };
  if ($('#bprop')) $('#bprop').onclick = recalc;
  if ($('#bprop2')) $('#bprop2').onclick = recalc;
  if ($('#bsim')) $('#bsim').onclick = modalSimular;
  if ($('#baprobar')) $('#baprobar').onclick = async () => {
    const mover = $$('.smov:checked').map(c => +c.value);
    try { await api(`/api/programacion/${d.propuesto.id}/aprobar`, { method: 'POST', body: { mover_preventivos: mover } }); toast('Plan aprobado'); location.hash = '#/programacion?ver=apr'; vProgramacion('ver=apr'); } catch (e) { toast(e.message, 1); } };
  if ($('#bdescartar')) $('#bdescartar').onclick = async () => { await api(`/api/programacion/${d.propuesto.id}/descartar`, { method: 'POST' }); toast('Propuesta descartada'); location.hash = '#/programacion?ver=apr'; vProgramacion('ver=apr'); };
}

function detalleProcesos(x) {
  $('#gproc').innerHTML = `<h4 style="margin:10px 0 6px">${esc(x.codigo)} · procesos (P50)</h4><table class="tabla"><tr><th>Proceso</th><th>Inicio</th><th>Fin</th><th class="num">HH que faltan</th></tr>
    ${x.procesos.map(p => { const pc = S.cat.procesos[p.proceso - 1]; return `<tr><td><i style="display:inline-block;width:10px;height:10px;margin-right:6px;background:${CAT[pc.categoria][1]}"></i>${esc(pc.nombre)}</td><td>${fmtCorta(p.inicio)}</td><td>${fmtCorta(p.fin)}</td><td class="num">${fmtNum(p.hh)}</td></tr>`; }).join('')}</table>`;
  $('#gproc').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function ganttMaestro(r) {
  const P = r.proyectos, M = r.carga, t = s => new Date(s + 'T00:00').getTime(), DIA = 864e5;
  const filasP = P.map(x => x.codigo), filasM = M.map(c => c.maquina);
  const dataP = P.map((x, i) => ({ value: [i, t(x.inicio), t(x.p50) + DIA, t(x.p80) + DIA, x.compromiso ? t(x.compromiso) + DIA / 2 : null] }));
  const dataM = [];
  M.forEach((c, k) => c.horas.forEach((h, j) => { const cap = c.capacidad[j]; dataM.push({ value: [k, t(r.fechas[j]), t(r.fechas[j]) + DIA, cap <= 0.01 ? -1 : h / cap, h, cap] }); }));
  const fin = Math.max(...P.map(x => t(x.p80)), ...P.filter(x => x.compromiso).map(x => t(x.compromiso))) + 5 * DIA;
  const colorCarga = u => u < 0 ? C.gris : u < 0.7 ? C.verde : u < 0.95 ? C.ambar : C.rojo;
  chart($('#gmaestro'), {
    tooltip: { formatter: p => {
      if (p.seriesIndex === 0) { const x = P[p.value[0]]; return `<b>${esc(x.codigo)}</b> · prioridad ${x.prioridad}<br>Inicio ${fmtCorta(x.inicio)}<br>P50 ${fmtCorta(x.p50)} · P80 ${fmtCorta(x.p80)}<br>Comprometida ${fmtCorta(x.compromiso)}<br>P(cumplir) ${x.prob_cumplir == null ? '—' : pct(x.prob_cumplir)}`; }
      const v = p.value; return `<b>${esc(filasM[v[0]])}</b><br>${fmtCorta(new Date(v[1]).toISOString().slice(0, 10))}: ${v[3] < 0 ? 'sin capacidad (preventivo o parada)' : `${fmtNum(v[4], 1)} de ${fmtNum(v[5], 1)} h (${Math.round(100 * v[3])} %)`}`; } },
    grid: [{ left: 120, right: 24, top: 30, height: 44 * P.length }, { left: 120, right: 24, top: 60 + 44 * P.length, height: 40 * M.length }],
    xAxis: [{ type: 'time', gridIndex: 0, position: 'top', min: t(r.hoy), max: fin, splitLine: { show: true }, axisLabel: { formatter: { month: '{dd}/{MM}', day: '{dd}/{MM}' }, hideOverlap: true } },
      { type: 'time', gridIndex: 1, min: t(r.hoy), max: fin, axisLabel: { show: false }, splitLine: { show: true } }],
    yAxis: [{ type: 'category', gridIndex: 0, data: filasP, inverse: true, axisTick: { show: false }, axisLabel: { fontWeight: 600 } },
      { type: 'category', gridIndex: 1, data: filasM, inverse: true, axisTick: { show: false }, axisLabel: { width: 110, overflow: 'truncate', fontSize: 11 } }],
    dataZoom: [{ type: 'inside', xAxisIndex: [0, 1], filterMode: 'weakFilter' }],
    series: [
      { type: 'custom', xAxisIndex: 0, yAxisIndex: 0, data: dataP, encode: { x: [1, 3], y: 0 }, renderItem: (params, a) => {
        const y = a.coord([a.value(1), a.value(0)])[1], alto = a.size([0, 1])[1] * 0.42;
        const x0 = a.coord([a.value(1), 0])[0], x50 = a.coord([a.value(2), 0])[0], x80 = a.coord([a.value(3), 0])[0];
        const x = P[a.value(0)], tarde = x.compromiso && x.p80 > x.compromiso;
        const hijos = [{ type: 'rect', shape: { x: x0, y: y - alto / 2, width: Math.max(x50 - x0, 2), height: alto }, style: { fill: C.acento } },
          { type: 'rect', shape: { x: x50, y: y - alto / 2, width: Math.max(x80 - x50, 1), height: alto }, style: { fill: C.acentoM } },
          { type: 'text', style: { x: x0 + 6, y, text: `#${x.prioridad} · ${pct(x.prob_cumplir ?? 1)}`, fill: '#fff', fontSize: 10.5, verticalAlign: 'middle' } }];
        if (a.value(4)) { const xc = a.coord([a.value(4), 0])[0]; hijos.push({ type: 'polygon', shape: { points: [[xc, y - alto / 2 - 4], [xc + 6, y], [xc, y + alto / 2 + 4], [xc - 6, y]] }, style: { fill: tarde ? C.rojo : C.verde, stroke: '#fff', lineWidth: 1 } }); }
        return { type: 'group', children: hijos }; } },
      { type: 'custom', xAxisIndex: 1, yAxisIndex: 1, data: dataM, encode: { x: [1, 2], y: 0 }, renderItem: (params, a) => {
        const p0 = a.coord([a.value(1), a.value(0)]), p1 = a.coord([a.value(2), a.value(0)]), alto = a.size([0, 1])[1] * 0.7;
        return { type: 'rect', shape: { x: p0[0], y: p0[1] - alto / 2, width: Math.max(p1[0] - p0[0] - 1, 1), height: alto }, style: { fill: colorCarga(a.value(3)), opacity: a.value(3) < 0 ? 0.5 : Math.max(0.25, Math.min(1, a.value(3) + 0.15)) } }; } },
      { type: 'line', xAxisIndex: 0, yAxisIndex: 0, data: [], markLine: { symbol: 'none', silent: true, label: { formatter: 'hoy' }, lineStyle: { color: C.ambar }, data: [{ xAxis: t(r.hoy) }] } }],
  }).on('click', p => { if (p.seriesIndex === 0) detalleProcesos(P[p.value[0]]); });
}

function modalSimular() {
  const hoy = hoyISO(), mes = new Date(); mes.setMonth(mes.getMonth() + 3);
  const mo = modal('¿Cabe un proyecto nuevo en la planta?', `<div class="form">
    <label class="ancho">Tipo de estructura<select name="tipo">${S.cat.tipos.map((t, i) => `<option ${i === 1 ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select></label>
    <label>Toneladas<input name="ton" type="number" min="1" step="0.5" value="40" required></label>
    <label>Día 1 (planos + OC)<input name="inicio" type="date" value="${hoy}" required></label>
    <label>Meta<select name="tmeta"><option value="mes">En un mes</option><option value="fecha">En una fecha</option><option value="">Lo antes posible</option></select></label>
    <label id="lmes">Mes de entrega<input name="mes" type="month" value="${mes.toISOString().slice(0, 7)}"></label>
    <label id="lfecha" class="oculto">Fecha de entrega<input name="fecha" type="date"></label>
    <label>Presupuesto (USD)<input name="presupuesto" type="number" min="1000" step="1000" value="150000"></label>
    <label>Confianza<select name="alpha"><option value="0.8">80 %</option><option value="0.9">90 %</option></select></label>
    <p class="nota ancho">«En un mes» compromete el último día hábil de ese mes. Se programa junto con los proyectos en curso, sus prioridades y los preventivos; no se guarda nada.</p>
    <div class="ancho" id="rsim"></div></div>`,
  async f => {
    const tm = f.get('tmeta'), meta = tm === 'mes' ? f.get('mes') : tm === 'fecha' ? f.get('fecha') : null;
    $('#rsim', mo).innerHTML = cargando();
    let r;
    try { r = await api('/api/programacion/simular', { method: 'POST', body: { tipo: f.get('tipo'), ton: +f.get('ton'), inicio: f.get('inicio'), meta, presupuesto: +f.get('presupuesto'), alpha: +f.get('alpha'), regla: ($('#regla') || {}).value || 'penalidad' } }); }
    catch (e) { $('#rsim', mo).innerHTML = ''; throw e; }
    const n = r.nuevo;
    $('#rsim', mo).innerHTML = `${r.meta ? `<div class="semaforo ${r.cabe ? 'VERDE' : 'ROJO'}"><span class="luz"></span><div><b>${r.cabe ? 'Cabe' : 'No cabe'}</b> en la meta del ${fmtFecha(r.meta)}: P(cumplir) ${pct(n.prob_cumplir)}.
        ${r.cabe && n.inicio_mas_tardio ? `Puede empezar a más tardar el <b>${fmtFecha(n.inicio_mas_tardio)}</b>.` : ''}</div></div>` : ''}
      <p>Fin probable (P50) <b>${fmtFecha(n.p50)}</b> · con 80 % <b>${fmtFecha(n.p80)}</b> · prioridad ${n.prioridad} de ${r.plan.proyectos.length}.</p>
      ${r.efecto_en_otros.length ? `<p class="nota"><b>Efecto en los proyectos en curso:</b> ${r.efecto_en_otros.map(e => `${esc(e.codigo)} ${e.dias ? `${e.dias > 0 ? '+' : ''}${e.dias} días` : ''}${e.cambio_prob ? ` (P(cumplir) ${e.cambio_prob > 0 ? '+' : ''}${Math.round(100 * e.cambio_prob)} pts)` : ''}`).join(' · ')}</p>` : '<p class="nota">No mueve la fecha de los proyectos en curso.</p>'}`;
    throw new Error('');            // el modal queda abierto para leer el resultado
  }, 'Simular');
  const sel = $('[name=tmeta]', mo);
  sel.onchange = () => { $('#lmes', mo).classList.toggle('oculto', sel.value !== 'mes'); $('#lfecha', mo).classList.toggle('oculto', sel.value !== 'fecha'); };
}

/* aviso del plan para Inicio y para cada proyecto */
async function avisoPlan(el, codigo) {
  if (!el) return;
  let d; try { d = await api('/api/programacion'); } catch (e) { return; }
  const ap = d.aprobado, pr = d.propuesto, nueva = pr && (!ap || pr.id > ap.id);
  if (codigo) {
    const x = ap && ap.resultado.proyectos.find(z => z.codigo === codigo);
    const av = nueva && pr.avisos.find(a => a.codigo === codigo);
    el.innerHTML = x || av ? `<div class="${av ? 'aviso' : 'nota'}" style="margin-bottom:12px">${ic('gantt', 15)} ${x ? `Plan de la cartera #${ap.id}: prioridad ${x.prioridad}, fin P80 ${fmtCorta(x.p80)}, P(cumplir) ${x.prob_cumplir == null ? '—' : pct(x.prob_cumplir)}.` : ''}
      ${av ? ` La propuesta #${pr.id} lo pone en riesgo (${pct(av.prob)}).` : ''} <a href="#/programacion">Ver programación</a></div>` : '';
    return;
  }
  const msgs = [];
  if (nueva && pr.avisos.length) msgs.push(`La propuesta de plan #${pr.id} avisa: ${pr.avisos.map(a => esc(a.texto)).join(' · ')}`);
  else if (nueva) msgs.push(`Hay una propuesta de plan #${pr.id} (${esc(pr.motivo)}) esperando aprobación`);
  if (!ap) msgs.push('La cartera todavía no tiene un plan aprobado');
  el.innerHTML = msgs.length ? `<div class="aviso" style="margin-bottom:14px">${ic('gantt', 16)} ${msgs.join('. ')}. <a href="#/programacion">Abrir programación</a></div>` : '';
}
