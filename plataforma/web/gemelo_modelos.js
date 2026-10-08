/* SteelPlan · assets 3D procedurales del gemelo (sin descargas): texturas, perfiles de acero con sección real, personas articuladas,
   camiones de plataforma y las cuatro máquinas con componentes nombrados (vista explosionada y rayos X).
   Las máquinas son esquemas genéricos de cada tipo de equipo, no el modelo exacto de la planta. */
import * as THREE from '/static/vendor/three/three.module.js';

/* ============================================================ utilidades de geometría y material */
export const GEO = { caja: new THREE.BoxGeometry(1, 1, 1), cil: new THREE.CylinderGeometry(1, 1, 1, 24), cil8: new THREE.CylinderGeometry(1, 1, 1, 8), esf: new THREE.SphereGeometry(1, 18, 12) };
const cacheGeo = new Map();
const geo = (clave, f) => { let g = cacheGeo.get(clave); if (!g) { g = f(); cacheGeo.set(clave, g); } return g; };
const cacheMat = new Map();
export const mat = (c, o = {}) => { const k = c + '|' + JSON.stringify(o); let m = cacheMat.get(k); if (!m) { m = new THREE.MeshStandardMaterial({ color: c, roughness: .6, metalness: .25, ...o }); cacheMat.set(k, m); } return m; };
export const M = {
  acero: () => mat(0x8c96a1, { metalness: .85, roughness: .38 }), aceroOsc: () => mat(0x4b5560, { metalness: .8, roughness: .5 }), cromo: () => mat(0xd6dbe0, { metalness: 1, roughness: .15 }),
  pintAzul: () => mat(0x1f5aa6, { metalness: .35, roughness: .42 }), pintAzulCl: () => mat(0x4c86d4, { metalness: .35, roughness: .42 }), pintGris: () => mat(0x9aa4ae, { metalness: .35, roughness: .5 }),
  amarillo: () => mat(0xf2b705, { metalness: .2, roughness: .5 }), naranja: () => mat(0xe0661a, { metalness: .2, roughness: .5 }), rojo: () => mat(0xc43d32, { metalness: .2, roughness: .5 }),
  goma: () => mat(0x1d1f22, { metalness: 0, roughness: .95 }), negro: () => mat(0x15171a, { metalness: .3, roughness: .6 }), blanco: () => mat(0xf1f3f5, { metalness: .1, roughness: .55 }),
  vidrio: () => mat(0x1c2c3c, { metalness: .9, roughness: .08, transparent: true, opacity: .62 }), piel: () => mat(0xe0b08c, { metalness: 0, roughness: .8 }),
  oxido: () => mat(0x7a3b2a, { metalness: .4, roughness: .7 }), madera: () => mat(0x9a7448, { metalness: 0, roughness: .9 }),
};
export const caja = (w, h, d, m, sombra = true) => { const x = new THREE.Mesh(GEO.caja, m); x.scale.set(w, h, d); x.castShadow = sombra; x.receiveShadow = true; return x; };
export const cil = (r, h, m, sombra = true) => { const x = new THREE.Mesh(GEO.cil, m); x.scale.set(r, h, r); x.castShadow = sombra; x.receiveShadow = true; return x; };
export const esf = (r, m) => { const x = new THREE.Mesh(GEO.esf, m); x.scale.set(r, r, r); x.castShadow = true; return x; };
export const en = (o, x, y, z) => { o.position.set(x, y, z); return o; };
export const rot = (o, x = 0, y = 0, z = 0) => { o.rotation.set(x, y, z); return o; };
/* caja con aristas redondeadas (carcasas, cabinas): se extruye un rectángulo redondeado con bisel */
export function cajaRedonda(w, h, d, r, m) {
  const g = geo(`cr${w}|${h}|${d}|${r}`, () => {
    const s = new THREE.Shape(), a = w - 2 * r, b = h - 2 * r; s.moveTo(-a / 2, -h / 2); s.lineTo(a / 2, -h / 2); s.absarc(a / 2, -b / 2, r, -Math.PI / 2, 0); s.lineTo(w / 2, b / 2); s.absarc(a / 2, b / 2, r, 0, Math.PI / 2);
    s.lineTo(-a / 2, h / 2); s.absarc(-a / 2, b / 2, r, Math.PI / 2, Math.PI); s.lineTo(-w / 2, -b / 2); s.absarc(-a / 2, -b / 2, r, Math.PI, Math.PI * 1.5);
    const e = new THREE.ExtrudeGeometry(s, { depth: Math.max(d - r, .01), bevelEnabled: true, bevelThickness: r / 2, bevelSize: r / 2, bevelSegments: 2, curveSegments: 6 }); e.translate(0, 0, -(d - r) / 2); return e;
  });
  const x = new THREE.Mesh(g, m); x.castShadow = true; x.receiveShadow = true; return x;
}

