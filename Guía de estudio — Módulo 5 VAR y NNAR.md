# Guía de estudio — Módulo 5: VAR y NNAR

Nov 25, 2026 · @Edgar Quintero

## Panorama

El Módulo 5 tiene dos lecciones y ambas rompen un supuesto de los módulos anteriores: **VAR** deja de tratar los predictores como dados (todas las series se explican entre sí) y **NNAR** deja de suponer relaciones lineales. Es el último módulo del repo del curso; no hay Módulo 6.

| Lección | Pregunta que responde | Función en fable | Idea central |
| --- | --- | --- | --- |
| VAR (Vector Autoregression) | ¿Qué pasa si varias series se influyen en ambas direcciones? | `VAR(vars(y1, y2))` | Cada variable se explica con los rezagos de **todas** las variables |
| NNAR (Neural Network Autoregression) | ¿Qué pasa si la relación con el pasado no es lineal? | `NNETAR(y)` | Una red neuronal con una capa oculta usa los rezagos de la serie como entradas |

**Cómo encaja con lo anterior** (tabla de la lección de VAR, con NNAR agregado):

| Modelo | Predictores | ¿Quién pronostica los predictores? | ¿Lineal? |
| --- | --- | --- | --- |
| ARIMA (Módulo 2) | Ninguno, solo su pasado | — | Sí |
| Regresión dinámica (Módulo 3) | Variables exógenas x | **Tú** (escenarios, pronóstico ex ante) | Sí |
| **VAR** (Módulo 5) | Cada variable predice a las demás | **El propio modelo** | Sí |
| **NNAR** (Módulo 5) | Su propio pasado (y opcionalmente x) | Tú, si usas regresores | **No** |

La regla que se repite en todo el curso aplica aquí también: un modelo más complejo tiene que **ganarle** al benchmark en validación cruzada, no se da por hecho que gana.

## VAR: conceptos clave

Un VAR trata todas las variables como **endógenas**: cada una se explica con p rezagos de todas las K variables, y el modelo las pronostica juntas. Resuelve dos problemas de la regresión: ignora la retroalimentación (y también afecta a x) y obliga a pronosticar x por fuera.

**Cuándo hace falta.** Si la relación es en una sola dirección (x → y), basta la regresión dinámica; si es en ambas (x ↔ y), considera un VAR. Ejemplos de la clase: estímulo fiscal australiano (ventas ↔ ingresos), tasa de Banxico ↔ inflación ↔ tipo de cambio, publicidad ↔ ventas. Contraejemplo: producción industrial de EE. UU. → manufactura mexicana (solo va en una dirección).

**VAR(1) con dos variables** (K = 2, p = 1): una ecuación por variable, cada una con su constante y los rezagos de **ambas**.

```latex
\begin{aligned}
y_{1,t} &= c_1 + \phi_{11,1}\, y_{1,t-1} + \phi_{12,1}\, y_{2,t-1} + \varepsilon_{1,t} \\
y_{2,t} &= c_2 + \phi_{21,1}\, y_{1,t-1} + \phi_{22,1}\, y_{2,t-1} + \varepsilon_{2,t}
\end{aligned}
```

- φ\_ij,ℓ = efecto del rezago ℓ de la variable j sobre la variable i. Ejemplo: φ\_12,1 = cuánto afecta y₂ del periodo pasado a y₁ de hoy.
- Los errores ε₁ y ε₂ son ruido blanco, pero **pueden estar correlacionados entre sí** en el mismo t. Esa correlación vive en la matriz de covarianza Σ.
- Con K = 1 el sistema se reduce a un AR(1): un VAR es a los vectores lo que un AR es a los escalares.

**VAR(p) general**, en forma matricial (y\_t y c son vectores K × 1, cada Φ es una matriz K × K):

