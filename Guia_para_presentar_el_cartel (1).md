# Guía para presentar el cartel, recuadro por recuadro

Para cada parte del cartel: **qué dice**, **qué significa en palabras simples**, **de dónde sale** (notebook y sección) y **qué te pueden preguntar**.

> **Dónde está cada cosa.** El cartel que mandaste a imprimir se armó con la versión anterior del proyecto. Esos archivos están en `_archivo/` (`03_modelo_celda_dia`, `A1_riesgo_esperado_EB`, `A3_lluvia`). Para cada dato también va dónde está en la versión final (`00_datos`, `01_tablas`, `02_modelos`, `03_eda_y_cartel`). La diferencia principal: la versión final ya no incluye Empirical Bayes ni intervalos de confianza. El cartel sí los trae, así que abajo se explican.

---

## 0. Antes de empezar: 3 detalles del cartel impreso que conviene saber

1. **93% vs 96%.** El recuadro del Resumen dice **93%**. La gráfica "¿Qué pesa más?" y la primera conclusión dicen **96%**.
   - El 96% salió de una corrida de prueba con clima simulado.
   - El 93% es de tu corrida con datos reales.
   - Si alguien lo nota: *"Depende de la corrida; en todas sale arriba de 90%. Lo importante es que el lugar explica casi todo."*
2. **"Cuatro modelos" vs cinco.** El Resumen dice "cuatro modelos, del conteo histórico y Empirical Bayes a XGBoost". Las gráficas muestran **cinco**: Historial, Empirical Bayes, Poisson, Random Forest y XGBoost. Si preguntan: *"Son cinco; Empirical Bayes es el estándar de la literatura de seguridad vial."*
3. **Trabajo a futuro.** "Adición de próximos años" y "pronóstico 2025 cuando el INEGI lo publique" dicen casi lo mismo. Al exponerlo, menciónalos como una sola idea.

---

## 1. Título y autores
**"Riesgo vial en avenidas principales de la ZMG: dónde y cuándo, con aprendizaje automático. Caso Av. López Mateos"**
- **Dónde:** qué celdas de las avenidas concentran el riesgo.
- **Cuándo:** qué días (día de la semana, festivos, lluvia).
- **Caso López Mateos:** el modelo se entrena con toda la zona metropolitana y se **aplica** a López Mateos como ejemplo.

---

## 2. Resumen (el párrafo)

> "Se construyó una tabla celda por día…"

**Qué significa:** se armó **una sola tabla** donde cada fila es *una celda en un día*. Son 4,143 celdas × 1,096 días ≈ **4.5 millones de filas**, y cada fila dice cuántos accidentes hubo y todo lo que sabemos de esa celda ese día.
**De dónde:** `02_modelos`, sección 1 (antes, `tabla_maestra.py`).

> "…4,143 celdas geohash de ~150 m sobre las avenidas principales de Guadalajara, Zapopan y Tlaquepaque…"

- **Celda geohash:** un cuadrito de ~143 × 152 m con un código, por ejemplo `9ewmqyw`. Se explica en la sección 7.
- **¿Por qué 4,143?** Sobre avenidas principales hay 5,775 celdas en toda la ZMG, pero solo **4,143 están en los 3 municipios de buen registro**.
- **Buen registro:** Tonalá, Tlajomulco y El Salto registran muchos menos accidentes por habitante. Lo más probable es que **no se reporten**, no que sean más seguros. Si se entrenara con ellos, el modelo aprendería que esas calles "son seguras". Por eso se excluyen.
- **De dónde:** `01_tablas`, paso 5 (antes, `02_panel_zmg.py`). La gráfica de accidentes por habitante está en `03_eda_y_cartel`, pregunta 2.

> "…cada día de 2022–2024, los accidentes del INEGI…"

