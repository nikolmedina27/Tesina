"""Definición única del formato de registro (hojas, columnas y listas).

La usan scripts/generar_formato_unico.py (para crear el Excel) y plataforma/importador.py (para leerlo),
así ambos nunca se desalinean. Tipos de columna: nombre de una lista de LISTAS, 'int', 'num', 'pct',
'horas', 'fecha', 'fechahora', 'formula_*' (calculada en Excel, se ignora al importar) o None (texto).
"""

LISTAS = {
    'PROCESOS': ['01 Ingeniería', '02 Compra de material', '03 Habilitado - sierra cinta', '04 Habilitado - cizalla-punzonadora',
                 '05 Habilitado - mesa CNC', '06 Roscado de barra lisa', '07 Doblez (servicio externo)', '08 Armado', '09 Soldeo',
                 '10 Limpieza', '11 Despacho a pintura', '12 Granallado y pintura (externo)', '13 Despacho a obra'],
    'TIPO_ESTRUCTURA': ['Nave industrial / packing / cobertura', 'Planta industrial / minería', 'Edificación / infraestructura',
                        'Mezzanine / plataformas / oficinas', 'Equipo especial / otro'],
    'TIPO_ELEMENTO': ['COLUMNA', 'VIGA', 'TIJERAL', 'CERCHA', 'CORREA', 'ARRIOSTRE', 'TEMPLADOR', 'TORNAPUNTA', 'TRAVESAÑO',
                      'PERFIL SOLDADO', 'PLACA DE CONEXIÓN', 'PLACA BASE', 'INSERTO', 'CONECTOR', 'SOPORTE', 'DINTEL', 'COLUMNETA',
                      'PLATINA', 'ESCALERA', 'BARANDA', 'TAPA / CUBIERTA', 'TUBERÍA ROLADA', 'OTRO'],
    'CLASE_PESO': ['Liviana (0-250 kg)', 'Mediana (251-1000 kg)', 'Pesada (>1000 kg)'],
    'MAQUINAS': ['Sierra Cinta Kaltenbach', 'Cizalladora Punzonadora Pedimax', 'Mesa CNC', 'Roscadora RIDGID'],
    'CAUSA_PARADA': ['Falla mecánica', 'Falla eléctrica', 'Falta de repuesto', 'Lubricación', 'Cambio de herramienta / setup',
                     'Falta de operador', 'Falta de material', 'Mantenimiento preventivo', 'Otro'],
    'SI_NO': ['Sí', 'No'],
    'FUENTE_TON': ['Estimada (cotización)', 'Planos de fabricación', 'Despacho real (guías)'],
    'SERVICIO': ['Doblez', 'Granallado y pintura', 'Rolado', 'Corte plasma', 'Galvanizado', 'Otro'],
    'EVENTO': ['Cambio de alcance', 'Revisión de planos', 'Retraso de información del cliente (RFI)', 'Suspensión por el cliente',
               'Falta de material', 'Retrabajo / no conformidad', 'Clima', 'Otro'],
    'IMPUTABLE': ['Cliente', 'Steelser', 'Proveedor', 'Contratista', 'Fuerza mayor'],
    'RESULTADO_COT': ['Ganada', 'Perdida', 'Retirada', 'Pendiente'],
    'CONTRATISTAS': ['T&C FABRICACION', 'FRANCISCO TARRILLO', 'RFR METALICAS', 'ROGGER TORRES', 'LHL INGENIERIA', 'Personal propio', 'Otro'],
    'MONEDA': ['USD', 'PEN'],
}