```latex
\mathbf{y}_t = \mathbf{c} + \boldsymbol{\Phi}_1 \mathbf{y}_{t-1} + \cdots + \boldsymbol{\Phi}_p \mathbf{y}_{t-p} + \boldsymbol{\varepsilon}_t, \qquad \boldsymbol{\varepsilon}_t \sim \text{WN}(\mathbf{0}, \boldsymbol{\Sigma})
```

**Estimación.** Como todas las ecuaciones tienen los mismos regresores, se estima **ecuación por ecuación con mínimos cuadrados**, y eso es igual de eficiente que estimar el sistema completo.

**Número de coeficientes** = K + pK² (constantes + rezagos), más K(K+1)/2 en Σ. Crece con K²: es la **maldición de la dimensionalidad**.

| K | p | Coeficientes |
| --- | --- | --- |
| 2 | 1 | 6 |
| 2 | 5 | 22 |
| 5 | 4 | 105 |
| 10 | 4 | 410 |

Con 198 observaciones (us\_change), un VAR de 5 variables y 4 rezagos gasta 105 coeficientes: \~21 por ecuación. Cada variable o rezago extra cuesta precisión y ensancha los intervalos.

## VAR: estacionariedad y preparación de datos

Como ARIMA, un VAR necesita series **estacionarias**, y la estacionariedad decide qué versión del modelo ajustar. Revisa cada variable con `unitroot_ndiffs()`, igual que en el Módulo 2.

| Las series son… | Modelo |
| --- | --- |
| Todas estacionarias | **VAR en niveles** (datos originales) |
| No estacionarias y **no** cointegradas | **VAR en diferencias** (diferencias tú primero) |
| No estacionarias **y** cointegradas | **VECM** (modelo de corrección de errores) |

**Trampa de examen:** `VAR()` **no diferencia por ti**. No tiene argumento `d` (a diferencia de `ARIMA()`), y `diff()` dentro de la fórmula falla porque fable no puede invertirlo. Diferencia antes y luego suma los pronósticos de vuelta a los últimos niveles a mano:

```r
data |>
  mutate(dy1 = difference(y1), dy2 = difference(y2)) |>
  filter(!is.na(dy1)) |>
  model(VAR(vars(dy1, dy2)))
```

**Condición de estacionariedad (opcional en la lección).** Un VAR(1) es estacionario si todos los eigenvalores de Φ₁ cumplen |λ| < 1, la versión matricial de |φ₁| < 1 en un AR(1). Un VAR(p) se reescribe como VAR(1) de dimensión Kp apilando los rezagos (**forma compañera**), y es estacionario si todos los eigenvalores de esa matriz Kp × Kp están dentro del círculo unitario.

**Cointegración y VECM.** Dos series I(1) están cointegradas si una combinación lineal de ellas es estacionaria: "vagan, pero juntas". Ejemplos de clase: CETES a 28 y 364 días, el precio de un producto en Guadalajara y en CDMX, consumo e ingreso en **niveles**.

```latex
y_t \sim I(1), \quad x_t \sim I(1), \quad y_t - \beta x_t \sim I(0)
```

Un VAR en diferencias tira la información de que los niveles están amarrados; el VECM la conserva:

```latex
\Delta \mathbf{y}_t = \mathbf{c} + \boldsymbol{\alpha}\, \boldsymbol{\beta}' \mathbf{y}_{t-1} + \sum_{\ell=1}^{p} \boldsymbol{\Gamma}_\ell\, \Delta \mathbf{y}_{t-\ell} + \boldsymbol{\varepsilon}_t
```

- β′y\_{t−1} = **término de corrección de errores**: qué tan lejos estaba el sistema de su equilibrio de largo plazo.
- α = **velocidades de ajuste**: qué tan fuerte regresa cada variable al equilibrio.
- Γ = dinámica de corto plazo, como en un VAR en diferencias.
- El número de relaciones de cointegración r se prueba con el **test de Johansen** (`urca::ca.jo(type = "trace")`): se lee de abajo hacia arriba; rechazas r = 0 si el estadístico supera el valor crítico, luego pruebas r ≤ 1.
- `VECM(vars(y, x) ~ AR(1:4), r = 1)`: fable **no prueba el rango por ti**, el `r` se lo das tú (por defecto 1).
- En el ejemplo simulado (y = 2 + 0.8x + ruido AR(1)), el VECM recupera β ≈ (1, −0.79) y solo y corrige hacia el equilibrio (α ≈ −0.49); x, que es una caminata aleatoria, no se ajusta.