- **INEGI, base ATUS:** accidentes de tránsito registrados, con fecha, hora, coordenadas y gravedad.
- Son **24,872 accidentes** en la ZMG en 2022–2024. De esos, **16,607 (67%)** ocurrieron sobre avenidas principales.
- **De dónde:** `00_datos` (lectura) y `01_tablas`, paso 4 (asignación a celdas).

> "…19 variables de infraestructura de OpenStreetMap…"

- **OpenStreetMap:** el mapa abierto del mundo (como Wikipedia, pero de mapas). De ahí salen carriles, intersecciones, semáforos, puentes, paradas y comercios.
- **19 variables:** se calcularon 21, pero 2 eran casi copias de otras y se quitaron (ver Metodología).
- **De dónde:** `01_tablas`, paso 3.

> "…el calendario, la lluvia y el historial de cada celda."

- **Calendario:** día de la semana, mes, festivo, Semana Santa, quincena.
- **Lluvia:** de **Open-Meteo**, un servicio gratuito de clima histórico (reanálisis ERA5). Da la lluvia por hora en el centro de Guadalajara.
- **Historial:** cuántos accidentes tuvo esa celda en los **365 y 90 días anteriores**. Ver sección 9.

> "Se compararon cuatro modelos… entrenando con 2022–2023 y probando con 2024."

- **Entrenar:** el modelo aprende con abril 2022 – diciembre 2023. Enero a marzo de 2022 solo sirven para calcular el historial de los primeros días.
- **Probar:** se le pide predecir **2024, que nunca vio**, y se compara con lo que pasó. Así se sabe si de verdad anticipa, y no solo memoriza.

> "XGBoost ubica mejor las zonas de riesgo que el conteo histórico y el riesgo depende sobre todo del lugar; la lluvia fuerte se asocia con +31% de accidentes por hora."

Son los 3 hallazgos. Se explican en los recuadros de números y en Resultados.

---

## 3. Los 3 recuadros de números

### "58% de los accidentes de 2024 en el 10% de las celdas"
- **Qué es:** XGBoost marcó, con datos de 2022–2023, el 10% de las celdas más riesgosas (**414 celdas**). En esas celdas cayó el **58%** de los accidentes de 2024.
- **Cómo decirlo:** *"Si tránsito vigilara solo 414 celdas, las que dice el modelo, cubriría casi 6 de cada 10 accidentes del año siguiente."*
- **Ojo:** no confundir con el **64%** de la Introducción. Ese es descriptivo (viendo hacia atrás) y este es una **predicción**.
- **De dónde:** `02_modelos`, secciones 4–6 (antes, `03_modelo_celda_dia`, sección 5).

### "93% del riesgo lo explica el lugar (infraestructura + historial)"
- **Qué es:** con **SHAP** se mide cuánto aporta cada variable a cada predicción del modelo. Sumando por grupos, las variables de *lugar* (infraestructura e historial) explican ~93%. Las de *momento* (calendario y clima diario) explican ~7%.
- **Cómo decirlo:** *"El riesgo depende mucho más de dónde estás que de qué día es."*
- **De dónde:** `02_modelos`, sección 7.

### "+31% accidentes en horas con lluvia fuerte (preliminar)"
- **Qué es:** en las horas con lluvia fuerte (más de 5 mm en una hora) hubo **31% más accidentes** que en horas secas *equivalentes*: la misma hora del día, el mismo día de la semana, el mismo mes y el mismo año.
- **Por qué "preliminar":**
  - Solo hubo **58 horas** de lluvia fuerte en 3 años.
  - La lluvia se mide en **un solo punto** de la ciudad.
  - El efecto es significativo, pero por poco (p = 0.04).
- **De dónde:** `03_eda_y_cartel`, pregunta 5 (antes, anexo `A3_lluvia`).

---

## 4. Introducción y descripción del problema

> "En la ZMG se registran más de 8 mil siniestros viales al año…"

24,872 accidentes en 3 años ≈ 8,300 al año. **De dónde:** `00_datos`.

> "…el 10% de las celdas de avenidas principales reúne el 64% de los accidentes."

