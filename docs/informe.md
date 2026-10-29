# Informe del miniproyecto 1

Informe reproducible de la serie mensual de ventas netas de calzado.
Las cifras corresponden a la ejecución local de `python miniproyecto.py`;
las gráficas se generan en `figuras/` y las tablas en `resultados/`.

## 1. La serie

La serie corresponde a la **cantidad de pares netos vendidos mensualmente** por una empresa del sector calzado. Fue consolidada a partir de la columna `Pares` de la hoja `Detalle` del archivo empresarial anonimizado V2, conservando las devoluciones negativas. Abarca **enero de 2022 a diciembre de 2025**, con **48 observaciones mensuales consecutivas** y **93.411 pares netos** acumulados. Se eligió por su relación directa con la planificación comercial y de inventarios.

**Fuente y permiso:** información empresarial suministrada al grupo y resumida en un CSV mensual agregado que se publica en `datos/ventas_calzado_mensual_V2.csv` bajo autorización empresarial de divulgación confirmada por el grupo. La fuente empresarial original no es pública y no se ha declarado una licencia abierta para que terceros reutilicen los agregados. Además, 48 meses no alcanzan el mínimo de 60 requerido por el enunciado; el grupo solicitó una excepción al docente. Se preserva esta limitación sin añadir observaciones artificiales.

![La serie](../figuras/serie.png)

La serie **no tiene huecos** ni meses duplicados en la consolidación. Como verificación exploratoria de extremos se aplicó el criterio IQR sobre las ventas mensuales (Q1 = **1.366**, Q3 = **2.667,25** pares; límites de **−585,88** y **4.619,13** pares), que **no marca observaciones**. Esto no demuestra la ausencia de cambios comerciales extraordinarios: por ejemplo, mayo y diciembre de 2025 registran **292** y **197** pares, respectivamente. Se decidió **conservar todos los meses sin imputaciones, eliminación ni recorte**; esta decisión está implementada en `preparar()` y se traslada a la columna `decision` de las métricas. La interpretación comercial de los meses bajos sigue siendo una limitación.

## 2. Componentes

![STL](../figuras/stl.png)

Se aplicó **STL robusta con periodicidad de 12 meses**, sin alterar la serie original. La descomposición aditiva representa las ventas de cada mes como:

$$y_t = T_t + S_t + R_t$$

Aquí $T_t$ es la tendencia suavizada, $S_t$ el componente estacional y $R_t$ el residuo. La tendencia estimada comienza en **2,613.84 pares** (2022-01) y finaliza en **709.08 pares** (2025-12), una diferencia de **-1,904.76 pares**. Es consistente con una disminución sostenida del nivel de ventas; las cifras son estimaciones de STL, no ventas observadas de esos meses.

Para interpretar la estacionalidad se calculó, por cada mes calendario, el **promedio del componente $S_t$ en los cuatro años**. La contribución promedio más alta corresponde a **agosto (+852.72 pares)** y la más baja a **enero (-1,689.18 pares)**. Estos efectos indican aumentos o disminuciones *respecto a la tendencia estimada*, no el total esperado de ventas de esos meses.

El residuo de mayor magnitud absoluta aparece en **2024-05 (+1,502.06 pares)**: es la parte de esa observación que no explica la suma de tendencia y estacionalidad. No puede atribuirse a una causa comercial específica sin otras fuentes. Con **solo cuatro ciclos anuales**, estos patrones son **exploratorios** y podrían verse afectados por los cambios de demanda de 2024–2025.

Los valores anteriores se imprimen directamente mediante `descomponer()` y su representación está en `figuras/stl.png`.

## 3. Líneas base y backtest

Se utilizó el **backtest de `comun.py` sin modificaciones**, con 24 meses finales destinados al esquema de evaluación por orígenes móviles y un horizonte de **12 meses** en cada origen. Con 48 observaciones, se evalúan **13 orígenes** entre **diciembre de 2023 y diciembre de 2024**. Para cada origen, las funciones de pronóstico reciben únicamente la serie de entrenamiento disponible hasta ese momento; el pronóstico se contrasta con los 12 meses siguientes. El promedio de métricas corresponde a la **media de las 13 métricas por origen**, no a una RMSE agrupada por todos los errores.

El primer origen utiliza **24 meses de entrenamiento** (solo dos ciclos anuales), limitación derivada de tener 48 meses totales. Esta restricción se deja explícita por la exigencia de al menos 60 observaciones y no se modifica el procedimiento compartido.

