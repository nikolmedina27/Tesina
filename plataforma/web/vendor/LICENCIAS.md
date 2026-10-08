# Librerías de terceros (copias locales)

Se sirven desde aquí para que SteelPlan funcione en la red de planta sin internet.

| Archivo | Librería | Versión | Licencia | Origen |
|---|---|---|---|---|
| `frappe-gantt.min.js`, `frappe-gantt.css` | Frappe Gantt | 0.6.1 | MIT | https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/ |
| `echarts.min.js` | Apache ECharts | 5.5.0 | Apache-2.0 | https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/ |
| `three/three.module.js`, `three/three.core.js`, `three/OrbitControls.js`, `three/RoomEnvironment.js` | three.js | 0.186.1 | MIT | paquete npm `three@0.186.1` (`build/` y `examples/jsm/controls/`; en `OrbitControls.js` y `RoomEnvironment.js` solo se cambió la ruta del import a `./three.module.js`; `RoomEnvironment` viene de `examples/jsm/environments/`) |

Para actualizar: descargar la nueva versión de esos mismos orígenes, reemplazar los archivos y subir `VERSION` en `../sw.js`.