Se ordenan las 5,775 celdas de más a menos accidentes (2022–2024). El 10% de arriba tiene el 64% de todos los accidentes. **Pocos lugares concentran casi todo**, y por eso vale la pena priorizar.
**De dónde:** `03_eda_y_cartel`, pregunta 3 (curva de concentración).

> "Para decidir dónde intervenir suele contarse cuántos accidentes hubo en cada punto…"

Es el método de los "puntos negros": contar choques y atender los lugares con más. En el cartel ese método es el modelo **"Historial"**.

> "…pero ese conteo no explica por qué un cruce es peligroso ni cuándo…"

Contar dice *dónde hubo*. No dice *por qué* (¿carriles, cruce, puente?) ni *cuándo* (¿viernes, lluvia?).

> "…y sufre de regresión a la media: un mal año no hace peligroso a un sitio."

**Regresión a la media:** si un lugar tuvo un año con muchos choques, en parte fue mala suerte, y lo más probable es que el siguiente año tenga menos aunque no se haga nada. Pasa lo mismo con un alumno que sacó 10 de suerte: el siguiente examen probablemente saque menos.
En los datos: en las celdas del 5% con más accidentes en 2022–23, el conteo sobreestimó 2024 en ~15%, y Empirical Bayes solo en ~6%. Ese resultado está en el anexo A1.

### Pregunta de investigación
> "¿Qué tan bien se puede anticipar dónde y cuándo ocurren los accidentes en las avenidas principales de la ZMG con infraestructura, calendario, clima e historial, y qué factores pesan más?"

Tiene dos partes, y el cartel responde las dos:
1. **¿Qué tan bien?** 58% de captura, contra 54% del método actual y un máximo posible de 63%.
2. **¿Qué pesa más?** El lugar (~93%), y dentro de él vías rápidas, puentes, cruces y carriles.

---

## 5. Metodología: el diagrama de 6 cajas

| Caja | Qué dice | En palabras simples | Notebook |
|---|---|---|---|
| **Datos** | INEGI 24,872 accidentes · OSM · Open-Meteo | Las 3 fuentes, todas abiertas y gratuitas | `00`, `01` |
| **Asignación** | accidente → avenida (≤ 40 m) → celda · 16,607 acc. | A cada accidente se le busca la avenida principal más cercana. Si está a más de 40 m, no fue en una avenida principal y se descarta. Si está más cerca, se "pega" a la avenida y toma la celda de ese punto | `01`, paso 4 |
| **Celdas** | geohash-7 · 4,143 celdas · ~150 × 150 m · 19 variables | La avenida se parte en cuadritos y a cada uno se le calculan sus 19 variables | `01`, pasos 2–3 |
| **Tabla** | celda × día · 4.5 M filas · infraestructura, calendario, clima, historial | La tabla con la que aprenden los modelos | `02`, sección 1 |
| **5 modelos** | Historial, Empirical Bayes, Poisson, Random Forest, XGBoost | Desde lo más simple (contar) hasta lo más complejo | `02`, sección 5 |
| **Prueba 2024** | captura de accidentes · IC bootstrap · SHAP · razones de tasas | Cómo se mide y se explica el resultado | `02`, secciones 6–8 |

---

## 6. Metodología: "Una celda por dentro: López Mateos × Mariano Otero"

**Para qué está:** muestra **cómo una esquina real se convierte en una fila de la tabla**.

- **El cuadro azul claro:** la celda geohash `9ewmqyw`, de ~150 × 150 m.
- **Líneas:**
  - azules = la avenida principal (López Mateos);
  - naranjas = las avenidas que la cruzan (Mariano Otero y sus laterales y retornos);
  - grises = calles chicas.
- **Puntos:**
  - negros = intersecciones (donde llegan 3 o más calles);
  - triángulos morados = cruces peatonales;
  - cuadros verdes = paradas;
  - puntos rojos = accidentes.
