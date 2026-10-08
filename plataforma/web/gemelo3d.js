/* SteelPlan · gemelo 3D de la planta (three.js local). Todo es SIMULADO.
   Reconstruye la planta hora a hora desde la API /api/gemelo/estado: máquinas con piezas móviles, puentes grúa que llevan los
   lotes, cuadrillas trabajando, camiones en los muelles, material en racks, ciclo de día y noche. */
import * as THREE from '/static/vendor/three/three.module.js';
import { OrbitControls } from '/static/vendor/three/OrbitControls.js';

const CX = 50, CZ = 25;
const V = (x, z, y = 0) => new THREE.Vector3(x - CX, y, z - CZ);
const hash = s => [...String(s)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
const COLOR_ETAPA = { HABILITADO: 0x6bb6ff, MOVIMIENTO: 0xffffff, DOBLEZ: 0xc9b2ee, ARMADO: 0xffb066, SOLDEO: 0xff8a4c, RETRABAJO: 0xff5a4c,
  LIMPIEZA: 0x8fd6a3, LISTO_PINTURA: 0xffd966, PINTURA: 0x61cdc0, PINTADO: 0x3fb0a6, ENTREGADO: 0xb0bac5 };
const COLOR_CONTR = { 'T&C FABRICACION': 0xe9730c, 'FRANCISCO TARRILLO': 0x925ace, 'RFR METALICAS': 0x107e3e, 'ROGGER TORRES': 0xbb0000, 'LHL INGENIERIA': 0x0a6ed1 };
const unoBox = new THREE.BoxGeometry(1, 1, 1);
const unoCil = new THREE.CylinderGeometry(1, 1, 1, 18);
const unoEsf = new THREE.SphereGeometry(1, 14, 10);
const cacheMat = {};
const mat = (c, o = {}) => { const k = c + '|' + JSON.stringify(o); return cacheMat[k] || (cacheMat[k] = new THREE.MeshStandardMaterial({ color: c, roughness: .72, metalness: .12, ...o })); };
const box = (w, h, d, c, o) => { const m = new THREE.Mesh(unoBox, mat(c, o)); m.scale.set(w, h, d); m.castShadow = true; m.receiveShadow = true; return m; };
const cil = (r, h, c, o) => { const m = new THREE.Mesh(unoCil, mat(c, o)); m.scale.set(r, h, r); m.castShadow = true; m.receiveShadow = true; return m; };
const esf = (r, c, o) => { const m = new THREE.Mesh(unoEsf, mat(c, o)); m.scale.set(r, r, r); return m; };
const en = (obj, x, y, z) => { obj.position.set(x, y, z); return obj; };

export function crearGemelo(contenedor, meta, opts = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(0x000000, 0);
  contenedor.appendChild(renderer.domElement);
  renderer.domElement.style.cssText = 'display:block;width:100%;height:100%;outline:none';
  const escena = new THREE.Scene();
  const camara = new THREE.PerspectiveCamera(30, 1, .5, 900);
  const ctl = new OrbitControls(camara, renderer.domElement);
  ctl.enableDamping = true; ctl.dampingFactor = .08; ctl.maxPolarAngle = 1.5; ctl.minDistance = 4; ctl.maxDistance = 280;
  ctl.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };
  const hemi = new THREE.HemisphereLight(0xffffff, 0xb7c8da, 1.1); escena.add(hemi);
  const sol = new THREE.DirectionalLight(0xffffff, 1.4); sol.castShadow = true; sol.shadow.mapSize.set(2048, 2048);
  Object.assign(sol.shadow.camera, { left: -95, right: 95, top: 70, bottom: -70, near: 10, far: 320 }); sol.shadow.bias = -0.0004;
  escena.add(sol); escena.add(sol.target);
  const estatico = new THREE.Group(), dinamico = new THREE.Group(), grupoGruas = new THREE.Group();
  escena.add(estatico, dinamico, grupoGruas);
  const anim = [], techos = [], lamparas = [], etiquetas = [];
  const capaEt = document.createElement('div'); capaEt.className = 'p3d-etiquetas'; contenedor.appendChild(capaEt);
  const tip = document.createElement('div'); tip.className = 'p3d-tip oculto'; contenedor.appendChild(tip);
  const etiqueta = (texto, v, clase = '') => { const e = document.createElement('div'); e.className = 'p3d-et ' + clase; e.textContent = texto; capaEt.appendChild(e); const o = { el: e, v }; etiquetas.push(o); return o; };
  const marcar = (obj, ref) => { obj.traverse(o => { o.userData.ref = ref; }); return obj; };

  /* ---------- posiciones de las estaciones (de la tabla sim_planta_elemento) ---------- */
  const E = {}; meta.elementos.forEach(e => { E[e.nombre] = e; });
  const por = pref => meta.elementos.filter(e => e.nombre.startsWith(pref)).sort((a, b) => a.nombre.localeCompare(b.nombre, 'es', { numeric: true }));
  const MAQN = ['Sierra Cinta Kaltenbach', 'Cizalladora Punzonadora Pedimax', 'Mesa CNC', 'Roscadora RIDGID'];
  const maqE = MAQN.map(n => E[n]);
  const mesasE = por('Mesa de armado'), puestosE = por('Puesto de soldeo'), zonasE = por('Zona de limpieza');
  const bufferE = por('Buffer')[0], patioE = por('Patio')[0], racksE = por('Rack de perfiles');
  const muelleD = E['Muelle de doblez (servicio externo)'], muelleP = E['Muelle a granallado y pintura (externo)'], muelleO = E['Muelle de despacho a obra'];
  const ofiE = E['Oficina técnica'], compE = E['Compras'];
  const posMaq = k => V(maqE[k].x, maqE[k].z), posMesa = n => V(mesasE[n - 1].x, mesasE[n - 1].z), posPuesto = n => V(puestosE[n - 1].x, puestosE[n - 1].z);
  const posLimp = c => { const z = zonasE[c <= 4 ? 0 : 1]; const i = (c - 1) % 4; return V(z.x - 2 + (i % 2) * 4, z.z - 2 + Math.floor(i / 2) * 4); };
  const COLAS = { patio: [V(patioE.x, patioE.z), 20, 6], buffer: [V(bufferE.x, bufferE.z), 3, 26], mesa: [V(68, 11.5), 30, 1.8], puesto: [V(72, 19.2), 34, 1.4],
    limpieza: [V(83.5, 13), 1.6, 18], salida: [V(80, 35.5), 30, 4], externo: [V(100, 17), 0, 0] };

  /* ---------- entorno ---------- */
  const suelo = new THREE.Mesh(new THREE.PlaneGeometry(300, 220), mat(0xd7e3ef)); suelo.rotation.x = -Math.PI / 2; suelo.position.y = -.25; suelo.receiveShadow = true; estatico.add(suelo);
  const predio = new THREE.Mesh(new THREE.PlaneGeometry(100, 50), mat(0xe9eff5)); predio.rotation.x = -Math.PI / 2; predio.position.y = -.12; predio.receiveShadow = true; estatico.add(predio);
  const calle = new THREE.Mesh(new THREE.PlaneGeometry(300, 14), mat(0x9fa9b6)); calle.rotation.x = -Math.PI / 2; calle.position.set(0, -.15, 44); calle.receiveShadow = true; estatico.add(calle);
  for (let i = -7; i <= 7; i++) { const r = new THREE.Mesh(new THREE.PlaneGeometry(5, .3), mat(0xf4f6f8)); r.rotation.x = -Math.PI / 2; r.position.set(i * 18, -.1, 44); estatico.add(r); }
  const cerco = (x0, z0, x1, z1) => { const L = Math.hypot(x1 - x0, z1 - z0); const m = box(L, 1.6, .1, 0x8a96a3, { transparent: true, opacity: .55 }); m.position.set((x0 + x1) / 2 - CX, .8, (z0 + z1) / 2 - CZ); m.rotation.y = -Math.atan2(z1 - z0, x1 - x0); estatico.add(m); };
  cerco(0, 0, 100, 0); cerco(0, 0, 0, 50); cerco(0, 50, 60, 50); cerco(72, 50, 100, 50); cerco(100, 0, 100, 3); cerco(100, 36, 100, 50);
  const arbol = (x, z, s = 1) => { const g = new THREE.Group(); g.add(en(box(.45 * s, 2.2 * s, .45 * s, 0x8b5a2b), 0, 1.1 * s, 0)); g.add(en(esf(1.8 * s, 0x6fbf73), 0, 3.6 * s, 0)); g.position.set(x - CX, 0, z - CZ); estatico.add(g); };
  [[-10, -8], [-12, 10], [-9, 30], [112, -6], [114, 14], [110, 30], [20, -10], [50, -12], [80, -10], [-10, 48], [112, 52]].forEach(([x, z], i) => arbol(x, z, .8 + (i % 3) * .2));
  const farola = (x, z) => { const g = new THREE.Group(); g.add(en(cil(.12, 6, 0x5b738b), 0, 3, 0)); const l = en(esf(.4, 0xfff2c4, { emissive: 0x000000 }), 0, 6.2, 0); g.add(l); lamparas.push(l); g.position.set(x - CX, 0, z - CZ); estatico.add(g); };
  [[10, 36], [45, 36], [75, 36], [97, 45], [3, 3], [97, 3]].forEach(([x, z]) => farola(x, z));
  for (const [x, z, c] of [[8, 52, 0xc14a4a], [14, 52, 0x4a7fc1], [20, 52, 0xdddddd]]) { const a = new THREE.Group(); a.add(en(box(4, 1.2, 1.9, c), 0, .8, 0)); a.add(en(box(2.2, .9, 1.7, 0x9ec7f0), -.3, 1.7, 0)); a.position.set(x - CX, 0, z - CZ); estatico.add(a); }
  const estacionamiento = V(14, 54); etiqueta('Estacionamiento', V(14, 54, 3), 'zona');

  /* ---------- naves, oficinas y edificios ---------- */
  const luzNave = [];
  const nave = (e, texto) => {
    const g = new THREE.Group(); const w = e.ancho, d = e.largo, h = e.alto;
    g.add(en(box(w, .2, d, 0xf3f6f9), 0, .1, 0));
    for (const z of [-d / 2 + 2.2, 0, d / 2 - 2.2]) { const l = box(w - 2, .02, .25, 0xe0b020); l.position.set(0, .22, z); g.add(l); }
    for (const [x, z, ww, dd] of [[0, -d / 2, w, .35], [0, d / 2, w, .35], [-w / 2, 0, .35, d], [w / 2, 0, .35, d]]) g.add(en(box(ww, 3.4, dd, 0xb9cde4), x, 1.9, z));
    for (let x = -w / 2; x <= w / 2 + .1; x += w / 6) for (const z of [-d / 2, d / 2]) { g.add(en(box(.55, h, .55, 0x5b738b), x, h / 2, z)); g.add(en(box(.3, .3, d, 0x7a8da1), x, h - .15, 0)); }
    const techoIzq = box(w + 1, .35, d / 2 + .6, 0x1b6fd1, { transparent: true, opacity: .5 }); techoIzq.position.set(0, h + 1.2, -d / 4); techoIzq.rotation.x = .09; g.add(techoIzq); techos.push(techoIzq);
    const techoDer = box(w + 1, .35, d / 2 + .6, 0x1b6fd1, { transparent: true, opacity: .5 }); techoDer.position.set(0, h + 1.2, d / 4); techoDer.rotation.x = -.09; g.add(techoDer); techos.push(techoDer);
    for (let x = -w / 2 + 5; x < w / 2; x += 9) { const lz = box(2.2, .15, .6, 0xfff7d6, { emissive: 0x000000 }); lz.position.set(x, h - .3, 0); g.add(lz); luzNave.push(lz); }
    g.position.copy(V(e.x, e.z)); estatico.add(g); etiqueta(texto, V(e.x, e.z - d / 2 - .5, h + 2), 'nave'); return g;
  };
  nave(E['Nave A · recepción y habilitado'], 'Nave A · recepción y habilitado'); nave(E['Nave B · armado y soldeo'], 'Nave B · armado, soldeo y limpieza');
  const edificio = (e, color, texto, techo = 0x0a6ed1) => {
    const g = new THREE.Group(); g.add(en(box(e.ancho, 3.6, e.largo, color), 0, 1.8, 0)); g.add(en(box(e.ancho + .8, .5, e.largo + .8, techo), 0, 3.85, 0));
    for (let i = -1; i <= 1; i++) { const v = box(e.ancho * .22, 1.2, .12, 0x9ec7f0, { emissive: 0x000000 }); v.position.set(i * e.ancho * .3, 2.1, -e.largo / 2 - .07); g.add(v); luzNave.push(v); }
    g.add(en(box(1.6, 2.2, .12, 0x5b738b), 0, 1.1, -e.largo / 2 - .07));
    g.position.copy(V(e.x, e.z)); marcar(g, { tipo: 'edificio', nombre: texto, etiqueta: texto }); estatico.add(g); etiqueta(texto, V(e.x, e.z, 6), 'zona'); return g;
  };
  edificio(ofiE, 0xf7f9fb, 'Oficina técnica'); edificio(compE, 0xf0f3f6, 'Compras');
  { const g = new THREE.Group(); g.add(en(box(10, 3.2, 6, 0xeef1f4), 0, 1.6, 0)); g.add(en(box(10.8, .45, 6.8, 0x8a96a3), 0, 3.4, 0)); g.position.copy(V(55, 43)); marcar(g, { tipo: 'edificio', nombre: 'Comedor y vestuarios', etiqueta: 'Comedor y vestuarios' }); estatico.add(g); etiqueta('Comedor y vestuarios', V(55, 43, 5.5), 'zona'); }
  { const g = new THREE.Group(); g.add(en(box(3, 2.6, 3, 0xf1f1f1), 0, 1.3, 0)); g.add(en(box(3.6, .35, 3.6, 0xe9730c), 0, 2.8, 0)); g.position.copy(V(100, 43)); estatico.add(g); etiqueta('Garita', V(100, 43, 4.2), 'zona'); }

  /* ---------- patios, buffer y muelles ---------- */
  const zonaPlana = (e, color, texto, nombre) => { const z = box(e.ancho, .1, e.largo, color); z.position.copy(V(e.x, e.z, .05)); estatico.add(z); const b = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(e.ancho, .11, e.largo)), new THREE.LineBasicMaterial({ color: 0xe0b020 })); b.position.copy(V(e.x, e.z, .08)); estatico.add(b); marcar(z, { tipo: 'zona', nombre, etiqueta: nombre }); if (texto) etiqueta(texto, V(e.x, e.z, 1.4), 'zona'); };
  zonaPlana(patioE, 0xe7e2d2, 'Patio de acopio', 'Patio de acopio de perfiles y planchas'); zonaPlana(bufferE, 0xdce8f3, 'Buffer', 'Buffer de piezas habilitadas');
  { const z = box(36, .1, 6, 0xdfe7ef); z.position.copy(V(80, 35.5, .05)); estatico.add(z); marcar(z, { tipo: 'zona', nombre: 'Patio de salida', etiqueta: 'Patio de salida (piezas listas y pintadas)' }); etiqueta('Patio de salida', V(80, 35.5, 1.4), 'zona'); }
  for (const e of [muelleD, muelleP, muelleO]) { const m = box(e.ancho, .5, e.largo, 0xcfd8e1); m.position.copy(V(e.x, e.z, .25)); estatico.add(m); marcar(m, { tipo: 'muelle', nombre: e.nombre, etiqueta: e.nombre }); const t = box(e.ancho + .6, .25, e.largo + .6, 0x0a6ed1); t.position.copy(V(e.x, e.z, 4.2)); estatico.add(t); for (const dz of [-e.largo / 2, e.largo / 2]) estatico.add(en(box(.2, 4, .2, 0x5b738b), e.x - CX, 2, e.z - CZ + dz)); etiqueta(e.nombre.replace(' (servicio externo)', '').replace(' (externo)', ''), V(e.x, e.z, 5.4), 'zona'); }
  racksE.forEach((e, i) => { const g = new THREE.Group(); for (const dx of [-e.ancho / 2, e.ancho / 2]) for (const dz of [-e.largo / 2, 0, e.largo / 2]) g.add(en(box(.18, 4, .18, 0xe9730c), dx, 2, dz)); for (let n = 0; n < 3; n++) g.add(en(box(e.ancho + .4, .16, e.largo + .3, 0xf4a259), 0, .5 + n * 1.2, 0)); g.position.copy(V(e.x, e.z)); marcar(g, { tipo: 'rack', n: i + 1, etiqueta: 'Rack de perfiles R' + (i + 1) }); estatico.add(g); });

  /* ---------- estaciones: mesas, puestos, zonas de limpieza ---------- */
  const mesaObj = {}, puestoObj = {}, limpObj = {};
  mesasE.forEach((e, i) => { const g = new THREE.Group(); const t = box(e.ancho, .3, e.largo, 0x8fa3b8); t.position.y = 1; g.add(t); for (const dx of [-e.ancho / 2 + .4, e.ancho / 2 - .4]) for (const dz of [-e.largo / 2 + .3, e.largo / 2 - .3]) g.add(en(box(.25, 1, .25, 0x5b738b), dx, .5, dz));
    for (const dx of [-2.2, 0, 2.2]) g.add(en(box(.3, .45, .3, 0xe9730c), dx, 1.35, e.largo / 2 - .5)); g.add(en(box(e.ancho - 1, .06, .12, 0x223548), 0, 1.18, 0));
    g.position.copy(V(e.x, e.z)); marcar(g, { tipo: 'estacion', clase: 'mesa', n: i + 1, etiqueta: 'Mesa de armado M' + (i + 1) }); estatico.add(g); mesaObj[i + 1] = g; });
  puestosE.forEach((e, i) => { const g = new THREE.Group(); g.add(en(box(e.ancho, .12, e.largo, 0xdfe6ee), 0, .06, 0));
    for (const [x, z, w, d] of [[0, -e.largo / 2, e.ancho, .1], [-e.ancho / 2, 0, .1, e.largo], [e.ancho / 2, 0, .1, e.largo]]) g.add(en(box(w, 2.1, d, 0xffb347, { transparent: true, opacity: .55 }), x, 1.1, z));
    g.add(en(box(1.6, .8, 1.0, 0x8fa3b8), 0, .5, 0)); g.add(en(box(.7, .9, .6, 0x2f6fb3), e.ancho / 2 - .6, .55, -e.largo / 2 + .6)); g.add(en(cil(.05, 2, 0x223548), -e.ancho / 2 + .5, 1.6, e.largo / 2 - .5));
    const luz = en(esf(.2, 0x9aa6b2, { emissive: 0x000000 }), 0, 2.3, 0); g.add(luz); g.userData.luz = luz;
    g.position.copy(V(e.x, e.z)); marcar(g, { tipo: 'estacion', clase: 'puesto', n: i + 1, etiqueta: 'Puesto de soldeo S' + (i + 1) }); estatico.add(g); puestoObj[i + 1] = g; });
  zonasE.forEach((e, i) => { const g = new THREE.Group(); g.add(en(box(e.ancho, .1, e.largo, 0xe3e9ef), 0, .05, 0)); for (const dx of [-2, 2]) for (const dz of [-2, 2]) g.add(en(box(1.6, .9, 1.1, 0x8fa3b8), dx, .45, dz)); g.add(en(box(.6, 1.2, .4, 0x5b738b), 0, .6, 0));
    g.position.copy(V(e.x, e.z)); marcar(g, { tipo: 'estacion', clase: 'limpieza', n: i + 1, etiqueta: 'Zona de limpieza y liberación L' + (i + 1) }); estatico.add(g); limpObj[i + 1] = g; etiqueta('Limpieza L' + (i + 1), V(e.x, e.z, 3), 'zona'); });

  /* ---------- máquinas detalladas ---------- */
  const maq = [];
  function construirMaquina(k) {
    const e = maqE[k], g = new THREE.Group(), p = { k, g, activa: false, falla: false, partes: {} };
    const azul = 0x2f6fb3, gris = 0xc3ccd5, osc = 0x4b5b6b;
    if (k === 0) {                                                     // sierra cinta de ménsula Kaltenbach
      g.add(en(box(5.6, .7, 2.4, osc), 0, .35, 0));
      const mesaS = box(3.4, .22, 1.6, gris); mesaS.position.set(0, 1.1, 0); g.add(mesaS);
      for (const dz of [-.9, .9]) g.add(en(box(.35, .9, .35, osc), -1.4, .75, dz));
      const cab = new THREE.Group(); cab.add(en(box(.9, 2.6, .9, azul), 0, 1.3, 0)); cab.add(en(box(.7, .9, 1.9, 0x1b90ff), 0, 2.7, 0));
      const rueda1 = en(cil(.55, .22, 0x223548), 0, 2.5, -.75); const rueda2 = en(cil(.55, .22, 0x223548), 0, 2.5, .75); rueda1.rotation.x = rueda2.rotation.x = Math.PI / 2;
      cab.add(rueda1, rueda2); const banda = en(box(.04, .14, 1.9, 0xdce2e8), .62, 2.5, 0); cab.add(banda); p.partes.rueda = [rueda1, rueda2]; p.partes.cab = cab; cab.position.set(-.9, 0, 0); g.add(cab);
      g.add(en(box(.55, .9, 1.2, 0xd9dde2), 1.8, 1.55, 0));                                             // morsa
      const rod = []; for (let i = 0; i < 7; i++) { const r = en(cil(.12, 1.6, 0x9aa6b2), -4.2 - i * .6, .85, 0); r.rotation.x = Math.PI / 2; g.add(r); rod.push(r); }
      g.add(en(box(4.4, .12, .12, 0x7a8da1), -5.6, .78, .8)); g.add(en(box(4.4, .12, .12, 0x7a8da1), -5.6, .78, -.8));
      for (let i = 0; i < 6; i++) { const r = en(cil(.12, 1.6, 0x9aa6b2), 3.8 + i * .6, .85, 0); r.rotation.x = Math.PI / 2; g.add(r); }
      g.add(en(box(1.1, 1.3, .8, 0xe9ecef), 3.2, 1.2, 1.7)); g.add(en(box(1.1, .6, .9, 0x5b9bd5), 1, .3, -1.7));
    } else if (k === 1) {                                              // cizalladora-punzonadora Pedimax (ironworker)
      g.add(en(box(4.2, .6, 2.6, osc), 0, .3, 0)); g.add(en(box(1.3, 3.6, 1.8, azul), -.4, 2.1, -.2)); g.add(en(box(2.8, 1, 1.9, 0x1b90ff), .8, 3.4, -.2));
      const ram1 = box(.35, 1.4, .5, 0xd9dde2); ram1.position.set(-1.4, 2.2, .45); g.add(ram1); const ram2 = box(.35, 1.4, .5, 0xd9dde2); ram2.position.set(1.7, 2.2, .45); g.add(ram2);
      p.partes.ram = [ram1, ram2]; g.add(en(box(2.2, .22, 1.3, gris), -2.2, 1.35, .7)); g.add(en(box(2.2, .22, 1.3, gris), 2.8, 1.35, .7)); g.add(en(box(1, .9, 1.4, 0x374b5c), -.2, 1.0, -1.5)); g.add(en(box(.9, .5, .7, 0xe9ecef), 3.4, 1.0, -1.2));
      for (let i = 0; i < 5; i++) { const r = en(cil(.1, 3.2, 0x9aa6b2), -4 - i * .5, .85, .9); r.rotation.z = Math.PI / 2; g.add(r); }
    } else if (k === 2) {                                              // mesa CNC de plasma y oxicorte
      g.add(en(box(7.4, .9, 4, osc), 0, .45, 0)); g.add(en(box(6.9, .12, 3.5, 0x6d7b8a), 0, 1, 0));
      for (let i = -3; i <= 3; i++) g.add(en(box(.06, .22, 3.3, 0x9aa6b2), i * .9, 1.1, 0));
      for (const dz of [-2.1, 2.1]) g.add(en(box(7.8, .2, .18, azul), 0, 1.15, dz));
      const portico = new THREE.Group(); portico.add(en(box(.45, 1.9, .5, azul), 0, 1.5, -2.1)); portico.add(en(box(.45, 1.9, .5, azul), 0, 1.5, 2.1)); portico.add(en(box(.55, .5, 4.9, 0x1b90ff), 0, 2.6, 0));
      const carro = new THREE.Group(); carro.add(en(box(.9, .6, 1), 0, 2.15, 0)); carro.add(en(cil(.07, .9, 0xd9dde2), 0, 1.55, 0)); const chispa = en(esf(.18, 0xffb347, { emissive: 0xff7a00, emissiveIntensity: 1.6 }), 0, 1.15, 0); chispa.visible = false; carro.add(chispa);
      portico.add(carro); portico.position.x = -2.5; g.add(portico); p.partes.portico = portico; p.partes.carro = carro; p.partes.chispa = chispa;
      g.add(en(box(1.6, 1.4, 1.3, 0xe9ecef), -4.8, 1.0, 2.9)); const campana = box(6.4, .35, 3, 0xaab6c3, { transparent: true, opacity: .45 }); campana.position.set(0, 3.9, 0); g.add(campana); g.add(en(cil(.45, 2.4, 0x9aa6b2), 3.2, 5.1, 0));
    } else {                                                           // roscadora RIDGID
      g.add(en(box(2.8, .5, 1.6, osc), 0, .25, 0)); g.add(en(box(1.4, 1.5, 1.2, azul), -.2, 1.3, 0));
      const mandril = en(cil(.5, .8, 0xd9dde2), 1.0, 1.3, 0); mandril.rotation.z = Math.PI / 2; g.add(mandril); p.partes.mandril = mandril;
      g.add(en(box(.5, .9, 1, 0x374b5c), 1.7, .8, 0)); g.add(en(box(1.2, .22, .9, 0x4a7fc1), -.2, 2.2, 0));
      for (let i = 0; i < 6; i++) { const r = en(cil(.08, 3.2, 0xb0b8c0), -2.6 - i * .3, .9, -.9); r.rotation.z = Math.PI / 2; g.add(r); }
    }
    const torre = new THREE.Group(); torre.add(en(cil(.08, 2.2, 0x223548), 0, 1.1, 0)); const luces = [0xe74c3c, 0xffb020, 0x2ecc71].map((c, i) => { const l = en(cil(.22, .28, 0x4b5b6b, { emissive: 0x000000 }), 0, 2.4 + i * .32, 0); l.userData.color = c; torre.add(l); return l; });
    torre.position.set(-e.ancho / 2 - .3, 0, e.largo / 2 + .6); g.add(torre); p.luces = luces;
    g.position.copy(V(e.x, e.z)); marcar(g, { tipo: 'maquina', k, etiqueta: MAQN[k] }); estatico.add(g);
    p.et = etiqueta(MAQN[k].replace('Cizalladora Punzonadora', 'Cizalla-punzonadora').replace('Sierra Cinta', 'Sierra cinta'), V(e.x, e.z, 4.6), 'maq');
    p.lote = new THREE.Group(); p.lote.position.copy(V(e.x, e.z, k === 2 ? 1.25 : 1.3)); estatico.add(p.lote);
    anim.push(t => {
      const a = p.activa && !p.falla;
      if (k === 0 && p.partes.rueda) { p.partes.rueda.forEach(r => { r.rotation.y += a ? .28 : 0; }); p.partes.cab.position.y = a ? Math.abs(Math.sin(t * .0016)) * -.35 : 0; }
      if (k === 1 && p.partes.ram) p.partes.ram.forEach((r, i) => { r.position.y = a ? 2.2 - Math.max(0, Math.sin(t * .006 + i * 2)) * .75 : 2.2; });
      if (k === 2 && p.partes.portico) { const f = a ? Math.sin(t * .0007) : 0; p.partes.portico.position.x = -2.5 + (a ? (f * .5 + .5) * 5 : 0); p.partes.carro.position.z = a ? Math.sin(t * .0021) * 1.5 : 0; p.partes.chispa.visible = a && Math.sin(t * .05) > -.4; }
      if (k === 3 && p.partes.mandril) p.partes.mandril.rotation.x += a ? .35 : 0;
      const col = p.falla ? 0 : a ? 2 : (p.espera ? 1 : -1);
      p.luces.forEach((l, i) => { const on = i === col; l.material = on ? mat(l.userData.color, { emissive: l.userData.color, emissiveIntensity: .9 }) : mat(0x4b5b6b); });
    });
    maq[k] = p; return p;
  }
  for (let k = 0; k < 4; k++) construirMaquina(k);

  /* ---------- puentes grúa ---------- */
  const gruas = [];
  [['Puente grúa A (10 t)', 0], ['Puente grúa B (10 t)', 1]].forEach(([nombre, gi]) => {
    const e = E[nombre], g = new THREE.Group(), alto = e.alto;
    for (const dz of [-13.8, 13.8]) { g.add(en(box(e.ancho, .45, .5, 0xe9730c), 0, alto, dz)); for (let x = -e.ancho / 2 + 3; x < e.ancho / 2; x += 7) g.add(en(box(.3, alto - .4, .3, 0xb85c0a), x, (alto - .4) / 2, dz)); }
    g.position.copy(V(e.x, e.z)); grupoGruas.add(g);
    const puente = new THREE.Group(); puente.add(en(box(.95, .95, 28, 0xffb347), 0, 0, 0)); puente.add(en(box(1.3, .5, .9, 0x5b738b), 0, -.3, -13.8)); puente.add(en(box(1.3, .5, .9, 0x5b738b), 0, -.3, 13.8));
    const carro = new THREE.Group(); carro.add(en(box(1.9, .7, 1.9, 0x5b738b), 0, -.8, 0)); const cable = en(cil(.04, 1, 0x223548), 0, -2, 0); carro.add(cable); const gancho = new THREE.Group(); gancho.add(en(box(.5, .6, .5, 0xe9730c), 0, 0, 0)); carro.add(gancho); puente.add(carro);
    puente.position.set(e.x - CX, alto, e.z - CZ); grupoGruas.add(puente);
    const carga = new THREE.Group(); grupoGruas.add(carga);
    const o = { gi, e, puente, carro, cable, gancho, carga, x: e.x, z: e.z, h: 3, parado: true };
    marcar(puente, { tipo: 'grua', g: gi, etiqueta: nombre }); gruas[gi] = o;
  });
  function ponerGrua(o, x, z, h) {
    o.puente.position.x = x - CX; o.carro.position.z = z - o.e.z; o.puente.position.z = o.e.z - CZ;
    const alto = o.e.alto; const largo = Math.max(.6, alto - h - 1.2); o.cable.scale.set(.04, largo, .04); o.cable.position.y = -.9 - largo / 2; o.gancho.position.y = -.9 - largo - .3;
    o.carga.position.set(x - CX, h, z - CZ);
  }

  /* ---------- dinámico: lotes, personal, camiones, material ---------- */
  const lotesObj = new Map();
  let estadoAct = null, ctxAct = {};
  function limpiarDin() { for (const o of [...dinamico.children]) dinamico.remove(o); for (const g of gruas) while (g.carga.children.length) g.carga.remove(g.carga.children[0]); animDin.length = 0; }
  const animDin = [];
  function figuraLote(l, escala = 1) {
    const g = new THREE.Group(); const n = Math.min(Math.max(1, l.n_piezas), 6), color = COLOR_ETAPA[l.etapa] || 0x8a97a6, largo = Math.min(Math.max(l.largo, 1.5), 7.5) * escala;
    const grosor = .14 + Math.min(.26, Math.sqrt(l.kg) / 220);
    for (let i = 0; i < n; i++) { const perfil = l.perfil.startsWith('PL') ? box(largo * .5, .06, .8, color) : box(largo, grosor, grosor * 1.4, color); perfil.position.set((i % 2) * .15, (Math.floor(i / 3)) * (grosor + .05), ((i % 3) - 1) * (grosor * 2 + .06)); g.add(perfil); }
    if (l.nc) { const m = esf(.2, 0xe74c3c, { emissive: 0xe74c3c, emissiveIntensity: .6 }); m.position.set(0, grosor * 2 + .4, 0); g.add(m); }
    marcar(g, { tipo: 'lote', lote: l, etiqueta: `OT ${l.cod ?? l.pid} · ${l.elemento} ${l.perfil} · ${Math.round(l.kg)} kg` }); return g;
  }
  const avatar = (c, ref, pose = 'quieto') => {
    const g = new THREE.Group(); g.add(en(cil(.26, 1.1, c), 0, .72, 0)); g.add(en(esf(.25, 0xf1c9a5), 0, 1.5, 0)); const casco = en(esf(.28, 0xffd23f), 0, 1.58, 0); casco.scale.y = .62; g.add(casco);
    const brazo = en(box(.12, .7, .12, c), .34, 1.0, 0); g.add(brazo); g.userData.brazo = brazo; marcar(g, ref); return g;
  };
  function ubicarCola(zona, i) {
    const [c, sx, sz] = COLAS[zona]; const cols = zona === 'limpieza' || zona === 'buffer' ? 1 : Math.max(1, Math.floor(sx / 4.2));
    if (zona === 'limpieza') return c.clone().add(new THREE.Vector3(0, 0, (i - 8) * 2.2));
    if (zona === 'buffer') return c.clone().add(new THREE.Vector3((i % 2) * 1.8 - .9, 0, (Math.floor(i) - 6) * 2.0));
    const fila = Math.floor(i / cols), col = i % cols; return c.clone().add(new THREE.Vector3((col - cols / 2) * 4.2 + 2, fila * .5, (fila % 3) * 1.3 - 1.3));
  }
  const nombrePersona = (grupo, k) => { const lista = (meta.personal || []).filter(p => p.grupo === grupo); return lista.length ? lista[Math.abs(k) % lista.length] : { nombre: grupo + ' ' + k, rol: '' }; };

  function actualizar(est, ctx = {}) {
    estadoAct = est; ctxAct = ctx; limpiarDin();
    const T = est.t, h = est.hora;
    const paradasMaq = {}; est.paradas.forEach(p => { paradasMaq[p.maquina] = p; });
    const opPorLote = {}; est.ops.forEach(o => { opPorLote[o.lote_id] = o; });
    const proyPorPid = Object.fromEntries(est.proyectos.map(p => [p.pid, p]));
    // máquinas
    maq.forEach(m => { m.activa = false; m.espera = false; m.falla = !!paradasMaq[m.k]; m.lote.clear(); });
    est.ops.forEach(o => { if (String(o.recurso).startsWith('maq')) { const m = maq[+o.recurso[3]]; m.activa = true; const L = est.lotes.find(l => l.id === o.lote_id); if (L) { const f = figuraLote({ ...L, etapa: 'HABILITADO' }); m.lote.add(f); } } });
    // personal y estaciones
    const ocupados = {};
    let nPers = 0; const colaIdx = {};
    est.ops.forEach(o => {
      const L = est.lotes.find(l => l.id === o.lote_id); if (!L) return; const pr = proyPorPid[o.pid]; const colr = COLOR_CONTR[pr && pr.contratista] || 0x0a6ed1;
      const pos = o.recurso === 'armado' ? posMesa(o.estacion) : o.recurso === 'soldeo' ? posPuesto(o.estacion) : o.recurso === 'limpieza' ? posLimp(o.estacion) : null;
      if (o.recurso.startsWith('maq')) {
        const m = maqE[+o.recurso[3]]; const per = nombrePersona('Planta', o.id); const av = avatar(0x2f6fb3, { tipo: 'persona', persona: per, estacion: m.nombre, trabajo: o.tipo, etiqueta: per.nombre }); av.position.copy(V(m.x - m.ancho / 2 - .8, m.z + m.largo / 2 + .9)); dinamico.add(av); nPers++;
        animDin.push(t => { av.userData.brazo.rotation.z = Math.sin(t * .006 + o.id) * .5; }); return;
      }
      const n = o.personas || 1; const fig = figuraLote({ ...L, etapa: o.recurso === 'armado' ? 'ARMADO' : o.recurso === 'soldeo' ? (o.tipo === 'retrabajo' ? 'RETRABAJO' : 'SOLDEO') : 'LIMPIEZA' });
      fig.position.copy(pos).add(new THREE.Vector3(0, o.recurso === 'armado' ? 1.25 : .9, 0)); dinamico.add(fig);
      for (let i = 0; i < n; i++) {
        const per = nombrePersona(pr ? pr.contratista : 'Planta', o.id * 7 + i); const a = (i / n) * Math.PI * 2 + .5;
        const av = avatar(colr, { tipo: 'persona', persona: { ...per, grupo: pr ? pr.contratista : per.grupo }, estacion: o.recurso, trabajo: o.tipo, etiqueta: per.nombre }, 'trabajo');
        av.position.copy(pos).add(new THREE.Vector3(Math.cos(a) * 2.3, 0, Math.sin(a) * 1.5)); av.lookAt(pos.x, 0, pos.z); dinamico.add(av); nPers++;
        animDin.push(t => { av.userData.brazo.rotation.x = Math.sin(t * .008 + o.id + i) * .8; });
      }
      ocupados[o.pid] = (ocupados[o.pid] || 0) + n;
      if (o.recurso === 'soldeo') {
        const arco = esf(.22, 0xcfe8ff, { emissive: 0x88c4ff, emissiveIntensity: 2.2 }); arco.position.copy(pos).add(new THREE.Vector3(0, 1.4, 0)); dinamico.add(arco);
        const luz = new THREE.PointLight(0x88c4ff, 3, 7); luz.position.copy(arco.position); dinamico.add(luz);
        animDin.push(t => { const v = .5 + .5 * Math.sin(t * .09 + o.id); arco.visible = v > .25; luz.intensity = 2 + 4 * v; });
      }
      if (o.recurso === 'limpieza') { const ch = esf(.14, 0xffb347, { emissive: 0xff8800, emissiveIntensity: 1.6 }); ch.position.copy(pos).add(new THREE.Vector3(.4, 1.0, 0)); dinamico.add(ch); animDin.push(t => { ch.visible = Math.sin(t * .05 + o.id) > -.2; }); }
      if (o.recurso === 'armado' || o.recurso === 'soldeo') { const est2 = o.recurso === 'armado' ? mesaObj[o.estacion] : puestoObj[o.estacion]; }
    });
    // luces de puestos
    Object.entries(puestoObj).forEach(([n, g]) => { const usado = est.ops.some(o => o.recurso === 'soldeo' && o.estacion == n); g.userData.luz.material = usado ? mat(0x2ecc71, { emissive: 0x2ecc71, emissiveIntensity: .9 }) : mat(0x9aa6b2); });
    // personal en espera (de las cuadrillas de los proyectos activos) durante el turno
    const enTurno = (h >= 7 && h < 15) || est.ops.some(o => !String(o.recurso).startsWith('maq') && (o.t_ini % 24) >= 15);
    if (h >= 7 && h < 15) {
      let k = 0;
      est.proyectos.forEach(p => { [7, 8, 9].forEach(j => { const libres = Math.max(0, Math.round(p.crew[j]) - (ocupados[p.pid] || 0) / 3); for (let i = 0; i < Math.min(libres, 5); i++, k++) { if (k > 36) return; const per = nombrePersona(p.contratista, p.pid * 13 + j * 5 + i); const av = avatar(COLOR_CONTR[p.contratista] || 0x0a6ed1, { tipo: 'persona', persona: { ...per, grupo: p.contratista }, estacion: 'En espera', trabajo: 'sin lote asignado', etiqueta: per.nombre + ' (en espera)' }); av.position.copy(V(48 + (k % 6) * 1.1, 37.5 + Math.floor(k / 6) * 1.1)); av.rotation.y = Math.PI; dinamico.add(av); nPers++; } }); });
    }
    est.ing.forEach(i => { const p = proyPorPid[i.pid]; for (let n = 0; n < Math.min(i.personas, 6); n++) { const per = nombrePersona('Oficina técnica', i.pid * 3 + n); const av = avatar(0x7a8da1, { tipo: 'persona', persona: per, estacion: 'Oficina técnica', trabajo: 'ingeniería', etiqueta: per.nombre }); av.position.copy(V(ofiE.x - 4 + n * 1.5, ofiE.z - ofiE.largo / 2 - 1.4)); dinamico.add(av); } });
    // lotes que no están en una estación: colas, grúa, externos
    const cuenta = {};
    est.lotes.forEach(l => {
      if (opPorLote[l.id] && !String(opPorLote[l.id].recurso).startsWith('grua')) return;
      if (l.estado === 'grua') { l._grua = true; return; }
      let zona = 'patio';
      if (l.estado === 'externo') return;
      if (l.estado === 'entregado') return;
      if (l.etapa === 'ARMADO') zona = 'mesa'; else if (l.etapa === 'SOLDEO') zona = 'puesto'; else if (l.etapa === 'LIMPIEZA' || l.etapa === 'RETRABAJO') zona = 'limpieza';
      else if (l.etapa === 'DOBLEZ') zona = 'buffer'; else if (l.etapa === 'LISTO_PINTURA' || l.etapa === 'PINTADO') zona = 'salida';
      else if (l.etapa === 'MOVIMIENTO') zona = l.ubic === 'buffer' ? 'buffer' : l.ubic === 'mesa' ? 'mesa' : l.ubic === 'puesto' ? 'puesto' : l.ubic === 'limpieza' ? 'limpieza' : 'salida';
      let p;
      if (l.etapa === 'MOVIMIENTO' && l.origen_recurso) p = l.origen_recurso.startsWith('maq') ? posMaq(+l.origen_recurso[3]).clone().add(new THREE.Vector3(3.6, 0, -1.8)) : l.origen_recurso === 'armado' ? posMesa(l.origen_estacion) : l.origen_recurso === 'soldeo' ? posPuesto(l.origen_estacion) : posLimp(l.origen_estacion);
      else { const i = cuenta[zona] = (cuenta[zona] || 0) + 1; p = ubicarCola(zona, i - 1); }
      const f = figuraLote(l); f.position.copy(p).add(new THREE.Vector3(0, l.etapa === 'MOVIMIENTO' && l.origen_recurso === 'armado' ? 1.25 : .2, 0)); dinamico.add(f);
    });
    // grúas: lotes en traslado
    gruas.forEach(g => { g._mov = null; });
    est.movs.forEach(m => {
      const l = est.lotes.find(x => x.id === m.lote_id); if (!l) return; const g = gruas[m.grua];
      const origen = l.origen_recurso ? (l.origen_recurso.startsWith('maq') ? posMaq(+l.origen_recurso[3]) : l.origen_recurso === 'armado' ? posMesa(l.origen_estacion) : l.origen_recurso === 'soldeo' ? posPuesto(l.origen_estacion) : posLimp(l.origen_estacion)) : ubicarCola('patio', 0);
      const dest = m.destino === 'buffer' ? ubicarCola('buffer', 5) : m.destino === 'mesa' ? ubicarCola('mesa', 8) : m.destino === 'puesto' ? ubicarCola('puesto', 8) : m.destino === 'limpieza' ? ubicarCola('limpieza', 8) : ubicarCola('salida', 8);
      const fig = figuraLote({ ...l, etapa: 'MOVIMIENTO' }); g.carga.add(fig); g._mov = { m, origen, dest, fig };
    });
    // camiones
    est.camiones.forEach(c => {
      const dock = c.tipo === 'doblez' ? muelleD : c.tipo === 'pintura' ? muelleP : muelleO; const saliendo = T <= c.t_ini + .2 && T >= c.t_ini - 2.5; const entrando = T >= c.t_fin - .1 && T <= c.t_fin + 3;
      if (c.tipo === 'obra' ? !(T >= c.t_ini - 1 && T <= c.t_fin + 1) : !(saliendo || entrando)) return;
      const t = new THREE.Group(); const cab = box(2.4, 2.4, 2.5, c.tipo === 'obra' ? 0x0a6ed1 : c.tipo === 'pintura' ? 0x61cdc0 : 0xffd23f); cab.position.set(-4.8, 1.7, 0); const rem = box(8, 2.7, 2.7, 0xf5f7fa); rem.position.set(0, 1.85, 0);
      for (const dx of [-4.8, -1.8, 2]) for (const dz of [-1.35, 1.35]) { const r = cil(.55, .4, 0x223548); r.rotation.x = Math.PI / 2; r.position.set(dx, .65, dz); t.add(r); }
      t.add(cab, rem); if (c.kg > 0) { const carga = box(Math.min(6.5, 1.5 + c.kg / 4500), .9, 2, entrando ? 0x3fb0a6 : 0xff8a4c); carga.position.set(0, 3.3, 0); t.add(carga); }
      t.rotation.y = Math.PI / 2; t.position.copy(V(dock.x - 5.2, dock.z)).add(new THREE.Vector3(0, .5, 0)); t.rotation.y = -Math.PI / 2; t.position.x = V(dock.x - 5, dock.z).x;
      marcar(t, { tipo: 'camion', camion: c, etiqueta: `Camión ${c.tipo} · ${Math.round(c.kg)} kg · ${c.n_lotes} lotes` }); dinamico.add(t);
    });
    // material en racks y patio
    const stockKg = est.proyectos.reduce((a, p) => a + p.stock_kg, 0); let fardos = Math.min(40, Math.round(stockKg / 1800)); let i0 = 0;
    racksE.forEach((e, ri) => { for (let n = 0; n < 9 && fardos > 0; n++, fardos--, i0++) { const f = box(e.ancho * .8, .5, e.largo * .22, [0x4b86c5, 0x2f6fb3, 0x7aa5d6, 0x8a97a6][i0 % 4]); f.position.copy(V(e.x, e.z - e.largo / 2 + .9 + Math.floor(n / 3) * 2.4, .9 + (n % 3) * 1.2)); marcar(f, { tipo: 'material', etiqueta: 'Fardo de perfiles en rack R' + (ri + 1), rack: ri + 1 }); dinamico.add(f); } });
    for (let n = 0; fardos > 0; n++, fardos--) { const f = box(3.4, .5, 1.3, [0x8a97a6, 0xd9a066][n % 2]); f.position.copy(V(patioE.x - 16 + (n % 8) * 4.4, patioE.z - 5 + Math.floor(n / 8) * 2.4, .4)); marcar(f, { tipo: 'material', etiqueta: 'Fardo de planchas/perfiles en el patio' }); dinamico.add(f); }
    luzDelDia(h, enTurno || est.ops.some(o => (o.t_ini % 24) >= 15));
  }

  /* ---------- hora del día ---------- */
  function luzDelDia(h) {
    const dia = Math.max(0, Math.min(1, (Math.sin(((h - 6) / 24) * Math.PI * 2 - Math.PI / 2 + Math.PI / 2 * 0) + .35) / 1.35)); const noche = 1 - Math.max(0, Math.min(1, ((h >= 6 && h <= 18) ? 1 : (h > 18 && h < 20 ? (20 - h) / 2 : h > 4 && h < 6 ? (h - 4) / 2 : 0))));
    sol.intensity = 1.5 * (1 - noche) + .15; hemi.intensity = 1.15 * (1 - noche) + .35; sol.position.set(Math.cos(((h - 6) / 12) * Math.PI) * 70, 90 * Math.max(.2, 1 - noche), 40);
    contenedor.style.background = noche > .6 ? 'linear-gradient(180deg,#1a2740 0%,#0e1626 70%,#0a101c 100%)' : noche > .1 ? 'linear-gradient(180deg,#f6b98a 0%,#a8b7d8 55%,#6f86b5 100%)' : 'linear-gradient(180deg,#f4f9ff 0%,#dfeeff 55%,#cfe3f7 100%)';
    const on = noche > .3; lamparas.forEach(l => { l.material = on ? mat(0xfff2c4, { emissive: 0xffe9a0, emissiveIntensity: 1.2 }) : mat(0xfff2c4); }); luzNave.forEach(l => { l.material = on ? mat(0xfff7d6, { emissive: 0xfff0b0, emissiveIntensity: 1.1 }) : mat(0xfff7d6); });
  }

  /* ---------- animación continua (grúas con interpolación) ---------- */
  function animarT(T) {
    gruas.forEach(g => {
      const mv = g._mov;
      if (!mv) { const s = Math.sin(performance.now() * .0002 + g.gi) * 4; ponerGrua(g, g.e.x + s, g.e.z + s * .3, 3); return; }
      const f = Math.max(0, Math.min(1, (T - mv.m.t_ini) / Math.max(mv.m.t_fin - mv.m.t_ini, 1e-6))); const a = mv.origen, b = mv.dest; const e = f < .5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2;
      const x = a.x + (b.x - a.x) * e + CX, z = a.z + (b.z - a.z) * e + CZ; const alt = 1.3 + Math.sin(Math.PI * Math.min(1, f * 1.1)) * 2.2; ponerGrua(g, x, z, alt);
    });
  }

  /* ---------- selección, vuelo de cámara y bucle ---------- */
  const rayo = new THREE.Raycaster(), p2 = new THREE.Vector2(); let selBox = null, vuelo = null;
  const refDe = o => { while (o) { if (o.userData && o.userData.ref) return o.userData.ref; o = o.parent; } return null; };
  function buscar(ev) {
    const r = renderer.domElement.getBoundingClientRect(); p2.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1); rayo.setFromCamera(p2, camara);
    const hit = rayo.intersectObjects([...dinamico.children, ...grupoGruas.children, ...estatico.children], true).find(h => refDe(h.object) && h.object.visible && !techos.includes(h.object)); return hit ? { ref: refDe(hit.object), obj: hit.object } : null;
  }
  function raizDe(obj, ref) { let o = obj; while (o.parent && refDe(o.parent) === ref) o = o.parent; return o; }
  function seleccionar(ref, obj) { if (selBox) { escena.remove(selBox); selBox = null; } if (!ref || !obj) return; const raiz = raizDe(obj, ref); selBox = new THREE.Box3Helper(new THREE.Box3().setFromObject(raiz), 0x1b90ff); escena.add(selBox); }
  function volarA(v, dist = 26) { const dir = camara.position.clone().sub(ctl.target).normalize(); vuelo = { t0: performance.now(), dur: 900, a: ctl.target.clone(), b: v.clone(), pa: camara.position.clone(), pb: v.clone().add(dir.multiplyScalar(dist)) }; }
  function enfocar(ref, obj) { if (!obj) return; const bb = new THREE.Box3().setFromObject(raizDe(obj, ref)); const c = bb.getCenter(new THREE.Vector3()); const tam = bb.getSize(new THREE.Vector3()).length(); volarA(c, Math.max(12, tam * 2.2)); }
  const VISTAS = { general: [V(50, 25), [78, 66, 88]], navea: [V(22, 17), [4, 46, 52]], naveb: [V(72, 17), [4, 48, 54]], patio: [V(36, 38), [6, 30, 36]], muelles: [V(96, 17), [-28, 26, 32]],
    oficina: [V(80, 43), [-4, 20, 28]], maquinas: [V(27, 6, 1), [8, 30, 26]] };
  function vista(n) { const [c, o] = VISTAS[n] || VISTAS.general; const k = n === 'general' ? Math.max(1, 1.5 / camara.aspect) : 1; vuelo = { t0: performance.now(), dur: 1000, a: ctl.target.clone(), b: c.clone(), pa: camara.position.clone(), pb: c.clone().add(new THREE.Vector3(o[0] * k, o[1] * k, o[2] * k)) }; }
  let abajo = null;
  renderer.domElement.addEventListener('pointerdown', e => { abajo = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener('pointerup', e => { if (!abajo || Math.hypot(e.clientX - abajo[0], e.clientY - abajo[1]) > 5) return; const h = buscar(e); seleccionar(h && h.ref, h && h.obj); if (opts.alSeleccionar) opts.alSeleccionar(h ? h.ref : null, h ? h.obj : null); });
  renderer.domElement.addEventListener('dblclick', e => { const h = buscar(e); if (h) enfocar(h.ref, h.obj); });
  let ultimo = 0;
  renderer.domElement.addEventListener('pointermove', e => { const t = performance.now(); if (t - ultimo < 60) return; ultimo = t; const h = buscar(e), r = contenedor.getBoundingClientRect(); if (h && (h.ref.etiqueta || h.ref.nombre)) { tip.textContent = h.ref.etiqueta || h.ref.nombre; tip.style.left = (e.clientX - r.left + 14) + 'px'; tip.style.top = (e.clientY - r.top + 12) + 'px'; tip.classList.remove('oculto'); renderer.domElement.style.cursor = 'pointer'; } else { tip.classList.add('oculto'); renderer.domElement.style.cursor = 'grab'; } });
  renderer.domElement.addEventListener('pointerleave', () => tip.classList.add('oculto'));
  function tam() { const w = contenedor.clientWidth, h = contenedor.clientHeight; renderer.setSize(w, h, false); camara.aspect = w / Math.max(h, 1); camara.updateProjectionMatrix(); }
  const ro = new ResizeObserver(tam); ro.observe(contenedor); tam(); camara.position.set(128, 86, 114); ctl.update();
  let vivo = true, Tlocal = 0, ultT = performance.now(), techosOn = true; const v3 = new THREE.Vector3();
  function bucle(t) {
    if (!vivo) return; requestAnimationFrame(bucle);
    if (vuelo) { const f = Math.min(1, (t - vuelo.t0) / vuelo.dur); const e = f < .5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2; ctl.target.lerpVectors(vuelo.a, vuelo.b, e); camara.position.lerpVectors(vuelo.pa, vuelo.pb, e); if (f >= 1) vuelo = null; }
    ctl.update(); anim.forEach(f => f(t)); animDin.forEach(f => f(t));
    const cerca = camara.position.distanceTo(ctl.target) < 75; techos.forEach(r => { r.visible = techosOn && !cerca; });     // al acercarse se abre el techo
    if (estadoAct) animarT(Tlocal || estadoAct.t);
    const w = contenedor.clientWidth, h = contenedor.clientHeight;
    for (const e of etiquetas) { v3.copy(e.v).project(camara); const vis = v3.z < 1 && Math.abs(v3.x) < 1.1 && Math.abs(v3.y) < 1.1; e.el.style.display = vis ? '' : 'none'; if (vis) e.el.style.transform = `translate(-50%,-100%) translate(${(v3.x * .5 + .5) * w}px, ${(-v3.y * .5 + .5) * h}px)`; }
    renderer.render(escena, camara);
  }
  requestAnimationFrame(bucle); vista('general');
  return {
    actualizar, seleccionar: (ref) => seleccionar(ref, null), enfocar, vista, setT: T => { Tlocal = T; },
    techos: v => { techosOn = v; }, etiquetas: v => { capaEt.style.display = v ? '' : 'none'; },
    destruir() { vivo = false; ro.disconnect(); ctl.dispose(); renderer.dispose(); renderer.domElement.remove(); capaEt.remove(); tip.remove(); },
  };
}
