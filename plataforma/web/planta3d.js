/* SteelPlan · escena 3D de la planta (three.js, copia local en vendor/three/).
   Se genera a partir del modelo de planta (tabla sim_planta_elemento): máquinas, mesas, puestos, racks, naves, muelles.
   Cada día se redibuja lo dinámico: personal, lotes en proceso o en cola y material en stock. Todo es SIMULADO. */
import * as THREE from '/static/vendor/three/three.module.js';
import { OrbitControls } from '/static/vendor/three/OrbitControls.js';

const CX = 50, CZ = 25;                                   // el predio (100 × 50 m) se centra en el origen
const COLOR_ETAPA = { ACOPIO: 0xb0bac5, HABILITADO: 0x6bb6ff, DOBLEZ: 0xc9b2ee, ARMADO: 0xffb066, SOLDEO: 0xff8a4c,
  LIMPIEZA: 0x8fd6a3, PINTURA: 0x61cdc0, DESPACHO: 0xffd966 };
const COLOR_MATERIAL = { PERFIL_W: 0x4b86c5, PERFIL_HEA: 0x2f6fb3, CANAL: 0x7aa5d6, ANGULO: 0x9ab7d6, PLANCHA: 0x8a97a6, TUBO: 0xd9a066 };
const COLOR_GRUPO = ['#e9730c', '#925ace', '#107e3e', '#bb0000', '#0a6ed1'];
const hash = s => [...String(s)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);

const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: .78, metalness: .05, ...o });
const caja = (w, h, d, c, o) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), c.isMaterial ? c : mat(c, o)); m.castShadow = true; m.receiveShadow = true; return m; };