- **Columna de la derecha:** los valores que esa celda tiene en la tabla.
  - **Geohash 9ewmqyw:** su código.
  - **Vía primaria, 2 carriles:** tipo y carriles de la avenida principal según OSM. Lo de los 2 carriles es por sentido, según cómo esté etiquetado.
  - **Cruce de avenidas: sí:** hay 2 o más avenidas principales distintas en la celda.
  - **Intersecciones: 8:** los puntos negros dentro del cuadro.
  - **Paso deprimido / puente: sí:** López Mateos pasa por un paso a desnivel ahí.
  - **Cruces peatonales (100 m): 15:** cruces peatonales a menos de 100 m de la celda.
  - **Accidentes 2022 · 23 · 24 = 11 · 21 · 47:** accidentes registrados en esa celda cada año. El brinco de 2024 es en buena parte el **cambio de registro** (sección 11).

**De dónde:** `03_eda_y_cartel`, pregunta 4 (antes, `figuras_cartel.py` y `explorar_celda.py`).

---

## 7. Metodología: "¿Por qué celdas geohash-7? [3]"

**Qué es un geohash:** un sistema que divide el mundo en una cuadrícula y le da a cada cuadro un código de letras y números. Cada letra extra divide el cuadro en 32 más chicos. Con **7 caracteres**, el cuadro mide ~150 m.

> "Miden lo mismo en toda la ciudad: conteos comparables, sin depender de límites administrativos [4]."

Si se usaran colonias, unas son enormes y otras chiquitas, y una colonia grande tendría más accidentes solo por ser grande. Con celdas iguales, 10 accidentes significan lo mismo en cualquier lugar. Que los resultados cambien según cómo se dibujan los límites tiene nombre: **problema de la unidad de área modificable** (Openshaw, 1984, ref. [4]).

> "~150 m ≈ un cruce y su zona de influencia (76 m en el HSM [1])."

El *Highway Safety Manual*, el manual de referencia en seguridad vial, considera que un choque "es de una intersección" si ocurre a menos de **76 m (250 pies)** de ella. Una celda de ~150 m cubre el cruce y sus accesos.

> "Jerárquicas: 5 caracteres = bloque de ~5 km para la validación espacial."

Si a `9ewmqyw` le quitas los últimos 2 caracteres, queda `9ewmq`: el bloque de ~5 km que la contiene. Sirvió para la **validación espacial** de Empirical Bayes: el modelo se entrenaba sin un bloque completo y luego predecía ese bloque, para comprobar que funciona en zonas que no vio y no solo copia a las celdas vecinas.

> "Estándar y reproducibles; ya usadas para predecir accidentes [5]."

- Cualquier persona con las mismas coordenadas obtiene el mismo código, así que el estudio se puede repetir.
- Moosavi et al. (2019) usaron geohash para predecir accidentes en Estados Unidos.

---

## 8. Metodología: los 4 puntos de abajo

### "Datos: ATUS-INEGI 2022–2024, OpenStreetMap con OSMnx [8]… y lluvia horaria de Open-Meteo."
- **ATUS:** "Accidentes de Tránsito Terrestre en Zonas Urbanas y Suburbanas", del INEGI.
- **OSMnx:** la librería de Python que descarga y procesa OpenStreetMap (Boeing, 2017).
- **Open-Meteo:** clima histórico por hora, gratuito.