| Línea base | RMSE (pares) | MAE (pares) | MAPE (%) |
|---|---:|---:|---:|
| Ingenuo | 1081.80 | 887.45 | 138.60 |
| Estacional ingenuo | **842.94** | **680.98** | **90.89** |

La línea **estacional ingenua** obtiene el menor RMSE (mejora del **22.08 %** frente a la ingenua), y también menores MAE y MAPE. Los MAPE son elevados porque algunos meses tienen ventas bajas y el error porcentual se amplifica. Estos son los resultados que el SARIMA y SARIMAX deberán intentar superar.

## 4. Estacionariedad e identificación

Se aplicó la **prueba Dickey-Fuller aumentada (ADF)** bajo la hipótesis nula **H₀: existe una raíz unitaria** y con nivel de significancia del 5 %. Se evaluaron la serie original, la diferencia regular (lag 1), la diferencia estacional (lag 12) y ambas diferencias; adicionalmente, la serie original **con constante y tendencia**, por la caída apreciada en STL. Para cada prueba, el número de rezagos ADF se eligió automáticamente por AIC.

| Transformación | Estadístico ADF | Valor p | Rezagos ADF |
|---|---:|---:|---:|
| Original | -4.725 | 7.5370133e-05 | 0 |
| Original con tendencia | -6.866 | 2.8386636e-08 | 0 |
| Diferencia regular | -5.545 | 1.6686566e-06 | 10 |
| Diferencia estacional (12) | -1.364 | 0.59942165 | 9 |
| Diferencia regular y estacional | -2.846 | 0.051982991 | 10 |

La serie original **rechaza H₀** tanto con constante (p = **7.5370133e-05**) como con constante y tendencia (p = **2.8386636e-08**). Como decisión inicial se adopta **`d = 0`**: diferenciar regularmente no parece indispensable para eliminar una raíz unitaria. La diferencia estacional no rechaza H₀ (p = **0.599422**), resultado que **no debe interpretarse como prueba de que `D = 1` es obligatorio**. ADF no es una prueba específica de raíces unitarias estacionales; se adopta provisionalmente **`D = 0`** por parsimonia y se representa el patrón anual mediante términos SARIMA estacionales (`P`, `Q`).

![ACF y PACF](../figuras/acf_pacf.png)

Para la **serie sin diferencias (`d = 0`, `D = 0`)**, la banda exploratoria aproximada al 95 % es **±0.283**. En la **ACF** sobresalen los rezagos **1 (r = 0.304)** y **12 (r = 0.351)**; en la **PACF** destacan también **1 (r = 0.304)** y **12 (r = 0.336)**. Se consideran, por ello, candidatos con **AR(1)** no estacional y **AR(1)** estacional de periodo 12. La inclusión de términos MA(1) y otras combinaciones se evaluará mediante AIC y diagnóstico de residuos en la siguiente sección, sin asignar el orden final solo por inspección visual.

**Limitaciones:** el rechazo de raíz unitaria por ADF **no demuestra estacionariedad estricta**, las bandas ACF/PACF son orientativas y los **48 meses** representan únicamente cuatro ciclos anuales. Los resultados estacionales y la elección de `D` deben interpretarse con cautela y contrastarse mediante ajuste y evaluación fuera de muestra.

## 5. Modelos clásicos

Se evaluó una rejilla pequeña de **16 SARIMA**, con $p,q,P,Q\in\{0,1\}$,
$d=0$, $D=0$ y periodo estacional $m=12$ fijados con el análisis de la
sección anterior. Se ajustó sobre las ventas divididas por una **escala de 10**
para mejorar la estabilidad numérica; los pronósticos se regresan a **pares
netos originales** antes de calcular las métricas. Se utilizó constante
porque la serie no se diferenció. Se descartaría cualquier ajuste que no
convergiera; los 16 ajustes de esta ejecución convergieron.

El criterio AIC penaliza la complejidad del modelo, pero **no mide por sí mismo
el desempeño predictivo fuera de muestra**. La rejilla y sus valores numéricos,
generados por código, están disponibles en `resultados/rejilla_aic.csv`.