export function crearEscena(contenedor, modelo, opts = {}) {
  if (!window.WebGLRenderingContext) throw new Error('Este navegador no admite WebGL');
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(0x000000, 0);
  contenedor.appendChild(renderer.domElement);
  renderer.domElement.style.cssText = 'display:block;width:100%;height:100%;outline:none';

  const escena = new THREE.Scene();
  const camara = new THREE.PerspectiveCamera(32, 1, 1, 900);
  const controles = new OrbitControls(camara, renderer.domElement);
  controles.enableDamping = true; controles.dampingFactor = .08;
  controles.maxPolarAngle = 1.42; controles.minDistance = 18; controles.maxDistance = 260;
  controles.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };

  escena.add(new THREE.HemisphereLight(0xffffff, 0xb7c8da, 1.15));
  const sol = new THREE.DirectionalLight(0xffffff, 1.35);
  sol.position.set(60, 90, 40); sol.castShadow = true;
  sol.shadow.mapSize.set(2048, 2048);
  Object.assign(sol.shadow.camera, { left: -85, right: 85, top: 60, bottom: -60, near: 10, far: 260 });
  sol.shadow.bias = -0.0004;
  escena.add(sol);

  const estatico = new THREE.Group(), dinamico = new THREE.Group();
  escena.add(estatico, dinamico);
  const porId = {};               // id de elemento → { grupo, el, pos (Vector3 centro), luz }
  const techos = [];
  const animEst = [], animDin = [];       // animaciones fijas (grúas) y del día (personal)
  const etiquetas = [];
  const capaEt = document.createElement('div');
  capaEt.className = 'p3d-etiquetas';
  contenedor.appendChild(capaEt);
  const tip = document.createElement('div');
  tip.className = 'p3d-tip oculto';
  contenedor.appendChild(tip);

  const pos = (x, z, y = 0) => new THREE.Vector3(x - CX, y, z - CZ);
  const etiqueta = (texto, v, clase = '') => {
    const e = document.createElement('div'); e.className = 'p3d-et ' + clase; e.textContent = texto; capaEt.appendChild(e);
    etiquetas.push({ el: e, v });
  };
  const marcar = (obj, ref) => { obj.traverse(o => { o.userData.ref = ref; }); };

  /* ---------- terreno, calle y árboles ---------- */
  const suelo = new THREE.Mesh(new THREE.PlaneGeometry(260, 190), mat(0xd9e6f2));
  suelo.rotation.x = -Math.PI / 2; suelo.position.y = -0.2; suelo.receiveShadow = true; estatico.add(suelo);
  const calle = new THREE.Mesh(new THREE.PlaneGeometry(260, 14), mat(0xaeb9c7));
  calle.rotation.x = -Math.PI / 2; calle.position.set(0, -0.15, 44); calle.receiveShadow = true; estatico.add(calle);
  for (let i = -6; i <= 6; i++) {
    const r = new THREE.Mesh(new THREE.PlaneGeometry(5, .35), mat(0xf6f8fa));
    r.rotation.x = -Math.PI / 2; r.position.set(i * 18, -0.12, 44); estatico.add(r);
  }
  const arbol = (x, z, s = 1) => {
    const g = new THREE.Group();
    const t = caja(.5 * s, 2.2 * s, .5 * s, 0x8b5a2b); t.position.y = 1.1 * s; g.add(t);
    const c = new THREE.Mesh(new THREE.IcosahedronGeometry(2 * s, 1), mat(0x6fbf73)); c.position.y = 3.6 * s; c.castShadow = true; g.add(c);
    g.position.set(x, 0, z); estatico.add(g);
  };
  [[-62, -10], [-66, 8], [-60, 28], [64, -18], [70, 6], [66, 30], [-30, -36], [10, -38], [40, -36], [-70, -26], [74, -30]]
    .forEach(([x, z], i) => arbol(x, z, .8 + (i % 3) * .2));

  /* ---------- elementos del modelo ---------- */
  const cuerpoMaquina = (po, w, d, h) => {
    const g = new THREE.Group();
    const base = caja(w, .8, d, 0x5b738b); base.position.y = .4; g.add(base);
    if (po === 3) {                                    // sierra cinta: cama larga + arco
      const cama = caja(w, .5, d * .5, 0xc3ccd5); cama.position.set(0, 1.05, 0); g.add(cama);
      const arco = caja(.7, 2.0, d * .8, 0x2f6fb3); arco.position.set(-w * .15, 1.8, 0); g.add(arco);
      const cab = caja(2.2, .8, d * .9, 0x1b90ff); cab.position.set(-w * .15, 2.9, 0); g.add(cab);
    } else if (po === 4) {                             // cizalla-punzonadora: cuerpo alto
      const cu = caja(w * .6, 2.4, d * .8, 0x2f6fb3); cu.position.set(w * .1, 1.8, 0); g.add(cu);
      const mesa = caja(w * .9, .35, d, 0xc3ccd5); mesa.position.set(0, 1.1, 0); g.add(mesa);
    } else if (po === 5) {                             // mesa CNC: mesa grande + pórtico
      const mesa = caja(w, .5, d, 0xc3ccd5); mesa.position.y = 1.1; g.add(mesa);
      const p1 = caja(.4, 1.9, d + .6, 0x1b90ff); p1.position.set(-w * .3, 2.0, 0); g.add(p1);
      const p2 = caja(.4, 1.9, d + .6, 0x1b90ff); p2.position.set(w * .3, 2.0, 0); g.add(p2);
      const v = caja(w * .7, .4, .6, 0x2f6fb3); v.position.set(0, 3.05, 0); g.add(v);
    } else {                                           // roscadora
      const cu = caja(w * .5, 1.5, d * .8, 0x2f6fb3); cu.position.set(-w * .1, 1.5, 0); g.add(cu);
      const eje = new THREE.Mesh(new THREE.CylinderGeometry(.25, .25, w, 12), mat(0xc3ccd5)); eje.rotation.z = Math.PI / 2; eje.position.set(w * .25, 1.6, 0); g.add(eje);
    }
    return g;
  };

  for (const e of modelo.elementos) {
    const v = pos(e.x, e.z), g = new THREE.Group();
    const ref = { tipo: 'elemento', id: e.id, nombre: e.nombre, tipo_elemento: e.tipo };
    let luz = null;
    if (e.tipo === 'terreno') {
      const borde = new THREE.Mesh(new THREE.PlaneGeometry(e.ancho, e.largo), mat(0xeef3f8));
      borde.rotation.x = -Math.PI / 2; borde.position.set(v.x, -0.1, v.z); borde.receiveShadow = true; estatico.add(borde);
      continue;
    } else if (e.tipo === 'nave') {
      const piso = caja(e.ancho, .2, e.largo, 0xf7f9fb); piso.position.y = .1; g.add(piso);
      const paredes = [[0, -e.largo / 2, e.ancho, .35], [0, e.largo / 2, e.ancho, .35], [-e.ancho / 2, 0, .35, e.largo], [e.ancho / 2, 0, .35, e.largo]];
      paredes.forEach(([x, z, w, d]) => { const p = caja(w, 3.2, d, 0xc7d8ec); p.position.set(x, 1.7, z); g.add(p); });
      for (let x = -e.ancho / 2; x <= e.ancho / 2 + .1; x += e.ancho / 6) for (const z of [-e.largo / 2, e.largo / 2]) {
        const c = caja(.5, e.alto, .5, 0x5b738b); c.position.set(x, e.alto / 2, z); g.add(c);
      }
      const techo = caja(e.ancho + 1, .5, e.largo + 1, 0x1b6fd1, { transparent: true, opacity: .42 });
      techo.position.y = e.alto + .25; techo.castShadow = false; g.add(techo); techos.push(techo);
      g.position.copy(v); estatico.add(g);
      etiqueta(e.nombre, pos(e.x, e.z - e.largo / 2 - .5, e.alto + 1), 'nave');
      continue;
    } else if (e.tipo === 'zona') {
      const color = e.nombre.startsWith('Patio') ? 0xe7e2d2 : e.nombre.startsWith('Buffer') ? 0xdce8f3 : 0xe6ecf2;
      const z = caja(e.ancho, .12, e.largo, color); z.position.y = .06; g.add(z);
      const borde = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(e.ancho, .13, e.largo)),
        new THREE.LineBasicMaterial({ color: 0xe0b020 })); borde.position.y = .08; g.add(borde);
      etiqueta(e.nombre.replace(' de perfiles y planchas', '').replace(' de piezas habilitadas', ''), pos(e.x, e.z, 1.2), 'zona');
    } else if (e.tipo === 'grua') {
      const rail = (dz) => { const r = caja(e.ancho, .4, .45, 0xe9730c); r.position.set(0, e.alto, dz); return r; };
      g.add(rail(-13.5), rail(13.5));
      const puente = new THREE.Group();
      const viga = caja(.9, .9, 27, 0xffb347); puente.add(viga);
      const carro = caja(2, .8, 2, 0x5b738b); carro.position.y = -.8; puente.add(carro);
      const cable = caja(.08, 4.5, .08, 0x223548); cable.position.y = -3.3; puente.add(cable);
      const gancho = caja(.5, .6, .5, 0xe9730c); gancho.position.y = -5.8; puente.add(gancho);
      puente.position.set(0, e.alto, 0); g.add(puente);
      animEst.push(t => { puente.position.x = Math.sin(t * .00022 + e.id) * (e.ancho / 2 - 3); carro.position.z = Math.sin(t * .00041 + e.id) * 11; cable.position.z = gancho.position.z = carro.position.z; });
    } else if (e.tipo === 'rack') {
      for (const dx of [-e.ancho / 2, e.ancho / 2]) for (const dz of [-e.largo / 2, e.largo / 2]) {
        const p = caja(.18, e.alto, .18, 0xe9730c); p.position.set(dx, e.alto / 2, dz); g.add(p);
      }
      for (let n = 0; n < 3; n++) { const b = caja(e.ancho + .3, .15, e.largo + .3, 0xf4a259); b.position.y = .4 + n * 1.2; g.add(b); }
    } else if (e.tipo === 'maquina') {
      g.add(cuerpoMaquina(e.proceso_orden, e.ancho, e.largo, e.alto));
      luz = new THREE.Mesh(new THREE.SphereGeometry(.35, 16, 12), new THREE.MeshStandardMaterial({ color: 0x9aa6b2, emissive: 0x000000 }));
      luz.position.set(0, e.alto + 1.4, 0); g.add(luz);
      etiqueta(e.nombre.replace('Cizalladora Punzonadora', 'Cizalla-punzonadora').replace('Sierra Cinta', 'Sierra cinta'), pos(e.x, e.z, e.alto + 3.2), 'maq');
    } else if (e.tipo === 'mesa') {
      const top = caja(e.ancho, .35, e.largo, 0x8fa3b8); top.position.y = 1.0; g.add(top);
      for (const dx of [-e.ancho / 2 + .4, e.ancho / 2 - .4]) for (const dz of [-e.largo / 2 + .3, e.largo / 2 - .3]) {
        const p = caja(.25, 1.0, .25, 0x5b738b); p.position.set(dx, .5, dz); g.add(p);
      }
    } else if (e.tipo === 'puesto') {
      const f = caja(e.ancho, .15, e.largo, 0xdfe6ee); f.position.y = .08; g.add(f);
      for (const [x, z, w, d] of [[0, -e.largo / 2, e.ancho, .12], [-e.ancho / 2, 0, .12, e.largo], [e.ancho / 2, 0, .12, e.largo]]) {
        const p = caja(w, 2.1, d, 0xffb347, { transparent: true, opacity: .6 }); p.position.set(x, 1.1, z); g.add(p);
      }
      const banco = caja(1.4, .8, 1.0, 0x8fa3b8); banco.position.set(0, .5, 0); g.add(banco);
      luz = new THREE.Mesh(new THREE.SphereGeometry(.22, 12, 10), new THREE.MeshStandardMaterial({ color: 0x9aa6b2, emissive: 0x000000 }));
      luz.position.set(0, 1.5, 0); g.add(luz);
    } else if (e.tipo === 'muelle') {
      const pl = caja(e.ancho, .5, e.largo, 0xcfd8e1); pl.position.y = .25; g.add(pl);
      const linea = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(e.ancho, .52, e.largo)), new THREE.LineBasicMaterial({ color: 0xe0b020 }));
      linea.position.y = .26; g.add(linea);
      const camion = new THREE.Group();
      const cab = caja(2.2, 2.2, 2.4, 0x0a6ed1); cab.position.set(-4.6, 1.5, 0);
      const remol = caja(7, 2.6, 2.6, 0xf5f7fa); remol.position.set(0, 1.7, 0);
      for (const dx of [-4.6, -1.5, 1.8]) for (const dz of [-1.3, 1.3]) { const r = new THREE.Mesh(new THREE.CylinderGeometry(.55, .55, .4, 14), mat(0x223548)); r.rotation.x = Math.PI / 2; r.position.set(dx, .6, dz); camion.add(r); }
      camion.add(cab, remol); camion.rotation.y = Math.PI / 2; camion.position.set(0, .5, 0); camion.visible = false; g.add(camion);
      luz = camion;
      etiqueta(e.nombre.replace(' (servicio externo)', '').replace(' (externo)', ''), pos(e.x, e.z, 4.2), 'zona');
    } else if (e.tipo === 'oficina') {
      const b = caja(e.ancho, 3.4, e.largo, 0xf7f9fb); b.position.y = 1.7; g.add(b);
      const t = caja(e.ancho + .6, .5, e.largo + .6, 0x0a6ed1); t.position.y = 3.65; g.add(t);
      const vent = caja(e.ancho * .7, 1.1, .1, 0x9ec7f0); vent.position.set(0, 2, e.largo / 2 + .06); g.add(vent);
      etiqueta(e.nombre, pos(e.x, e.z, 5.2), 'zona');
    }
    g.position.copy(v);
    marcar(g, ref);
    estatico.add(g);
    porId[e.id] = { grupo: g, el: e, pos: v.clone(), luz };
  }

  /* ---------- dinámico: personal, lotes y material ---------- */
  const matLuz = { verde: 0x2ecc71, ambar: 0xffb020, rojo: 0xe74c3c, gris: 0x9aa6b2 };
  const avatar = (color, ref) => {
    const g = new THREE.Group();
    const cuerpo = new THREE.Mesh(new THREE.CylinderGeometry(.28, .34, 1.15, 10), mat(color)); cuerpo.position.y = .75; cuerpo.castShadow = true; g.add(cuerpo);
    const cab = new THREE.Mesh(new THREE.SphereGeometry(.27, 12, 10), mat(0xf1c9a5)); cab.position.y = 1.58; cab.castShadow = true; g.add(cab);
    const casco = new THREE.Mesh(new THREE.SphereGeometry(.3, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), mat(0xffd23f)); casco.position.y = 1.64; g.add(casco);
    marcar(g, ref);
    return g;
  };
  const anillo = (cantidad, rx, rz, i) => { const a = (i / Math.max(cantidad, 1)) * Math.PI * 2 + .6; return [Math.cos(a) * rx, Math.sin(a) * rz]; };

  function limpiarDinamico() {
    for (const o of [...dinamico.children]) {
      dinamico.remove(o);
      o.traverse(m => { if (m.geometry && !m.geometry.userData.compartida) m.geometry.dispose(); });
    }
    animDin.length = 0;
  }

  function actualizar(estado, ctx = {}) {
    limpiarDinamico();
    const porEst = Object.fromEntries(estado.estaciones.map(s => [s.id, s]));
    // luces de estado y camiones
    for (const [id, d] of Object.entries(porId)) {
      const s = porEst[id];
      if (d.el.tipo === 'maquina' || d.el.tipo === 'puesto') {
        const col = s ? (d.el.tipo === 'maquina' && s.proyectos.length > 1 ? matLuz.ambar : matLuz.verde) : matLuz.gris;
        d.luz.material.color.setHex(col); d.luz.material.emissive.setHex(s ? col : 0x000000); d.luz.material.emissiveIntensity = .7;
      }
      if (d.el.tipo === 'muelle') d.luz.visible = !!s;
    }
    // personal
    let total = 0;
    for (const s of estado.estaciones) {
      const d = porId[s.id]; if (!d || !s.gente.length) continue;
      const e = d.el, n = s.gente.length;
      s.gente.forEach((p, i) => {
        if (total++ > 120) return;
        const [ox, oz] = anillo(n, Math.max(e.ancho / 2 + .9, 1.6), Math.max(e.largo / 2 + .9, 1.6), i);
        const av = avatar(COLOR_GRUPO[hash(p.grupo) % COLOR_GRUPO.length], { tipo: 'persona', persona: p, estacion: s.id, etiqueta: p.nombre });
        av.position.set(d.pos.x + ox, e.tipo === 'mesa' || e.tipo === 'muelle' ? 0 : 0, d.pos.z + oz);
        av.lookAt(d.pos.x, 0, d.pos.z);
        const fase = i * 1.7 + s.id;
        animDin.push(t => { av.position.y = Math.abs(Math.sin(t * .004 + fase)) * .12; });
        dinamico.add(av);
      });
    }
    // lotes
    const sel = ctx.pidSel;
    const grupos = {};
    for (const l of estado.lotes) { if (l.ubicacion && l.estado !== 'DESPACHADO') (grupos[l.ubicacion] = grupos[l.ubicacion] || []).push(l); }
    for (const [uid, ls] of Object.entries(grupos)) {
      const d = porId[uid]; if (!d) continue;
      const e = d.el;
      ls.sort((a, b) => a.pid - b.pid || a.lote - b.lote);
      ls.forEach((l, i) => {
        const w = Math.min(3.2, 1.0 + Math.sqrt(l.kg) / 38), h = .55 + Math.min(.6, l.kg / 12000);
        const color = COLOR_ETAPA[l.estado === 'ACOPIO' ? 'ACOPIO' : l.etapa] || 0xb0bac5;
        const m = caja(w, h, w * .55, color, l.estado === 'EN_COLA' ? { transparent: true, opacity: .62 } : {});
        const cols = Math.max(1, Math.floor((e.ancho + 2) / (w + .3)));
        const fila = Math.floor(i / cols), col = i % cols;
        let x, y, z;
        if (e.tipo === 'maquina') { x = -e.ancho / 2 + 1 + col * (w + .3); z = e.largo / 2 + 1.6 + fila * 1.4; y = h / 2; }
        else if (e.tipo === 'mesa') { x = -e.ancho / 2 + 1.5 + col * (w + .3); z = ((i % 2) - .5) * 1.2; y = 1.18 + h / 2 + Math.floor(i / 6) * h; }
        else if (e.tipo === 'puesto') { x = (col - .5) * 1.2; z = e.largo / 2 + 1.2 + fila * 1.2; y = h / 2; }
        else { x = -e.ancho / 2 + 1.5 + col * (w + .5); z = -e.largo / 2 + 1.5 + fila * 1.6; y = h / 2 + .12; }
        m.position.set(d.pos.x + x, y, d.pos.z + z);
        if (sel && l.pid === sel) { const ed = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry), new THREE.LineBasicMaterial({ color: 0x0a6ed1 })); m.add(ed); }
        marcar(m, { tipo: 'lote', lote: l, etiqueta: `OT ${l.cod} · ${l.descripcion}` });
        dinamico.add(m);
      });
    }
    // material en stock (racks, patio)
    const slots = {};
    for (const mt of estado.material) {
      const d = porId[mt.ubicacion]; if (!d) continue;
      const e = d.el, k = (slots[mt.ubicacion] = (slots[mt.ubicacion] || 0) + 1) - 1;
      const w = Math.min(2.4, .7 + Math.sqrt(mt.kg) / 55);
      const m = caja(e.tipo === 'rack' ? Math.min(w, e.ancho) : w, .5, e.tipo === 'rack' ? e.largo * .8 : w * 1.6, COLOR_MATERIAL[mt.tipo] || 0x8a97a6);
      if (e.tipo === 'rack') { m.position.set(d.pos.x, .75 + (k % 3) * 1.2, d.pos.z - e.largo / 2 + .8 + Math.floor(k / 3) * 1.6); }
      else { const cols = 12; m.position.set(d.pos.x - e.ancho / 2 + 2 + (k % cols) * 3.4, .12 + .25, d.pos.z - e.largo / 2 + 2 + Math.floor(k / cols) * 3.2); }
      marcar(m, { tipo: 'material', material: mt, etiqueta: `${mt.perfil} · OT ${mt.cod}` });
      dinamico.add(m);
    }
  }

  /* ---------- selección y picking ---------- */
  const rayo = new THREE.Raycaster(), p2 = new THREE.Vector2();
  let sel = null, caja_sel = null;
  const ref_de = o => { while (o) { if (o.userData && o.userData.ref) return o.userData.ref; o = o.parent; } return null; };
  function buscar(ev) {
    const r = renderer.domElement.getBoundingClientRect();
    p2.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    rayo.setFromCamera(p2, camara);
    const hit = rayo.intersectObjects([...dinamico.children, ...estatico.children], true).find(h => ref_de(h.object) && h.object.visible && !(techos.includes(h.object)));
    return hit ? { ref: ref_de(hit.object), obj: hit.object } : null;
  }
  function seleccionar(ref, obj) {
    sel = ref;
    if (caja_sel) { escena.remove(caja_sel); caja_sel = null; }
    if (!ref) return;
    let objetivo = obj;
    if (ref.tipo === 'elemento' && porId[ref.id]) objetivo = porId[ref.id].grupo;
    else { while (objetivo && !(objetivo.userData && objetivo.userData.ref === ref && (!objetivo.parent || objetivo.parent.userData.ref !== ref))) objetivo = objetivo.parent; }
    if (objetivo) { caja_sel = new THREE.Box3Helper(new THREE.Box3().setFromObject(objetivo), 0x1b90ff); caja_sel.material.linewidth = 2; escena.add(caja_sel); }
  }
  let abajo = null;
  renderer.domElement.addEventListener('pointerdown', e => { abajo = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener('pointerup', e => {
    if (!abajo || Math.hypot(e.clientX - abajo[0], e.clientY - abajo[1]) > 5) return;
    const h = buscar(e);
    seleccionar(h && h.ref, h && h.obj);
    if (opts.alSeleccionar) opts.alSeleccionar(h ? h.ref : null);
  });
  let ultimoHover = 0;
  renderer.domElement.addEventListener('pointermove', e => {
    const t = performance.now(); if (t - ultimoHover < 60) return; ultimoHover = t;
    const h = buscar(e), r = contenedor.getBoundingClientRect();
    if (h && (h.ref.etiqueta || h.ref.nombre)) { tip.textContent = h.ref.etiqueta || h.ref.nombre; tip.style.left = (e.clientX - r.left + 14) + 'px'; tip.style.top = (e.clientY - r.top + 12) + 'px'; tip.classList.remove('oculto'); renderer.domElement.style.cursor = 'pointer'; }
    else { tip.classList.add('oculto'); renderer.domElement.style.cursor = 'grab'; }
  });
  renderer.domElement.addEventListener('pointerleave', () => tip.classList.add('oculto'));

  /* ---------- cámara, tamaño y bucle ---------- */
  function encuadrar() {
    const k = Math.max(1, 1.5 / camara.aspect);          // en pantallas angostas se aleja para que entre toda la planta
    camara.position.set(78 * k, 64 * k, 86 * k); controles.target.set(0, 0, 0); controles.update();
  }
  function enfocar(ref) {
    if (ref && ref.tipo === 'elemento' && porId[ref.id]) { const p = porId[ref.id].pos; controles.target.set(p.x, 0, p.z); }
  }
  function tamano() {
    const w = contenedor.clientWidth, h = contenedor.clientHeight;
    renderer.setSize(w, h, false); camara.aspect = w / Math.max(h, 1); camara.updateProjectionMatrix();
  }
  const ro = new ResizeObserver(tamano); ro.observe(contenedor);
  tamano(); encuadrar();

  let vivo = true;
  const v3 = new THREE.Vector3();
  function bucle(t) {
    if (!vivo) return;
    requestAnimationFrame(bucle);
    controles.update();
    animEst.forEach(f => f(t)); animDin.forEach(f => f(t));
    if (caja_sel) caja_sel.visible = true;
    const w = contenedor.clientWidth, h = contenedor.clientHeight;
    for (const et of etiquetas) {
      v3.copy(et.v).project(camara);
      const visible = v3.z < 1 && Math.abs(v3.x) < 1.1 && Math.abs(v3.y) < 1.1;
      et.el.style.display = visible ? '' : 'none';
      if (visible) et.el.style.transform = `translate(-50%,-100%) translate(${(v3.x * .5 + .5) * w}px, ${(-v3.y * .5 + .5) * h}px)`;
    }
    renderer.render(escena, camara);
  }
  requestAnimationFrame(bucle);

  return {
    actualizar, seleccionar: (ref) => seleccionar(ref, null), enfocar, encuadrar,
    techos: v => techos.forEach(t => { t.visible = v; }),
    etiquetas: v => { capaEt.style.display = v ? '' : 'none'; },
    elemento: id => porId[id] && porId[id].el,
    destruir() {
      vivo = false; ro.disconnect(); controles.dispose();
      escena.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) [].concat(o.material).forEach(m => m.dispose()); });
      renderer.dispose(); renderer.domElement.remove(); capaEt.remove(); tip.remove();
    },
  };
}