### "Transformaciones: …"
| Frase | Qué significa |
|---|---|
| **coordenadas a UTM** | Latitud y longitud están en *grados*. UTM es un sistema en *metros* (zona 13 norte para Guadalajara). Se necesita para medir "a 40 m" o "a 100 m". |
| **cada accidente a la avenida más cercana (≤ 40 m) y a su celda** | Ver la caja "Asignación" de la sección 5. Los 40 m cubren el ancho de una avenida grande más el error típico del GPS. |
| **conteo por celda y día** | Se cuenta cuántos accidentes hubo en cada celda cada día. Casi siempre es 0: solo el 0.3% de las filas tiene un accidente. |
| **historial de los 365 y 90 días previos** | Para cada celda y día: accidentes de esa celda en el último año y en los últimos 3 meses, **sin contar ese día**. |
| **lluvia por hora → indicadores diarios** | La lluvia de cada hora se resume por día: lluvia total, la hora más lluviosa, horas con lluvia y temperatura media. |
| **calendario (festivos, quincena)** | Días de descanso oficiales, Semana Santa, días 15 y fin de mes (quincena). |
| **faltantes imputados** | En OSM a veces no viene la velocidad o los carriles. Se rellena con un valor típico (60 km/h, 2 carriles) y se marca que faltaba. |
| **2 variables redundantes fuera (correlación 0.99)** | `n_avenidas` era casi igual a `cruce_avenidas`, y `semaforo` a `n_100m_semaforo`. Dos variables que dicen lo mismo confunden a la regresión (**multicolinealidad**), así que se quitó una de cada par. |

### "Modelos: Historial (promedio de la celda), Empirical Bayes [1, 2], regresión de Poisson, Random Forest y XGBoost Poisson [6]."
| Modelo | Explicación de una línea |
|---|---|
| **Historial** | El promedio de accidentes por día de la celda en 2022–2023. Es **lo que se hace hoy**: contar. |
| **Empirical Bayes** | El estándar del *Highway Safety Manual*. Mezcla lo que *debería* tener la celda por su infraestructura con lo que *sí* tuvo. Si la celda tiene pocos datos, confía más en la infraestructura; si tiene muchos, en su historia. Ejemplo: esperaba 6 por su diseño, tuvo 2 → EB dice ~4. Corrige la regresión a la media. |
| **Regresión de Poisson** | La regresión clásica para **conteos**. Es interpretable: cada variable multiplica el riesgo por un número (×1.2 = +20%). |
| **Random Forest** | Cientos de árboles de decisión, cada uno aprende con una muestra distinta, y se promedian. |
| **XGBoost** | Árboles en cadena: cada árbol nuevo corrige los errores de los anteriores. Usa objetivo **Poisson** porque se predicen conteos. |

### "Evaluación: entrenamiento abr 2022 – dic 2023, prueba 2024; captura en el 10% de celdas (IC por bootstrap); importancia SHAP [7]."
- **Captura en el 10% de celdas:** el porcentaje de los accidentes de 2024 que cae en el 10% de celdas que el modelo marcó como más riesgosas.
  - **¿Por qué no "accuracy"?** El 99.7% de las filas son ceros. Un modelo que diga siempre "no pasa nada" tendría 99.7% de accuracy y no serviría para nada.
- **IC por bootstrap:** el intervalo de confianza dice qué tanto podría variar el resultado por suerte. Bootstrap = se reinventan 1,000 versiones de los datos (se sacan celdas al azar, con repetición) y se recalcula el resultado en cada una. El rango donde caen 95 de cada 100 es el IC 95%.
  - **Frase:** *"Es el rango donde muy probablemente está el valor real."*
- **SHAP:** reparte cada predicción entre las variables, por ejemplo: "esta celda tiene riesgo alto: +40% por ser troncal, +20% por su historial…". Se promedia para saber qué pesa más. Viene de la teoría de juegos (valores de Shapley).

---

## 9. ¿Qué es el historial y por qué no es trampa? (pregunta probable)
- **Qué es:** el número de accidentes que tuvo la celda en los 365 (y 90) días **anteriores** al día que se predice, anualizado.
- **No es trampa:** nunca incluye el día que se predice ni días futuros. Es información que **sí tendrías** en la vida real al momento de predecir.
- **No hay sobreajuste:** la prueba es 2024, que el modelo nunca vio, y ahí sigue funcionando. Sobreajustar sería que funcione en entrenamiento y falle en la prueba.
- **Por qué pesa tanto:** el riesgo es **persistente**. Donde chocan, siguen chocando.

---

## 10. Resultados