## VAR: cómo elegir K y p

**K (cuántas variables) no se elige con un criterio de información: es una decisión de modelado.** p (cuántos rezagos) sí se elige con AICc o BIC, como en ARIMA.

**Para K:**

- Incluye solo variables **correlacionadas entre sí** y **útiles para pronosticarse** mutuamente.
- Mantén K chico (2 a 4): los parámetros crecen con K².
- Pregunta si la retroalimentación es real. Si una variable solo empuja a la otra, usa regresión dinámica.

**Para p:** fable ajusta cada p de 0 a 5 y se queda con el menor criterio.

```r
VAR(vars(y1, y2) ~ AR(p = 0:5), ic = "aicc")   # rango y criterio por defecto
VAR(vars(y1, y2), ic = "bic")                   # mismo rango, BIC
VAR(vars(y1, y2) ~ AR(1))                       # p fijo en 1
```

```latex
\text{AIC}_c = -2\log L + 2k + \frac{2k(k+1)}{T - k - 1} \qquad \text{BIC} = -2\log L + k\log T
```

**¿Por qué se suele preferir BIC en un VAR?** Cada rezago extra agrega K² parámetros de golpe, y FPP3 señala que AICc tiende a elegir **demasiados rezagos**. BIC castiga más (log T). Pero es una tendencia, no una regla: **el diagnóstico de residuales tiene la última palabra**.

**El ejemplo de clase (us\_change, consumo e ingreso en % de cambio, ya estacionarios → VAR en niveles):**

| Criterio | Modelo elegido | Coeficientes | Diagnóstico |
| --- | --- | --- | --- |
| AICc | VAR(5) | 22 | Residuales OK |
| BIC | VAR(1) | 6 | La ecuación de Consumo **falla Ljung-Box**: deja autocorrelación |

Lectura del VAR(1): φ̂\_12,1 ≈ 0.11 (el ingreso pasado afecta poco al consumo), φ̂\_21,1 ≈ 0.49 (el consumo pasado afecta **más** al ingreso), y la covarianza de los errores (0.197) es positiva: los choques llegan juntos. FPP3 pronostica con el VAR(5) por los residuales.

## VAR: pronóstico, diagnóstico e interpretación

**El pronóstico es recursivo y no necesita `new_data`**: el VAR pronostica todas las variables a la vez, así que `forecast(h = 8)` basta. Desaparece el problema de la regresión dinámica, donde tú tenías que inventar los valores futuros del predictor.

```latex
\hat{\mathbf{y}}_{T+1|T} = \hat{\mathbf{c}} + \hat{\boldsymbol{\Phi}}_1 \mathbf{y}_T, \qquad \hat{\mathbf{y}}_{T+h|T} = \hat{\mathbf{c}} + \hat{\boldsymbol{\Phi}}_1 \hat{\mathbf{y}}_{T+h-1|T}
```

El primer paso usa datos observados; cada paso siguiente usa el pronóstico anterior. En la clase se verifica a mano con `phi_1 %*% y_T` y coincide con `forecast()`. El `.mean` es una columna matriz (una columna por variable) y la distribución es normal multivariada (`MVN[2]`).

**Intervalos.** La varianza del error a horizonte h para un VAR(1) es la suma de Φ₁ⁱ Σ (Φ₁ⁱ)′ de i = 0 a h − 1: en h = 1 es Σ y crece con h. Ignoran la incertidumbre de los coeficientes estimados, que pesa cuando K y p son grandes.

**Diagnóstico de residuales.** `augment()` da residuales por modelo **y por variable** (`.response`); se revisa el ACF y Ljung-Box de cada ecuación. La prueba de sistema completo es `vars::serial.test()`.

