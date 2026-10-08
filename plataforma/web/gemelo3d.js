/* SteelPlan · gemelo 3D de la planta (three.js local). Todo es SIMULADO.
   Reconstruye la planta hora a hora desde /api/gemelo/estado. Cámaras 3D (perspectiva), 2D (plano), caminata y seguimiento, con atajos de
   teclado; personas articuladas que caminan por las puertas, camiones que recorren la calle de servicio hasta su muelle, máquinas con
   componentes (inspección, vista explosionada y rayos X). La geometría y las texturas son procedurales (gemelo_modelos.js). */
import * as THREE from '/static/vendor/three/three.module.js';
import { OrbitControls } from '/static/vendor/three/OrbitControls.js';
import { RoomEnvironment } from '/static/vendor/three/RoomEnvironment.js';
import * as MD from '/static/gemelo_modelos.js';

const { caja, cil, esf, en, rot, mat, M } = MD;
const CX = 50, CZ = 25;
const V = (x, z, y = 0) => new THREE.Vector3(x - CX, y, z - CZ);
const hash = s => [...String(s)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
const lerp = (a, b, t) => a + (b - a) * t;
const ease = f => f < .5 ? 4 * f * f * f : 1 - Math.pow(-2 * f + 2, 3) / 2;
const lerpAng = (a, b, f) => { const d = ((b - a + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI; return a + d * f; };
const COLOR_ETAPA = { HABILITADO: 0x4c86d4, MOVIMIENTO: 0xffffff, DOBLEZ: 0xa58be6, ARMADO: 0xf0a04b, SOLDEO: 0xe0661a, RETRABAJO: 0xe0392b, LIMPIEZA: 0x4fb37d, LISTO_PINTURA: 0xf2c94c, PINTURA: 0x3fb0a6, PINTADO: 0x2d9a90, ENTREGADO: 0x9aa4ae };
const COLOR_CONTR = { 'T&C FABRICACION': 0xd9731a, 'FRANCISCO TARRILLO': 0x7b5cc4, 'RFR METALICAS': 0x23915b, 'ROGGER TORRES': 0xb8342b, 'LHL INGENIERIA': 0x2f6fb8 };

export function crearGemelo(contenedor, meta, opts = {}) {
  /* ------------------------------------------------------------ renderer, luces y entorno */
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0; renderer.setClearColor(0x000000, 0);
  contenedor.appendChild(renderer.domElement);
  const dom = renderer.domElement; dom.style.cssText = 'display:block;width:100%;height:100%;outline:none;touch-action:none'; dom.tabIndex = 0;
  const escena = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer); escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture; escena.environmentIntensity = .55;
  const hemi = new THREE.HemisphereLight(0xffffff, 0xaab6c4, .7); escena.add(hemi);
  const sol = new THREE.DirectionalLight(0xfff4e0, 2.1); sol.castShadow = true; sol.shadow.mapSize.set(2048, 2048);
  Object.assign(sol.shadow.camera, { left: -85, right: 85, top: 62, bottom: -62, near: 10, far: 340 }); sol.shadow.bias = -0.0003; sol.shadow.normalBias = .04;
  escena.add(sol, sol.target);
  const estatico = new THREE.Group(), dinamico = new THREE.Group(), grupoGruas = new THREE.Group(), grupoAgentes = new THREE.Group(), grupoCamiones = new THREE.Group();
  escena.add(estatico, dinamico, grupoGruas, grupoAgentes, grupoCamiones);
  const techos = [], lamparas = [], luzNave = [], animEst = [], etiquetas = [], maquinas = [];
  const capaEt = document.createElement('div'); capaEt.className = 'p3d-etiquetas'; contenedor.appendChild(capaEt);
  const tip = document.createElement('div'); tip.className = 'p3d-tip oculto'; contenedor.appendChild(tip);
  const ayuda = document.createElement('div'); ayuda.className = 'p3d-ayuda oculto'; contenedor.appendChild(ayuda);
  const marcar = (obj, ref) => { obj.traverse(o => { if (!o.userData.ref) o.userData.ref = ref; }); return obj; };
  const marcarFuerte = (obj, ref) => { obj.traverse(o => { o.userData.ref = ref; }); return obj; };

  /* ------------------------------------------------------------ cámaras: 3D (perspectiva), 2D (plano ortogonal) y caminata */
  const camP = new THREE.PerspectiveCamera(32, 1, .4, 1200), camO = new THREE.OrthographicCamera(-50, 50, 30, -30, -400, 800);
  camO.up.set(0, 0, -1); camO.position.set(0, 300, 0); camO.lookAt(0, 0, 0);
  const ctlP = new OrbitControls(camP, dom), ctlO = new OrbitControls(camO, dom);
  for (const c of [ctlP, ctlO]) { c.enableDamping = true; c.dampingFactor = .06; c.zoomToCursor = true; c.zoomSpeed = .9; c.panSpeed = .9; c.rotateSpeed = .55; c.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN }; c.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN }; }
  ctlP.maxPolarAngle = 1.52; ctlP.minDistance = 2.5; ctlP.maxDistance = 330; ctlP.screenSpacePanning = false;
  ctlO.enableRotate = false; ctlO.screenSpacePanning = true; ctlO.minZoom = .5; ctlO.maxZoom = 16; ctlO.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.PAN, RIGHT: THREE.MOUSE.PAN };
  ctlO.enabled = false;
  let modo = '3d', cam = camP, ctl = ctlP, poseP = null;
  const walk = { yaw: 0, pitch: 0, arrastra: null }, teclas = new Set();
  let vuelo = null, seguir = null, rotarAuto = false, selRef = null, selObj = null, selBox = null, techosOn = true, etiquetasOn = true, hintOn = false, Tlocal = 0, Tprev = null;

  /* ------------------------------------------------------------ posiciones (tabla sim_planta_elemento) */
  const E = {}; meta.elementos.forEach(e => { E[e.nombre] = e; });
  const por = pref => meta.elementos.filter(e => e.nombre.startsWith(pref)).sort((a, b) => a.nombre.localeCompare(b.nombre, 'es', { numeric: true }));
  const MAQN = ['Sierra Cinta Kaltenbach', 'Cizalladora Punzonadora Pedimax', 'Mesa CNC', 'Roscadora RIDGID'];
  const maqE = MAQN.map(n => E[n]), mesasE = por('Mesa de armado'), puestosE = por('Puesto de soldeo'), zonasE = por('Zona de limpieza'), racksE = por('Rack de perfiles');
  const bufferE = por('Buffer')[0], patioE = por('Patio')[0], muelleD = E['Muelle de doblez (servicio externo)'], muelleP = E['Muelle a granallado y pintura (externo)'], muelleO = E['Muelle de despacho a obra'];
  const ofiE = E['Oficina técnica'], compE = E['Compras'];
  const posMaq = k => V(maqE[k].x, maqE[k].z), posMesa = n => V(mesasE[n - 1].x, mesasE[n - 1].z), posPuesto = n => V(puestosE[n - 1].x, puestosE[n - 1].z);
  const posLimp = c => { const z = zonasE[c <= 4 ? 0 : 1]; const i = (c - 1) % 4; return V(z.x - 2 + (i % 2) * 4, z.z - 2 + Math.floor(i / 2) * 4); };
  const COLAS = { patio: [V(patioE.x, patioE.z), 45, 16], buffer: [V(bufferE.x, bufferE.z), 3, 26], mesa: [V(68, 11.5), 30, 1.8], puesto: [V(72, 19.2), 34, 1.4], limpieza: [V(83.5, 13), 1.6, 18], salida: [V(80, 35.5), 30, 4] };
  const LOTE_MAQ = [[-2.6, 1.08, 0], [3.2, 1.62, .1], [0, 1.12, 0], [-2.4, 1.42, 0]];     // dónde apoya el lote en cada máquina (x, y, z locales)
  const salidaOffMaq = k => V(maqE[k].x + (k === 0 ? 4.6 : k === 1 ? 4.6 : k === 2 ? 4.8 : 4.2), maqE[k].z + 2.6);

  /* ------------------------------------------------------------ etiquetas ancladas (con mástil al piso) y letreros pintados */
  const mastiles = new THREE.Group(); estatico.add(mastiles);
  function etiqueta(texto, v, clase = '', prio = 5, mastil = true) {
    const e = document.createElement('div'); e.className = 'p3d-et ' + clase; e.textContent = texto; capaEt.appendChild(e);
    const o = { el: e, v: v.clone(), clase, prio, w: 0 }; etiquetas.push(o);
    if (mastil && v.y > .5) { const m = cil(.02, v.y, mat(0x5b6570, { metalness: .3 }), false); m.position.set(v.x, v.y / 2, v.z); mastiles.add(m); o.mastil = m; }
    return o;
  }
  function letreroPiso(texto, e, o = {}) {
    const t = MD.pintarPiso(texto, e.ancho, e.largo, o), w = e.ancho * .86, h = Math.min(e.largo * .9, w * (t.image.height / t.image.width));
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
    m.rotation.x = -Math.PI / 2; m.rotation.z = o.giro || 0; m.position.copy(V(e.x, e.z, .06)); estatico.add(m);
  }
  /* material con una copia de la textura (para repetirla distinto sin afectar a las demás superficies) */
  const matRep = (nombre, rx, ry, o = {}) => { const t = MD.texturas()[nombre].clone(); t.needsUpdate = true; t.repeat.set(rx, ry); return new THREE.MeshStandardMaterial({ map: t, roughness: .9, metalness: .02, ...o }); };

  /* ------------------------------------------------------------ entorno: suelo, calle de servicio, cerco, árboles, alumbrado */
  const plano = (w, d, m, x, y, z) => { const p = new THREE.Mesh(new THREE.PlaneGeometry(w, d), m); p.rotation.x = -Math.PI / 2; p.position.set(x, y, z); p.receiveShadow = true; estatico.add(p); return p; };
  plano(340, 240, matRep('pasto', 80, 56), 0, -.3, 0);
  plano(100, 50, matRep('concreto', 24, 12), 0, -.1, 0);
  plano(340, 16, matRep('asfalto', 56, 2.6), 0, -.12, 44);                       // calle frontal (z mundo 69)
  plano(16, 150, matRep('asfalto', 2.6, 25), 58, -.11, -8);                      // calle de servicio al este (x mundo 108)
  for (let i = -8; i <= 8; i++) plano(5, .3, new THREE.MeshBasicMaterial({ color: 0xf2f4f6 }), i * 18, -.09, 44);
  for (let i = -5; i <= 4; i++) plano(.3, 5, new THREE.MeshBasicMaterial({ color: 0xf2f4f6 }), 58, -.09, i * 14 - 8);
  estatico.add(en(caja(1.6, .16, 52, mat(0xb3b8be, { roughness: .9 }), false), 49.8, -.02, 0));       // vereda
  const cerco = (x0, z0, x1, z1) => { const L = Math.hypot(x1 - x0, z1 - z0), a = Math.atan2(z1 - z0, x1 - x0), g = new THREE.Group();
    g.add(en(caja(L, 1.7, .03, mat(0x8a96a3, { transparent: true, opacity: .45, metalness: .5, roughness: .5 }), false), 0, .95, 0));
    for (let d = 0; d <= L; d += 4) g.add(en(cil(.04, 2.0, M.aceroOsc(), false), d - L / 2, 1, 0)); g.add(en(caja(L, .05, .05, M.aceroOsc(), false), 0, 1.92, 0));
    g.position.set((x0 + x1) / 2 - CX, 0, (z0 + z1) / 2 - CZ); g.rotation.y = -a; estatico.add(g); };
  cerco(0, 0, 100, 0); cerco(0, 0, 0, 50); cerco(0, 50, 60, 50); cerco(72, 50, 100, 50); cerco(100, 0, 100, 3); cerco(100, 36, 100, 50);
  const arbol = (x, z, s = 1) => { const g = new THREE.Group(); g.add(en(cil(.16 * s, 2.4 * s, mat(0x6b4a2b, { roughness: .95, metalness: 0 })), 0, 1.2 * s, 0));
    for (const [dx, dy, dz, r] of [[0, 3.5, 0, 1.9], [.9, 2.9, .4, 1.35], [-.8, 3.0, -.5, 1.4], [.1, 4.4, .2, 1.3]]) g.add(en(esf(r * s, mat(0x4f8a4a, { roughness: .9, metalness: 0 })), dx * s, dy * s, dz * s));
    g.position.set(x - CX, 0, z - CZ); estatico.add(g); };
  [[-10, -8], [-13, 10], [-9, 30], [124, -6], [126, 14], [124, 30], [20, -10], [50, -12], [80, -10], [-10, 48], [128, 52], [-18, 20], [134, 2], [136, 24], [-6, 62], [60, 85], [110, 90]].forEach(([x, z], i) => arbol(x, z, .85 + (i % 3) * .18));
  const farola = (x, z) => { const g = new THREE.Group(); g.add(en(cil(.1, 7, mat(0x59636d, { metalness: .5 }), false), 0, 3.5, 0)); g.add(en(caja(1.4, .1, .1, M.aceroOsc(), false), .6, 7, 0)); const l = en(caja(.8, .12, .35, mat(0xfff2c4)), 1.2, 6.92, 0); g.add(l); lamparas.push(l); g.position.set(x - CX, 0, z - CZ); estatico.add(g); };
  [[10, 60], [45, 60], [75, 60], [4, 3], [96, 3], [104, 40], [104, -10], [30, 78], [80, 78]].forEach(([x, z]) => farola(x, z));
  const auto = (x, z, c) => { const a = new THREE.Group(); a.add(en(MD.cajaRedonda(4.3, .8, 1.8, .2, mat(c, { metalness: .5, roughness: .3 })), 0, .75, 0)); a.add(en(MD.cajaRedonda(2.3, .62, 1.6, .2, M.vidrio()), -.2, 1.3, 0));
    for (const dx of [-1.4, 1.4]) for (const dz of [-.9, .9]) a.add(en(rot(cil(.34, .22, M.goma()), Math.PI / 2, 0, 0), dx, .34, dz)); a.position.set(x - CX, 0, z - CZ); a.rotation.y = Math.PI / 2; estatico.add(a); };
  [[8, 56, 0xb23a3a], [12.5, 56, 0x3a6fb2], [17, 56, 0xe8eaed], [21.5, 56, 0x2a2d31]].forEach(([x, z, c]) => auto(x, z, c));
  etiqueta('Estacionamiento', V(15, 56, 3), 'zona', 2);

  /* ------------------------------------------------------------ naves: losa, columnas I, cerchas, techo ondulado, puertas, luminarias */
  const nave = (e, texto) => {
    const g = new THREE.Group(), w = e.ancho, d = e.largo, h = e.alto, acero = mat(0x6e7a86, { metalness: .6, roughness: .5 });
    const piso = new THREE.Mesh(new THREE.PlaneGeometry(w, d), matRep('piso', w / 5, d / 5)); piso.rotation.x = -Math.PI / 2; piso.position.y = .02; piso.receiveShadow = true; g.add(piso);
    for (const z of [-d / 2 + 1.4, d / 2 - 1.4]) g.add(en(caja(w - 3, .02, .16, mat(0x2e9e5b, { roughness: .6 }), false), 0, .04, z));   // pasillos peatonales
    for (let x = -w / 2; x <= w / 2 + .1; x += w / 6) for (const z of [-d / 2, d / 2]) {
      const col = new THREE.Mesh(new THREE.BoxGeometry(.36, h, .24), acero); col.position.set(x, h / 2, z); col.castShadow = true; g.add(col); g.add(en(caja(.7, .12, .5, M.aceroOsc(), false), x, .06, z));
    }
    for (let x = -w / 2; x <= w / 2 + .1; x += w / 6) { for (const z of [-1, 1]) { const v = caja(.14, .3, d / 2 + .5, acero, false); v.position.set(x, h + .6, z * d / 4); v.rotation.x = -z * .1; g.add(v); } g.add(en(caja(.12, 1.8, .12, acero, false), x, h + .9, 0)); }
    for (const z of [-1, 1]) { const t = new THREE.Mesh(new THREE.BoxGeometry(w + 1.4, .12, d / 2 + 1.0), matRep('ondulado', w / 1.2, 1, { color: 0x2f6fb3, metalness: .5, roughness: .45, transparent: true, opacity: .62 })); t.position.set(0, h + 1.3, z * d / 4); t.rotation.x = -z * .1; t.receiveShadow = true; g.add(t); techos.push(t); }
    const mpar = () => matRep('ondulado', w / 1.2, 1, { color: 0xb9c6d4, metalness: .5, roughness: .55 });
    const px = w / 4, hueco = 2.6;                                                                                        // el muro frontal y trasero deja el vano del portón
    for (const z of [-d / 2, d / 2]) for (const [x0, x1] of [[-w / 2, px - hueco], [px + hueco, w / 2]]) { const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, 3.6, .25), mpar()); m.position.set((x0 + x1) / 2, 1.9, z); m.castShadow = true; m.receiveShadow = true; g.add(m); }
    for (const x of [-w / 2, w / 2]) { const m = new THREE.Mesh(new THREE.BoxGeometry(.25, 3.6, d), mpar()); m.position.set(x, 1.9, 0); m.receiveShadow = true; g.add(m); }
    for (const z of [-d / 2, d / 2]) {                                                                                       // portones abiertos (marco naranja y vano oscuro)
      g.add(en(caja(5.4, .3, .4, M.naranja(), false), w / 4, 3.75, z)); for (const dx of [-2.6, 2.6]) g.add(en(caja(.25, 3.7, .4, M.naranja(), false), w / 4 + dx, 1.85, z));
    }
    for (let x = -w / 2 + 5; x < w / 2; x += 9) { const lz = caja(2.4, .12, .5, mat(0xfff7d6)); lz.position.set(x, h - .3, 0); g.add(lz); luzNave.push(lz); }
    g.position.copy(V(e.x, e.z)); estatico.add(g); etiqueta(texto, V(e.x, e.z - d / 2 - .5, h + 3.2), 'nave', 9);
  };
  nave(E['Nave A · recepción y habilitado'], 'Nave A · recepción y habilitado'); nave(E['Nave B · armado y soldeo'], 'Nave B · armado, soldeo y limpieza');

  const edificio = (e, color, texto, techo) => {
    const g = new THREE.Group(), w = e.ancho, d = e.largo, fz = d / 2 + .08;       // el frente da a la calle (sur)
    g.add(en(caja(w, 7, d, mat(color, { roughness: .7, metalness: .05 })), 0, 3.5, 0)); g.add(en(caja(w + .8, .4, d + .8, mat(techo, { roughness: .5, metalness: .3 })), 0, 7.2, 0));
    for (const piso of [1.6, 5]) for (let i = -1; i <= 1; i++) { const v = caja(w * .2, 1.5, .12, M.vidrio(), false); v.position.set(i * w * .3, piso + .5, fz); g.add(v); luzNave.push(v); }
    g.add(en(caja(1.8, 2.7, .12, M.aceroOsc(), false), 0, 1.35, fz)); g.add(en(caja(w * .7, .7, .1, new THREE.MeshBasicMaterial({ map: MD.etiquetaTex(texto.toUpperCase(), { w: 512, h: 96, tam: 46 }) }), false), 0, 6.4, fz + .05));
    g.add(en(caja(1.2, .8, .9, M.pintGris()), w / 2 - 1.5, 7.8, 0)); g.position.copy(V(e.x, e.z)); marcar(g, { tipo: 'edificio', nombre: texto, etiqueta: texto }); estatico.add(g);
  };
  edificio(ofiE, 0xeef1f4, 'Oficina técnica', 0x1f5aa6); edificio(compE, 0xe9edf1, 'Compras', 0x1f5aa6);
  { const g = new THREE.Group(); g.add(en(caja(11, 3.4, 6.4, mat(0xe9edf1)), 0, 1.7, 0)); g.add(en(caja(11.8, .4, 7.2, mat(0x6e7a86, { metalness: .4 })), 0, 3.6, 0)); for (let i = -2; i <= 2; i++) g.add(en(caja(1.3, 1.2, .1, M.vidrio(), false), i * 2.1, 1.9, 3.25));
    g.position.copy(V(55, 43)); marcar(g, { tipo: 'edificio', nombre: 'Comedor y vestuarios', etiqueta: 'Comedor y vestuarios' }); estatico.add(g); etiqueta('Comedor y vestuarios', V(55, 43, 5.4), 'zona', 4); }
  { const g = new THREE.Group(); g.add(en(caja(3, 2.6, 3, mat(0xf4f4f1)), 0, 1.3, 0)); g.add(en(caja(3.8, .3, 3.8, mat(0xd9731a)), 0, 2.8, 0)); g.position.copy(V(102, 43)); estatico.add(g); etiqueta('Garita', V(102, 43, 4.2), 'zona', 2); }

  /* ------------------------------------------------------------ patios, buffer, muelles y racks */
  const zonaPlana = (e, tinte, nombre, texto, o = {}) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(e.ancho, e.largo), matRep('concreto', e.ancho / 6, e.largo / 6, { color: tinte })); m.rotation.x = -Math.PI / 2; m.position.copy(V(e.x, e.z, .03)); m.receiveShadow = true; estatico.add(m);
    const borde = (a, b, c, d) => { const l = caja(a, .02, b, mat(0xf2c40f, { roughness: .6 }), false); l.position.copy(V(e.x + c, e.z + d, .05)); estatico.add(l); };
    borde(e.ancho, .18, 0, -e.largo / 2); borde(e.ancho, .18, 0, e.largo / 2); borde(.18, e.largo, -e.ancho / 2, 0); borde(.18, e.largo, e.ancho / 2, 0);
    marcar(m, { tipo: 'zona', nombre, etiqueta: nombre }); if (texto) letreroPiso(texto, e, o);
  };
  zonaPlana(patioE, 0xdad5c3, 'Patio de acopio de perfiles y planchas', 'PATIO DE ACOPIO'); zonaPlana(bufferE, 0xcfd9e4, 'Buffer de piezas habilitadas', null);
  zonaPlana({ x: 80, z: 35.5, ancho: 36, largo: 6 }, 0xcfd6dd, 'Patio de salida (piezas listas y pintadas)', 'PATIO DE SALIDA');
  { const m = new THREE.Mesh(new THREE.PlaneGeometry(22, 1.6), new THREE.MeshBasicMaterial({ map: MD.pintarPiso('BUFFER', 22, 1.6, { tam: 120, color: 'rgba(60,120,200,.85)' }), transparent: true, depthWrite: false })); m.rotation.x = -Math.PI / 2; m.rotation.z = Math.PI / 2; m.position.copy(V(bufferE.x, bufferE.z, .06)); estatico.add(m); }
  for (const [e, texto] of [[muelleD, 'Doblez (externo)'], [muelleP, 'Granallado y pintura'], [muelleO, 'Despacho a obra']]) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(e.ancho, .6, e.largo), matRep('concreto', 1, 1.5, { color: 0xc2cad2 })); m.position.copy(V(e.x, e.z, .3)); m.receiveShadow = true; m.castShadow = true; estatico.add(m); marcar(m, { tipo: 'muelle', nombre: e.nombre, etiqueta: e.nombre });
    estatico.add(en(caja(.3, .9, e.largo - 1, M.negro()), e.x - CX + e.ancho / 2 + .1, .6, e.z - CZ));
    estatico.add(en(caja(e.ancho + .6, .2, e.largo + .6, mat(0x1f5aa6, { metalness: .4 })), e.x - CX, 4.6, e.z - CZ));
    for (const dz of [-e.largo / 2, e.largo / 2]) estatico.add(en(cil(.1, 4.2, M.aceroOsc(), false), e.x - CX, 2.4, e.z - CZ + dz));
    etiqueta(texto, V(e.x, e.z, 6.3), 'zona', 4);
  }
  racksE.forEach((e, i) => { const g = new THREE.Group(), rk = mat(0xd9731a, { metalness: .4, roughness: .55 });
    for (const dz of [-e.largo / 2, 0, e.largo / 2]) { g.add(en(caja(.2, 4.4, .2, rk), 0, 2.2, dz)); for (let n = 0; n < 3; n++) for (const lado of [-1, 1]) g.add(en(caja(e.ancho / 2 + .3, .12, .1, rk), lado * (e.ancho / 4 + .1), .7 + n * 1.3, dz)); }
    g.add(en(caja(.12, 4.6, e.largo + .2, M.aceroOsc(), false), 0, 2.3, 0)); g.position.copy(V(e.x, e.z)); marcarFuerte(g, { tipo: 'rack', n: i + 1, etiqueta: 'Rack de perfiles R' + (i + 1) }); estatico.add(g); });

  /* ------------------------------------------------------------ estaciones: mesas, puestos, zonas de limpieza */
  const puestoObj = {}, placaMat = () => MD.matTex('placa', { color: 0xaab3bc, metalness: .6, roughness: .55 });
  mesasE.forEach((e, i) => { const g = new THREE.Group(); g.add(en(caja(e.ancho, .2, e.largo, placaMat()), 0, 1.0, 0));
    for (let k = -3; k <= 3; k++) g.add(en(caja(.04, .02, e.largo - .2, M.aceroOsc(), false), k * 1.0, 1.11, 0));
    for (const dx of [-e.ancho / 2 + .35, e.ancho / 2 - .35]) for (const dz of [-e.largo / 2 + .3, e.largo / 2 - .3]) g.add(en(caja(.2, 1.0, .2, M.aceroOsc(), false), dx, .5, dz));
    for (const dx of [-2.4, 0, 2.4]) { g.add(en(caja(.12, .4, .12, M.naranja()), dx, 1.3, e.largo / 2 - .3)); g.add(en(caja(.35, .05, .12, M.naranja()), dx + .1, 1.52, e.largo / 2 - .3)); }
    g.position.copy(V(e.x, e.z)); marcarFuerte(g, { tipo: 'estacion', clase: 'mesa', n: i + 1, etiqueta: 'Mesa de armado M' + (i + 1) }); estatico.add(g); });
  puestosE.forEach((e, i) => { const g = new THREE.Group(); g.add(en(caja(e.ancho, .06, e.largo, mat(0xdfe6ee, { roughness: .8 }), false), 0, .03, 0));
    for (const [x, z, w, d] of [[0, -e.largo / 2, e.ancho, .08], [-e.ancho / 2, 0, .08, e.largo], [e.ancho / 2, 0, .08, e.largo]]) g.add(en(caja(w, 2.1, d, mat(0xf29a2e, { transparent: true, opacity: .55, roughness: .8 }), false), x, 1.1, z));
    g.add(en(caja(1.6, .75, 1.0, placaMat()), 0, .45, 0));
    const mq = new THREE.Group(); mq.add(en(caja(.6, .9, .5, M.pintAzul()), 0, .45, 0)); mq.add(en(rot(cil(.05, .04, M.cromo(), false), Math.PI / 2, 0, 0), 0, .95, .26)); mq.position.set(e.ancho / 2 - .5, 0, -e.largo / 2 + .5); g.add(mq);
    g.add(en(cil(.12, 1.3, M.rojo()), -e.ancho / 2 + .35, .65, e.largo / 2 - .35));
    const luz = en(esf(.13, mat(0x9aa6b2)), 0, 2.3, 0); g.add(luz); g.userData.luz = luz;
    g.position.copy(V(e.x, e.z)); marcarFuerte(g, { tipo: 'estacion', clase: 'puesto', n: i + 1, etiqueta: 'Puesto de soldeo S' + (i + 1) }); estatico.add(g); puestoObj[i + 1] = g; });
  zonasE.forEach((e, i) => { const g = new THREE.Group(); g.add(en(caja(e.ancho, .05, e.largo, mat(0xdde3e9, { roughness: .8 }), false), 0, .03, 0));
    for (const dx of [-2, 2]) for (const dz of [-2, 2]) { g.add(en(caja(1.7, .8, 1.1, placaMat()), dx, .4, dz)); g.add(en(cil(.12, .2, M.negro(), false), dx - .4, .9, dz)); }
    g.add(en(caja(.6, 1.3, .5, M.pintAzul()), 0, .65, 0)); g.position.copy(V(e.x, e.z)); marcarFuerte(g, { tipo: 'estacion', clase: 'limpieza', n: i + 1, etiqueta: 'Zona de limpieza y liberación L' + (i + 1) }); estatico.add(g);
    letreroPiso('LIMPIEZA L' + (i + 1), { x: e.x, z: e.z + e.largo / 2 + .9, ancho: e.ancho, largo: 1.4 }, { tam: 90, color: 'rgba(60,170,110,.9)' }); });
  letreroPiso('ARMADO', { x: 67, z: 11.6, ancho: 18, largo: 1.6 }, { tam: 100 }); letreroPiso('SOLDEO', { x: 72, z: 24.2, ancho: 18, largo: 1.6 }, { tam: 100 });

  /* ------------------------------------------------------------ máquinas (modelos con componentes) */
  for (let k = 0; k < 4; k++) {
    const e = maqE[k], m = MD.crearMaquina(k); maquinas[k] = m; m.activa = false; m.falla = false; m.espera = false;
    m.g.position.copy(V(e.x, e.z)); marcarFuerte(m.g, { tipo: 'maquina', k, etiqueta: m.nombre }); estatico.add(m.g);
    m.lote = new THREE.Group(); m.lote.position.copy(V(e.x + LOTE_MAQ[k][0], e.z + LOTE_MAQ[k][2], LOTE_MAQ[k][1])); estatico.add(m.lote);
    const zona = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(e.ancho + .6, .02, e.largo + .6)), new THREE.LineBasicMaterial({ color: 0xf2c40f })); zona.position.copy(V(e.x, e.z, .07)); estatico.add(zona);
    m.et = etiqueta(m.nombre, V(e.x, e.z - e.largo / 2 - .4, m.alto + 2.4), 'maq', 8);
    animEst.push(t => { const a = m.activa && !m.falla; m.anim(t, a); const col = m.falla ? 0 : a ? 2 : (m.espera ? 1 : -1); m.luces.forEach((l, i) => { const on = i === col; l.material = on ? mat(l.userData.color, { emissive: l.userData.color, emissiveIntensity: 1.1 }) : mat(0x4b5563); }); });
  }

  /* ------------------------------------------------------------ puentes grúa */
  const gruas = [];
  [['Puente grúa A (10 t)', 0], ['Puente grúa B (10 t)', 1]].forEach(([nombre, gi]) => {
    const e = E[nombre], g = new THREE.Group(), alto = e.alto, acero = mat(0xe08a1a, { metalness: .5, roughness: .5 });
    for (const dz of [-13.8, 13.8]) { g.add(en(caja(e.ancho, .45, .5, acero), 0, alto, dz)); for (let x = -e.ancho / 2 + 3; x < e.ancho / 2; x += 7) g.add(en(caja(.3, alto - .3, .3, mat(0x7c8792, { metalness: .6 }), false), x, (alto - .3) / 2, dz)); }
    g.position.copy(V(e.x, e.z)); grupoGruas.add(g);
    const puente = new THREE.Group(); puente.add(en(caja(.95, 1.0, 28, acero), 0, 0, 0)); puente.add(en(caja(1.3, .5, .9, M.aceroOsc()), 0, -.3, -13.8)); puente.add(en(caja(1.3, .5, .9, M.aceroOsc()), 0, -.3, 13.8)); puente.add(en(caja(.3, .8, 26, M.aceroOsc(), false), .6, -.05, 0));
    const carro = new THREE.Group(); carro.add(en(caja(1.9, .7, 1.9, M.aceroOsc()), 0, -.85, 0)); carro.add(en(rot(cil(.28, 1.2, M.pintAzul()), 0, 0, Math.PI / 2), .5, -.7, .4));
    const cable = en(cil(.03, 1, M.negro(), false), 0, -2, 0); carro.add(cable); const gancho = new THREE.Group(); gancho.add(en(caja(.4, .5, .4, M.amarillo()), 0, 0, 0)); gancho.add(en(cil(.03, .45, M.cromo(), false), 0, -.35, 0)); carro.add(gancho); puente.add(carro);
    puente.position.set(e.x - CX, alto, e.z - CZ); grupoGruas.add(puente);
    const carga = new THREE.Group(); grupoGruas.add(carga);
    gruas[gi] = { gi, e, puente, carro, cable, gancho, carga, mov: null }; marcarFuerte(puente, { tipo: 'grua', g: gi, etiqueta: nombre });
  });
  function ponerGrua(o, x, z, h) {
    o.puente.position.x = x - CX; o.carro.position.z = z - o.e.z; const alto = o.e.alto, ganchoY = h + 1.4, largo = Math.max(.6, alto - 1.2 - ganchoY);
    o.cable.scale.set(.03, largo, .03); o.cable.position.y = -1.2 - largo / 2; o.gancho.position.y = -1.2 - largo; o.carga.position.set(x - CX, h, z - CZ);
  }

  /* ------------------------------------------------------------ dinámico: lotes, personal (agentes que caminan), camiones y material */
  const agentes = new Map(), camiones = new Map(), dinKey = new Map(); let estadoAct = null, animDin = [], deseados = new Map(), insp = null;
  function figuraLote(l) {
    const etapa = l.etapa === 'ESPERA' ? 'HABILITADO' : l.etapa, pintado = l.etapa === 'PINTADO' || l.etapa === 'ENTREGADO';
    const g = MD.crearHaz(l, COLOR_ETAPA[etapa], pintado);
    if (l.nc) { const m = esf(.22, mat(0xe74c3c, { emissive: 0xe74c3c, emissiveIntensity: .8 })); m.position.set(0, g.userData.dim.alto + .45, 0); g.add(m); }
    marcarFuerte(g, { tipo: 'lote', lote: l, etiqueta: `OT ${l.cod ?? l.pid} · ${l.elemento} ${l.perfil} · ${Math.round(l.kg)} kg` }); return g;
  }
  function limpiarDin() { for (const o of [...dinamico.children]) dinamico.remove(o); for (const g of gruas) while (g.carga.children.length) g.carga.remove(g.carga.children[0]); for (const m of maquinas) m.lote.clear(); animDin = []; dinKey.clear(); }
  function ubicarCola(zona, i) {
    const [c, sx] = COLAS[zona];
    if (zona === 'limpieza') return c.clone().add(new THREE.Vector3(0, 0, (i - 8) * 2.6));
    if (zona === 'buffer') return c.clone().add(new THREE.Vector3((i % 2) * 1.8 - .9, 0, (Math.floor(i) - 6) * 2.4));
    const cols = Math.max(1, Math.floor(sx / 5.4)), fila = Math.floor(i / cols), col = i % cols; return c.clone().add(new THREE.Vector3((col - cols / 2) * 5.4 + 2.7, 0, ((fila % 3) - 1) * 2.0));
  }
  const nombrePersona = (grupo, k) => { const lista = (meta.personal || []).filter(p => p.grupo === grupo); return lista.length ? lista[Math.abs(k) % lista.length] : { nombre: grupo + ' ' + k, rol: '', grupo }; };
  const SALIDA = V(55, 40.2);                                                                          // puerta del comedor
  const pedirAgente = (id, ref, pos, mira, pose, color) => { deseados.set(id, { id, ref, pos, mira, pose, color }); };
  function aplicarAgentes(salto) {
    for (const [id, d] of deseados) {
      let a = agentes.get(id);
      if (!a) { const obj = MD.crearPersona({ camisa: d.color, altura: ((hash(id) % 9) - 4) * .012 }); a = { obj, pos: (salto ? d.pos : SALIDA).clone(), fase: (hash(id) % 628) / 100, pose: 'quieto' }; obj.position.copy(a.pos); grupoAgentes.add(obj); agentes.set(id, a); }
      a.dest = d.pos; a.mira = d.mira; a.deseada = d.pose; a.saliendo = false; a.ref = d.ref;
      if (salto) { a.pos.copy(d.pos); a.obj.position.copy(a.pos); }
      marcarFuerte(a.obj, d.ref); dinKey.set('p:' + id, a.obj);
    }
    for (const [id, a] of agentes) if (!deseados.has(id)) { if (salto) { grupoAgentes.remove(a.obj); agentes.delete(id); } else { a.dest = SALIDA; a.saliendo = true; a.deseada = 'quieto'; a.mira = null; } }
  }
  const puertaX = x => (x < -3 ? 33.75 : 83.75) - CX;                                                  // portón de cada nave en el muro sur (z mundo 30)
  function objetivo(a) {
    const p = a.pos, d = a.dest, fuera = p.z > 5.3, dentro = p.z < 4.7, vaDentro = d.z < 4.7, vaFuera = d.z > 5.3;
    if (fuera && vaDentro) { const dx = puertaX(d.x); return Math.abs(p.x - dx) > .6 && p.z > 6.2 ? new THREE.Vector3(dx, 0, 6.5) : new THREE.Vector3(dx, 0, 4.2); }
    if (dentro && vaFuera) { const dx = puertaX(p.x); return Math.abs(p.x - dx) > .6 && p.z < 4.2 ? new THREE.Vector3(dx, 0, 4.2) : new THREE.Vector3(dx, 0, 6.5); }
    return d;
  }
  function moverAgentes(dt, t) {
    for (const [id, a] of agentes) {
      const tg = objetivo(a), dx = tg.x - a.pos.x, dz = tg.z - a.pos.z, d = Math.hypot(dx, dz), llego = tg === a.dest && d <= .12;
      if (!llego) { const v = Math.min(d, 1.5 * dt); a.pos.x += dx / d * v; a.pos.z += dz / d * v; a.obj.rotation.y = lerpAng(a.obj.rotation.y, Math.atan2(dx, dz), Math.min(1, dt * 8)); a.pose = 'caminar'; }
      else { a.pose = a.deseada; if (a.mira) a.obj.rotation.y = lerpAng(a.obj.rotation.y, Math.atan2(a.mira.x - a.pos.x, a.mira.z - a.pos.z), Math.min(1, dt * 6)); if (a.saliendo) { grupoAgentes.remove(a.obj); agentes.delete(id); continue; } }
      a.obj.position.copy(a.pos); MD.posar(a.obj, a.pose, t, a.fase);
    }
  }

  /* camiones: llegan por la calle de servicio, se estacionan junto al muelle y salen hacia el norte */
  const caminoLlega = z => [[150, 69], [112, 69], [108.5, 62], [103.5, z + 26], [103.0, z + 8], [103.0, z - 4.5]].map(([x, zz]) => V(x, zz));
  const caminoSale = z => [[103.0, z - 4.5], [104.5, -22], [108, -44]].map(([x, zz]) => V(x, zz));
  function puntoEnCamino(pts, u) {
    const L = []; let tot = 0; for (let i = 1; i < pts.length; i++) { const l = pts[i].distanceTo(pts[i - 1]); L.push(l); tot += l; }
    let d = Math.min(Math.max(u, 0), 1) * tot, i = 0; while (i < L.length - 1 && d > L[i]) { d -= L[i]; i++; }
    const f = Math.min(1, d / L[i]); return { p: pts[i].clone().lerp(pts[i + 1], f), dir: pts[i + 1].clone().sub(pts[i]).normalize(), dist: Math.min(Math.max(u, 0), 1) * tot };
  }
  function pedirCamion(c, T) {
    const vuelta = c.tipo !== 'obra' && T >= c.t_fin - .1, key = `${c.pid}|${c.tipo}|${Math.round(c.t_ini)}|${Math.round(c.t_fin)}|${vuelta ? 'v' : 'i'}`; let o = camiones.get(key);
    if (!o) {
      const color = c.tipo === 'obra' ? 0x1f5aa6 : c.tipo === 'pintura' ? 0xe9edf1 : 0xe9b410, g = MD.crearCamion({ color }), dock = c.tipo === 'doblez' ? muelleD : c.tipo === 'pintura' ? muelleP : muelleO;
      o = { g, c, vuelta, ant: null, lleg: caminoLlega(dock.z), sal: caminoSale(dock.z) }; grupoCamiones.add(g); camiones.set(key, o);
      const n = Math.min(8, Math.max(2, Math.round(c.kg / 3500))), haz = MD.crearHaz({ perfil: 'W16x31', largo: 9, n_piezas: n, kg: c.kg, etapa: vuelta && c.tipo === 'pintura' ? 'PINTADO' : 'LISTO_PINTURA' }, 0xf2c94c, vuelta && c.tipo === 'pintura');
      haz.position.set(-.5, .02, 0); g.userData.carga.add(haz); o.haz = g.userData.carga;
    }
    o.vivo = true; marcarFuerte(o.g, { tipo: 'camion', camion: c, etiqueta: `Camión de ${c.tipo} · ${Math.round(c.kg)} kg · ${c.n_lotes} lotes` }); dinKey.set('c:' + key, o.g); return o;
  }
  function moverCamiones(T) {
    for (const [, o] of camiones) {
      const c = o.c; let a, b;
      if (c.tipo === 'obra') { a = c.t_ini - 1.4; b = c.t_fin + 1.6; } else if (o.vuelta) { a = c.t_fin - .1; b = c.t_fin + 3.2; } else { a = c.t_ini - 2.6; b = c.t_ini + .6; }
      if (T < a || T > b) { o.g.visible = false; continue; } o.g.visible = true;
      const f = (T - a) / (b - a); let r, fase;
      if (f < .35) { r = puntoEnCamino(o.lleg, f / .35); fase = 'llega'; } else if (f < .7) { r = puntoEnCamino(o.lleg, 1); fase = 'parado'; } else { r = puntoEnCamino(o.sal, (f - .7) / .3); fase = 'sale'; }
      const dir = fase === 'parado' ? new THREE.Vector3(0, 0, -1) : r.dir;
      o.g.position.copy(r.p); o.g.rotation.y = Math.atan2(dir.z, -dir.x);                               // el frente del modelo apunta a −x local
      const dist = (fase === 'sale' ? 1000 : 0) + r.dist; if (o.ant != null) { const dd = dist - o.ant; if (Math.abs(dd) < 200) (o.g.userData.ruedas || []).forEach(w => { w.rotation.z -= dd / .52; }); } o.ant = dist;
      o.haz.visible = o.vuelta ? f < .5 : (c.tipo === 'obra' ? f > .45 : f > .45);
    }
  }

  /* ------------------------------------------------------------ actualizar(estado): reconstruye lo dinámico */
  function actualizar(est) {
    estadoAct = est; limpiarDin(); deseados = new Map();
    const salto = Tprev == null || Math.abs(est.t - Tprev) > 3 || est.t < Tprev - .01; Tprev = est.t; if (salto) Tlocal = est.t;
    const h = est.hora, paradasMaq = {}; est.paradas.forEach(p => { paradasMaq[p.maquina] = p; });
    const opPorLote = {}; est.ops.forEach(o => { opPorLote[o.lote_id] = o; });
    const proyPorPid = Object.fromEntries(est.proyectos.map(p => [p.pid, p])), loteDe = Object.fromEntries(est.lotes.map(l => [l.id, l]));
    maquinas.forEach(m => { m.activa = false; m.espera = false; m.falla = !!paradasMaq[m.k]; });
    est.ops.forEach(o => { if (String(o.recurso).startsWith('maq')) { const m = maquinas[+o.recurso[3]]; m.activa = true; const L = loteDe[o.lote_id]; if (L) { const f = figuraLote({ ...L, etapa: 'HABILITADO' }); f.scale.setScalar(.7); m.lote.add(f); dinKey.set('l:' + L.id, f); } } });
    const ocupados = {};
    est.ops.forEach(o => {
      const L = loteDe[o.lote_id]; if (!L) return; const pr = proyPorPid[o.pid], colr = COLOR_CONTR[pr && pr.contratista] || 0x2f6fb8;
      if (String(o.recurso).startsWith('maq')) {
        const k = +o.recurso[3], e = maqE[k], per = nombrePersona('Planta', o.id);
        pedirAgente('op:' + k, { tipo: 'persona', persona: { ...per, grupo: 'Planta' }, estacion: e.nombre, trabajo: o.tipo, etiqueta: per.nombre }, V(e.x + (k === 0 ? -.5 : k === 1 ? 1.2 : k === 2 ? 3.2 : 1.0), e.z + e.largo / 2 + .9), V(e.x, e.z), 'operar', 0x2f6fb8); return;
      }
      const n = o.personas || 1, pos = o.recurso === 'armado' ? posMesa(o.estacion) : o.recurso === 'soldeo' ? posPuesto(o.estacion) : posLimp(o.estacion);
      const fig = figuraLote({ ...L, etapa: o.recurso === 'armado' ? 'ARMADO' : o.recurso === 'soldeo' ? (o.tipo === 'retrabajo' ? 'RETRABAJO' : 'SOLDEO') : 'LIMPIEZA' }); fig.scale.setScalar(.75);
      fig.position.copy(pos).add(new THREE.Vector3(0, o.recurso === 'armado' ? 1.14 : .8, 0)); dinamico.add(fig); dinKey.set('l:' + L.id, fig);
      const pose = o.recurso === 'armado' ? 'martillar' : o.recurso === 'soldeo' ? 'soldar' : 'esmerilar';
      for (let i = 0; i < n; i++) {
        const per = nombrePersona(pr ? pr.contratista : 'Planta', o.id * 7 + i), ang = (i / n) * Math.PI * 2 + .6, rx = o.recurso === 'armado' ? 2.9 : 1.7, rz = o.recurso === 'armado' ? 1.6 : 1.4;
        pedirAgente(`${o.recurso}:${o.estacion}:${i}`, { tipo: 'persona', persona: { ...per, grupo: pr ? pr.contratista : per.grupo }, estacion: o.recurso, trabajo: o.tipo, etiqueta: per.nombre }, pos.clone().add(new THREE.Vector3(Math.cos(ang) * rx, 0, Math.sin(ang) * rz)), pos, pose, colr);
      }
      ocupados[o.pid] = (ocupados[o.pid] || 0) + n;
      if (o.recurso === 'soldeo') { const arco = esf(.12, mat(0xcfe8ff, { emissive: 0x88c4ff, emissiveIntensity: 3 })); arco.position.copy(pos).add(new THREE.Vector3(0, 1.45, 0)); dinamico.add(arco); const luz = new THREE.PointLight(0x88c4ff, 4, 8); luz.position.copy(arco.position); dinamico.add(luz); animDin.push(t => { const v = .5 + .5 * Math.sin(t * .09 + o.id); arco.visible = v > .25; luz.intensity = 2 + 5 * v; }); }
      if (o.recurso === 'limpieza') { const ch = esf(.1, mat(0xffb347, { emissive: 0xff8800, emissiveIntensity: 2 })); ch.position.copy(pos).add(new THREE.Vector3(.6, 1.0, 0)); dinamico.add(ch); animDin.push(t => { ch.visible = Math.sin(t * .05 + o.id) > -.2; }); }
    });
    Object.entries(puestoObj).forEach(([n, g]) => { const usado = est.ops.some(o => o.recurso === 'soldeo' && o.estacion == n); g.userData.luz.material = usado ? mat(0x2ecc71, { emissive: 0x2ecc71, emissiveIntensity: 1 }) : mat(0x9aa6b2); });
    if (h >= 7 && h < 15) {                                                  // cuadrilla sin lote asignado: espera junto al comedor
      let k = 0; est.proyectos.forEach(p => { [7, 8, 9].forEach(j => { const libres = Math.max(0, Math.round(p.crew[j]) - (ocupados[p.pid] || 0) / 3); for (let i = 0; i < Math.min(libres, 4); i++, k++) { if (k > 30) return;
        const per = nombrePersona(p.contratista, p.pid * 13 + j * 5 + i); pedirAgente(`espera:${p.pid}:${j}:${i}`, { tipo: 'persona', persona: { ...per, grupo: p.contratista }, estacion: 'En espera', trabajo: 'sin lote asignado', etiqueta: per.nombre + ' (en espera)' }, V(48.5 + (k % 6) * 1.2, 38.0 + Math.floor(k / 6) * 1.2), V(50, 30), 'quieto', COLOR_CONTR[p.contratista] || 0x2f6fb8); } }); });
    }
    est.ing.forEach(i => { for (let n = 0; n < Math.min(i.personas, 6); n++) { const per = nombrePersona('Oficina técnica', i.pid * 3 + n); pedirAgente(`ing:${i.pid}:${n}`, { tipo: 'persona', persona: per, estacion: 'Oficina técnica', trabajo: 'ingeniería', etiqueta: per.nombre }, V(ofiE.x - 4 + n * 1.6, ofiE.z + ofiE.largo / 2 + 1.8), V(ofiE.x, ofiE.z), 'quieto', 0x7a8da1); } });
    aplicarAgentes(salto);
    const cuenta = {}, simple = est.lotes.length > 90;
    est.lotes.forEach(l => {
      if (opPorLote[l.id] && !String(opPorLote[l.id].recurso).startsWith('grua')) return;
      if (l.estado === 'grua' || l.estado === 'externo' || l.estado === 'entregado') return;
      let zona = 'patio';
      if (l.etapa === 'ARMADO') zona = 'mesa'; else if (l.etapa === 'SOLDEO') zona = 'puesto'; else if (l.etapa === 'LIMPIEZA' || l.etapa === 'RETRABAJO') zona = 'limpieza';
      else if (l.etapa === 'DOBLEZ') zona = 'buffer'; else if (l.etapa === 'LISTO_PINTURA' || l.etapa === 'PINTADO') zona = 'salida';
      else if (l.etapa === 'MOVIMIENTO') zona = l.ubic === 'buffer' ? 'buffer' : l.ubic === 'mesa' ? 'mesa' : l.ubic === 'puesto' ? 'puesto' : l.ubic === 'limpieza' ? 'limpieza' : 'salida';
      let p;
      if (l.etapa === 'MOVIMIENTO' && l.origen_recurso) p = origenDe(l);
      else { const i = cuenta[zona] = (cuenta[zona] || 0) + 1; p = ubicarCola(zona, i - 1); }
      const f = figuraLote(simple ? { ...l, n_piezas: Math.min(l.n_piezas, 3) } : l); f.scale.setScalar(.8); f.position.copy(p); f.rotation.y = zona === 'limpieza' || zona === 'buffer' ? Math.PI / 2 : 0; dinamico.add(f); dinKey.set('l:' + l.id, f);
    });
    gruas.forEach(g => { g.mov = null; });
    est.movs.forEach(m => {
      const l = loteDe[m.lote_id]; if (!l) return; const g = gruas[m.grua], origen = l.origen_recurso ? origenDe(l) : ubicarCola('patio', 0);
      const dest = m.destino === 'buffer' ? ubicarCola('buffer', 5) : m.destino === 'mesa' ? ubicarCola('mesa', 8) : m.destino === 'puesto' ? ubicarCola('puesto', 8) : m.destino === 'limpieza' ? ubicarCola('limpieza', 8) : ubicarCola('salida', 8);
      const fig = figuraLote({ ...l, etapa: 'MOVIMIENTO' }); fig.scale.setScalar(.8); g.carga.add(fig); dinKey.set('l:' + l.id, fig); g.mov = { m, origen, dest, fig };
    });
    camiones.forEach(o => { o.vivo = false; }); est.camiones.forEach(c => pedirCamion(c, est.t));
    for (const [k, o] of camiones) if (!o.vivo) { grupoCamiones.remove(o.g); camiones.delete(k); }
    // material en los racks (perfiles largos sobre los brazos) y en el patio
    const stockKg = est.proyectos.reduce((a, p) => a + p.stock_kg, 0), perfiles = ['W12x26', 'W16x31', 'HEA 200', 'C 10x15.3', 'L 3x3x1/4', 'Tubo 4"']; let fardos = Math.min(36, Math.round(stockKg / 1800)), i0 = 0;
    racksE.forEach((e, ri) => { for (let n = 0; n < 6 && fardos > 0; n++, fardos--, i0++) {
      const f = MD.crearHaz({ perfil: perfiles[i0 % perfiles.length], largo: 6.5, n_piezas: 4, etapa: 'ESPERA' }, 0x8aa0b8); f.rotation.y = Math.PI / 2; f.scale.setScalar(.85);
      f.position.copy(V(e.x + (n % 2 ? 1.2 : -1.2), e.z, .78 + Math.floor(n / 2) * 1.3)); marcarFuerte(f, { tipo: 'material', etiqueta: 'Fardo de perfiles en rack R' + (ri + 1) }); dinamico.add(f); } });
    for (let n = 0; fardos > 0; n++, fardos--) { const f = MD.crearHaz({ perfil: perfiles[n % perfiles.length], largo: 6, n_piezas: 5, etapa: 'ESPERA' }, 0x8aa0b8); f.position.copy(V(patioE.x - 18 + (n % 5) * 8.6, patioE.z + 4 + Math.floor(n / 5) * 3.4, .0)); marcarFuerte(f, { tipo: 'material', etiqueta: 'Fardo de perfiles en el patio de acopio' }); dinamico.add(f); }
    luzDelDia(h);
    // la selección sigue al objeto reconstruido
    if (selRef) { const nuevo = reencontrar(selRef); if (nuevo) selObj = nuevo; }
    if (insp && opts.alInspeccionar) opts.alInspeccionar(infoInsp());
  }
  function origenDe(l) {
    const r = l.origen_recurso;
    return r.startsWith('maq') ? salidaOffMaq(+r[3]) : r === 'armado' ? posMesa(l.origen_estacion).add(new THREE.Vector3(0, 1.14, 0)) : r === 'soldeo' ? posPuesto(l.origen_estacion).add(new THREE.Vector3(0, .8, 0)) : posLimp(l.origen_estacion).add(new THREE.Vector3(0, .8, 0));
  }
  function reencontrar(ref) {
    if (ref.tipo === 'lote') return dinKey.get('l:' + ref.lote.id) || null;
    if (ref.tipo === 'persona') { for (const [, a] of agentes) if (a.ref && a.ref.persona && ref.persona && a.ref.persona.nombre === ref.persona.nombre) return a.obj; }
    if (ref.tipo === 'camion') { for (const [k, o] of camiones) if (k.startsWith(`${ref.camion.pid}|${ref.camion.tipo}|${Math.round(ref.camion.t_ini)}|`)) return o.g; }
    return null;
  }

  /* ------------------------------------------------------------ hora del día */
  function luzDelDia(h) {
    const noche = h >= 6.5 && h <= 18 ? 0 : h > 18 && h < 20 ? (h - 18) / 2 : h > 4.5 && h < 6.5 ? (6.5 - h) / 2 : 1;
    sol.intensity = 2.1 * (1 - noche) + .12; hemi.intensity = .75 * (1 - noche) + .22; escena.environmentIntensity = .55 * (1 - noche) + .15;
    sol.color.set(noche > .05 && noche < .9 ? 0xffb27a : 0xfff4e0); const ang = ((h - 6) / 12) * Math.PI; sol.position.set(Math.cos(ang) * 80, 70 + 30 * Math.sin(Math.max(0, Math.min(Math.PI, ang))), 50 - Math.sin(ang) * 18);
    const bg = noche > .6 ? 'linear-gradient(180deg,#141f35 0%,#0b1220 70%,#080d17 100%)' : noche > .1 ? 'linear-gradient(180deg,#f4b183 0%,#9fb0d4 55%,#6b82b3 100%)' : 'linear-gradient(180deg,#eaf3ff 0%,#cfe3f8 55%,#b9d3ee 100%)';
    if (contenedor._bg !== bg) { contenedor.style.background = bg; contenedor._bg = bg; }
    const on = noche > .3; lamparas.forEach(l => { l.material = on ? mat(0xfff2c4, { emissive: 0xffe9a0, emissiveIntensity: 1.5 }) : mat(0xfff2c4); }); luzNave.forEach(l => { l.material = on ? mat(0xfff7d6, { emissive: 0xfff0b0, emissiveIntensity: 1.2 }) : mat(0xfff7d6); });
  }

  /* ------------------------------------------------------------ grúas: interpolación dentro de la hora */
  function animarGruas(T) {
    gruas.forEach(g => {
      const mv = g.mov;
      if (!mv) { const s = Math.sin(performance.now() * .0002 + g.gi) * 4; ponerGrua(g, g.e.x + s, g.e.z + s * .3, 1.6); return; }
      const f = Math.max(0, Math.min(1, (T - mv.m.t_ini) / Math.max(mv.m.t_fin - mv.m.t_ini, 1e-6))), a = mv.origen, b = mv.dest, e = ease(f);
      ponerGrua(g, lerp(a.x, b.x, e) + CX, lerp(a.z, b.z, e) + CZ, 1.6 + Math.sin(Math.PI * Math.min(1, f * 1.08)) * 2.3);
    });
  }

  /* ------------------------------------------------------------ selección, inspección de máquinas */
  const rayo = new THREE.Raycaster(), p2 = new THREE.Vector2();
  const refDe = o => { while (o) { if (o.userData && o.userData.ref) return o.userData.ref; o = o.parent; } return null; };
  const parteDe = o => { while (o) { if (o.userData && o.userData.parte) return o; o = o.parent; } return null; };
  const raizDe = (obj, ref) => { let o = obj; while (o.parent && refDe(o.parent) === ref) o = o.parent; return o; };
  function buscar(ev) {
    const r = dom.getBoundingClientRect(); p2.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1); rayo.setFromCamera(p2, cam);
    const hit = rayo.intersectObjects([...dinamico.children, ...grupoAgentes.children, ...grupoCamiones.children, ...(insp ? [] : grupoGruas.children), ...estatico.children], true)
      .find(h => h.object.visible && refDe(h.object) && !techos.includes(h.object) && !(h.object.material && h.object.material.transparent && h.object.material.opacity < .35));
    return hit ? { ref: refDe(hit.object), obj: hit.object } : null;
  }
  function seleccionar(ref, obj) {
    selRef = ref; selObj = obj; if (selBox) { escena.remove(selBox); selBox = null; }
    if (!ref || !obj) return; selBox = new THREE.Box3Helper(new THREE.Box3().setFromObject(raizDe(obj, ref)), 0x5b9bf0); escena.add(selBox);
  }
  let expl = 0, explObj = 0, xray = false, realce = null, realceEt = null;
  const infoInsp = () => insp ? { k: insp.k, nombre: insp.nombre, partes: insp.partes.map(p => ({ id: p.userData.parte.id, nombre: p.userData.parte.nombre, descr: p.userData.parte.descr, carcasa: p.userData.parte.carcasa })), expl: explObj, xray } : null;
  function quitarRealce() {
    if (realce) { escena.remove(realce); realce = null; } if (realceEt) { realceEt.el.remove(); etiquetas.splice(etiquetas.indexOf(realceEt), 1); realceEt = null; }
  }
  function inspeccionar(k) {
    quitarRealce(); maquinas.forEach(x => { MD.rayosX(x, false); MD.explotar(x, 0); }); expl = 0;
    if (k == null) { insp = null; explObj = 0; xray = false; grupoGruas.visible = true; if (opts.alInspeccionar) opts.alInspeccionar(null); return; }
    const m = maquinas[k]; insp = { k, nombre: m.nombre, partes: m.partes, maq: m }; explObj = 0; xray = false; grupoGruas.visible = false;
    const e = maqE[k]; setModo('3d'); volarA(V(e.x, e.z, m.alto * .5), new THREE.Vector3(.35, .55, .76).normalize().multiplyScalar(m.largo * 3.6)); if (opts.alInspeccionar) opts.alInspeccionar(infoInsp());
  }
  const explotarA = f => { explObj = f; if (insp && opts.alInspeccionar) opts.alInspeccionar(infoInsp()); };
  const rayosXOn = on => { xray = on; if (insp) { MD.rayosX(insp.maq, on); if (opts.alInspeccionar) opts.alInspeccionar(infoInsp()); } };
  function resaltar(id) {
    quitarRealce(); if (!insp || !id) return; const p = insp.partes.find(x => x.userData.parte.id === id); if (!p) return;
    const bb = new THREE.Box3().setFromObject(p); realce = new THREE.Box3Helper(bb, 0xffc84a); escena.add(realce); realceEt = etiqueta(p.userData.parte.nombre, bb.getCenter(new THREE.Vector3()).setY(bb.max.y + .5), 'parte', 20, false);
  }

  /* ------------------------------------------------------------ modos de cámara y vuelos */
  function setModo(nuevo) {
    if (nuevo === modo) return;
    if (modo === 'caminata') { const f = new THREE.Vector3(); camP.getWorldDirection(f); f.y = 0; f.normalize(); camP.position.y = 14; ctlP.target.set(camP.position.x + f.x * 20, 0, camP.position.z + f.z * 20); ctlP.enabled = true; }
    else if (modo === '3d') poseP = { pos: camP.position.clone(), tgt: ctlP.target.clone() };
    const dist = camP.position.distanceTo(ctlP.target); modo = nuevo;
    if (nuevo === '2d') { const t = ctlP.target.clone(); cam = camO; ctl = ctlO; ctlP.enabled = false; ctlO.enabled = true; ctlO.target.set(t.x, 0, t.z); camO.position.set(t.x, 300, t.z); camO.zoom = Math.max(.7, Math.min(8, 209 / Math.max(dist, 30))); ajustarOrto(); ctlO.update(); }
    else if (nuevo === '3d') { cam = camP; ctl = ctlP; ctlO.enabled = false; ctlP.enabled = true; if (poseP && !vuelo) { camP.position.copy(poseP.pos); ctlP.target.copy(poseP.tgt); } camP.rotation.order = 'XYZ'; ctlP.update(); }
    else if (nuevo === 'caminata') { vuelo = null; seguir = null; cam = camP; ctl = ctlP; ctlO.enabled = false; ctlP.enabled = false; camP.position.set(-16.25, 1.7, 14); walk.yaw = 0; walk.pitch = -.03; camP.rotation.order = 'YXZ'; aplicarMirada(); }
    if (opts.alCambiarModo) opts.alCambiarModo(modo);
  }
  const aplicarMirada = () => camP.rotation.set(walk.pitch, walk.yaw, 0);
  function ajustarOrto() { const w = contenedor.clientWidth, h = contenedor.clientHeight, alto = 60; camO.left = -alto * (w / Math.max(h, 1)); camO.right = alto * (w / Math.max(h, 1)); camO.top = alto; camO.bottom = -alto; camO.updateProjectionMatrix(); }
  function volarA(destino, offset, dur = 1100) {
    if (modo === 'caminata') setModo('3d');
    if (modo === '2d') { vuelo = { t0: performance.now(), dur, a: ctlO.target.clone(), b: new THREE.Vector3(destino.x, 0, destino.z), z0: camO.zoom, z1: Math.max(.9, Math.min(8, 209 / Math.max(offset.length(), 25))), o: true }; return; }
    vuelo = { t0: performance.now(), dur, a: ctlP.target.clone(), b: destino.clone(), pa: camP.position.clone(), pb: destino.clone().add(offset) };
  }
  const VISTAS = { general: [V(50, 25), [78, 66, 88]], navea: [V(22, 17), [4, 46, 52]], naveb: [V(72, 17), [4, 48, 54]], patio: [V(22, 40), [6, 30, 36]], muelles: [V(96, 17), [-34, 28, 38]], oficina: [V(82, 43), [-4, 20, 28]], maquinas: [V(21, 6, 1), [8, 24, 28]], comedor: [V(55, 42), [0, 14, 20]] };
  function vista(n) { const [c, o] = VISTAS[n] || VISTAS.general; const k = n === 'general' ? Math.max(1, 1.5 / camP.aspect) : 1; volarA(c, new THREE.Vector3(o[0] * k, o[1] * k, o[2] * k)); }
  function enfocar(ref, obj) {
    obj = obj || selObj; ref = ref || selRef; if (!obj) { vista('general'); return; }
    const bb = new THREE.Box3().setFromObject(raizDe(obj, ref)), c = bb.getCenter(new THREE.Vector3()), tam = bb.getSize(new THREE.Vector3()).length();
    volarA(c, new THREE.Vector3(.5, .7, 1).normalize().multiplyScalar(Math.max(7, tam * 1.9)));
  }
  function pan(dx, dz) {
    const f = new THREE.Vector3(); cam.getWorldDirection(f); f.y = 0; if (f.lengthSq() < 1e-4) f.set(0, 0, -1); f.normalize(); const r = new THREE.Vector3(-f.z, 0, f.x);
    if (modo === '2d') { const d = new THREE.Vector3(dx, 0, dz).multiplyScalar(8 / camO.zoom); ctlO.target.add(d); camO.position.add(d); }
    else { const k = Math.max(2, ctlP.target.distanceTo(camP.position) * .06), d = r.multiplyScalar(dx * k).add(f.multiplyScalar(-dz * k)); ctlP.target.add(d); camP.position.add(d); }
  }
  function zoom(f) { if (modo === '2d') { camO.zoom = Math.min(ctlO.maxZoom, Math.max(ctlO.minZoom, camO.zoom * f)); camO.updateProjectionMatrix(); } else if (modo === '3d') camP.position.copy(ctlP.target).add(camP.position.clone().sub(ctlP.target).multiplyScalar(1 / f)); }
  function girar(ang) { if (modo !== '3d') return; const d = camP.position.clone().sub(ctlP.target), c = Math.cos(ang), s = Math.sin(ang); camP.position.set(ctlP.target.x + d.x * c - d.z * s, camP.position.y, ctlP.target.z + d.x * s + d.z * c); }

  /* ------------------------------------------------------------ interacción: ratón y teclado */
  let abajo = null, ult = 0;
  dom.addEventListener('pointerdown', e => { abajo = [e.clientX, e.clientY]; dom.focus({ preventScroll: true }); if (modo === 'caminata') { walk.arrastra = [e.clientX, e.clientY]; dom.setPointerCapture(e.pointerId); } vuelo = null; seguir = null; });
  dom.addEventListener('pointermove', e => {
    if (modo === 'caminata' && walk.arrastra) { walk.yaw -= (e.clientX - walk.arrastra[0]) * .004; walk.pitch = Math.max(-1.2, Math.min(1.2, walk.pitch - (e.clientY - walk.arrastra[1]) * .004)); walk.arrastra = [e.clientX, e.clientY]; aplicarMirada(); return; }
    const t = performance.now(); if (t - ult < 70) return; ult = t; const h = buscar(e), r = contenedor.getBoundingClientRect();
    if (h && (h.ref.etiqueta || h.ref.nombre)) { const p = insp && h.ref.tipo === 'maquina' ? parteDe(h.obj) : null; tip.textContent = p ? p.userData.parte.nombre : (h.ref.etiqueta || h.ref.nombre); tip.style.left = (e.clientX - r.left + 14) + 'px'; tip.style.top = (e.clientY - r.top + 12) + 'px'; tip.classList.remove('oculto'); dom.style.cursor = 'pointer'; }
    else { tip.classList.add('oculto'); dom.style.cursor = modo === 'caminata' ? 'crosshair' : 'grab'; }
  });
  dom.addEventListener('pointerup', e => {
    walk.arrastra = null; if (!abajo || Math.hypot(e.clientX - abajo[0], e.clientY - abajo[1]) > 5) return; const h = buscar(e);
    const parte = h && insp && h.ref.tipo === 'maquina' && h.ref.k === insp.k ? parteDe(h.obj) : null;
    seleccionar(h && h.ref, h && h.obj); if (parte) { resaltar(parte.userData.parte.id); if (opts.alParte) opts.alParte(parte.userData.parte.id); }
    if (opts.alSeleccionar) opts.alSeleccionar(h ? h.ref : null, h ? h.obj : null);
  });
  dom.addEventListener('dblclick', e => { const h = buscar(e); if (!h) return; if (h.ref.tipo === 'maquina') inspeccionar(h.ref.k); else enfocar(h.ref, h.obj); });
  dom.addEventListener('pointerleave', () => tip.classList.add('oculto'));
  const AYUDA = [['Ratón', ''], ['Izquierdo + arrastrar', 'Girar (3D) o desplazar (2D)'], ['Derecho / central + arrastrar', 'Desplazar la vista'], ['Rueda', 'Acercar o alejar hacia el cursor'], ['Doble clic', 'Enfocar el objeto; en una máquina abre su inspección'],
    ['Vista', ''], ['2 / 3', 'Plano 2D / perspectiva 3D'], ['C', 'Caminata en primera persona (W A S D, arrastrar para mirar, Mayús corre)'], ['R', 'Rotación automática (Esc la detiene)'], ['G  o  Inicio', 'Vista general'], ['F', 'Enfocar la selección'], ['K', 'Seguir la selección con la cámara'],
    ['Movimiento', ''], ['W A S D  o  flechas', 'Desplazar la vista'], ['Q / E', 'Girar la vista'], ['+ / −  o  Z', 'Acercar / alejar'],
    ['Máquinas', ''], ['I', 'Inspeccionar la máquina seleccionada'], ['V', 'Vista explosionada'], ['X', 'Rayos X (carcasas transparentes)'],
    ['Escena', ''], ['T / L / M', 'Techos / etiquetas / modo limpio'], ['Espacio', 'Reproducir o pausar'], [', / .', 'Una hora atrás / adelante'], ['[ / ]', 'Más lento / más rápido'], ['H', 'Mostrar u ocultar esta ayuda'], ['Esc', 'Cerrar inspección, soltar selección o salir de la caminata']];
  ayuda.innerHTML = '<b>Atajos</b><button class="p3d-ayuda-x" aria-label="Cerrar">×</button>' + AYUDA.map(([a, b]) => b ? `<div><kbd>${a}</kbd><span>${b}</span></div>` : `<h6>${a}</h6>`).join('');
  ayuda.querySelector('.p3d-ayuda-x').onclick = () => verAyuda(false);
  function verAyuda(v) { hintOn = v === undefined ? !hintOn : v; ayuda.classList.toggle('oculto', !hintOn); if (opts.alCambiarAyuda) opts.alCambiarAyuda(hintOn); }
  const MOV = ['w', 'a', 's', 'd', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
  function alTecla(e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return; const t = e.target;
    if (t && t.matches && t.matches('input:not([type=range]):not([type=checkbox]), textarea, select, [contenteditable]')) return;
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key, acc = n => opts.accion && opts.accion(n);
    if (modo === 'caminata' && (MOV.includes(k) || k === 'Shift')) { teclas.add(k); e.preventDefault(); return; }
    switch (k) {
      case '2': setModo('2d'); break; case '3': setModo('3d'); break; case 'c': setModo(modo === 'caminata' ? '3d' : 'caminata'); break;
      case 'r': rotarAuto = !rotarAuto; break; case 'h': case '?': verAyuda(); break;
      case 'f': enfocar(); break; case 'g': case 'Home': vista('general'); break; case 'k': seguir = selRef && selRef.tipo !== 'maquina' ? { ref: selRef } : null; break;
      case 'q': girar(.26); break; case 'e': girar(-.26); break; case '+': case '=': case 'z': zoom(1.25); break;
      case '-': case '_': zoom(.8); break; case 'x': if (insp) rayosXOn(!xray); else zoom(.8); break;
      case 'w': case 'ArrowUp': pan(0, -1); break; case 's': case 'ArrowDown': pan(0, 1); break; case 'a': case 'ArrowLeft': pan(-1, 0); break; case 'd': case 'ArrowRight': pan(1, 0); break;
      case 'i': if (selRef && selRef.tipo === 'maquina') inspeccionar(selRef.k); else if (insp) inspeccionar(null); break; case 'v': if (insp) explotarA(explObj > .5 ? 0 : 1); break;
      case 't': acc('techos'); break; case 'l': acc('etiquetas'); break; case 'm': acc('limpio'); break; case ' ': acc('play'); break; case ',': acc('atras'); break; case '.': acc('adelante'); break; case '[': acc('lento'); break; case ']': acc('rapido'); break;
      case 'Escape': if (rotarAuto) rotarAuto = false; else if (modo === 'caminata') setModo('3d'); else if (insp) inspeccionar(null); else if (selRef) { seleccionar(null); if (opts.alSeleccionar) opts.alSeleccionar(null); } else if (hintOn) verAyuda(false); break;
      default: return;
    }
    e.preventDefault();
  }
  const alSoltar = e => { teclas.delete(e.key.length === 1 ? e.key.toLowerCase() : e.key); };
  document.addEventListener('keydown', alTecla); document.addEventListener('keyup', alSoltar);

  /* ------------------------------------------------------------ tamaño y bucle */
  function tam() { const w = contenedor.clientWidth, h = contenedor.clientHeight; renderer.setSize(w, h, false); camP.aspect = w / Math.max(h, 1); camP.updateProjectionMatrix(); ajustarOrto(); }
  const ro = new ResizeObserver(tam); ro.observe(contenedor); tam(); camP.position.set(130, 86, 114); ctlP.update();
  let vivo = true, tAnt = performance.now(); const v3 = new THREE.Vector3(), cajasEt = [];
  const seguirObj = () => seguir ? reencontrar(seguir.ref) : null;
  function bucle(ahora) {
    if (!vivo) return; requestAnimationFrame(bucle); const dt = Math.min(.1, (ahora - tAnt) / 1000); tAnt = ahora;
    if (vuelo) {
      const f = Math.min(1, (ahora - vuelo.t0) / vuelo.dur), e = ease(f);
      if (vuelo.o) { ctlO.target.lerpVectors(vuelo.a, vuelo.b, e); camO.position.set(ctlO.target.x, 300, ctlO.target.z); camO.zoom = lerp(vuelo.z0, vuelo.z1, e); camO.updateProjectionMatrix(); }
      else { ctlP.target.lerpVectors(vuelo.a, vuelo.b, e); camP.position.lerpVectors(vuelo.pa, vuelo.pb, e); }
      if (f >= 1) vuelo = null;
    }
    const so = seguirObj(); if (so) { const w = so.getWorldPosition(new THREE.Vector3()); if (modo === '3d') { const d = w.clone().sub(ctlP.target).multiplyScalar(.12); ctlP.target.add(d); camP.position.add(d); } else if (modo === '2d') { ctlO.target.lerp(new THREE.Vector3(w.x, 0, w.z), .12); camO.position.set(ctlO.target.x, 300, ctlO.target.z); } }
    if (rotarAuto && modo === '3d') girar(dt * .2);
    if (modo === 'caminata') {
      const v = (teclas.has('Shift') ? 9 : 4) * dt, fx = -Math.sin(walk.yaw), fz = -Math.cos(walk.yaw); let mx = 0, mz = 0;
      if (teclas.has('w') || teclas.has('ArrowUp')) { mx += fx; mz += fz; } if (teclas.has('s') || teclas.has('ArrowDown')) { mx -= fx; mz -= fz; } if (teclas.has('a') || teclas.has('ArrowLeft')) { mx += fz; mz -= fx; } if (teclas.has('d') || teclas.has('ArrowRight')) { mx -= fz; mz += fx; }
      camP.position.x = Math.max(-95, Math.min(95, camP.position.x + mx * v)); camP.position.z = Math.max(-60, Math.min(80, camP.position.z + mz * v)); camP.position.y = 1.7;
    } else ctl.update();
    if (Math.abs(expl - explObj) > .002) { expl += (explObj - expl) * Math.min(1, dt * 5); if (insp) MD.explotar(insp.maq, expl); }
    animEst.forEach(f => f(ahora)); animDin.forEach(f => f(ahora)); moverAgentes(dt, ahora); animarGruas(Tlocal); moverCamiones(Tlocal);
    const baja = modo === '2d' || modo === 'caminata' || camP.position.distanceTo(ctlP.target) < 75; techos.forEach(r => { r.visible = techosOn && !baja; });
    if (selBox && selRef && selObj && selObj.parent) selBox.box.setFromObject(raizDe(selObj, selRef));
    if (realce && insp) { const p = insp.partes.find(x => realceEt && x.userData.parte.nombre === realceEt.el.textContent); if (p) realce.box.setFromObject(p); }
    // etiquetas: nivel de detalle por distancia y prioridad, sin superponerse
    const w = contenedor.clientWidth, h = contenedor.clientHeight, dist = modo === '2d' ? 60 / camO.zoom : camP.position.distanceTo(ctlP.target); cajasEt.length = 0;
    for (const e of etiquetas.slice().sort((a, b) => b.prio - a.prio)) {
      v3.copy(e.v).project(cam); let vis = (etiquetasOn || e.clase === 'parte') && v3.z < 1 && Math.abs(v3.x) < 1.05 && Math.abs(v3.y) < 1.05 && modo !== 'caminata';
      if (vis && e.clase === 'zona' && (dist < 14 || dist > 120)) vis = false; if (vis && e.clase === 'maq' && (dist > 120 || insp)) vis = false; if (vis && e.clase === 'nave' && dist < 22) vis = false;
      if (vis) {
        if (!e.w) e.w = e.el.offsetWidth || 90; const x = (v3.x * .5 + .5) * w, y = (-v3.y * .5 + .5) * h, c2 = [x - e.w / 2 - 3, y - 24, x + e.w / 2 + 3, y + 3];
        if (e.clase !== 'parte' && cajasEt.some(c => !(c2[2] < c[0] || c2[0] > c[2] || c2[3] < c[1] || c2[1] > c[3]))) vis = false; else { cajasEt.push(c2); e.el.style.transform = `translate(-50%,-100%) translate(${x}px, ${y}px)`; }
      }
      e.el.style.display = vis ? '' : 'none'; if (e.mastil) e.mastil.visible = vis;
    }
    renderer.render(escena, cam);
  }
  requestAnimationFrame(bucle); vista('general');
  const api = {
    actualizar, seleccionar: ref => seleccionar(ref, null), enfocar, vista, setT: T => { Tlocal = T; }, modo: setModo, getModo: () => modo, inspeccionar, explotar: explotarA, rayosX: rayosXOn, resaltarParte: resaltar,
    techos: v => { techosOn = v; }, etiquetas: v => { etiquetasOn = v; capaEt.style.display = v ? '' : 'none'; mastiles.visible = v; }, ayuda: verAyuda, rotar: v => { rotarAuto = v === undefined ? !rotarAuto : v; },
    seguir: () => { seguir = selRef && selRef.tipo !== 'maquina' ? { ref: selRef } : null; return !!seguir; }, pose: () => ({ modo, pos: cam.position.toArray(), T: Tlocal, camiones: [...camiones.entries()].map(([k, o]) => ({ k, vis: o.g.visible, pos: o.g.position.toArray(), ry: o.g.rotation.y })) }),
    destruir() { vivo = false; document.removeEventListener('keydown', alTecla); document.removeEventListener('keyup', alSoltar); ro.disconnect(); ctlP.dispose(); ctlO.dispose(); pmrem.dispose(); renderer.dispose(); dom.remove(); capaEt.remove(); tip.remove(); ayuda.remove(); },
  };
  api.escena = escena; api.camaraP = camP; contenedor.__gemelo = api; return api;
}