### Gráfica 1: "¿Qué modelo ubica mejor las zonas de riesgo? (prueba 2024)"
| Modelo | Captura |
|---|---|
| Random Forest | 57.9% |
| XGBoost | 57.8% |
| Regresión de Poisson | 57.3% |
| Empirical Bayes | 53.9% |
| Historial (lo que se hace hoy) | 53.7% |
| **Máximo posible** | **63%** |

- **Las rayitas negras** son el intervalo de confianza (IC 95%).
- **"Máximo posible 63%":** si alguien supiera de antemano cuántos accidentes tendrá cada celda en 2024 y eligiera las 414 con más, capturaría 63%. **Ningún modelo puede pasar de ahí**, porque el resto de los accidentes está repartido en muchas celdas con 1 o 2 choques.
- **Cómo leerla:**
  - Los 3 modelos que usan infraestructura y calendario (Poisson, RF, XGBoost) le ganan al conteo por ~4 puntos.
  - Empirical Bayes empata con el conteo en esta métrica; su ventaja es que corrige la regresión a la media.
  - RF y XGBoost empatan entre sí, así que el límite son los datos, no el algoritmo.
- **De dónde:** `02_modelos`, secciones 5–6 (antes, `03_modelo_celda_dia`, sección 5).

### Recuadro: "XGBoost vs conteo histórico: +4.1 puntos (IC 95% +2.8 a +5.9), ≈ 233 accidentes más cubiertos con las mismas 414 celdas."
- **+4.1 puntos** = 57.8% − 53.7%.
- **IC 95% +2.8 a +5.9:** incluso en el peor caso razonable, la mejora es positiva. **No es casualidad**: en ninguna de las 1,000 remuestras el historial le ganó.
- **≈ 233 accidentes:** 4.1% de los 5,636 accidentes de 2024.
- **414 celdas** = 10% de 4,143.
- **Si dicen "4 puntos es poco":** *"Del historial (54%) al máximo posible (63%) solo hay 9 puntos de margen. El modelo gana 4, casi la mitad de lo que se puede ganar. Además, con los mismos recursos se cubren ~233 accidentes más al año."*

### Gráfica 2: "¿Qué pesa más en la predicción?"
- **DÓNDE (lugar):** Infraestructura 50% + Historial 46% = 96% *(en tu corrida real ~93%; ver sección 0)*.
- **CUÁNDO (momento):** Calendario 3% + Clima diario 1% = 4%.
- **Por qué el clima diario pesa tan poco:** la lluvia se mide *por día* y en *un solo punto*. Si llovió a las 4 am, el día cuenta como lluvioso aunque a las 7 pm esté seco. Por hora sí se ve el efecto (+31%, gráfica 3).
- **De dónde:** `02_modelos`, sección 7.

### Gráfica 3: "¿Qué aumenta el riesgo?"
Cada punto es **cuántas veces más accidentes** espera una celda con esa característica. Es la **razón de tasas (RR o IRR)**.

| Variable | Valor | Cómo decirlo |
|---|---|---|
| Autopista / vía rápida* | ×2.48 | 2.5 veces más accidentes que una vía secundaria |
| Vía troncal* | ×2.33 | 2.3 veces más que una secundaria |
| Puente / paso elevado | ×1.87 | 87% más |
| Cruce de dos avenidas | ×1.49 | 49% más que una celda sin cruce |
| Carriles de la avenida (c/u) | ×1.30 | +30% por cada carril extra |
| Intersecciones (c/u) | ×1.26 | +26% por cada esquina extra |
| Distancia al centro (km) | ×0.92 | −8% por cada km que te alejas del centro |
| Lluvia fuerte (> 5 mm/h) | ×1.31 | +31% en esas horas |
| Lluvia ligera (0.5–2 mm/h) | ×1.05 | gris = **no significativo**: podría ser casualidad |

