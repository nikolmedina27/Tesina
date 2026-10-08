/* SteelPlan · Tableros fijos (v3.2): Gerencia, Producción, Informe mensual (PDF) y Modo TV para la planta.
   Diseño fijo; los números salen de los módulos de detalle. Usa los helpers de app.js y se carga antes que él. */
'use strict';
const SEMT = { v: ['En camino', 'b-ver'], a: ['En riesgo', 'b-nar'], r: ['Atraso probable', 'b-roj'], n: ['Sin fecha', 'b-gris'] };
const usoCls = u => u == null ? 'b-gris' : u < 0.7 ? 'b-ver' : u < 0.95 ? 'b-nar' : 'b-roj';
const pctU = u => u == null ? 'sin capacidad' : `${Math.round(100 * u)} %`;
/* tablero por defecto de cada rol al entrar */
const TABLERO_ROL = { gerencia: 'tgerencia', jefe_taller: 'tproduccion', supervisor: 'tproduccion', mantenimiento: 'tproduccion', calidad: 'tproduccion', cotizador: 'inicio' };
const avisoPlanTab = d => d.plan && d.plan.estado === 'PROPUESTO'
  ? `<div class="aviso">${ic('gantt', 16)} Todavía no hay un plan aprobado: se muestra la propuesta #${d.plan.id} sin aprobar. <a href="#/programacion">Revisarla en Programación</a></div>`
  : d.propuesta_pendiente ? `<div class="aviso">${ic('gantt', 16)} Hay una propuesta de plan #${d.propuesta_pendiente.id} esperando aprobación${d.propuesta_pendiente.avisos.length ? ': ' + d.propuesta_pendiente.avisos.map(a => esc(a.texto)).join(' · ') : ''}. <a href="#/programacion">Abrir</a></div>` : '';
const tablaRiesgo = P => P.length ? `<table class="tabla"><tr><th>#</th><th>OT</th><th>Comprometida</th><th>Fin P80</th><th>P(cumplir)</th><th class="num">Penalidad esperada</th></tr>
  ${P.map(x => `<tr class="clic" onclick="location.hash='${x.id ? '#/proyecto/a/' + x.id : '#/programacion'}'"><td>${x.prioridad}</td><td><b>${esc(x.codigo)}</b></td><td>${fmtCorta(x.compromiso)}</td><td>${fmtCorta(x.p80)}</td>
    <td><span class="badge ${SEMT[x.semaforo][1]}">${x.prob == null ? '—' : pct(x.prob)}</span></td><td class="num">${fmtNum(x.penalidad)}</td></tr>`).join('')}</table>`
  : '<div class="vacio">Sin plan de la cartera. Calcúlalo en <a href="#/programacion">Programación</a>.</div>';

