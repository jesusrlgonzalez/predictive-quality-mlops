# Recolectar más datos; no desplegar hoy

**Caso evaluado:** histórico, datos públicos UCI SECOM (1,567 lotes de una línea de semiconductores, 19 jul – 17 oct 2008). No es una planta en operación ni un cliente.
**Fecha del análisis:** resultados de `reports/metrics.json` (holdout cronológico evaluado una sola vez); reproducidos desde cero en una copia aislada el 20 nov 2026 con cifras idénticas.
**Autor:** Jesús R. L. González · **Costos:** supuestos ilustrativos en MXN (`src/pqm/config.py`), no costos de una empresa.

## Dictamen

| Nivel | Resultado | Quién lo emite |
|---|---|---|
| Clasificación algorítmica | **RECOLECTAR MÁS DATOS** | La regla del proyecto (`pqm.viability.verdict`, la misma que usa la demo), aplicada a las métricas publicadas |
| Recomendación operativa | **No desplegar hoy** | Decisión de gobierno que se sigue de esa clasificación; la toma una persona, no el algoritmo |

**Por qué la regla clasifica así.** El ahorro estimado es positivo, pero su intervalo incluye pérdidas y ganancias, así que **no se ha demostrado un beneficio económico positivo**. Para demostrarlo harían falta ≈ 278 fallas en el periodo evaluado, unos 9 meses más al ritmo observado (536 lotes por mes), dentro del plazo máximo de 24 meses que fija la regla.

**Por qué la recomendación es no desplegar hoy.** Desplegar antes de reunir esa evidencia expondría la línea a un costo que puede ser mayor que el de la referencia. Mientras tanto, la mejor alternativa simple sigue siendo la referencia y se siguen recolectando datos.

Esto no significa que el modelo «cause pérdidas» ni que el beneficio sea cero. Tampoco es una regla para toda fábrica: con otros costos, otra señal u otro proceso, el dictamen puede ser distinto.

## Evidencia (holdout cronológico: último 20 %, 313 lotes, 17 fallas)

| Pregunta | Resultado | Lectura |
|---|---|---|
| ¿Ordena mejor que el azar? | PR-AUC 0.089 (IC 95 % 0.043 – 0.197) frente a una prevalencia de 0.054; ROC-AUC 0.62; lift en el top 10 % = 2.4 | Señal débil. El intervalo de PR-AUC **incluye la prevalencia**: la señal no está demostrada |
| ¿Cuántas fallas encuentra? | Marca 61 lotes: 5 de 17 fallas detectadas, 56 falsas alarmas | Baja sensibilidad con el umbral por costo |
| ¿Ahorra frente a la mejor alternativa simple? | Costo 77,750 frente a 85,000 sin modelo (inspeccionar todo: 86,750). Ahorro 7,250 (8.5 %), **IC 95 % −22,031 a +19,769**; P(ahorro > 0) = 0.55 | El intervalo cruza el cero |
| ¿Depende de los costos? | Ahorro según la razón costo de scrap ÷ costo de inspección: −1,500 (×5), −1,750 (×10), +7,250 (×20, supuesto base), +2,750 (×40), −7,250 (×80) | Solo es positivo en una banda intermedia de costos |
| ¿Hay fuga de información? | Partición aleatoria: PR-AUC 0.154; temporal: 0.089. Las pruebas adversas (`tests/test_data_leakage.py`) detectan entrenamiento con el holdout, umbral elegido con el holdout, validación con lotes futuros y limpieza reajustada | La cifra publicada es la temporal (honesta) |
| ¿Es estable el proceso? | 142 de 273 sensores usados con PSI > 0.25 entre entrenamiento y holdout | Deriva fuerte: un modelo entrenado hoy envejece rápido |

## Alternativas comparadas

1. **Sin modelo** (dejar pasar y pagar el scrap): 85,000 en el holdout. Es la mejor alternativa simple con los costos base.
2. **Inspeccionar todo:** 86,750.
3. **Modelo con umbral por costo:** 77,750, con un intervalo de ahorro que incluye pérdidas.

## Costo de equivocarse

- **Desplegar y que no ahorre:** con el límite inferior del intervalo, hasta ≈ 22,000 MXN más que la alternativa simple en 313 lotes, sin contar el costo de implementación ni de vigilancia.
- **No desplegar y que sí ahorrara:** se dejarían de ganar hasta ≈ 19,800 MXN en 313 lotes (límite superior), recuperables si la evidencia adicional lo demuestra.

## Condiciones para reevaluar (responsable: comité de calidad de la planta que lo adopte)

| Condición | Umbral |
|---|---|
| Fallas acumuladas en el periodo de evaluación | ≥ 278 (o las que calcule `make dictamen` con datos nuevos) |
| Señal | Límite inferior del IC de PR-AUC por encima de la prevalencia |
| Ahorro | Límite inferior del IC del ahorro > 0 frente a la mejor alternativa simple |
| Costos | Sustituir los supuestos por costos reales de la planta y repetir la sensibilidad |

## Criterios de suspensión si algún día se despliega

- PSI > 0.25 en los sensores críticos o un cambio significativo en la tasa de falla (prueba exacta de Fisher, como en el dictamen).
- El ahorro observado en una ventana móvil cae por debajo de la mejor alternativa simple.
- Cambio de proceso, receta o proveedor que invalide el histórico.

## Datos que faltan

- Más lotes con falla confirmada.
- Costos reales de scrap, inspección y retrabajo.
- Nombres reales de los sensores: los de SECOM están anonimizados y los alias del proyecto son ilustrativos.
- Una ventana de operación posterior para medir la deriva.

**Reproducir:** `make train` (en una copia, porque reescribe `models/` y `reports/`) · `make test` · `make dictamen LOTES=lotes.csv` para un proceso propio.