/* ============================================================ texturas procedurales */
function lienzo(w, h, f, repX = 1, repY = 1) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; f(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repX, repY); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}
function motas(g, w, h, n, c0, c1, tam = 1.6) { for (let i = 0; i < n; i++) { g.fillStyle = Math.random() < .5 ? c0 : c1; g.globalAlpha = .08 + Math.random() * .16; g.fillRect(Math.random() * w, Math.random() * h, tam * (1 + Math.random() * 2), tam * (1 + Math.random() * 2)); } g.globalAlpha = 1; }
let _tex = null;
export function texturas() {
  if (_tex) return _tex;
  _tex = {
    concreto: lienzo(512, 512, (g, w, h) => { g.fillStyle = '#c4c7cb'; g.fillRect(0, 0, w, h); motas(g, w, h, 5000, '#a9adb2', '#dcdfe2'); g.strokeStyle = 'rgba(70,74,80,.55)'; g.lineWidth = 2; g.strokeRect(1, 1, w - 2, h - 2); g.strokeStyle = 'rgba(70,74,80,.18)'; g.beginPath(); g.moveTo(w / 2, 0); g.lineTo(w / 2, h); g.moveTo(0, h / 2); g.lineTo(w, h / 2); g.stroke(); }),
    piso: lienzo(512, 512, (g, w, h) => { g.fillStyle = '#d3d6da'; g.fillRect(0, 0, w, h); motas(g, w, h, 4000, '#b9bdc2', '#e6e8ea'); g.strokeStyle = 'rgba(80,84,90,.5)'; g.lineWidth = 2; g.strokeRect(1, 1, w - 2, h - 2); }),
    asfalto: lienzo(512, 512, (g, w, h) => { g.fillStyle = '#4d5157'; g.fillRect(0, 0, w, h); motas(g, w, h, 9000, '#3a3d42', '#6a6f76', 1.2); }),
    pasto: lienzo(512, 512, (g, w, h) => { g.fillStyle = '#6f9a62'; g.fillRect(0, 0, w, h); motas(g, w, h, 8000, '#5b8650', '#86b277', 2); }),
    placa: lienzo(256, 256, (g, w, h) => { g.fillStyle = '#9aa2ab'; g.fillRect(0, 0, w, h); g.fillStyle = '#c9ced4'; for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { g.save(); g.translate(x * 32 + 16 + (y % 2) * 8, y * 32 + 16); g.rotate((x + y) % 2 ? .78 : -.78); g.fillRect(-9, -2.5, 18, 5); g.restore(); } }, 4, 4),
    ondulado: lienzo(256, 256, (g, w, h) => { for (let x = 0; x < w; x++) { const v = 150 + 55 * Math.sin((x / w) * Math.PI * 16); g.fillStyle = `rgb(${v},${v + 6},${v + 14})`; g.fillRect(x, 0, 1, h); } }, 8, 1),
    madera: lienzo(256, 128, (g, w, h) => { g.fillStyle = '#a07b4d'; g.fillRect(0, 0, w, h); for (let i = 0; i < 70; i++) { g.strokeStyle = `rgba(${70 + Math.random() * 40},${45 + Math.random() * 30},25,${.15 + Math.random() * .25})`; g.lineWidth = 1 + Math.random() * 2; g.beginPath(); const y = Math.random() * h; g.moveTo(0, y); g.bezierCurveTo(w * .3, y + 4, w * .6, y - 4, w, y + Math.random() * 3); g.stroke(); } }),
  };
  return _tex;
}
export const matTex = (nombre, o = {}) => { const k = 'tex:' + nombre + JSON.stringify(o); let m = cacheMat.get(k); if (!m) { m = new THREE.MeshStandardMaterial({ map: texturas()[nombre], roughness: .9, metalness: .02, ...o }); cacheMat.set(k, m); } return m; };
export function etiquetaTex(texto, o = {}) {      // letrero (cartel) con texto
  const { w = 512, h = 128, fondo = '#0b4b8f', color = '#fff', tam = 54 } = o;
  const t = lienzo(w, h, (g) => { g.fillStyle = fondo; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(255,255,255,.35)'; g.lineWidth = 4; g.strokeRect(6, 6, w - 12, h - 12); g.fillStyle = color; g.font = `700 ${tam}px Inter, Segoe UI, Arial`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(texto, w / 2, h / 2 + 3); });
  return t;
}
export function pintarPiso(texto, ancho, largo, o = {}) {      // texto pintado en el piso (patios, zonas)
  const w = 1024, h = Math.round(1024 * largo / ancho), c = document.createElement('canvas'); c.width = w; c.height = Math.max(h, 64); const g = c.getContext('2d');
  g.clearRect(0, 0, c.width, c.height); g.fillStyle = o.color || 'rgba(240,200,40,.95)'; g.font = `800 ${o.tam || 78}px Inter, Segoe UI, Arial`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(texto, w / 2, c.height / 2);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}

/* ============================================================ perfiles de acero con sección real */
const SECC = {   // designación → forma y medidas (m): I (alto, ala, espesor ala, espesor alma), C, L, PL (ancho, espesor), tubo, barra
  'W12x26': ['I', .31, .165, .0096, .0058], 'W16x31': ['I', .403, .14, .011, .007], 'W8x18': ['I', .207, .133, .0084, .0058], 'HEA 200': ['I', .19, .2, .01, .0065], 'HEA 160': ['I', .152, .16, .009, .006],
  'C 10x15.3': ['C', .254, .077, .0111, .0061], 'C 8x11.5': ['C', .203, .0575, .0099, .0056], 'L 3x3x1/4': ['L', .0762, .0064], 'L 2x2x3/16': ['L', .0508, .0048],
  'PL 3/8"': ['P', 1.2, .0095], 'PL 1/2"': ['P', 1.5, .0127], 'PL 1/4"': ['P', 1.2, .0064], 'Tubo 4"': ['T', .1016, .003], 'Tubo 6"': ['T', .1683, .004], 'Barra 5/8"': ['B', .0159],
};
export function seccionDe(perfil) { const k = Object.keys(SECC).find(x => String(perfil).startsWith(x.replace(/ ·.*/, ''))); return SECC[k] || ['I', .2, .13, .009, .006]; }
function geoPerfil(sec, largo) {
  const L = Math.round(largo * 10) / 10, clave = sec.join('|') + '|' + L;
  return geo('p' + clave, () => {
    const [t, a, b, c, d] = sec; let sh;
    if (t === 'I') { const h = a, bf = b, tf = c, tw = d; sh = new THREE.Shape([[-bf / 2, -h / 2], [bf / 2, -h / 2], [bf / 2, -h / 2 + tf], [tw / 2, -h / 2 + tf], [tw / 2, h / 2 - tf], [bf / 2, h / 2 - tf], [bf / 2, h / 2], [-bf / 2, h / 2], [-bf / 2, h / 2 - tf], [-tw / 2, h / 2 - tf], [-tw / 2, -h / 2 + tf], [-bf / 2, -h / 2 + tf]].map(p => new THREE.Vector2(...p))); }
    else if (t === 'C') { const h = a, bf = b, tf = c, tw = d; sh = new THREE.Shape([[-bf / 2, -h / 2], [bf / 2, -h / 2], [bf / 2, -h / 2 + tf], [-bf / 2 + tw, -h / 2 + tf], [-bf / 2 + tw, h / 2 - tf], [bf / 2, h / 2 - tf], [bf / 2, h / 2], [-bf / 2, h / 2]].map(p => new THREE.Vector2(...p))); }
    else if (t === 'L') { const s = a, e = b; sh = new THREE.Shape([[-s / 2, -s / 2], [s / 2, -s / 2], [s / 2, -s / 2 + e], [-s / 2 + e, -s / 2 + e], [-s / 2 + e, s / 2], [-s / 2, s / 2]].map(p => new THREE.Vector2(...p))); }
    else if (t === 'T') { sh = new THREE.Shape(); sh.absarc(0, 0, a / 2, 0, Math.PI * 2, false); const h = new THREE.Path(); h.absarc(0, 0, a / 2 - b, 0, Math.PI * 2, true); sh.holes.push(h); }
    else if (t === 'B') { sh = new THREE.Shape(); sh.absarc(0, 0, a / 2, 0, Math.PI * 2, false); }
    else { sh = new THREE.Shape([[-a / 2, -b / 2], [a / 2, -b / 2], [a / 2, b / 2], [-a / 2, b / 2]].map(p => new THREE.Vector2(...p))); }
    const e = new THREE.ExtrudeGeometry(sh, { depth: t === 'P' ? Math.min(L, 2.4) : L, bevelEnabled: false, curveSegments: 10 }); e.translate(0, 0, -(t === 'P' ? Math.min(L, 2.4) : L) / 2); e.rotateY(Math.PI / 2); return e;
  });
}
/* haz (paquete) de piezas de un lote: vigas apiladas sobre tacos de madera, con flejes y una banderola del color de la etapa */
export function crearHaz(lote, colorEtapa, pintado = false) {
  const g = new THREE.Group(), sec = seccionDe(lote.perfil), largo = Math.min(Math.max(lote.largo, 1.5), 9), n = Math.min(Math.max(lote.n_piezas, 1), 9);
  const m = pintado ? mat(0x3d5f8f, { metalness: .3, roughness: .45 }) : lote.etapa === 'LISTO_PINTURA' ? mat(0x8a929b, { metalness: .8, roughness: .5 }) : M.acero();
  const geom = geoPerfil(sec, largo); const alto = sec[0] === 'I' || sec[0] === 'C' ? sec[1] : sec[0] === 'P' ? sec[2] : sec[0] === 'T' ? sec[1] : sec[0] === 'B' ? sec[1] : sec[1];
  const ancho = sec[0] === 'I' || sec[0] === 'C' ? sec[2] : sec[0] === 'P' ? sec[1] : sec[1];
  const pasoY = sec[0] === 'P' ? sec[2] + .004 : alto + .01, pasoZ = sec[0] === 'P' ? 0 : ancho + .03, porFila = sec[0] === 'P' ? 1 : Math.min(4, n);
  for (let i = 0; i < n; i++) {
    const fila = Math.floor(i / porFila), col = i % porFila; const x = new THREE.Mesh(geom, m); x.castShadow = true; x.receiveShadow = true;
    if (sec[0] === 'P') { x.position.set(0, .13 + fila * pasoY, 0); x.scale.set(1, 1, 1); }
    else { x.position.set(0, .13 + alto / 2 + fila * pasoY, (col - (porFila - 1) / 2) * pasoZ); }
    g.add(x);
  }
  const anchoTot = sec[0] === 'P' ? sec[1] : porFila * pasoZ, altoTot = sec[0] === 'P' ? n * pasoY : Math.ceil(n / porFila) * pasoY;
  for (const dx of [-largo * .38, 0, largo * .38]) g.add(en(caja(.1, .12, anchoTot + .1, M.madera()), dx, .06, 0));                 // tacos de madera
  for (const dx of [-largo * .3, largo * .3]) g.add(en(caja(.04, altoTot + .04, anchoTot + .06, M.naranja(), false), dx, .13 + altoTot / 2, 0));   // flejes
  const bandera = caja(.02, .3, .22, mat(colorEtapa || 0xffffff, { emissive: colorEtapa || 0xffffff, emissiveIntensity: .25, roughness: .6 })); bandera.position.set(largo * .45, .13 + altoTot + .2, 0); g.add(bandera);
  g.userData.dim = { largo, ancho: anchoTot, alto: altoTot + .13 }; g.userData.bandera = bandera; return g;
}
export function crearTarima() {
  const g = new THREE.Group(); const m = matTex('madera');
  for (const z of [-.5, 0, .5]) g.add(en(caja(1.2, .09, .12, m), 0, .045, z)); for (const x of [-.5, 0, .5]) g.add(en(caja(.12, .08, 1.0, m), x, .13, 0)); for (let i = -2; i <= 2; i++) g.add(en(caja(1.2, .02, .16, m), 0, .18, i * .22));
  return g;
}

/* ============================================================ persona articulada */
const geoCap = (r, l) => geo(`cap${r}|${l}`, () => new THREE.CapsuleGeometry(r, l, 4, 8));
export function crearPersona(o = {}) {
  const { camisa = 0x2f6fb8, pantalon = 0x2c3a52, casco = 0xf5f5f0, chaleco = 0xff7a1a, escala = 1 + (o.altura || 0) } = o;
  const g = new THREE.Group(), R = {};
  const mc = mat(camisa, { roughness: .85, metalness: 0 }), mp = mat(pantalon, { roughness: .9, metalness: 0 }), mch = mat(casco, { roughness: .4, metalness: .1 }), mv = mat(chaleco, { roughness: .7, metalness: 0 }), mb = M.negro();
  const pelvis = new THREE.Group(); pelvis.position.y = .98; g.add(pelvis); R.pelvis = pelvis;
  pelvis.add(en(caja(.34, .2, .2, mp), 0, 0, 0));
  const torso = new THREE.Group(); torso.position.y = .1; pelvis.add(torso); R.torso = torso;
  torso.add(en(caja(.38, .5, .22, mc), 0, .27, 0)); torso.add(en(caja(.4, .36, .235, mv), 0, .26, 0)); torso.add(en(caja(.41, .035, .24, M.blanco(), false), 0, .24, 0)); torso.add(en(caja(.41, .035, .24, M.blanco(), false), 0, .36, 0));
  const cabeza = new THREE.Group(); cabeza.position.y = .56; torso.add(cabeza); R.cabeza = cabeza;
  cabeza.add(en(cil(.05, .08, M.piel(), false), 0, .02, 0)); cabeza.add(en(esf(.105, M.piel()), 0, .15, 0));
  const hc = new THREE.Mesh(geo('casco', () => new THREE.SphereGeometry(1, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2)), mch); hc.scale.set(.125, .115, .13); hc.position.set(0, .17, 0); hc.castShadow = true; cabeza.add(hc);
  cabeza.add(en(caja(.2, .018, .08, mch, false), 0, .175, .1));
  const visera = caja(.2, .16, .02, mat(0x0b0d10, { metalness: .6, roughness: .2 }), false); visera.position.set(0, .15, .12); visera.visible = false; cabeza.add(visera); R.visera = visera;
  const brazo = lado => {
    const hombro = new THREE.Group(); hombro.position.set(.235 * lado, .45, 0); torso.add(hombro);
    hombro.add(en(new THREE.Mesh(geoCap(.045, .22), mc), 0, -.14, 0));
    const codo = new THREE.Group(); codo.position.y = -.28; hombro.add(codo);
    codo.add(en(new THREE.Mesh(geoCap(.04, .2), mc), 0, -.12, 0)); codo.add(en(esf(.05, mat(0x25282c, { roughness: .8, metalness: 0 })), 0, -.27, 0));
    hombro.children.forEach(c => { c.castShadow = true; }); return { hombro, codo };
  };
  R.bI = brazo(-1); R.bD = brazo(1);
  const pierna = lado => {
    const cadera = new THREE.Group(); cadera.position.set(.095 * lado, -.08, 0); pelvis.add(cadera);
    cadera.add(en(new THREE.Mesh(geoCap(.065, .32), mp), 0, -.22, 0));
    const rodilla = new THREE.Group(); rodilla.position.y = -.44; cadera.add(rodilla);
    rodilla.add(en(new THREE.Mesh(geoCap(.055, .32), mp), 0, -.2, 0)); rodilla.add(en(caja(.11, .09, .27, mb), 0, -.44, .05));
    cadera.children.forEach(c => { c.castShadow = true; }); return { cadera, rodilla };
  };
  R.pI = pierna(-1); R.pD = pierna(1);
  g.scale.setScalar(escala); g.userData.rig = R; g.userData.pose = 'quieto'; return g;
}
/* poses: se escriben las rotaciones de las articulaciones en función del tiempo t (ms) y de la fase de cada persona */
export function posar(p, pose, t, fase = 0, vel = 0) {
  const R = p.userData.rig, s = t * .001 + fase, z = (...a) => a;
  const reset = () => { R.torso.rotation.set(0, 0, 0); R.pelvis.position.y = .98; R.pelvis.rotation.set(0, 0, 0); R.cabeza.rotation.set(0, 0, 0); R.visera.visible = false;
    R.bI.hombro.rotation.set(0, 0, .06); R.bD.hombro.rotation.set(0, 0, -.06); R.bI.codo.rotation.set(0, 0, 0); R.bD.codo.rotation.set(0, 0, 0);
    R.pI.cadera.rotation.set(0, 0, 0); R.pD.cadera.rotation.set(0, 0, 0); R.pI.rodilla.rotation.set(0, 0, 0); R.pD.rodilla.rotation.set(0, 0, 0); };
  reset();
  if (pose === 'caminar') {
    const w = s * 7.5, a = Math.sin(w); R.pI.cadera.rotation.x = a * .62; R.pD.cadera.rotation.x = -a * .62;
    R.pI.rodilla.rotation.x = Math.max(0, -Math.sin(w + 1.2)) * .9; R.pD.rodilla.rotation.x = Math.max(0, Math.sin(w + 1.2)) * .9;
    R.bI.hombro.rotation.x = -a * .55; R.bD.hombro.rotation.x = a * .55; R.bI.codo.rotation.x = -.25; R.bD.codo.rotation.x = -.25; R.pelvis.position.y = .98 + Math.abs(Math.cos(w)) * .035; R.torso.rotation.y = a * .08;
  } else if (pose === 'martillar') {
    const a = Math.sin(s * 6); R.torso.rotation.x = .28; R.pelvis.position.y = .9; R.pI.cadera.rotation.x = -.35; R.pD.cadera.rotation.x = -.15; R.pI.rodilla.rotation.x = .55; R.pD.rodilla.rotation.x = .3;
    R.bD.hombro.rotation.x = -1.2 - Math.max(0, a) * 1.1; R.bD.codo.rotation.x = -.8 - Math.max(0, a) * .5; R.bI.hombro.rotation.x = -.9; R.bI.codo.rotation.x = -.7; R.cabeza.rotation.x = .2;
  } else if (pose === 'soldar') {
    R.torso.rotation.x = .55; R.pelvis.position.y = .84; R.pI.cadera.rotation.x = -.7; R.pD.cadera.rotation.x = -.45; R.pI.rodilla.rotation.x = 1.0; R.pD.rodilla.rotation.x = .75; R.visera.visible = true; R.cabeza.rotation.x = .35;
    R.bD.hombro.rotation.x = -1.35 + Math.sin(s * 3) * .05; R.bD.codo.rotation.x = -.5; R.bI.hombro.rotation.x = -1.15; R.bI.codo.rotation.x = -.45;
  } else if (pose === 'esmerilar') {
    R.torso.rotation.x = .4; R.pelvis.position.y = .9; R.pI.cadera.rotation.x = -.4; R.pD.cadera.rotation.x = -.2; R.pI.rodilla.rotation.x = .6; R.pD.rodilla.rotation.x = .35;
    R.bD.hombro.rotation.x = -1.1 + Math.sin(s * 9) * .12; R.bI.hombro.rotation.x = -1.0 + Math.sin(s * 9) * .1; R.bD.codo.rotation.x = -.6; R.bI.codo.rotation.x = -.6; R.visera.visible = true;
  } else if (pose === 'operar') {
    R.torso.rotation.x = .1; R.bD.hombro.rotation.x = -1.0 + Math.sin(s * 1.3) * .05; R.bD.codo.rotation.x = -.5; R.bI.hombro.rotation.x = -.15; R.cabeza.rotation.y = Math.sin(s * .8) * .3;
  } else if (pose === 'sentado') {
    R.pelvis.position.y = .66; R.pI.cadera.rotation.x = -1.5; R.pD.cadera.rotation.x = -1.5; R.pI.rodilla.rotation.x = 1.5; R.pD.rodilla.rotation.x = 1.5; R.bI.hombro.rotation.x = -.9; R.bD.hombro.rotation.x = -.9; R.bI.codo.rotation.x = -.5; R.bD.codo.rotation.x = -.5;
  } else {   // quieto
    R.torso.rotation.x = Math.sin(s * 1.4) * .012; R.bI.hombro.rotation.z = .07 + Math.sin(s * 1.4) * .01; R.cabeza.rotation.y = Math.sin(s * .5) * .18;
  }
}

/* ============================================================ camión tractocamión con plataforma */
function rueda(r = .52, ancho = .3) {
  const g = new THREE.Group(), neu = cil(r, ancho, M.goma()); neu.rotation.x = Math.PI / 2; g.add(neu);
  const llanta = cil(r * .62, ancho + .02, M.cromo(), false); llanta.rotation.x = Math.PI / 2; g.add(llanta);
  const buje = cil(r * .22, ancho + .05, M.aceroOsc(), false); buje.rotation.x = Math.PI / 2; g.add(buje);
  for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; const t = cil(.025, ancho + .07, M.negro(), false); t.rotation.x = Math.PI / 2; t.position.set(Math.cos(a) * r * .38, Math.sin(a) * r * .38, 0); g.add(t); }
  g.userData.radio = r; return g;
}
export function crearCamion(o = {}) {
  const { color = 0x1f5aa6, plataforma = true } = o, g = new THREE.Group(), cab = new THREE.Group(), pintura = mat(color, { metalness: .35, roughness: .35 });
  g.userData.ruedas = [];
  // chasis del tractor y cabina (cab-over)
  cab.add(en(caja(5.9, .28, 1.0, M.aceroOsc()), -.2, 1.0, 0));
  const cabina = cajaRedonda(2.35, 2.5, 2.3, .22, pintura); cabina.position.set(-3.3, 2.35, 0); cabina.rotation.y = Math.PI / 2; cab.add(cabina);
  cab.add(en(cajaRedonda(2.3, 1.0, 1.4, .18, pintura), -3.15, 3.95, 0)); cab.children[cab.children.length - 1].rotation.y = Math.PI / 2;
  const pb = caja(.04, .9, 1.7, M.vidrio(), false); pb.position.set(-4.43, 2.95, 0); pb.rotation.z = -.12; cab.add(pb);                 // parabrisas
  for (const lado of [-1, 1]) { const v = caja(1.2, .75, .04, M.vidrio(), false); v.position.set(-3.55, 2.95, lado * 1.17); cab.add(v); cab.add(en(caja(.06, .08, .8, M.negro(), false), -3.0, 2.3, lado * 1.18)); cab.add(en(caja(.3, .36, .2, M.negro()), -4.35, 3.15, lado * 1.3)); }  // ventanas, manijas, espejos
  cab.add(en(caja(.12, .55, 1.9, M.negro()), -4.46, 1.5, 0)); cab.add(en(caja(.1, .9, 1.7, M.pintGris()), -4.5, 2.1, 0));                  // parachoques y rejilla
  for (let i = 0; i < 4; i++) cab.add(en(caja(.02, .06, 1.4, M.negro(), false), -4.56, 1.95 + i * .13, 0));
  for (const lado of [-1, 1]) { cab.add(en(caja(.1, .22, .42, mat(0xfff3c4, { emissive: 0xfff3c4, emissiveIntensity: .35 })), -4.55, 2.35, lado * .75)); g.userData.faro = true; cab.add(en(cil(.28, .6, M.cromo()), -3.2, 1.0, lado * 1.15)); }  // faros y tanques
  cab.add(en(cil(.07, 1.7, M.cromo()), -2.45, 3.1, -1.1)); cab.add(en(caja(.06, .5, .02, mat(0xfafafa), false), -4.58, 1.75, 0));        // escape y placa
  g.add(cab);
  const quinta = caja(1.2, .12, 1.2, M.aceroOsc()); quinta.position.set(.9, 1.2, 0); g.add(quinta);
  const eje = (x, steer) => { for (const lado of [-1, 1]) { const w = rueda(); w.position.set(x, .52, lado * 1.02); g.add(w); g.userData.ruedas.push(w); } g.add(en(rot(cil(.08, 2.0, M.aceroOsc(), false), Math.PI / 2, 0, 0), x, .52, 0)); };
  eje(-3.35, true); eje(-.35); eje(.95);
  // semirremolque de plataforma
  const tr = new THREE.Group(); tr.position.x = 1.0; g.add(tr);
  tr.add(en(caja(12.6, .18, 2.5, matTex('placa', { color: 0xbfc6cd, metalness: .6, roughness: .55 })), 6.2, 1.38, 0));
  for (const z of [-1.05, 1.05]) tr.add(en(caja(12.6, .3, .14, M.aceroOsc()), 6.2, 1.15, z));
  for (let i = 0; i < 8; i++) tr.add(en(caja(.1, .26, 2.3, M.aceroOsc(), false), 1 + i * 1.6, 1.15, 0));
  for (let i = 0; i < 7; i++) for (const z of [-1.28, 1.28]) tr.add(en(caja(.07, .35, .07, M.aceroOsc(), false), .4 + i * 2.0, 1.62, z));          // postes laterales
  tr.add(en(caja(.18, .5, 2.5, M.aceroOsc()), 12.5, 1.55, 0));                                                                                       // tope trasero
  for (const x of [9.4, 10.9, 12.4]) for (const lado of [-1, 1]) { const w = rueda(); w.position.set(x - 1, .52, lado * 1.02); tr.add(w); g.userData.ruedas.push(w); }
  for (const lado of [-1, 1]) tr.add(en(caja(.08, .1, .3, mat(0xff2a1a, { emissive: 0xff2a1a, emissiveIntensity: .3 })), 12.6, 1.4, lado * 1.0));
  const carga = new THREE.Group(); carga.position.set(6.2, 1.48, 0); tr.add(carga); g.userData.carga = carga; g.userData.largo = 17;
  g.traverse(x => { if (x.isMesh) { x.castShadow = true; } }); return g;
}

/* ============================================================ máquinas con componentes (vista explosionada, rayos X) */
function parte(maq, id, nombre, descr, grupo, dir = [0, 1, 0], dist = 1, carcasa = false) {
  grupo.userData.parte = { id, nombre, descr, carcasa }; grupo.userData.base = grupo.position.clone(); grupo.userData.dir = new THREE.Vector3(...dir).normalize().multiplyScalar(dist);
  maq.partes.push(grupo); maq.g.add(grupo); return grupo;
}
const carc = (maq, c, op = .55) => { const m = new THREE.MeshStandardMaterial({ color: c, metalness: .3, roughness: .45 }); m.userData.op = op; maq.carcasas.push(m); return m; };
function lucesTorre(maq, x, y, z) {
  const t = new THREE.Group(); t.add(en(cil(.04, 1.8, M.aceroOsc(), false), 0, .9, 0));
  maq.luces = [0xe74c3c, 0xffb020, 0x2ecc71].map((c, i) => { const l = en(cil(.12, .2, M.aceroOsc(), false), 0, 1.85 + i * .22, 0); l.userData.color = c; t.add(l); return l; });
  t.position.set(x, y, z); return t;
}
function consola(maq, w = .5, h = .9, d = .45) {
  const g = new THREE.Group(); g.add(en(caja(w, h, d, M.blanco()), 0, h / 2, 0)); g.add(en(caja(w * .8, h * .3, .03, mat(0x0d2b45, { emissive: 0x1a5f9a, emissiveIntensity: .5 }), false), 0, h * .72, d / 2 + .01));
  for (let i = 0; i < 4; i++) g.add(en(rot(cil(.025, .03, i === 0 ? M.rojo() : M.aceroOsc(), false), Math.PI / 2, 0, 0), -w * .25 + i * w * .17, h * .45, d / 2 + .015)); return g;
}
export function crearMaquina(k) {
  const maq = { k, g: new THREE.Group(), partes: [], carcasas: [], luces: [], anim: null, nombre: ['Sierra de cinta horizontal', 'Cizalla-punzonadora', 'Mesa de corte CNC (plasma)', 'Roscadora de barras'][k] };
  const azul = M.pintAzul(), gris = M.pintGris(), osc = M.aceroOsc(), placa = () => matTex('placa', { color: 0xc0c7ce, metalness: .6, roughness: .55 });
  const rodillos = (largo, z0 = 0, n = Math.round(largo / .36)) => { const g = new THREE.Group(); for (let i = 0; i < n; i++) g.add(en(rot(cil(.09, 1.5, M.cromo(), false), Math.PI / 2, 0, 0), -largo / 2 + (i + .5) * (largo / n), .98, z0)); for (const z of [-.82, .82]) g.add(en(caja(largo, .1, .08, osc), 0, .86, z0 + z)); for (const x of [-largo / 2 + .2, 0, largo / 2 - .2]) for (const z of [-.78, .78]) g.add(en(caja(.1, .86, .1, osc, false), x, .43, z0 + z)); return g; };
  if (k === 0) {                       /* ---- sierra de cinta horizontal: cabezal articulado, cinta en plano horizontal, pieza avanza sobre rodillos ---- */
    const base = new THREE.Group(); base.add(en(caja(3.4, .6, 2.8, osc), 0, .3, 0)); for (const x of [-1.5, 1.5]) for (const z of [-1.2, 1.2]) base.add(en(caja(.3, .12, .3, M.negro()), x, .06, z)); base.add(en(caja(3.2, .07, 2.4, placa()), 0, .64, 0));
    parte(maq, 'bastidor', 'Bastidor y mesa', 'Estructura soldada que soporta el equipo; la mesa lleva pletina antideslizante.', base, [0, -1, 0], .8);
    const cab = new THREE.Group(); cab.position.set(-1.7, 1.45, 0);
    cab.add(en(caja(2.5, .5, 3.4, azul), 1.2, .05, 0)); cab.add(en(caja(.5, 1.2, 1.2, azul), .1, -.4, 0));
    const volante = z => { const w = new THREE.Group(); w.add(en(cil(.52, .1, osc), 0, .33, 0)); w.add(en(cil(.12, .26, M.cromo(), false), 0, .33, 0)); w.add(en(cil(.54, .04, M.goma(), false), 0, .33, 0)); w.position.set(1.2, 0, z); return w; };
    const vM = volante(-1.2), vT = volante(1.2); cab.add(vM, vT);
    const cinta = new THREE.Group(); for (const x of [.68, 1.72]) cinta.add(en(caja(.018, .1, 2.4, M.cromo(), false), x, .33, 0)); cab.add(cinta);
    const guias = new THREE.Group(); for (const z of [-.55, .55]) { guias.add(en(caja(.14, .5, .14, osc), 1.72, -.15, z)); guias.add(en(caja(.2, .12, .2, M.cromo()), 1.72, -.4, z)); } cab.add(guias);
    parte(maq, 'cabezal', 'Cabezal de corte', 'Cabezal articulado que baja sobre la pieza; aloja la cinta, los volantes y las guías.', cab, [0, 1, 0], 1.8); maq.cabezal = cab; maq.vols = [vM, vT];
    const tapa = new THREE.Group(); tapa.position.copy(cab.position); const tm = carc(maq, 0x2f6fb3); tapa.add(en(caja(2.4, .1, 3.3, tm), 1.2, .62, 0)); tapa.add(en(caja(.08, .45, 3.3, tm), 2.38, .35, 0)); tapa.add(en(caja(.08, .45, 3.3, tm), .02, .35, 0)); for (const z of [-1.7, 1.7]) tapa.add(en(caja(2.4, .45, .08, tm), 1.2, .35, z));
    parte(maq, 'tapa', 'Protección de volantes', 'Carcasa de seguridad sobre volantes y cinta (se hace transparente en rayos X).', tapa, [0, 1, 0], 3.0, true); maq.tapa = tapa;
    const motor = new THREE.Group(); motor.add(en(caja(1.0, .55, .6, azul), 0, 0, 0)); motor.add(en(rot(cil(.2, .6, gris), 0, 0, Math.PI / 2), -.7, 0, 0)); motor.position.set(-.5, 1.75, -2.1); parte(maq, 'motor', 'Motor y reductor', 'Mueve el volante motriz mediante una caja reductora; fija la velocidad de corte.', motor, [0, 0, -1], 1.5);
    const cilh = new THREE.Group(); cilh.add(en(cil(.1, 1.0, M.cromo()), 0, .55, 0)); cilh.add(en(cil(.16, .7, gris), 0, .35, 0)); cilh.position.set(-1.5, .65, 1.0); parte(maq, 'cilindro', 'Cilindro hidráulico de avance', 'Baja y sube el cabezal controlando la presión de corte.', cilh, [-1, 0, 1], 1.4);
    const vise = new THREE.Group(); vise.add(en(caja(.35, .7, 1.2, osc), -.55, .98, 0)); const movil = caja(.3, .7, 1.0, gris); movil.position.set(.3, .98, 0); vise.add(movil); vise.add(en(rot(cil(.08, .9, M.cromo()), 0, 0, Math.PI / 2), 0, .98, 0)); maq.movil = movil; parte(maq, 'mordaza', 'Mordaza hidráulica', 'Sujeta el perfil durante el corte para evitar vibración y desvíos.', vise, [0, 0, 1], 1.5);
    const ent = rodillos(3.0); ent.position.set(-4.6, 0, 0); parte(maq, 'entrada', 'Mesa de rodillos de entrada', 'Alimenta las vigas y perfiles hasta el tope de longitud.', ent, [-1, 0, 0], 1.6);
    const sal = rodillos(3.0); sal.position.set(4.6, 0, 0); parte(maq, 'salida', 'Mesa de rodillos de salida', 'Recibe la pieza cortada para llevarla al buffer.', sal, [1, 0, 0], 1.6);
    const tope = new THREE.Group(); tope.add(en(caja(.12, .9, .8, M.amarillo()), 0, 1.15, 0)); tope.position.set(6.0, 0, 0); parte(maq, 'tope', 'Tope de longitud', 'Define el largo de corte; se desplaza con un motor y se lee en el control.', tope, [1, 0, 0], 1.8);
    const hid = new THREE.Group(); hid.add(en(caja(1.3, .9, .9, azul), 0, .45, 0)); hid.add(en(cil(.2, .45, gris), -.4, 1.05, 0)); hid.position.set(.3, 0, 2.1); parte(maq, 'hidraulica', 'Unidad hidráulica', 'Depósito, bomba y motor que alimentan los cilindros.', hid, [0, 0, 1], 1.6);
    const ref = new THREE.Group(); ref.add(en(caja(.9, .7, .7, gris), 0, .35, 0)); ref.add(en(cil(.03, 1.4, M.negro(), false), .5, .9, -.5)); ref.position.set(-1.3, 0, -2.1); parte(maq, 'refrigerante', 'Tanque de refrigerante', 'Bomba y depósito de fluido de corte que enfría y lubrica la cinta.', ref, [0, 0, -1], 1.6);
    const ctl = new THREE.Group(); ctl.add(consola(maq)); ctl.add(lucesTorre(maq, .5, 0, -.35)); ctl.position.set(1.9, 0, -2.2); parte(maq, 'control', 'Gabinete de control y torre de luces', 'Pantalla, botonera y semáforo del estado (verde operando, ámbar espera, rojo falla).', ctl, [0, 0, -1], 1.6);
    maq.largo = 12; maq.alto = 3.2;
    maq.anim = (t, a) => { maq.vols.forEach(v => { v.rotation.y += a ? .09 : 0; }); maq.cabezal.rotation.z = a ? -Math.abs(Math.sin(t * .0011)) * .2 : 0; maq.tapa.rotation.z = maq.cabezal.rotation.z; maq.movil.position.x = a ? .22 : .3; };
  } else if (k === 1) {                /* ---- cizalla-punzonadora (ironworker) ---- */
    const base = new THREE.Group(); base.add(en(caja(2.8, .5, 2.2, osc), 0, .25, 0)); for (const x of [-1.2, 1.2]) for (const z of [-.9, .9]) base.add(en(caja(.3, .12, .3, M.negro()), x, .06, z)); parte(maq, 'bastidor', 'Base y apoyos', 'Placa base anclada al piso que absorbe la reacción del corte y el punzonado.', base, [0, -1, 0], .8);
    const cm = carc(maq, 0x1f5aa6, .6), c = new THREE.Group(); c.add(en(caja(1.0, 2.7, 1.5, cm), 0, 1.85, 0)); c.add(en(caja(2.6, .9, 1.5, cm), .8, 3.0, 0)); c.add(en(caja(1.4, .5, 1.7, cm), .55, .75, 0));
    parte(maq, 'bastidor_c', 'Bastidor en C', 'Cuerpo de acero de gran espesor; su abertura permite meter perfiles largos.', c, [-1, 0, 0], 1.4, true);
    const ram = new THREE.Group(); ram.add(en(cil(.26, 1.1, M.cromo()), 0, 0, 0)); ram.add(en(caja(.5, .45, .55, osc), 0, -.75, 0)); ram.add(en(cil(.09, .45, M.cromo(), false), 0, -1.1, 0)); ram.position.set(-1.35, 2.7, .1); parte(maq, 'ariete', 'Ariete y punzón', 'El cilindro hidráulico empuja el punzón a través de la plancha o el perfil.', ram, [0, 1, 0], 1.6); maq.ram = ram;
    const cuch = new THREE.Group(); cuch.add(en(caja(.3, 1.4, .7, osc), 0, 0, 0)); cuch.add(en(caja(.1, 1.0, .9, M.cromo()), .2, -.1, 0)); cuch.position.set(1.7, 2.65, .1); parte(maq, 'cizalla', 'Cuchilla de cizalla', 'Cuchilla móvil contra cuchilla fija: corta platina, ángulo y barra.', cuch, [1, 0, 0], 1.6); maq.cuchilla = cuch;
    const mz = new THREE.Group(); mz.add(en(caja(.9, .3, .9, osc), 0, .15, 0)); mz.add(en(cil(.18, .18, M.cromo(), false), 0, .38, 0)); mz.position.set(-1.35, 1.2, .1); parte(maq, 'matriz', 'Matriz y portamatriz', 'Pieza de acero templado sobre la que se perfora el agujero.', mz, [0, -1, 0], 1.0);
    const mesa = z0 => { const g = new THREE.Group(); g.add(en(caja(2.4, .1, 1.1, placa()), 0, 0, 0)); for (const x of [-1, 1]) for (const z of [-.45, .45]) g.add(en(caja(.08, 1.1, .08, osc, false), x, -.55, z)); g.position.set(z0, 1.5, .1); return g; };
    parte(maq, 'mesa_i', 'Mesa de apoyo izquierda', 'Soporta la plancha o el perfil en la estación de punzonado.', mesa(-3.0), [-1, 0, 0], 1.5); parte(maq, 'mesa_d', 'Mesa de apoyo derecha', 'Soporta la platina en la estación de cizalla.', mesa(3.2), [1, 0, 0], 1.5);
    const hid = new THREE.Group(); hid.add(en(caja(1.4, 1.0, .9, azul), 0, .5, 0)); hid.add(en(cil(.25, .6, gris), -.3, 1.3, 0)); hid.position.set(-.2, 0, -1.9); parte(maq, 'hidraulica', 'Unidad motor-bomba', 'Motor eléctrico y bomba que alimentan los cilindros de punzón y cizalla.', hid, [0, 0, -1], 1.6);
    const ped = new THREE.Group(); ped.add(en(caja(.5, .12, .7, M.amarillo()), 0, .08, 0)); ped.add(en(caja(.35, .25, .4, M.negro()), 0, .25, 0)); ped.position.set(.6, 0, 1.7); parte(maq, 'pedal', 'Pedal de mando', 'El operario acciona el ciclo con el pie; tiene parada de emergencia.', ped, [0, 0, 1], 1.5);
    const ctl = new THREE.Group(); ctl.add(consola(maq, .5, .9, .4)); ctl.add(lucesTorre(maq, .6, 0, -.3)); ctl.position.set(2.0, 0, -1.7); parte(maq, 'control', 'Panel de control y torre de luces', 'Selector de estación, contador de golpes y semáforo de estado.', ctl, [0, 0, -1], 1.6);
    maq.largo = 8.4; maq.alto = 4;
    maq.anim = (t, a) => { maq.ram.position.y = 2.7 - (a ? Math.max(0, Math.sin(t * .006)) * .6 : 0); maq.cuchilla.position.y = 2.65 - (a ? Math.max(0, Math.sin(t * .006 + 2)) * .45 : 0); };
  } else if (k === 2) {                /* ---- mesa CNC de plasma ---- */
    const chas = new THREE.Group(); chas.add(en(caja(7.4, .9, 3.8, osc), 0, .45, 0)); for (const x of [-3.3, 3.3]) for (const z of [-1.7, 1.7]) chas.add(en(caja(.35, .16, .35, M.negro()), x, .08, z));
    parte(maq, 'chasis', 'Chasis y tanque de agua', 'Bastidor soldado con tanque de agua que recoge escoria y humos del corte.', chas, [0, -1, 0], .9);
    const cama = new THREE.Group(); cama.add(en(caja(6.8, .08, 3.3, mat(0x3f6f8f, { metalness: .2, roughness: .3 })), 0, .95, 0)); for (let i = -13; i <= 13; i++) cama.add(en(caja(.05, .22, 3.2, mat(0x9aa4ae, { metalness: .9, roughness: .45 }), false), i * .25, 1.1, 0));
    parte(maq, 'cama', 'Cama de rejillas', 'Láminas de acero sobre las que apoya la plancha; se reemplazan al desgastarse.', cama, [0, 1, 0], 1.0);
    const rieles = new THREE.Group(); for (const z of [-1.95, 1.95]) { rieles.add(en(caja(7.6, .1, .14, M.cromo(), false), 0, 1.3, z)); rieles.add(en(caja(7.6, .18, .1, osc, false), 0, 1.2, z)); } parte(maq, 'rieles', 'Rieles y cremalleras', 'Guías longitudinales con cremallera por donde viaja el pórtico.', rieles, [0, 0, 1], 1.2);
    const por = new THREE.Group(); por.add(en(caja(.55, 1.3, .6, azul), 0, 1.95, -1.95)); por.add(en(caja(.55, 1.3, .6, azul), 0, 1.95, 1.95)); por.add(en(caja(.6, .5, 4.7, M.pintAzulCl()), 0, 2.85, 0));
    const carro = new THREE.Group(); carro.add(en(caja(.85, .8, .6, M.blanco()), 0, 2.7, 0)); carro.add(en(caja(.18, 1.0, .12, osc), 0, 2.15, .35)); carro.add(en(cil(.07, .6, M.cromo()), 0, 1.5, .35)); carro.add(en(cil(.03, .14, mat(0xff9d3a, { emissive: 0xff7a00, emissiveIntensity: .8 }), false), 0, 1.15, .35));
    const ch = esf(.15, mat(0xffb347, { emissive: 0xff7a00, emissiveIntensity: 2 })); ch.position.set(0, 1.0, .35); ch.visible = false; carro.add(ch); maq.chispas = ch; por.add(carro); por.position.set(-2.4, 0, 0);
    parte(maq, 'portico', 'Pórtico, carro y antorcha', 'Viaja sobre los rieles; el carro lleva la antorcha de plasma y su elevador de altura (THC).', por, [0, 1, 0], 1.5); maq.portico = por; maq.carro = carro;
    const fte = new THREE.Group(); fte.add(en(caja(1.3, 1.6, 1.0, M.blanco()), 0, .8, 0)); fte.add(en(caja(1.0, .35, .04, mat(0x0d2b45, { emissive: 0x1a5f9a, emissiveIntensity: .4 }), false), 0, 1.15, .52)); fte.position.set(-3.6, 0, 2.9); parte(maq, 'fuente', 'Fuente de plasma', 'Genera la corriente y el arco; define el espesor máximo de corte.', fte, [-1, 0, 1], 1.5);
    const gas = new THREE.Group(); for (let i = 0; i < 3; i++) gas.add(en(cil(.18, 1.4, [M.rojo(), M.pintAzul(), M.pintGris()][i]), i * .45, .7, 0)); gas.position.set(-3.9, 0, -2.6); parte(maq, 'gas', 'Cilindros y consola de gas', 'Alimentan el gas de plasma y de protección (aire, oxígeno, nitrógeno).', gas, [-1, 0, -1], 1.4);
    const cad = new THREE.Group(); for (let i = 0; i < 16; i++) cad.add(en(caja(.2, .16, .3, M.negro(), false), i * .24, 0, 0)); cad.position.set(-2.4, 1.45, 2.3); parte(maq, 'cadena', 'Cadena portacables', 'Guía los cables y mangueras de la antorcha sin que se enganchen.', cad, [0, 0, 1], 1.4);
    const cam = new THREE.Group(), cmat = carc(maq, 0x9aa4ae, .4); cam.add(en(caja(6.4, .3, 3.1, cmat), 0, 4.6, 0)); cam.add(en(cil(.45, 2.6, gris), 2.6, 6.0, 0)); parte(maq, 'campana', 'Campana y ducto de extracción', 'Captura humos y polvo metálico del corte y los envía al filtro.', cam, [0, 1, 0], 2.2, true);
    const ctl = new THREE.Group(); ctl.add(consola(maq, .8, 1.3, .6)); ctl.add(lucesTorre(maq, .7, 0, -.4)); ctl.position.set(3.6, 0, 2.9); parte(maq, 'control', 'Control CNC', 'Computadora que lee los planos de corte (nesting) y ordena el movimiento del pórtico.', ctl, [1, 0, 1], 1.5);
    maq.largo = 8.2; maq.alto = 4.6;
    maq.anim = (t, a) => { const f = a ? Math.sin(t * .0007) : 0; maq.portico.position.x = -2.4 + (a ? (f * .5 + .5) * 4.4 : 0); maq.carro.position.z = a ? Math.sin(t * .0021) * 1.3 : 0; maq.chispas.visible = a && Math.sin(t * .05) > -.4; };
  } else {                             /* ---- roscadora de barras ---- */
    const bas = new THREE.Group(); bas.add(en(caja(3.2, .16, 1.5, osc), 0, .88, 0)); for (const x of [-1.3, 1.3]) for (const z of [-.6, .6]) bas.add(en(caja(.14, .86, .14, osc, false), x, .43, z)); bas.add(en(caja(3.0, .1, 1.3, gris, false), 0, .25, 0));
    parte(maq, 'soporte', 'Soporte y bastidor', 'Banco de acero con patas niveladoras.', bas, [0, -1, 0], .8);
    const mot = new THREE.Group(), mm = carc(maq, 0x1f5aa6, .55); mot.add(en(caja(1.4, 1.0, 1.1, mm), 0, .5, 0)); mot.add(en(rot(cil(.3, .6, gris), 0, 0, Math.PI / 2), -.9, .5, 0)); mot.position.set(-1.0, .96, 0); parte(maq, 'motor', 'Motor y caja reductora', 'Mueve el mandril; la caja de engranajes da el par para roscar barras gruesas.', mot, [-1, 1, 0], 1.3, true);
    const man = new THREE.Group(); man.add(en(rot(cil(.34, .5, osc), 0, 0, Math.PI / 2), 0, 0, 0)); for (let i = 0; i < 3; i++) { const a = i / 3 * Math.PI * 2; man.add(en(caja(.2, .1, .1, M.cromo(), false), .3, Math.cos(a) * .3, Math.sin(a) * .3)); } man.position.set(.2, 1.55, 0); parte(maq, 'mandril', 'Mandril', 'Sujeta y hace girar la barra mientras se corta la rosca.', man, [0, 1, 0], 1.3); maq.mandril = man;
    const car = new THREE.Group(); car.add(en(caja(1.0, .55, 1.0, azul), 0, 0, 0)); car.add(en(rot(cil(.28, .4, M.cromo()), 0, 0, Math.PI / 2), .1, .2, 0)); for (const dz of [-.3, .3]) car.add(en(caja(.1, .3, .05, M.cromo(), false), -.2, .35, dz)); car.position.set(1.2, 1.4, 0); parte(maq, 'cabezal', 'Cabezal de roscar y carro', 'El cabezal con peines corta la rosca; el carro lo desplaza a lo largo de la barra.', car, [1, 1, 0], 1.4); maq.carro = car;
    const cor = new THREE.Group(); cor.add(en(rot(cil(.2, .12, M.cromo()), Math.PI / 2, 0, 0), 0, 0, 0)); cor.add(en(caja(.1, .9, .1, osc), 0, .5, 0)); cor.position.set(1.2, 1.95, .6); parte(maq, 'cortador', 'Cortador y escariador', 'Corta la barra a medida y rebaja el borde antes de roscar.', cor, [0, 1, 1], 1.3);
    const ace = new THREE.Group(); ace.add(en(caja(1.2, .35, .8, gris), 0, .18, 0)); ace.add(en(cil(.1, .5, M.negro(), false), .3, .5, 0)); ace.position.set(.4, .25, .1); parte(maq, 'aceite', 'Bomba y bandeja de aceite', 'Lubrica y enfría el corte de la rosca y recoge las virutas.', ace, [0, -1, 1], 1.2);
    const ped = new THREE.Group(); ped.add(en(caja(.45, .1, .6, M.amarillo()), 0, .06, 0)); ped.position.set(0, 0, 1.4); parte(maq, 'pedal', 'Pedal de mando', 'Arranca y detiene el giro del mandril.', ped, [0, 0, 1], 1.4);
    const bar = new THREE.Group(); for (let i = 0; i < 7; i++) bar.add(en(rot(cil(.03, 3.4, M.acero(), false), 0, 0, Math.PI / 2), 0, 1.4 + i * .02, (i % 3 - 1) * .08)); bar.add(en(caja(.12, 1.1, .5, osc), -1.0, .55, 0)); bar.add(en(caja(.12, 1.1, .5, osc), 1.0, .55, 0)); bar.position.set(-3.2, 0, 0); parte(maq, 'barras', 'Soporte de barras', 'Caballetes que sostienen las barras largas alineadas con el mandril.', bar, [-1, 0, 0], 1.8);
    const ctl = new THREE.Group(); ctl.add(consola(maq, .4, .8, .35)); ctl.add(lucesTorre(maq, .5, 0, -.3)); ctl.position.set(-.3, 0, -1.4); parte(maq, 'control', 'Botonera y torre de luces', 'Arranque, parada de emergencia y semáforo de estado.', ctl, [0, 0, -1], 1.4);
    maq.largo = 8; maq.alto = 3;
    maq.anim = (t, a) => { maq.mandril.rotation.x += a ? .45 : 0; maq.carro.position.x = 1.2 + (a ? Math.sin(t * .0012) * .25 : 0); };
  }
  maq.g.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return maq;
}
/* despliega o repliega los componentes (f de 0 a 1) y activa los rayos X de las carcasas */
export function explotar(maq, f) { maq.partes.forEach(p => { p.position.copy(p.userData.base).addScaledVector(p.userData.dir, f * 2.2); }); }
export function rayosX(maq, on) { maq.carcasas.forEach(m => { m.transparent = on; m.opacity = on ? m.userData.op * .35 : 1; m.depthWrite = !on; m.needsUpdate = true; }); }