/* =====================================================================  GERENCIA */
async function vTGerencia() {
  const m = shell('tgerencia', `${ic('inicio', 20)} Tablero de gerencia`, `<a class="btn" href="#/tmensual">${ic('reporte', 15)} Informe mensual</a><a class="btn" href="#/tv">${ic('planta', 15)} Modo TV</a>`);
  const d = await api('/api/tableros/gerencia');
  const o = d.otd, riesgo = d.proyectos.filter(x => x.semaforo === 'r' || x.semaforo === 'a');
  const dks = d.maquinas.map(x => x.dk).filter(x => x != null), dkp = dks.length ? dks.reduce((a, b) => a + b, 0) / dks.length : null;
  m.innerHTML = `${avisoPlanTab(d)}
  <div class="kpis">
    ${kpi('Cumplimiento · 12 meses', o.otd == null ? '—' : pct(o.otd), `${o.a_tiempo} de ${o.entregas} entregas a tiempo · meta ${pct(d.meta_otd)}`, o.otd == null ? '' : o.otd >= d.meta_otd ? 'ver' : 'roj', 'check')}
    ${kpi('Proyectos en curso', d.en_curso, `${fmtNum(d.ton_en_curso)} t en planta`, '', 'proyectos')}
    ${kpi('En riesgo de atraso', riesgo.length, riesgo.length ? riesgo.map(x => esc(x.codigo)).join(', ') : 'todos en camino', riesgo.length ? 'roj' : 'ver', 'alerta')}
    ${kpi('Penalidad esperada', 'USD ' + fmtNum(d.penalidad_total), 'cartera con el plan vigente', d.penalidad_total > 0 ? 'nar' : 'ver', 'reloj')}
    ${kpi('Disponibilidad de máquinas', dkp == null ? '—' : pct(dkp, 1), `promedio 30 días · meta ${pct(d.meta_dk)}`, dkp == null ? '' : dkp >= d.meta_dk ? 'ver' : 'nar', 'engranaje')}
    ${kpi('Días imputables al cliente', fmtNum(d.rfi_cliente.dias, 1), `${d.rfi_cliente.abiertas} RFI/NC del cliente abiertas · Steelser ${fmtNum(d.rfi_cliente.dias_steelser, 1)} d`, 'mor', 'bandeja')}</div>
  <div class="grid g2" style="margin-bottom:14px">
    <div class="tarjeta"><h3>Entregas por mes · últimos 12 meses <span class="nota">histórico + plataforma</span></h3><div class="cuerpo"><div class="grafico bajo" id="gotd12"></div></div></div>
    <div class="tarjeta"><h3>Proyectos en curso según el plan <span class="nota">${d.plan ? `plan #${d.plan.id}${d.plan.estado === 'PROPUESTO' ? ' (sin aprobar)' : ''}` : ''}</span></h3><div class="cuerpo scroll" style="max-height:260px">${tablaRiesgo(d.proyectos)}</div></div>
    <div class="tarjeta"><h3>Carga del taller · próximas 4 semanas <span class="nota">horas planificadas / disponibles</span></h3><div class="cuerpo">${d.carga.length ? `<table class="tabla"><tr><th>Máquina</th>${d.carga[0].semanas.map(s => `<th>Sem. ${fmtCorta(s.desde).slice(0, 5)}</th>`).join('')}</tr>
      ${d.carga.map(c => `<tr><td>${esc(c.maquina)}</td>${c.semanas.map(s => `<td><span class="badge ${usoCls(s.uso)}">${pctU(s.uso)}</span></td>`).join('')}</tr>`).join('')}</table>` : '<div class="vacio">Sin plan de la cartera</div>'}</div></div>
    <div class="tarjeta"><h3>Disponibilidad por máquina · 30 días <span class="nota">meta ${pct(d.meta_dk)}</span></h3><div class="cuerpo"><div class="grafico bajo" id="gdk4"></div></div></div></div>
  <div class="tarjeta"><h3>Últimas entregas</h3><div class="cuerpo">${o.detalle.length ? `<table class="tabla"><tr><th>Fecha</th><th>Cliente</th><th>Proyecto</th><th>Resultado</th></tr>
    ${o.detalle.slice().reverse().map(e => `<tr><td>${fmtCorta(e.fin)}</td><td>${esc(e.cliente || '')}</td><td>${esc(e.nombre)}</td><td>${e.a_tiempo ? '<span class="badge b-ver">A tiempo</span>' : `<span class="badge b-roj">${e.retraso} d de retraso</span>`}</td></tr>`).join('')}</table>`
    : '<div class="vacio">Sin entregas en los últimos 12 meses</div>'}</div></div>
  <p class="nota">Actualizado ${esc(d.generado)}. Riesgo y penalidad salen del plan de la cartera (Programación); la disponibilidad, de Mantenimiento.</p>`;
  chart($('#gotd12'), { grid: { left: 36, right: 16, top: 24, bottom: 28 }, tooltip: { trigger: 'axis' }, legend: { top: 0, right: 0 },
    xAxis: { type: 'category', data: o.meses.map(x => x.mes.slice(5) + '/' + x.mes.slice(2, 4)) }, yAxis: { type: 'value', minInterval: 1 },
    series: [{ name: 'A tiempo', type: 'bar', stack: 'e', data: o.meses.map(x => x.a_tiempo), itemStyle: { color: C.verde } },
      { name: 'Con retraso', type: 'bar', stack: 'e', data: o.meses.map(x => x.entregas - x.a_tiempo), itemStyle: { color: C.rojo } }] });
  chart($('#gdk4'), { grid: { left: 190, right: 50, top: 8, bottom: 22 }, tooltip: { valueFormatter: v => v + ' %' }, xAxis: { type: 'value', min: v => Math.max(0, Math.floor(v.min / 10) * 10 - 10), max: 100 },
    yAxis: { type: 'category', data: d.maquinas.map(x => x.nombre).reverse() },
    series: [{ type: 'bar', barWidth: 14, data: d.maquinas.map(x => ({ value: x.dk == null ? null : +(100 * x.dk).toFixed(1), itemStyle: { color: x.dk == null ? C.borde : x.dk >= d.meta_dk ? C.verde : x.dk >= 0.8 ? C.ambar : C.rojo } })).reverse(),
      label: { show: true, position: 'right', formatter: '{c} %' }, markLine: { symbol: 'none', data: [{ xAxis: 100 * d.meta_dk }], lineStyle: { color: C.verde, type: 'dashed' }, label: { formatter: 'meta' } } }] });
}

/* =====================================================================  PRODUCCIÓN */
async function vTProduccion() {
  const m = shell('tproduccion', `${ic('planta', 20)} Tablero de producción`, `<a class="btn" href="#/mantgantt">${ic('gantt', 15)} Gantt de máquinas</a><a class="btn" href="#/tv">${ic('planta', 15)} Modo TV</a>`);
  const d = await api('/api/tableros/produccion');
  const parAhora = d.paradas_hoy.filter(x => x.abierta);
  m.innerHTML = `${avisoPlanTab(d)}
  <div class="kpis">
    ${kpi('HH registradas hoy', fmtNum(d.hh_hoy), `${d.proyectos_con_tareo_hoy} proyectos con tareo`, d.hh_hoy ? '' : 'nar', 'reloj')}
    ${kpi('Máquinas detenidas', parAhora.length, parAhora.length ? parAhora.map(x => esc(x.maquina)).join(', ') : 'todas operando', parAhora.length ? 'roj' : 'ver', 'llave')}
    ${kpi('Preventivos hoy y 2 días', d.preventivos.length, `${d.preventivos.filter(x => x.vencida).length} vencidos`, d.preventivos.some(x => x.vencida) ? 'roj' : '', 'engranaje')}
    ${kpi('Tareas bloqueadas', d.bloqueos.length, d.bloqueos.length ? 'requieren acción' : 'sin bloqueos', d.bloqueos.length ? 'roj' : 'ver', 'alerta')}</div>
  <div class="tarjeta" style="margin-bottom:14px"><h3>Semana ${fmtCorta(d.semana.desde)} – ${fmtCorta(d.semana.hasta)} · plan vs. real <span class="nota">avance físico ponderado (kg) y HH del tareo</span></h3><div class="cuerpo">
    ${d.proyectos.length ? `<table class="tabla"><tr><th>OT</th><th>kg plan</th><th>kg real</th><th style="min-width:160px">Cumplimiento kg</th><th>HH plan</th><th>HH real</th><th style="min-width:160px">Cumplimiento HH</th><th>Índice acumulado</th></tr>
      ${d.proyectos.map(x => { const ck = x.plan_kg ? (x.real_kg ?? 0) / x.plan_kg : null, ch = x.plan_hh ? (x.real_hh ?? 0) / x.plan_hh : null;
        const barra = c => c == null ? '<span class="nota">—</span>' : `<div class="barra ${c >= 0.9 ? '' : 'nar'}"><i style="width:${Math.min(100, 100 * c)}%"></i></div><span class="nota">${Math.round(100 * c)} %</span>`;
        return `<tr class="clic" onclick="location.hash='#/proyecto/a/${x.id}?tab=sem'"><td><b>${esc(x.codigo)}</b><div class="nota">${esc(x.nombre)}</div></td><td class="num">${x.plan_kg == null ? '—' : fmtNum(x.plan_kg)}</td><td class="num">${x.tiene_piezas ? fmtNum(x.real_kg) : '—'}</td><td>${x.tiene_piezas ? barra(ck) : '<span class="nota">sin piezas</span>'}</td>
          <td class="num">${x.plan_hh == null ? '—' : fmtNum(x.plan_hh)}</td><td class="num">${fmtNum(x.real_hh)}</td><td>${barra(ch)}</td>
          <td>${x.spi_kg != null ? `<span class="badge ${x.spi_kg >= 1 ? 'b-ver' : x.spi_kg >= 0.9 ? 'b-nar' : 'b-roj'}">kg ${x.spi_kg.toFixed(2)}</span> ` : ''}${x.spi_hh != null ? `<span class="badge ${x.spi_hh >= 1 ? 'b-ver' : x.spi_hh >= 0.9 ? 'b-nar' : 'b-roj'}">HH ${x.spi_hh.toFixed(2)}</span>` : x.plan_hh == null ? '<span class="nota">no empezó</span>' : ''}</td></tr>`; }).join('')}</table>
      <p class="nota">La semana en curso se mide hasta hoy. Índice acumulado = real / plan desde el inicio del proyecto.</p>` : '<div class="vacio">Sin proyectos en curso</div>'}</div></div>
  <div class="grid g2" style="margin-bottom:14px">
    <div class="tarjeta"><h3>Cuellos de botella · próximos 10 días laborables</h3><div class="cuerpo">${d.cuellos.length ? `<table class="tabla"><tr><th>Máquina</th><th>Uso</th><th class="num">Días saturada</th><th class="num">Días sin capacidad</th></tr>
      ${d.cuellos.map(c => `<tr><td>${esc(c.maquina)}</td><td><span class="badge ${usoCls(c.uso)}">${pctU(c.uso)}</span></td><td class="num">${c.dias_saturada}</td><td class="num">${c.dias_sin_capacidad}</td></tr>`).join('')}</table>`
      : '<div class="vacio">Sin plan de la cartera</div>'}</div></div>
    <div class="tarjeta"><h3>Máquinas ahora</h3><div class="cuerpo"><div class="miniq">${d.maquinas.map(x => `<a href="#/maquina/${x.id}" class="mq ${x.semaforo}"><b>${esc(x.nombre)}</b><span>${{ OPERANDO: 'Operando', MANTENIMIENTO: 'En mantenimiento', PARADA: 'Parada por falla' }[x.estado]}</span>
      <em>${x.indicadores_30d.dk == null ? '—' : pct(x.indicadores_30d.dk, 1)}</em></a>`).join('')}</div></div></div>
    <div class="tarjeta"><h3>Paradas de hoy</h3><div class="cuerpo">${d.paradas_hoy.length ? `<table class="tabla"><tr><th>Máquina</th><th>Desde</th><th>Hasta</th><th>Causa</th></tr>${d.paradas_hoy.map(x => `<tr><td>${esc(x.maquina)}</td><td>${esc(x.inicio.slice(5, 16))}</td><td>${x.abierta ? '<span class="badge b-roj">sigue parada</span>' : esc(x.fin.slice(11, 16))}</td><td>${esc(x.causa)}</td></tr>`).join('')}</table>` : '<div class="vacio">Sin paradas hoy</div>'}</div></div>
    <div class="tarjeta"><h3>Preventivos de hoy y los próximos 2 días</h3><div class="cuerpo">${d.preventivos.length ? `<table class="tabla"><tr><th>Fecha</th><th>Máquina</th><th>Tarea</th><th class="num">h</th></tr>${d.preventivos.map(x => `<tr class="clic" onclick="location.hash='#/mantordenes?o=${x.id}'"><td>${x.vencida ? `<span class="badge b-roj">${fmtCorta(x.programada_para)}</span>` : fmtCorta(x.programada_para)}</td><td>${esc(x.maquina)}</td><td>${esc(x.titulo)}</td><td class="num">${fmtNum(x.duracion_h, 1)}</td></tr>`).join('')}</table>` : '<div class="vacio">Ninguno programado</div>'}</div></div></div>
  <div class="tarjeta"><h3>Tareas bloqueadas</h3><div class="cuerpo">${d.bloqueos.length ? `<table class="tabla"><tr><th>ID</th><th>Bloqueo</th><th>OT</th><th>Responsable</th><th>Límite</th></tr>${d.bloqueos.map(b => `<tr class="clic" onclick="location.hash='#/tareas?t=${b.id}'"><td class="nota">STL-${b.id}</td><td>${esc(b.titulo)}</td><td>${esc(b.proyecto || '—')}</td><td>${esc(b.responsable || 'sin asignar')}</td><td>${fmtCorta(b.fecha_limite)}</td></tr>`).join('')}</table>` : '<div class="vacio">Sin bloqueos</div>'}</div></div>
  <p class="nota">Actualizado ${esc(d.generado)}.</p>`;
}

/* =====================================================================  INFORME MENSUAL (imprimible → PDF) */
async function vTMensual(qs = '') {
  const mes = new URLSearchParams(qs).get('mes') || hoyISO().slice(0, 7);
  const m = shell('tmensual', `${ic('reporte', 20)} Informe mensual`, `<input type="month" id="imes" value="${mes}"><button class="btn prim" id="bimpm">${ic('imprimir', 15)} Imprimir / guardar PDF</button>`);
  const d = await api('/api/tableros/mensual?mes=' + mes);
  const nomMes = new Date(d.mes + '-02').toLocaleDateString('es-PE', { month: 'long', year: 'numeric' });
  const I = d.incidencias;
  m.innerHTML = `<article class="reporte">
  <header class="rcab"><div class="marca"><img src="/static/img/logo-steelser.png" alt="Steelser" style="height:26px;filter:brightness(0) invert(1)"></div>
    <div><h1>Informe mensual · ${esc(nomMes)}</h1><div>Producción, cumplimiento y mantenimiento de la planta</div><div class="nota">Datos hasta el ${fmtFecha(d.hasta)} · emitido ${esc(d.generado)} por ${esc(S.me.nombre)}</div></div></header>
  <div class="kpis">
    ${kpi('Entregas del mes', d.entregas.length, d.otd == null ? 'sin entregas' : `${pct(d.otd)} a tiempo · meta ${pct(d.meta_otd)}`, d.otd == null ? '' : d.otd >= d.meta_otd ? 'ver' : 'roj', 'check')}
    ${kpi('Penalidad esperada de la cartera', 'USD ' + fmtNum(d.penalidad_total), d.plan ? `plan #${d.plan.id}${d.plan.estado === 'PROPUESTO' ? ' (sin aprobar)' : ''}` : 'sin plan', d.penalidad_total ? 'nar' : 'ver', 'reloj')}
    ${kpi('RFI, NC y bloqueos', I.n || 0, `${I.cerradas || 0} cerrados · cliente ${fmtNum(I.d_cli, 1)} d · Steelser ${fmtNum(I.d_ste, 1)} d`, 'mor', 'bandeja')}
    ${kpi('Planes de la cartera', d.planes.total, `${d.planes.aprobados} aprobados (reprogramaciones)`, '', 'gantt')}</div>
  <div class="grid g2">
    <section class="tarjeta"><h3>1. Entregas</h3><div class="cuerpo">${d.entregas.length ? `<table class="tabla"><tr><th>Fecha</th><th>Proyecto</th><th>Cliente</th><th>Resultado</th></tr>${d.entregas.map(e => `<tr><td>${fmtCorta(e.fin)}</td><td>${esc(e.nombre)}</td><td>${esc(e.cliente || '')}</td><td>${e.a_tiempo ? 'A tiempo' : `${e.retraso} d de retraso`}</td></tr>`).join('')}</table>` : '<p class="nota">No hubo entregas en el mes.</p>'}</div></section>
    <section class="tarjeta"><h3>2. Máquinas</h3><div class="cuerpo"><table class="tabla"><tr><th>Máquina</th><th>Disponibilidad</th><th class="num">Fallas</th><th class="num">Horas paradas</th><th class="num">MTTR</th><th>Preventivos</th></tr>
      ${d.maquinas.map(x => { const i = x.indicadores; return `<tr><td>${esc(x.nombre)}</td><td>${i ? `<span class="badge ${i.dk >= d.meta_dk ? 'b-ver' : i.dk >= 0.8 ? 'b-nar' : 'b-roj'}">${pct(i.dk, 1)}</span>` : '<span class="nota">sin registro</span>'}</td><td class="num">${i ? i.n_fallas : '—'}</td><td class="num">${i ? fmtNum(i.horas_parada, 1) : '—'}</td><td class="num">${i && i.mttr_h != null ? fmtNum(i.mttr_h, 1) + ' h' : '—'}</td>
        <td>${x.preventivos_programados ? `${x.preventivos_cumplidos} de ${x.preventivos_programados}` : '—'}</td></tr>`; }).join('')}</table>
      ${d.registro_desde ? `<p class="nota">Registro de paradas desde el ${fmtCorta(d.registro_desde)}; los días anteriores no cuentan.</p>` : ''}</div></section>
    <section class="tarjeta"><h3>3. Causas de parada</h3><div class="cuerpo">${d.causas.length ? `<table class="tabla"><tr><th>Causa</th><th class="num">Veces</th><th class="num">Horas</th></tr>${d.causas.map(c => `<tr><td>${esc(c.causa)}</td><td class="num">${c.n}</td><td class="num">${fmtNum(c.horas, 1)}</td></tr>`).join('')}</table>` : '<p class="nota">Sin paradas registradas en el mes.</p>'}</div></section>
    <section class="tarjeta"><h3>4. Horas-hombre por proyecto</h3><div class="cuerpo">${d.tareo.length ? `<table class="tabla"><tr><th>OT</th><th class="num">Días con tareo</th><th class="num">HH</th></tr>${d.tareo.map(t => `<tr><td>${esc(t.codigo)}</td><td class="num">${t.dias}</td><td class="num">${fmtNum(t.hh)}</td></tr>`).join('')}</table>` : '<p class="nota">Sin tareo en el mes.</p>'}</div></section>
  </div>
  <section class="tarjeta" style="margin-top:14px"><h3>5. Cartera al cierre (plan de la cartera)</h3><div class="cuerpo">${tablaRiesgo(d.proyectos)}</div></section>
  <p class="nota">El modelo de horas usa datos simulados hasta cargar tareos reales. Las cifras de máquinas siguen la Ec. 10 de la tesis (TPM); el riesgo, el plan de la cartera.</p></article>`;
  $('#imes').onchange = e => { location.hash = '#/tmensual?mes=' + e.target.value; };
  $('#bimpm').onclick = () => window.print();
}

/* =====================================================================  MODO TV (pantalla de planta) */
function limpiarTV() { (S.tvT || []).forEach(t => clearInterval(t)); S.tvT = []; document.body.classList.remove('modo-tv'); }
async function vTV() {
  limpiarTV();
  S.charts.forEach(c => c.dispose()); S.charts = [];
  $$('body > .velo, body > .lateral, body > .modal, body > .paleta').forEach(e => e.remove());
  document.body.classList.add('modo-tv');
  $('#app').innerHTML = `<div class="tv"><header><img src="/static/img/logo-steelser.png" alt="Steelser"><h1 id="tvtit">Planta</h1><div class="puntos" id="tvp"></div><div class="reloj" id="tvr"></div>
    <button class="icono-btn" id="tvfs" title="Pantalla completa">${ic('panel', 18)}</button><a class="icono-btn" href="#/tproduccion" title="Salir (Esc)">${ic('cerrar', 18)}</a></header>
    <main id="tvm"><div class="vacio">Cargando…</div></main><footer id="tvav"></footer></div>`;
  let d = null, k = 0, err = null;
  const panel = [
    ['Máquinas', () => `<div class="tvq">${d.maquinas.map(x => `<div class="tq ${x.semaforo}"><b>${esc(x.nombre)}</b><span>${{ OPERANDO: 'Operando', MANTENIMIENTO: 'En mantenimiento', PARADA: 'PARADA POR FALLA' }[x.estado]}</span>
      <em>${x.indicadores_30d.dk == null ? '—' : pct(x.indicadores_30d.dk, 1)}</em><small>disponibilidad 30 días${x.proximo_preventivo ? ` · preventivo ${fmtCorta(x.proximo_preventivo.programada_para)}` : ''}</small></div>`).join('')}</div>`],
    ['Proyectos de la semana', () => `<table class="tvt"><tr><th>OT</th><th>Avance semana (kg)</th><th>Avance semana (HH)</th><th>Fin probable (P80)</th><th>P(cumplir)</th></tr>
      ${d.proyectos.map(x => { const r = d.riesgo.find(z => z.codigo === x.codigo) || {}; const c = (a, b) => b ? `${Math.round(100 * (a || 0) / b)} %` : '—';
        return `<tr><td><b>${esc(x.codigo)}</b><small>${esc(x.nombre)}</small></td><td>${x.tiene_piezas ? c(x.real_kg, x.plan_kg) : '—'}</td><td>${c(x.real_hh, x.plan_hh)}</td><td>${fmtCorta(r.p80)}</td>
          <td>${r.prob == null ? '—' : `<span class="badge ${SEMT[r.semaforo][1]}">${pct(r.prob)}</span>`}</td></tr>`; }).join('') || '<tr><td colspan="5">Sin proyectos en curso</td></tr>'}</table>`],
    ['Hoy en planta', () => `<div class="tvh"><section><h2>Paradas de hoy</h2>${d.paradas_hoy.map(x => `<p><b>${esc(x.maquina)}</b> ${esc(x.inicio.slice(11, 16))} → ${x.abierta ? '<span class="badge b-roj">sigue</span>' : esc(x.fin.slice(11, 16))} · ${esc(x.causa)}</p>`).join('') || '<p>Ninguna</p>'}</section>
      <section><h2>Preventivos (hoy y 2 días)</h2>${d.preventivos.map(x => `<p><b>${fmtCorta(x.programada_para).slice(0, 5)}</b> ${esc(x.maquina)} · ${esc(x.titulo)}</p>`).join('') || '<p>Ninguno</p>'}</section>
      <section><h2>Bloqueos</h2>${d.bloqueos.map(b => `<p><b>STL-${b.id}</b> ${esc(b.titulo)}${b.proyecto ? ' · ' + esc(b.proyecto) : ''}</p>`).join('') || '<p>Ninguno</p>'}</section>
      <section><h2>Tareo de hoy</h2><p class="grande">${fmtNum(d.hh_hoy)} HH</p><p>${d.proyectos_con_tareo_hoy} proyectos con registro</p></section></div>`],
  ];
  const pintar = () => {
    if (!$('#tvm')) return limpiarTV();
    if (!d) { $('#tvm').innerHTML = `<div class="vacio">${err ? 'Sin conexión con el servidor, reintentando…' : 'Cargando…'}</div>`; return; }
    const [t, f] = panel[k % panel.length];
    $('#tvtit').textContent = t; $('#tvm').innerHTML = f();
    $('#tvp').innerHTML = panel.map((_, i) => `<i class="${i === k % panel.length ? 'on' : ''}"></i>`).join('');
    $('#tvav').innerHTML = d.avisos.length ? `<div class="cinta"><span>${d.avisos.map(esc).join('   ·   ')}</span></div>` : `<div class="cinta ok"><span>Sin avisos · actualizado ${esc(d.generado.slice(11))}</span></div>`;
  };
  const cargar = async () => { try { d = await api('/api/tableros/tv'); err = null; } catch (e) { err = e; } pintar(); };
  const reloj = () => { const r = $('#tvr'); if (r) r.textContent = new Date().toLocaleString('es-PE', { weekday: 'short', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }); };
  reloj(); await cargar();
  S.tvT.push(setInterval(() => { k++; pintar(); }, 20000), setInterval(cargar, 5 * 60000), setInterval(reloj, 15000));
  $('#tvfs').onclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()).catch(() => {});
}
document.addEventListener('keydown', e => { if (e.key === 'Escape' && document.body.classList.contains('modo-tv') && !document.fullscreenElement) location.hash = '#/tproduccion'; });