**Validación en us\_change (la conclusión importante):**

- Con una ventana de prueba (2016 Q1–2019 Q2), el ARIMA univariado le ganó ligeramente a los dos VAR en Consumo.
- Con validación cruzada (20 orígenes, h = 4): en **Consumo**, VAR(5) y ARIMA empatan; en **Ingreso**, los dos VAR le ganan al ARIMA. El VAR(1) de BIC es el peor para Consumo, igual que decía su diagnóstico.
- **La ganancia de un VAR no es simétrica**: solo aparece en la variable que recibe información útil de la otra.

**Para qué sirve un VAR** (FPP3), aunque sea **ateorético** (Sims, 1980), difícil de interpretar (coeficientes con signos que alternan entre rezagos) y sobreparametrizado:

1. **Pronosticar** un grupo de variables relacionadas.
2. **Causalidad de Granger**: x Granger-causa a y si el pasado de x mejora el pronóstico de y más allá del pasado de y. Es una prueba F con H₀: todos los coeficientes de los rezagos de x valen 0. En R: `lmtest::grangertest(Consumption ~ Income, order = 5, data = ...)`. Resultado de clase: Ingreso → Consumo p ≈ 0.15 (no); Consumo → Ingreso p < 0.001 (sí). **No es causalidad**, solo contenido predictivo: dos variables movidas por una tercera pueden "Granger-causarse".
3. **Funciones de impulso-respuesta (IRF)**: cómo responde cada variable, periodo a periodo, a un choque único en otra. `IRF(h = 12, impulse = "Income", orthogonal = TRUE)`. Las ortogonalizadas usan una descomposición de Cholesky de Σ, así que **el orden dentro de `vars()` importa**: la primera variable puede afectar a la segunda en el mismo periodo, pero no al revés.
4. **Descomposición de la varianza del error de pronóstico (FEVD)**: cuánto de la varianza del pronóstico de cada variable viene de los choques de cada variable. fable no la calcula; se usa `vars::fevd()`.

## VAR: cuándo usarlo y sus extensiones

**Usa un VAR cuando las variables se afectan mutuamente, necesitas pronósticos de todas y K es chico.** Si no, casi siempre hay una opción más simple.

| Usa un VAR cuando… | Prefiere otra cosa cuando… |
| --- | --- |
| Las variables plausiblemente **se afectan entre sí** | La relación es en una sola dirección → **regresión dinámica** |
| Necesitas pronósticos de **todas** las variables | Solo importa una variable y sus predictores son fáciles de pronosticar |
| K es chico (2 a 4 variables) | Tienes muchas variables → los parámetros explotan |
| Horizontes cortos o medianos | Necesitas coeficientes interpretables |
| Series estacionarias, o que se pueden diferenciar | Series no estacionarias **y** cointegradas → **VECM** |

**Sistemas grandes:** VAR dispersos (muchos coeficientes forzados a cero) y estimación con encogimiento, como los VAR bayesianos. Están fuera del curso.

**VARMA:** extiende el VAR con errores rezagados, igual que ARMA extiende a AR.

```latex
\mathbf{y}_t = \mathbf{c} + \sum_{\ell=1}^{p} \boldsymbol{\Phi}_\ell \mathbf{y}_{t-\ell} + \boldsymbol{\varepsilon}_t + \sum_{j=1}^{q} \boldsymbol{\Theta}_j \boldsymbol{\varepsilon}_{t-j}
```

- Más flexible (representa con pocos parámetros lo que un VAR necesita con muchos rezagos), pero tiene un **problema de identificación**: distintas matrices (Φ, Θ) describen el mismo proceso. Se resuelve con restricciones (índices de Kronecker o componentes escalares).
- En fable: `VARIMA(vars(y1, y2) ~ pdq(1, 0, 1), identification = "none")`. Necesita el paquete `MTS`, que **enmascara `fable::VAR()`** (después escribe `fable::VAR()`), no elige órdenes solo y su AIC/BIC no se compara con el de `VAR()`.
- En la práctica dominan los VAR, porque son más simples y se estiman con mínimos cuadrados.