- ***vs vía secundaria:** el tipo de vía se compara contra la categoría más baja.
- **Las barras azules** son el intervalo de confianza. Si no cruza la línea del 1, el efecto es real (significativo).
- **De dónde sale cada parte:**
  - **Infraestructura:** regresión **binomial negativa por celda**. Es como Poisson pero permite que unas celdas varíen más que otras. Se cuentan los accidentes 2022–23 de cada celda y se explican **solo con su infraestructura**. Anexo A1; en la versión final, `02_modelos`, sección 8.
  - **Lluvia:** regresión de Poisson **por hora** con controles. Anexo A3; versión final, `03_eda_y_cartel`, pregunta 5.
- **Ojo:** son **asociaciones, no causas**. Las autopistas tienen más accidentes en parte porque pasan más autos, y no hay datos de volumen de tráfico.

### Gráfica 4 (mapas): "Riesgo esperado 2024 por celda" y "López Mateos: los cruces más riesgosos"
- **Mapa izquierdo:** cada punto es una celda. Más oscuro y grande = más accidentes esperados en 2024. Gris = municipios fuera del modelo por registro deficiente. La línea naranja es López Mateos.
- **Mapa derecho:** zoom a López Mateos.
- **"30 esperados · 39 reales"**:
  - **Esperados:** lo que XGBoost predijo para 2024 **sin haber visto 2024**, sumando los 366 días.
  - **Reales:** lo que se registró.
- **"recalibrado":** en 2024 se registraron ~11% más accidentes que en 2022–23 por un cambio en el registro. El modelo no podía saberlo, así que las predicciones se multiplicaron por 1.11 para compararlas en la misma escala. Eso **no cambia qué celdas salen arriba**.
- **Cómo leerlo:**
  - El modelo identificó como más riesgosos los cruces con **Periférico, Mariano Otero, Vallarta y De la Calma**, y efectivamente fueron de los que más accidentes tuvieron en 2024.
  - Se quedó corto en cantidad (Mariano Otero: 25 vs 47) porque en 2024 los registros en López Mateos casi se duplicaron, y ese brinco no estaba en los datos de entrenamiento.
- **De dónde:** `02_modelos`, sección 9, y `03_eda_y_cartel`, pregunta 8.

---

## 11. Conclusiones

> "El riesgo es sobre todo de lugar: infraestructura e historial explican el 96% de la predicción; el calendario y el clima diario, el resto."

Gráfica 2. Ojo con el 93/96 (sección 0).

> "XGBoost ubica el 58% de los accidentes de 2024 en el 10% de las celdas, contra 54% del conteo histórico"

Gráfica 1 y recuadro de +4.1 puntos.

> "Vías rápidas, puentes, cruces de avenidas, más carriles e intersecciones elevan el riesgo; la lluvia fuerte, +31% por hora (preliminar)."

Gráfica 3.

> "En López Mateos destacan los cruces con Periférico, Mariano Otero y Vallarta."

Gráfica 4. Son las celdas con más riesgo esperado y más accidentes reales.

> "El cambio de registro de 2024 afecta el nivel, no el orden: se maneja con métricas de captura y recalibración; transformar con logaritmo empeora la predicción."

- **Cambio de registro:** 2022 = 4,757 accidentes, 2023 = 4,791 y 2024 = 5,636 en las celdas del estudio. 2024 brinca (+18%) por cómo se registra, no necesariamente por más choques.
- **Afecta el nivel, no el orden:** si todos los lugares suben parejo, *cuáles* son los más riesgosos no cambia. La captura solo mira el orden, así que no se ve afectada.
- **Recalibración:** para hablar de *cuántos*, se multiplica la predicción por real ÷ predicho (1.11).
- **Logaritmo:** se probó transformar los accidentes con log (`log(1 + y)`) y salió peor en todo. El total predicho bajó de 5,073 a 3,526 contra 5,636 reales. Razones:
  - con tantos ceros, el log casi no cambia nada;
  - al regresar con exp() el modelo subestima;
  - los modelos de conteo (Poisson) **ya trabajan en logaritmos** internamente.