| Orden regular | Orden estacional | AIC | Convergió |
|---|---|---:|---|
| `(1, 0, 1)` | `(1, 0, 0, 12)` | 552.77 | Sí |
| `(1, 0, 1)` | `(1, 0, 1, 12)` | 554.76 | Sí |
| `(1, 0, 1)` | `(0, 0, 1, 12)` | 554.93 | Sí |
| `(1, 0, 0)` | `(0, 0, 1, 12)` | 558.46 | Sí |
| `(1, 0, 0)` | `(1, 0, 0, 12)` | 558.83 | Sí |
| `(0, 0, 0)` | `(0, 0, 1, 12)` | 559.33 | Sí |
| `(0, 0, 1)` | `(0, 0, 1, 12)` | 559.67 | Sí |
| `(1, 0, 0)` | `(1, 0, 1, 12)` | 559.96 | Sí |
| `(0, 0, 0)` | `(1, 0, 1, 12)` | 560.32 | Sí |
| `(0, 0, 1)` | `(1, 0, 0, 12)` | 560.91 | Sí |
| `(0, 0, 1)` | `(1, 0, 1, 12)` | 561.09 | Sí |
| `(0, 0, 0)` | `(1, 0, 0, 12)` | 561.45 | Sí |
| `(1, 0, 1)` | `(0, 0, 0, 12)` | 567.06 | Sí |
| `(1, 0, 0)` | `(0, 0, 0, 12)` | 567.57 | Sí |
| `(0, 0, 1)` | `(0, 0, 0, 12)` | 568.87 | Sí |
| `(0, 0, 0)` | `(0, 0, 0, 12)` | 571.01 | Sí |

El mínimo entre modelos convergidos corresponde a **SARIMA(1,0,1)(1,0,0,12)**,
con **AIC = 552.7675**. En el componente regular, $p=1$ utiliza dependencia
a un mes, $d=0$ no aplica diferencias y $q=1$ incorpora un choque pasado.
En el estacional, $P=1$ introduce relación a 12 meses, $D=0$ evita diferenciar
por año y $Q=0$ no incorpora término MA estacional. Una forma de representar
su estructura es:

$$
(1-\phi_1 B)(1-\Phi_1 B^{12})(y_t-\mu)
= (1+\theta_1 B)\varepsilon_t,
$$

con $B$ como operador de rezago mensual y $\varepsilon_t$ como innovación.
La ecuación resume la estructura SARIMA; los coeficientes se estiman en el
ajuste y se vuelven a estimar por origen durante el backtest.

### Diagnóstico de residuos

![Diagnóstico de residuos SARIMA](../figuras/residuos.png)

La **prueba Ljung-Box** contrasta $H_0$: ausencia de autocorrelación conjunta
hasta el rezago evaluado. Se descontaron **3 grados de libertad AR/MA**
($p+q+P+Q=3$). Se obtuvo:

| Rezago | Estadístico Ljung-Box | Valor p | Interpretación al 5 % |
|---|---:|---:|---|
| 12 | 9.5288 | 0.389955 | No se rechaza $H_0$ |
| 24 | 21.2600 | 0.443168 | No se rechaza $H_0$ |

La ACF de residuos no presenta señales suficientes para rechazar la ausencia
de autocorrelación global mediante esas pruebas. Esto **no demuestra** que
los errores sean independientes, normales ni que el modelo sea el mejor
pronosticando. Con 48 observaciones, la potencia de diagnóstico es limitada.

### SARIMAX: festivos como variable exógena

Se agregó el **número de festivos legales de Colombia por mes**. El calendario
se calcula mediante las reglas de la Ley 51 de 1983: fechas fijas,
festividades trasladadas al lunes y fechas móviles asociadas a Pascua
([texto legal — Función Pública](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php/norma.php?i=4954)).
El índice incluye **2022-01 a 2026-12**, incorporando 12 meses futuros
para poder emitir pronósticos. En **2025 aparecen 17 fechas distintas**,
pues pueden coincidir dos festividades en una sola fecha de descanso.

La estructura del modelo SARIMAX es:

$$
y_t = \beta_0 + \beta_1 x_t + u_t,
\qquad u_t \sim SARIMA(1,0,1)(1,0,0)_{12},
$$

donde $x_t$ es el número de fechas festivas en el mes. El ajuste completo
produjo un efecto estimado de **-22.41 pares por festivo** y
**p = 0.868564**. Al superar 0,05, no se obtuvo evidencia
estadística suficiente de un efecto distinto de cero, manteniendo las demás
condiciones del modelo. Su coeficiente no implica causalidad. Los valores
quedaron registrados en `resultados/efecto_festivos.csv`.