**Lección de fondo:** en us\_change, para Consumo el VAR(5) estima 22 coeficientes y no gana nada contra un ARIMA univariado. Más complejo no siempre es mejor; el benchmark simple se tiene que vencer, no se da por vencido.

## NNAR: el modelo

Una NNAR (Neural Network AutoRegression) es una red neuronal con **una capa oculta** cuyas entradas son los rezagos de la serie. Existe porque todos los modelos anteriores (ARIMA, ETS aditivo, regresión dinámica, VAR) son **lineales** en el pasado, y no pueden reproducir, por ejemplo, ciclos **asimétricos** que suben rápido y bajan lento.

**Redes neuronales en corto:**

- Una **neurona** multiplica cada entrada por un **peso**, suma todo más un **sesgo** (bias) y pasa el resultado por una **función de activación**. NNAR usa la **sigmoide**, que dobla la suma al rango (0, 1).
- La red aprende ajustando los pesos para minimizar el error, de forma **iterativa** y desde pesos iniciales **aleatorios**.

**Sin capa oculta = regresión lineal = AR(p).** Las entradas se conectan directo a la salida: ŷ = b + w₁y\_{t−1} + … + w\_p y\_{t−p}, que es un AR(p). Es el mismo modelo, solo cambia el estimador:

|  | Regresión (MCO) | Red neuronal (`nnet`) |
| --- | --- | --- |
| Solución | Fórmula cerrada | Búsqueda iterativa |
| Punto de partida | No necesita | Pesos aleatorios |
| Resultado | Mínimo exacto y único | Aproximación, depende del inicio |
| Errores estándar y pruebas | Sí | No |

En la clase se comprueba: una NNAR(9, 0) (`n_nodes = 0, skip = TRUE`) da casi lo mismo que un AR(9) por mínimos cuadrados. Una red sin capa oculta es regresión "estimada por el camino difícil"; **la capa oculta es lo que vale su costo**.

**Con una capa oculta de k neuronas:**

```latex
\hat y_t = b + \sum_{j=1}^{k} w_j \, s\!\left(b_j + \sum_{i=1}^{p} w_{ij}\, y_{t-i}\right)
```

Cada neurona oculta hace su suma ponderada de los rezagos y la dobla con la sigmoide s(·); la salida suma esas k piezas dobladas. Con suficientes neuronas puede aproximar cualquier función suave (**teorema de aproximación universal**).

**El precio:** (p + 1)k + (k + 1) pesos. Con p = 9 y k = 5 son **56 pesos**, contra 10 coeficientes de un AR(9), y fable ajusta **20 redes**.

**Notación:**

- **NNAR(p, k):** p rezagos de entrada, k neuronas ocultas. NNAR(p, 0) es un AR(p) sin las restricciones de estacionariedad de ARIMA.
- **NNAR(p, P, k)ₘ:** agrega P rezagos estacionales (y\_{t−m}, …, y\_{t−Pm}). Ejemplo: NNAR(3, 1, 2)₁₂ usa y\_{t−1}, y\_{t−2}, y\_{t−3}, y\_{t−12} y 2 neuronas; es la contraparte no lineal de un ARIMA(3,0,0)(1,0,0)₁₂.

**Cómo elige `NNETAR()` los valores por defecto:**

| Valor | Por defecto |
| --- | --- |
| p | Orden del mejor AR **lineal** por AIC, sobre los datos desestacionalizados (STL) |
| P | 1 (solo datos estacionales) |
| k | round((p + P + 1) / 2) |
| Redes | 20, con pesos iniciales distintos; los pronósticos se promedian |

Ojo: el número de rezagos de un modelo no lineal se elige con un modelo **lineal**; es un atajo, no lo óptimo. Trátalo como un hiperparámetro que puedes afinar con validación cruzada.

**Más detalles que entran en examen:**