HOJAS = [
    ('PROYECTO', 'Cotizaciones · al adjudicar y al cerrar', 'Una fila por proyecto (OT).', [
        ('Código OT', 14, None), ('Cliente', 26, None), ('Nombre del proyecto', 38, None), ('Tipo de estructura', 30, 'TIPO_ESTRUCTURA'),
        ('Toneladas metrado', 12, 'num'), ('Fuente de tonelaje', 22, 'FUENTE_TON'), ('N° piezas', 10, 'int'), ('% planchas', 10, 'pct'),
        ('m² de pintura', 12, 'num'), ('Metros de soldadura', 12, 'num'), ('Incluye montaje', 10, 'SI_NO'), ('Presupuesto sin IGV', 14, 'num'),
        ('Moneda', 8, 'MONEDA'), ('Fecha pedida por el cliente', 14, 'fecha'), ('Fecha cotizada', 14, 'fecha'), ('Día 1 contractual', 14, 'fecha'),
        ('Fecha fin contractual', 14, 'fecha'), ('Ampliación de plazo (días)', 12, 'num'), ('Fecha fin real (acta)', 14, 'fecha'),
        ('Penalidad aplicada', 12, 'num'), ('Resultado cotización', 12, 'RESULTADO_COT'), ('Plazo del competidor (días)', 12, 'num'),
        ('Motivo si se perdió', 26, None)],
     ['OT-2026-015', 'Cliente ejemplo', 'Nave de almacén 2 aguas', 'Nave industrial / packing / cobertura', 47, 'Planos de fabricación', 420, 0.17,
      660, 850, 'No', 150000, 'USD', '2026-12-20', '2026-12-28', '2026-10-15', '2026-12-28', 0, None, None, 'Ganada', 50, None]),
    ('COTIZ_PROCESO', 'Cotizador · al cotizar (antes de ejecutar)', 'Lo que estimó el cotizador por proceso: es la línea base justa del modelo.', [
        ('Código OT', 14, None), ('Proceso', 34, 'PROCESOS'), ('HH estimadas', 12, 'num'), ('Días estimados', 12, 'num'),
        ('Cuadrilla supuesta', 12, 'int'), ('Contratista previsto', 22, 'CONTRATISTAS'), ('Estimado por', 18, None), ('Fecha de estimación', 14, 'fecha')],
     ['OT-2026-015', '08 Armado', 340, 9, 5, 'T&C FABRICACION', 'Cotizador', '2026-10-02']),
    ('PIEZAS', 'Oficina técnica + taller · por O.F.', 'Igual al control por pieza OPE-PRO-FR: una fila por elemento con sus fechas de avance.', [
        ('Código OT', 14, None), ('N° item', 8, 'int'), ('Tipo de elemento', 18, 'TIPO_ELEMENTO'), ('Conjunto / marca', 18, None), ('Perfil', 16, None),
        ('Longitud (mm)', 11, 'num'), ('Cantidad', 9, 'int'), ('Peso unit. neto (kg)', 12, 'num'), ('Peso total (kg)', 12, 'formula_peso'),
        ('Clase de peso', 18, 'formula_clase'), ('Área total (m²)', 11, 'num'), ('Contratista', 20, 'CONTRATISTAS'), ('O.F.', 7, None),
        ('P.U. (S/ por kg)', 10, 'num'), ('F. habilitado', 12, 'fecha'), ('F. armado', 12, 'fecha'), ('F. soldeo', 12, 'fecha'),
        ('F. liberación calidad', 12, 'fecha'), ('F. granallado', 12, 'fecha'), ('F. pintura', 12, 'fecha'), ('F. despacho', 12, 'fecha')],
     ['OT-2026-015', 1, 'TIJERAL', 'T-1', 'L3x3x1/4', 9850, 2, 412.5, None, None, 9.6, 'T&C FABRICACION', 5, 0.6,
      '2026-10-20', '2026-10-23', '2026-10-26', '2026-10-27', None, None, None]),
    ('TAREO', 'Jefe de taller / supervisor · cada día', 'Fuente de las HH reales. Una fila por día × proceso × cuadrilla.', [
        ('Fecha', 12, 'fecha'), ('Código OT', 14, None), ('Proceso', 34, 'PROCESOS'), ('Contratista / cuadrilla', 22, 'CONTRATISTAS'),
        ('N° personas', 10, 'int'), ('Horas por persona', 10, 'horas'), ('HH del día', 10, 'formula_hh'), ('Kg avanzados', 11, 'num'),
        ('Observación (falta de material, retrabajo, etc.)', 40, None)],
     ['2026-10-23', 'OT-2026-015', '08 Armado', 'T&C FABRICACION', 6, 8, None, 1850, 'Faltó perfil W8 en la mañana']),
    ('PROCESO_FECHAS', 'Jefe de taller · al iniciar y cerrar cada proceso', 'Mide los solapes reales entre procesos (los necesita el Gantt y el CRP).', [
        ('Código OT', 14, None), ('Proceso', 34, 'PROCESOS'), ('Fecha inicio real', 14, 'fecha'), ('Fecha fin real', 14, 'fecha'),
        ('Cuadrilla promedio', 12, 'num'), ('Observación', 36, None)],
     ['OT-2026-015', '08 Armado', '2026-10-21', '2026-11-04', 6, None]),
    ('PARADAS', 'Jefe de taller / operador · cuando ocurre', 'Base de la disponibilidad real (Dₖ) de las 4 máquinas.', [
        ('Máquina', 30, 'MAQUINAS'), ('Fecha y hora inicio', 18, 'fechahora'), ('Fecha y hora fin', 18, 'fechahora'), ('Horas', 8, 'formula_horas'),
        ('¿Planificada?', 11, 'SI_NO'), ('Causa', 28, 'CAUSA_PARADA'), ('Código OT afectada', 14, None), ('Observación', 36, None)],
     ['Mesa CNC', '2026-10-21 08:00', '2026-10-21 14:00', None, 'No', 'Falla eléctrica', 'OT-2026-015', 'Se cambió contactor']),
    ('SERV_EXTERNOS', 'Logística · envío y retorno', 'Plazos reales de proveedores externos.', [
        ('Código OT', 14, None), ('Servicio', 20, 'SERVICIO'), ('Proveedor', 24, None), ('Fecha envío', 12, 'fecha'), ('Fecha retorno', 12, 'fecha'),
        ('Días', 8, 'formula_dias'), ('Kg', 10, 'num'), ('m²', 10, 'num'), ('Observación', 30, None)],
     ['OT-2026-015', 'Granallado y pintura', 'Proveedor ejemplo', '2026-11-05', '2026-11-12', None, 9800, 210, None]),
    ('COMPRAS', 'Compras · por orden de compra', 'El proceso 2 (compra de material) es de los de mayor variación de plazo.', [
        ('Código OT', 14, None), ('N° OC', 12, None), ('Proveedor', 24, None), ('Perfil / material', 22, None), ('Kg', 10, 'num'),
        ('Fecha pedido', 12, 'fecha'), ('Fecha prometida', 12, 'fecha'), ('Fecha recepción', 12, 'fecha'), ('Días de atraso', 10, 'formula_atraso'),
        ('N° certificado / colada', 18, None)],
     ['OT-2026-015', 'OC-0451', 'Proveedor acero', 'W8x31 ASTM A572', 5200, '2026-10-16', '2026-10-21', '2026-10-23', None, 'Colada 23GG039']),
    ('EVENTOS', 'Jefe de proyecto · cuando ocurre', 'Separa el atraso imputable al cliente del atraso de planta (define el cumplimiento real).', [
        ('Código OT', 14, None), ('Fecha', 12, 'fecha'), ('Tipo de evento', 32, 'EVENTO'), ('Imputable a', 14, 'IMPUTABLE'),
        ('Días de impacto', 10, 'num'), ('¿Se pidió ampliación?', 12, 'SI_NO'), ('Descripción', 44, None)],
     ['OT-2026-015', '2026-10-28', 'Retraso de información del cliente (RFI)', 'Cliente', 2, 'Sí', 'Cliente demoró 4 días en confirmar espesor de placas base']),
]