- **De dónde:** anexo `03_modelo_celda_dia`, sección 5.2 (en `_archivo`).

---

## 12. Trabajo a futuro
- **Lluvia por celda y por hora:**
  - usar varios puntos de Open-Meteo para que cada zona tenga su lluvia;
  - o NASA IMERG, lluvia satelital cada 30 minutos.
  - Así la lluvia entraría al modelo principal a la escala donde sí importa.
- **Adición de próximos años / pronóstico 2025:** cuando el INEGI publique 2025, reentrenar con 2022–2024 y validar.
- **Volumen de tráfico:** es la gran limitación.
  - Aforos: conteos de autos, que se pueden pedir por transparencia a la Secretaría de Transporte o al IMEPLAN.
  - Aproximaciones:
    - **centralidad de la red**, qué tan "de paso obligado" es una calle;
    - **rutas GTFS**, cuántas rutas de transporte público pasan.
- **Sensibilidad:** repetir con celdas de otro tamaño, otro buffer (30 o 60 m) e incluyendo Tonalá, para ver si los resultados se sostienen.

---

## 13. Referencias (para qué se cita cada una)
| # | Referencia | Para qué |
|---|---|---|
| [1] | AASHTO, *Highway Safety Manual* (2010) | Empirical Bayes y los 76 m de una intersección |
| [2] | Hauer et al. (2002) | Cómo se calcula Empirical Bayes |
| [3] | Niemeyer, Geohash (2008) | El sistema de celdas |
| [4] | Openshaw (1984) | Por qué no usar colonias (unidad de área modificable) |
| [5] | Moosavi et al. (2019) | Antecedente: geohash para predecir accidentes |
| [6] | Chen y Guestrin (2016) | XGBoost |
| [7] | Lundberg y Lee (2017) | SHAP |
| [8] | Boeing (2017) | OSMnx, para bajar OpenStreetMap |

---

## 14. Preguntas probables y respuestas cortas

- **¿Por qué no usaron accuracy?** *"El 99.7% de los días-celda no tienen accidente; decir siempre 'no pasa nada' daría 99.7% sin servir. Medimos cuántos accidentes captura el 10% de celdas marcadas."*
- **¿Por qué solo 3 municipios?** *"Tonalá, Tlajomulco y El Salto registran muchos menos accidentes por habitante; es subregistro. Entrenar con ellos enseñaría al modelo que sus calles son seguras."*
- **¿No hay fuga de información con el historial?** *"No: solo usa días anteriores al que se predice, y la prueba es 2024, que el modelo nunca vio."*
- **¿Por qué XGBoost y no otro algoritmo?** *"Random Forest empata; el límite son los datos, no el algoritmo. XGBoost se eligió porque maneja faltantes, es rápido y se explica con SHAP."*
- **¿Qué es lo más novedoso?** *"Integrar en una sola tabla, con datos 100% abiertos, infraestructura, calendario, clima e historial por celda y día, y compararlo de forma justa contra lo que se hace hoy."*
- **¿Es causal?** *"No, son asociaciones. Sin volumen de tráfico no podemos separar 'más peligroso' de 'pasan más autos'."*
- **¿Para qué le sirve a una autoridad?** *"Para priorizar: con los mismos recursos, el modelo cubre ~233 accidentes más al año que contar choques, y explica por qué cada cruce es riesgoso (carriles, puente, cruce), lo que orienta el tipo de intervención."*
- **¿Por qué 2024 tuvo más accidentes?** *"Principalmente un cambio en el registro; por eso evaluamos el orden de las celdas y no el número absoluto."*
- **¿Qué es Open-Meteo / ERA5?** *"Un reanálisis: combina observaciones de estaciones y satélites con un modelo del clima para estimar la lluvia en cada hora. Es gratuito, pero su resolución es de ~10 km."*
- **¿Qué es un geohash?** *"Una cuadrícula con códigos; cada celda de 7 caracteres mide ~150 m. Todas son iguales, así que los conteos son comparables."*