- El pronóstico es **recursivo**, igual que en el VAR: cada pronóstico se vuelve entrada del siguiente.
- Las entradas se **escalan** por defecto (`scale_inputs = TRUE`): la sigmoide se satura con valores grandes.
- **Siempre `set.seed()`**: sin semilla, los pesos iniciales y los pronósticos cambian cada vez.
- fable solo ofrece esta arquitectura (feed-forward, una capa oculta, sigmoide). Redes profundas, LSTM o transformers viven en otros paquetes (`modeltime.gluonts`, `torch`, `neuralforecast`). En el M3, los métodos de machine learning perdieron contra métodos estadísticos simples; el ganador del M4 fue un híbrido (suavizamiento exponencial + red recurrente). El deep learning suele pagar con **muchas series relacionadas**.

## NNAR: intervalos, regresores, limitaciones y cuándo usarla

**Una NNAR gana cuando la serie es larga y su forma es no lineal (manchas solares), y pierde cuando es corta o casi lineal (us\_change) o tiene tendencia (población de México).**

**Ejemplos de la clase:**

| Serie | Resultado | Por qué |
| --- | --- | --- |
| Manchas solares (1700–1988, en √) | NNAR(9, 5) **le gana al ARIMA** en la ventana de prueba y en validación cruzada | Serie larga con ciclo estable de forma asimétrica |
| us\_change (Consumo con Ingreso) | Las NNAR **pierden** contra ARIMA y regresión dinámica | Serie corta y casi lineal; la NNAR por defecto usa 21 rezagos y 289 pesos con menos de 200 datos: memoriza |
| Población de México | NNAR en niveles se **aplana**; NNAR en diferencias se parece al drift | La sigmoide se satura: no extrapola tendencias |

**Diagnóstico:** en manchas solares, los residuales de la NNAR pasan Ljung-Box y los del ARIMA no. Pero no hay que creerlo demasiado: con 56 pesos un buen ajuste dentro de muestra es lo esperado, y la corrección de grados de libertad ni siquiera se puede aplicar. Los residuales dicen si la NNAR **dejó algo fuera**, no si pronosticará bien; para eso, validación cruzada.

**Regresores:** van en la fórmula como en `ARIMA()`, y cada uno es una entrada más. Necesitan valores futuros en `new_data`.

```r
NNETAR(y ~ x1 + x2)
NNETAR(y ~ AR(p = 2) + x1)
NNETAR(y ~ AR() + trend() + fourier(K = 2))
```

`trend()` **no** arregla la tendencia: también pasa por la sigmoide.

**Intervalos de predicción: no hay fórmula, se simulan.**

1. Se sortea un error ε\* y se calcula y\*\_{T+1} = f(y\_T, …) + ε\*.
2. y\**{T+1} entra como rezago para calcular y\**{T+2}, y así hasta el horizonte. Eso es una **trayectoria**.
3. Se repite muchas veces; los percentiles de las trayectorias son los intervalos.

Los errores son normales (por defecto) o remuestreados de los residuales (`bootstrap = TRUE`). En manchas solares las trayectorias conservan la forma del ciclo, pero se desfasan entre sí; por eso los intervalos se abren y el promedio se amortigua.

**Trampas de examen sobre `forecast()`:**

- Por defecto simula `times = 5000` trayectorias: es **lento**. Usa `times = 1000` para explorar y `times = 0` si solo necesitas el pronóstico puntual (por ejemplo, en `accuracy()` o validación cruzada).
- `times = 0` **no da la media**: mete cada pronóstico puntual de vuelta en la red, f(ŷ), mientras que la simulación promedia f(y\*). Por la desigualdad de Jensen, E\[f(Y)\] ≠ f(E\[Y\]) cuando f no es lineal. Compara modelos usando siempre el mismo.
- Los intervalos son **demasiado angostos**: solo consideran el error ε y tratan como conocidos los pesos, p y k.