En el **backtest** se utilizan para ajustar solamente los festivos de los
meses observados y, para pronosticar, los festivos conocidos de cada mes
futuro. No se utilizan ventas posteriores al origen en los ajustes.

**Limitación de selección:** el modelo y los órdenes SARIMA fueron escogidos
por AIC sobre los 48 meses **antes** del backtest. Por ello, aunque cada
ajuste de parámetros se hace solo con datos de entrenamiento, la elección
global de órdenes sí utiliza información de fechas posteriores a algunos
orígenes. Los resultados no deben presentarse como una selección anidada
completamente libre de fuga de información. Un backtest anidado exigiría
repetir la selección de órdenes dentro de cada entrenamiento, opción que no
se implementa en esta versión.

## 6. Tabla de métricas

La tabla de abajo procede de `resultados/metricas.csv`, creada con el **mismo
`backtest` de `comun.py` sin alterar**. Compara 13 orígenes móviles, cada uno
con pronósticos a 12 meses, y presenta el promedio de métricas por origen,
ordenado por RMSE ascendente. No se limitaron los pronósticos a cero, pues
se prefirió conservar la salida matemática del modelo y comparar en las
mismas condiciones.

| Modelo | Decisión de preparación | RMSE (pares) | MAE (pares) | MAPE (%) |
|---|---|---:|---:|---:|
| estacional ingenuo | 48 meses consecutivos sin faltantes; se conservan todos los valores mensuales sin imputar ni recortar; revisión comercial pendiente de meses bajos 2025 | 842.94 | 680.98 | 90.89 |
| SARIMA(1,0,1)(1,0,0,12) | 48 meses consecutivos sin faltantes; se conservan todos los valores mensuales sin imputar ni recortar; revisión comercial pendiente de meses bajos 2025 | 857.44 | 718.55 | 109.04 |
| SARIMAX(1,0,1)(1,0,0,12) + exógenas | 48 meses consecutivos sin faltantes; se conservan todos los valores mensuales sin imputar ni recortar; revisión comercial pendiente de meses bajos 2025 | 866.53 | 704.25 | 109.22 |
| ingenuo | 48 meses consecutivos sin faltantes; se conservan todos los valores mensuales sin imputar ni recortar; revisión comercial pendiente de meses bajos 2025 | 1081.80 | 887.45 | 138.60 |

**Resultado:** la línea base **estacional ingenua** mantiene el menor RMSE,
MAE y MAPE de esta comparación. El **SARIMA** es el mejor de los dos modelos
clásicos parametrizados, pero su RMSE fue **1.72 % mayor**
que el estacional ingenuo; el **SARIMAX** fue **2.80 % mayor**.
Los MAPE elevados deben leerse con cautela debido a los meses de ventas
muy reducidas: un error moderado en pares puede representar un porcentaje
muy grande cuando la base mensual es pequeña.

## 7. Conclusión

El ejercicio no justificó sustituir la **línea base estacional ingenua**
por un modelo más complejo. El mejor SARIMA por AIC,
**SARIMA(1,0,1)(1,0,0,12)**, logró un comportamiento residual compatible
con ausencia de autocorrelación relevante a 12 y 24 rezagos, pero en el
backtest presentó **RMSE de 857.44 pares**, frente a **842.94 pares**
del estacional ingenuo. El SARIMAX con número de festivos tampoco mejoró
el RMSE (**866.53 pares**) y su efecto exógeno no fue significativo.

![Pronóstico ingenuo estacional frente a la realidad 2025](../figuras/validacion_2025.png)

La caída de ventas durante **2025** es un reto visible: la línea base
estacional pronostica **22.902 pares** para ese año utilizando los valores
de 2024, mientras los datos observados suman **12.998 pares**, una
sobreestimación de **9.904 pares**. Esto ilustra que repetir el patrón del
año anterior puede fallar cuando cambia el nivel del negocio. La gráfica
se muestra para interpretar los errores, no para introducir un nuevo
criterio de selección.

**Conclusión para el Miniproyecto 2:** la referencia a superar, según el
criterio de RMSE adoptado, es el estacional ingenuo (**842.94 pares**).
Se sugiere investigar la caída de 2025, validar la estabilidad de la
estacionalidad y evaluar nuevos métodos con especial cuidado al seleccionar
hiperparámetros dentro de cada origen. Los 48 meses disponibles continúan siendo una excepción pendiente
de respuesta académica; aunque la empresa autorizó divulgar los
agregados mensuales, todavía no se dispone de una licencia pública
de reutilización expresamente definida.