**La solución a la tendencia:** volver la serie estacionaria antes de la red (diferenciar a mano, como en el VAR, o usar `decomposition_model()` con la serie desestacionalizada). Así la red solo aprende **cambios**, que sí están en el rango que conoce.

**Otras limitaciones:** necesita muchos datos, no se interpreta (no hay coeficientes ni pruebas), no es reproducible sin semilla, es lenta para pronosticar y sus intervalos son demasiado confiados.

| Usa una NNAR cuando… | Prefiere otra cosa cuando… |
| --- | --- |
| La serie es **larga** (cientos de datos) | La serie es corta → ETS, ARIMA |
| Los patrones son **no lineales** (ciclos asimétricos, cambios de régimen) | Los residuales de un modelo lineal ya son ruido blanco |
| Te importa más la precisión que la interpretación | Necesitas explicar el modelo → regresión, ETS |
| La serie es estacionaria, o se puede volver | Hay una tendencia fuerte que no puedes quitar |

## Código de referencia y glosario

**Código de la clase, en el orden en que lo usarías:**

```r
# 1. ¿Hace falta diferenciar? (cada variable)
datos |> features(y1, unitroot_ndiffs)

# 2. VAR: p automático (AICc por defecto) o con BIC
fit <- datos |>
  model(
    aicc = VAR(vars(y1, y2)),
    bic  = VAR(vars(y1, y2), ic = "bic"),
    var1 = VAR(vars(y1, y2) ~ AR(1))
  )
fit |> select(bic) |> report()

# 3. Residuales por modelo y por variable
fit |> augment() |> features(.innov, ljung_box, lag = 10)

# 4. Pronóstico: sin new_data
fit |> forecast(h = 8)

# 5. Granger e impulso-respuesta
lmtest::grangertest(y1 ~ y2, order = 5, data = as.data.frame(datos))
fit |> select(aicc) |> IRF(h = 12, impulse = "y2", orthogonal = TRUE)

# 6. Cointegración y VECM
urca::ca.jo(datos_tbl, type = "trace", ecdet = "const", K = 2)
datos |> model(VECM(vars(y, x) ~ AR(1:4), r = 1))

# 7. NNAR: siempre con semilla
set.seed(2026)
nn <- datos |> model(nnar = NNETAR(sqrt(y)))
nn |> forecast(h = 30, times = 1000)            # con intervalos
nn |> forecast(h = 30, times = 0)               # solo puntual (rápido)
NNETAR(y ~ AR(p = 3, P = 1), n_nodes = 4, n_networks = 50)
```

**Glosario:**

| Término | Qué significa |
| --- | --- |
| Endógena | Variable determinada dentro del sistema; en un VAR, todas lo son |
| K | Número de variables del VAR (decisión de modelado) |
| p | Número de rezagos (se elige con AICc o BIC) |
| Φ\_ℓ | Matriz K × K de coeficientes del rezago ℓ |
| Σ | Matriz de covarianza de los errores; capta choques simultáneos |
| Forma compañera | VAR(p) reescrito como VAR(1) de dimensión Kp |
| Causalidad de Granger | x mejora el pronóstico de y más allá del pasado de y; no es causalidad real |
| IRF | Respuesta de cada variable, en el tiempo, a un choque en otra |
| Ortogonalizada (Cholesky) | IRF que quita la correlación simultánea; depende del orden en `vars()` |
| FEVD | Qué parte de la varianza del pronóstico viene de cada choque (`vars::fevd()`) |
| Cointegración | Series I(1) cuya combinación lineal es I(0): se mueven juntas |
| VECM | VAR en diferencias + término de corrección de errores |
| α, β (VECM) | Velocidades de ajuste y vector de cointegración |
| Johansen | Prueba del número de relaciones de cointegración r |
| VARMA / `VARIMA()` | VAR con errores rezagados; tiene problema de identificación |
| Neurona | Suma ponderada + sesgo, pasada por una activación |
| Sigmoide | Activación que dobla la suma al rango (0, 1); se satura |
| NNAR(p, k) | Red con p rezagos de entrada y k neuronas ocultas |
| NNAR(p, P, k)ₘ | Agrega P rezagos estacionales de periodo m |
| Trayectoria simulada | Un futuro posible, generado paso a paso con errores sorteados |
| `times` | Número de trayectorias en `forecast()` de una NNAR (0 = solo puntual) |

## Preguntas de práctica

Intenta responder antes de leer la respuesta.

1. **¿Cuándo usarías un VAR en lugar de una regresión dinámica?** Cuando la relación va en ambas direcciones (x ↔ y) y necesitas pronosticar todas las variables. Si x solo afecta a y, basta la regresión dinámica.
2. **¿Cuántos coeficientes tiene un VAR con K = 3 y p = 2?** K + pK² = 3 + 2 × 9 = 21 (más 6 en Σ).
3. **¿Por qué un VAR no necesita `new_data` para pronosticar?** Porque pronostica todas las variables dentro del modelo, de forma recursiva; no hay predictores exógenos que inventar.
4. **Tus dos series necesitan una diferencia cada una. ¿Qué haces?** Pruebas cointegración (Johansen). Si no están cointegradas: VAR en diferencias, diferenciando tú los datos. Si lo están: VECM.
5. **¿Qué pasa si escribes `VAR(vars(difference(y1), difference(y2)))`?** Falla: `VAR()` no diferencia ni puede invertir la diferencia. Diferencia con `mutate()` antes y regresa los pronósticos a niveles a mano.
6. **AICc elige VAR(5) y BIC elige VAR(1). ¿Con cuál te quedas?** Con el que deje residuales como ruido blanco y pronostique mejor en validación cruzada. En us\_change, el VAR(1) falló Ljung-Box en Consumo y fue el peor en validación cruzada: se elige el VAR(5).
7. **"Ingreso Granger-causa a Consumo". ¿Significa que el ingreso causa el consumo?** No. Solo significa que el pasado del ingreso mejora el pronóstico del consumo. Una tercera variable podría mover a ambas.
8. **¿Por qué cambian las IRF ortogonalizadas si inviertes el orden en `vars()`?** Porque la descomposición de Cholesky supone que la primera variable puede afectar a la segunda en el mismo periodo, pero no al revés.
9. **¿Qué es una NNAR(9, 0) y a qué modelo equivale?** Una red sin capa oculta con 9 rezagos de entrada: equivale a un AR(9), estimado de forma iterativa en lugar de por mínimos cuadrados.
10. **¿Cuántos pesos tiene una NNAR(9, 5)? ¿Y cuántas neuronas ocultas pondría fable por defecto con p = 9 y sin estacionalidad?** (9 + 1) × 5 + (5 + 1) = 56 pesos. Por defecto k = round((9 + 1) / 2) = 5.
11. **¿Qué entradas usa una NNAR(3, 1, 2)₁₂?** y\_{t−1}, y\_{t−2}, y\_{t−3} y y\_{t−12}, con 2 neuronas ocultas.
12. **¿Por qué una NNAR no puede pronosticar bien la población de México en niveles, aunque le agregues `trend()`?** Porque la sigmoide se satura: la red solo reproduce valores parecidos a los del entrenamiento. `trend()` también pasa por la sigmoide. La solución es diferenciar la serie antes.
13. **¿Por qué los intervalos de una NNAR son demasiado angostos?** Porque la simulación solo considera el error ε y trata como conocidos los pesos, p y k.
14. **¿Qué diferencia hay entre `forecast(times = 0)` y el `.mean` con simulación?** `times = 0` calcula f(ŷ) metiendo el pronóstico puntual de vuelta; la simulación promedia f(y\*). Si f no es lineal, son distintos (desigualdad de Jensen).
15. **Los residuales de tu NNAR pasan Ljung-Box y los del ARIMA no. ¿Ya ganaste?** No. Con tantos pesos, un buen ajuste dentro de muestra es lo esperado. Lo que decide es la validación cruzada fuera de muestra.
