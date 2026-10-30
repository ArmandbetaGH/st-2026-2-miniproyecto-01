"""Miniproyecto 1: la serie del grupo, de las líneas base al mejor modelo clásico.

Se corre de principio a fin con

    python miniproyecto.py

y deja las figuras en figuras/ y la tabla en resultados/metricas.csv. Las
partes marcadas con TODO las completa el grupo; mientras falten, el guion las
reporta como pendientes y sigue. El informe, docs/informe.md, cita las cifras
y las figuras que produce este guion.
"""
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from comun import (RAIZ, backtest, cargar_serie, estacional_ingenuo,  # noqa: E402
                   fechas_siguientes, ingenuo)

warnings.filterwarnings("ignore")
FIGURAS = RAIZ / "figuras"
RESULTADOS = RAIZ / "resultados"
FIGURAS.mkdir(exist_ok=True)
RESULTADOS.mkdir(exist_ok=True)

# ============================================================
# 1. La serie
# ============================================================
# Cambie estos cuatro datos por los de la serie del grupo y documente la
# fuente en datos/README.md. La serie de ejemplo solo sirve para probar que
# el guion corre.
ARCHIVO = "datos/ventas_calzado_mensual_V2.csv"
FECHA = "mes"
VALOR = "pares_netos"
PERIODO = 12

# Lo que se hizo con los huecos y con los datos atípicos, en una línea. Va
# a la columna `decision` de la tabla de métricas.
DECISION = (
    "48 meses consecutivos sin faltantes; se conservan todos los valores "
    "mensuales sin imputar ni recortar; revisión comercial pendiente de meses bajos 2025"
)


def preparar(serie):
    """Valida la serie mensual; conserva todos los registros observados.

    Nuestra serie no requiere imputación. El criterio IQR funciona aquí como
    indicador exploratorio, no como prueba automática de errores comerciales.
    """
    serie = serie.sort_index().astype(float)
    if serie.index.has_duplicates:
        raise ValueError("La serie tiene meses duplicados: revisar el CSV.")
    faltantes = int(serie.isna().sum())
    if faltantes:
        raise ValueError(
            f"Hay {faltantes} meses sin dato: requieren decisión documentada "
            "antes de ejecutar modelos. No se imputan automáticamente."
        )
    if not np.isfinite(serie.to_numpy()).all():
        raise ValueError("La serie contiene valores no finitos.")

    q1, q3 = serie.quantile([0.25, 0.75])
    iqr = q3 - q1
    limite_inf, limite_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    marcados = serie[(serie < limite_inf) | (serie > limite_sup)]

    print("\nPREPARACIÓN — control de calidad de la serie")
    print(f"  Observaciones mensuales: {len(serie)}")
    print(f"  Periodo: {serie.index.min():%Y-%m} a {serie.index.max():%Y-%m}")
    print(f"  Meses sin datos: {faltantes}")
    print(f"  Total de pares netos: {serie.sum():,.0f}")
    print(f"  IQR: Q1={q1:.2f}; Q3={q3:.2f}; "
          f"límites=[{limite_inf:.2f}, {limite_sup:.2f}]")
    print(f"  Meses señalados por IQR: {len(marcados)}")
    print("  Tratamiento: se conservan todos los valores; no se imputan "
          "ni se sustituyen observaciones.")
    print("  Advertencia: el criterio IQR no demuestra ausencia de "
          "anomalías comerciales; revisar meses bajos de 2025.")
    return serie


def graficar_serie(serie):
    figura, eje = plt.subplots(figsize=(9, 3.4))
    eje.plot(serie.index, serie.to_numpy())
    eje.set_title(f"{VALOR}: serie mensual")
    eje.set_ylabel(VALOR)
    figura.tight_layout()
    figura.savefig(FIGURAS / "serie.png", dpi=120)
    plt.close(figura)


# ============================================================
# 2. Descomposición
# ============================================================

def descomponer(serie):
    """Descompone la serie con STL robusta y ciclo de 12 meses.

    Imprime los hallazgos numéricos que se incorporan a docs/informe.md.
    No elimina ni sustituye meses; STL solo descompone la señal observada.
    """
    from statsmodels.tsa.seasonal import STL

    resultado = STL(serie, period=PERIODO, robust=True).fit()
    tendencia = resultado.trend
    estacional = resultado.seasonal
    residuos = resultado.resid

    # ============================================================
    # CONTRIBUCIÓN MÓNICA — Fortaleza de componentes STL
    # ============================================================

    # Varianza del componente residual
    var_residuos = residuos.var()

    # Varianza de tendencia + residuos
    var_tendencia = (tendencia + residuos).var()

    # Varianza de estacionalidad + residuos
    var_estacional = (estacional + residuos).var()

    # Fortaleza de tendencia y estacionalidad
    fuerza_tendencia = max(
        0.0, 1 - var_residuos / var_tendencia
    ) if var_tendencia > 0 else 0.0

    fuerza_estacional = max(
        0.0, 1 - var_residuos / var_estacional
    ) if var_estacional > 0 else 0.0

    # Mostrar resultados en consola
    print("\nFORTALEZA DE COMPONENTES STL")
    print(f"  Fortaleza de tendencia: {fuerza_tendencia:.4f}")
    print(f"  Fortaleza estacional: {fuerza_estacional:.4f}")

    # Guardar resultados en archivo CSV
    pd.DataFrame([{
        "fuerza_tendencia": fuerza_tendencia,
        "fuerza_estacional": fuerza_estacional
    }]).to_csv(
        RESULTADOS / "fuerza_componentes.csv",
        index=False
    )

    # La estacionalidad STL puede variar por año: resumimos su promedio
    # por mes calendario, sin confundirlo con ventas reales del mes.
    promedio_mensual = (
        estacional.groupby(estacional.index.month)
        .mean()
        .reindex(range(1, PERIODO + 1))
    )
    nombres_meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    mes_max = int(promedio_mensual.idxmax())
    mes_min = int(promedio_mensual.idxmin())
    fecha_residuo_max = residuos.abs().idxmax()
    valor_residuo_max = float(residuos.loc[fecha_residuo_max])

    print("\nCOMPONENTES — descomposición STL robusta")
    print(f"  Periodo estacional: {PERIODO} meses")
    print(f"  Tendencia al inicio ({serie.index[0]:%Y-%m}): {tendencia.iloc[0]:.2f} pares")
    print(f"  Tendencia al final ({serie.index[-1]:%Y-%m}): {tendencia.iloc[-1]:.2f} pares")
    print(f"  Cambio tendencia (último - primero): {tendencia.iloc[-1] - tendencia.iloc[0]:.2f} pares")
    print("  Componente estacional medio por mes (pares):")
    for mes, efecto in promedio_mensual.items():
        print(f"    {nombres_meses[mes-1]:<11} {efecto:+.2f}")
    print(f"  Mayor contribución estacional media: {nombres_meses[mes_max-1]} ({promedio_mensual.loc[mes_max]:+.2f})")
    print(f"  Menor contribución estacional media: {nombres_meses[mes_min-1]} ({promedio_mensual.loc[mes_min]:+.2f})")
    print(f"  Residuo de mayor magnitud: {fecha_residuo_max:%Y-%m} ({valor_residuo_max:+.2f} pares)")

    # Cuatro componentes en la misma escala de pares; se conserva
    # el índice mensual original para hacerlos comparables visualmente.
    fig, ejes = plt.subplots(4, 1, figsize=(11, 8.5), sharex=True)
    componentes = [
        (serie, "Serie observada"),
        (tendencia, "Tendencia estimada"),
        (estacional, "Componente estacional"),
        (residuos, "Residuos"),
    ]
    for ax, (valores, etiqueta) in zip(ejes, componentes):
        ax.plot(serie.index, valores, linewidth=1.7)
        ax.set_ylabel("Pares netos")
        ax.set_title(etiqueta, loc="left", fontsize=10)
        ax.grid(alpha=0.2)
    ejes[2].axhline(0, linewidth=0.8, color="gray")
    ejes[3].axhline(0, linewidth=0.8, color="gray")
    ejes[-1].set_xlabel("Mes")
    fig.suptitle("Descomposición STL robusta — ventas netas de calzado (2022–2025)",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(FIGURAS / "stl.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    # ============================================================
    # CONTRIBUCIÓN MÓNICA — Comparación estacional por año
    # ============================================================

    fig, ax = plt.subplots(figsize=(11, 6))

    nombres_meses_cortos = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]

    # Comparar el componente estacional STL de cada año
    for anio in sorted(estacional.index.year.unique()):

        datos_anio = estacional[estacional.index.year == anio]

        ax.plot(
            datos_anio.index.month,
            datos_anio.values,
            marker="o",
            linewidth=2,
            label=str(anio)
        )

    ax.set_title(
        "Comparación de estacionalidad STL por año (2022–2025)",
        fontsize=14,
        fontweight="bold"
    )

    ax.set_xlabel("Mes")
    ax.set_ylabel("Componente estacional (pares netos)")

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(nombres_meses_cortos)

    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)

    ax.grid(alpha=0.3)
    ax.legend(title="Año")

    fig.tight_layout()

    fig.savefig(
        FIGURAS / "estacionalidad_por_anio.png",
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)
    return resultado


# ============================================================
# 3. Estacionariedad e identificación
# ============================================================

def estacionariedad(serie):
    """ADF en cuatro transformaciones, identificación ACF/PACF, y elección d,D.

    Se agrega ADF original con tendencia para distinguir raíz unitaria de
    una tendencia determinística. El ADF no prueba raíces unitarias
    *estacionales*; D se decide con evidencia estacional y parsimonia.
    """
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    from statsmodels.tsa.stattools import acf, adfuller, kpss, pacf

    casos = [
        ("Original", serie, "c"),
        ("Original con tendencia", serie, "ct"),
        ("Diferencia regular", serie.diff().dropna(), "c"),
        ("Diferencia estacional (12)", serie.diff(PERIODO).dropna(), "c"),
        ("Diferencia regular y estacional", serie.diff().diff(PERIODO).dropna(), "c"),
    ]
    filas_adf = []
    print("\nESTACIONARIEDAD — prueba Dickey-Fuller aumentada (ADF)")
    print("  H0: la serie tiene raíz unitaria; alfa = 0.05")
    for nombre, valores, regresion in casos:
        if len(valores) < 20:
            raise ValueError(f"Insuficientes datos para ADF de {nombre}: {len(valores)}")
        estadistico, p, lags, nobs, criticos, *_ = adfuller(
            valores, regression=regresion, autolag="AIC"
        )
        filas_adf.append({
            "transformacion": nombre, "observaciones": len(valores),
            "regresion": regresion, "estadistico_adf": estadistico,
            "valor_p": p, "rezagos_adf": lags, "observaciones_efectivas": nobs,
            "rechaza_raiz_unitaria_5pct": p < 0.05,
        })
        veredicto = "rechaza H0" if p < 0.05 else "no rechaza H0"
        print(f"  {nombre:<33} n={len(valores):>2}  ADF={estadistico:>8.3f}  "
              f"p={p:.8g}  rezagos={lags:>2}  {veredicto}")

    pd.DataFrame(filas_adf).to_csv(
        RESULTADOS / "estacionariedad_adf.csv", index=False
    )
        # ============================================================
    # CONTRIBUCIÓN MÓNICA — Pruebas KPSS de nivel y tendencia
    # ============================================================

    import warnings
    from statsmodels.tools.sm_exceptions import InterpolationWarning

    casos_kpss = [
        ("Nivel", "c"),
        ("Tendencia", "ct"),
    ]

    filas_kpss = []

    print("\nESTACIONARIEDAD — prueba KPSS")
    print("  H0: la serie es estacionaria alrededor de un nivel o tendencia.")
    print("  Nivel de significancia: 0.05")

    for nombre, regresion in casos_kpss:

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InterpolationWarning)

            estadistico, p, rezagos, valores_criticos = kpss(
                serie,
                regression=regresion,
                nlags="auto"
            )

        rechaza_h0 = p < 0.05

        filas_kpss.append({
            "prueba": nombre,
            "regresion": regresion,
            "estadistico_kpss": estadistico,
            "valor_p": p,
            "rezagos": rezagos,
            "rechaza_h0_5pct": rechaza_h0
        })

        veredicto = "rechaza H0" if rechaza_h0 else "no rechaza H0"

        print(
            f"  KPSS {nombre:<10} "
            f"estadístico={estadistico:.4f}  "
            f"p={p:.5f}  "
            f"rezagos={rezagos}  "
            f"{veredicto}"
        )

    pd.DataFrame(filas_kpss).to_csv(
        RESULTADOS / "kpss.csv",
        index=False
    )

    # Selección documentada de la serie del grupo, no regla automática universal:
    # los dos ADF de la serie original rechazan H0 y no hay evidencia sólida
    # de raíz unitaria estacional. La dependencia anual se modelará con (P,Q).
    d, D = 0, 0
    transformada = serie.copy()
    print(f"  Selección inicial: d={d}, D={D} (sin diferenciación).")
    print("  Criterio: ADF original rechaza raíz unitaria (con y sin tendencia); "
          "la diferencia estacional NO demuestra por sí sola que D=1 sea necesario.")
    print("  Precaución: solo cuatro ciclos anuales; ADF no verifica "
          "estacionariedad estricta ni raíces unitarias estacionales.")

    # Para una PACF válida con 48 observaciones: nlags debe ser < n/2.
    n = len(transformada)
    max_acf = min(24, n - 1)
    max_pacf = min(24, n // 2 - 1)
    if max_pacf < 1:
        raise ValueError("No hay observaciones suficientes para calcular la PACF.")
    valores_acf = acf(transformada, nlags=max_acf, fft=False)
    valores_pacf = pacf(transformada, nlags=max_pacf, method="ywm")
    # Bandas blancas aproximadas: se usan solo para identificación exploratoria.
    banda = 1.96 / np.sqrt(n)
    relevantes_acf = [(i, round(float(v), 3)) for i, v in
                      enumerate(valores_acf[1:], start=1) if abs(v) > banda]
    relevantes_pacf = [(i, round(float(v), 3)) for i, v in
                       enumerate(valores_pacf[1:], start=1) if abs(v) > banda]
    print(f"  Banda exploratoria aprox. 95 %: ±{banda:.3f}")
    print(f"  ACF: rezagos sobre la banda: {relevantes_acf}")
    print(f"  PACF: rezagos sobre la banda: {relevantes_pacf}")
    print("  Candidatos de partida: componente AR(1), componente estacional "
          "AR(1) en rezago 12; comparar también términos MA por AIC.")

    fig, ejes = plt.subplots(2, 1, figsize=(10, 7.2), sharex=False)
    plot_acf(transformada, lags=max_acf, ax=ejes[0], alpha=0.05,
             bartlett_confint=False, zero=False)
    plot_pacf(transformada, lags=max_pacf, ax=ejes[1], alpha=0.05,
              method="ywm", zero=False)
    for eje, titulo in zip(ejes, ["ACF — serie elegida (d=0, D=0)",
                                  "PACF — serie elegida (d=0, D=0)"]):
        eje.set_title(titulo, loc="center", fontsize=12)
        eje.axvline(PERIODO, color="gray", linestyle="--", alpha=0.7,
                    linewidth=1.0, label="Rezago estacional = 12")
        eje.axhline(0, color="gray", linewidth=0.7)
        eje.set_xlabel("Rezago (meses)")
        eje.set_ylabel("Correlación")
        eje.grid(axis="y", alpha=0.2)
        eje.legend(loc="upper right", fontsize=8)
    fig.suptitle("Identificación de dependencias mensuales y anuales",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(FIGURAS / "acf_pacf.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return d, D


# ============================================================
# 4. Modelos clásicos
# ============================================================
# Cada modelo es una función modelo(entrenamiento, h) que devuelve h
# pronósticos y solo usa `entrenamiento`. Así entra al backtest común.

# Escala de trabajo: la estimación se hace en decenas de pares y el
# pronóstico se convierte a pares originales antes de medir el error.
# Una escala positiva no cambia el patrón ni las métricas en pares.
ESCALA = 10.0


def _ajustar_arima(entrenamiento, orden, orden_estacional, exog=None):
    """Ajusta ARIMA/SARIMA/SARIMAX solo con el tramo de entrenamiento."""
    from statsmodels.tsa.arima.model import ARIMA

    if len(entrenamiento) < 2 * PERIODO:
        raise ValueError("Se necesitan por lo menos dos ciclos para el ajuste.")
    # d=D=0 en la serie actual: se incluye constante para la media no nula.
    tendencia = "c" if orden[1] == 0 and orden_estacional[1] == 0 else "n"
    resultado = ARIMA(
        entrenamiento.astype(float) / ESCALA,
        order=orden,
        seasonal_order=orden_estacional,
        exog=exog,
        trend=tendencia,
        enforce_stationarity=True,
        enforce_invertibility=True,
    ).fit(method_kwargs={"maxiter": 120})
    return resultado


def elegir_sarima(serie, d, D):
    """Rejilla (p,q,P,Q) en {0,1}, AIC y Ljung-Box del mejor convergido.

    Se seleccionan órdenes con TODA la serie a título exploratorio. El
    backtest reestima parámetros en cada origen, pero mantiene estos órdenes:
    esta elección previa sí ve fechas posteriores y se advierte en el informe.
    """
    from itertools import product
    from statsmodels.graphics.tsaplots import plot_acf
    from statsmodels.stats.diagnostic import acorr_ljungbox

    seleccionar órdenes sin mirar meses posteriores
    # al primer origen de backtesting (24 meses de entrenamiento).
    
    primeros_meses = len(serie) - 24  # comun.backtest: n_prueba=24
    serie_seleccion = serie.iloc[:primeros_meses]
    if len(serie_seleccion) < 2 * PERIODO:
        raise ValueError("El primer origen no tiene dos ciclos estacionales.")
    print(f"  Ventana AIC sin anticipación: {serie_seleccion.index[0]:%Y-%m} "
          f"a {serie_seleccion.index[-1]:%Y-%m} ({len(serie_seleccion)} meses)")
    # Comprobación de d=0 en el mismo periodo, no en los 48 meses.
    # D=0 es una decisión preespecificada por parsimonia; no pretende
    # descartar formalmente una raíz unitaria estacional.
    from statsmodels.tsa.stattools import adfuller
    p_adf_inicial = adfuller(serie_seleccion, regression="c", autolag="AIC")[1]
    print(f"  ADF solo ventana inicial: p={p_adf_inicial:.6g}; "
          f"d={d}, D={D} predefinidos y documentados")

    filas = []
    print("\nMODELOS — rejilla SARIMA pequeña (16 especificaciones)")
    for p, q, P, Q in product((0, 1), repeat=4):
        orden = (p, d, q)
        estacional = (P, D, Q, PERIODO)
        try:
            ajuste = _ajustar_arima(serie, orden, estacional)
            convergio = bool(ajuste.mle_retvals.get("converged", False))
            aic = float(ajuste.aic)
            filas.append({
                "order": str(orden), "seasonal_order": str(estacional),
                "p": p, "q": q, "P": P, "Q": Q,
                "AIC": aic, "convergio": convergio, "error": "",
            })
            print(f"  {orden!s:>9} x {estacional!s:<14} "
                  f"AIC={aic:>8.2f}  {'OK' if convergio else 'NO CONVERGIO'}")
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
            filas.append({
                "order": str(orden), "seasonal_order": str(estacional),
                "p": p, "q": q, "P": P, "Q": Q,
                "AIC": np.nan, "convergio": False, "error": str(exc),
            })
            print(f"  {orden} x {estacional}: fallo ({exc})")

    tabla = pd.DataFrame(filas).sort_values("AIC", na_position="last")
    tabla.to_csv(RESULTADOS / "rejilla_aic.csv", index=False)
    candidatos = tabla[tabla["convergio"] & tabla["AIC"].notna()]
    if candidatos.empty:
        raise RuntimeError("No convergió ningún SARIMA de la rejilla.")
    ganador = candidatos.iloc[0]
    orden = (int(ganador.p), int(d), int(ganador.q))
    estacional = (int(ganador.P), int(D), int(ganador.Q), PERIODO)
    ajuste = _ajustar_arima(serie_seleccion, orden, estacional)
    print(f"  Ganador por AIC convergido: SARIMA{orden}{estacional}; "
          f"AIC={ajuste.aic:.4f}")

    # Ljung-Box: H0 = ausencia de autocorrelación hasta cada rezago.
    # Ajustamos grados de libertad por términos AR/MA estimados.
    # No descontamos la constante del modelo.
    grados = orden[0] + orden[2] + estacional[0] + estacional[2]
    residuos = pd.Series(ajuste.resid * ESCALA, index=serie.index, name="residuo_pares")
    lb = acorr_ljungbox(
        residuos, lags=[PERIODO, 2 * PERIODO],
        model_df=grados, return_df=True,
    )
    lb.index.name = "rezago"
    lb.to_csv(RESULTADOS / "ljung_box.csv")
    print(f"  Ljung-Box (grados AR/MA descontados: {grados}):")
    for rezago, fila_lb in lb.iterrows():
        print(f"    rezago {rezago:>2}: Q={fila_lb['lb_stat']:.4f}; "
              f"p={fila_lb['lb_pvalue']:.6f}")

    fig, ejes = plt.subplots(2, 1, figsize=(10, 6.6))
    ejes[0].plot(residuos.index, residuos.to_numpy(), linewidth=1.4)
    ejes[0].axhline(0, color="gray", linewidth=0.9)
    ejes[0].set_title("Residuos SARIMA (pares netos)")
    ejes[0].set_ylabel("Error de ajuste")
    ejes[0].grid(alpha=0.2)
    plot_acf(residuos, ax=ejes[1], lags=min(24, len(residuos) - 1),
             alpha=0.05, zero=False)
    ejes[1].set_title("Autocorrelación de los residuos (ACF)")
    ejes[1].set_xlabel("Rezago mensual")
    ejes[1].grid(axis="y", alpha=0.2)
    fig.suptitle(f"Diagnóstico: SARIMA{orden}{estacional}", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(FIGURAS / "residuos.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return orden, estacional


def modelo_sarima(orden, orden_estacional):
    """Modelo entrenado desde cero en cada origen, sin observar el futuro."""
    def pronosticar(entrenamiento, h):
        ajuste = _ajustar_arima(entrenamiento, orden, orden_estacional)
        pred = np.asarray(ajuste.forecast(steps=h), dtype=float) * ESCALA
        if len(pred) != h or not np.isfinite(pred).all():
            raise ValueError("SARIMA no produjo h pronósticos finitos.")
        return pred
    return pronosticar


def _lunes_siguiente(fecha):
    """Traslado de festivos colombianos según Ley 51 de 1983."""
    from datetime import timedelta
    return fecha + timedelta(days=(7 - fecha.weekday()) % 7)


def _festivos_colombia_anio(anio):
    """Festivos nacionales de descanso remunerado; calendario conocido ex ante.

    Implementación local de la Ley 51 de 1983: fijos, trasladados al lunes
    y móviles de Semana Santa. No requiere conexión ni dependencias nuevas.
    """
    from datetime import date, timedelta
    from dateutil.easter import easter

    pascua = easter(anio)
    fijos = [(1, 1), (5, 1), (7, 20), (8, 7), (12, 8), (12, 25)]
    trasladados = [(1, 6), (3, 19), (6, 29), (8, 15), (10, 12),
                   (11, 1), (11, 11)]
    fechas = {date(anio, m, d) for m, d in fijos}
    fechas |= {_lunes_siguiente(date(anio, m, d)) for m, d in trasladados}
    fechas |= {pascua - timedelta(days=3), pascua - timedelta(days=2)}
    # Ascensión (39), Corpus (60) y Sagrado Corazón (68): lunes siguiente.
    fechas |= {_lunes_siguiente(pascua + timedelta(days=d))
               for d in (39, 60, 68)}
    return fechas


def exogenas(serie):
    """Conteo mensual de días festivos de Colombia, con 12 meses futuros.

    Solo usa el calendario legal y el índice temporal, no ventas futuras.
    No requiere internet ni el paquete opcional 'holidays'.
    """
    fechas = pd.date_range(serie.index[0], periods=len(serie) + PERIODO,
                           freq="MS")
    anios = range(fechas[0].year, fechas[-1].year + 1)
    calendario = set().union(*(_festivos_colombia_anio(anio) for anio in anios))
    conteo = pd.Series(0.0, index=fechas, name="festivos")
    for fecha in calendario:
        mes = pd.Timestamp(fecha).replace(day=1)
        if mes in conteo.index:
            conteo.loc[mes] += 1
    if conteo.isna().any() or len(conteo) != len(serie) + PERIODO:
        raise ValueError("El calendario de festivos tiene cobertura incorrecta.")
    x = conteo.to_frame()
    x.to_csv(RESULTADOS / "festivos_mensuales.csv", index_label="mes")
    print("\nEXÓGENA — festivos legales de Colombia por mes")
    print(f"  Cobertura: {fechas.min():%Y-%m} a {fechas.max():%Y-%m} "
          f"({len(x)} meses, incluidos 12 meses futuros)")
    print("  Fuente normativa: Ley 51 de 1983; la exógena es conocida antes de pronosticar.")
    print("  Totales por año:",
          {int(k): int(v) for k, v in x['festivos'].groupby(x.index.year).sum().items()})
    return x


def modelo_sarimax(orden, orden_estacional, x):
    """Modelo con festivos conocidos en cada origen y horizonte de pronóstico."""
    if not isinstance(x, pd.DataFrame) or list(x.columns) != ["festivos"]:
        raise ValueError("Se espera exógena DataFrame con columna 'festivos'.")
    def pronosticar(entrenamiento, h):
        futuro = fechas_siguientes(entrenamiento, h)
        x_entrenamiento = x.loc[entrenamiento.index]
        x_futuro = x.loc[futuro]
        if len(x_entrenamiento) != len(entrenamiento) or len(x_futuro) != h:
            raise ValueError("La exógena no cubre entrenamiento y horizonte.")
        ajuste = _ajustar_arima(entrenamiento, orden, orden_estacional,
                               exog=x_entrenamiento)
        pred = np.asarray(ajuste.forecast(steps=h, exog=x_futuro), dtype=float) * ESCALA
        if len(pred) != h or not np.isfinite(pred).all():
            raise ValueError("SARIMAX no produjo h pronósticos finitos.")
        return pred
    return pronosticar


# ============================================================
# 5. La tabla de métricas
# ============================================================

def fila(nombre, serie, modelo, detalles=None):
    por_origen, promedio = backtest(serie, modelo)
    # Aporte de Edison: guardar también el detalle por origen para auditoría.
    if detalles is not None:
        detalle = por_origen.copy()
        detalle.insert(0, "modelo", nombre)
        detalles.append(detalle)
    return {"modelo": nombre, "decision": DECISION,
            "RMSE": round(promedio["RMSE"], 2), "MAE": round(promedio["MAE"], 2),
            "MAPE": round(promedio["MAPE"], 2)}


def pendiente(parte, error):
    print(f"  pendiente: {parte} ({error})")


def main():
    cruda = cargar_serie(ARCHIVO, FECHA, VALOR)
    print(f"Serie: {len(cruda)} meses, de {cruda.index[0]:%Y-%m} a "
          f"{cruda.index[-1]:%Y-%m}, {cruda.isna().sum()} vacíos")
    serie = preparar(cruda)
    graficar_serie(serie)

    filas = [fila("ingenuo", serie, ingenuo),
             fila("estacional ingenuo", serie,
                  lambda t, h: estacional_ingenuo(t, h, PERIODO))]

    try:
        descomponer(serie)
    except NotImplementedError as error:
        pendiente("parte 2", error)

    try:
        d, D = estacionariedad(serie)
    except NotImplementedError as error:
        pendiente("parte 3", error)
        d = D = None

    if d is not None:
        try:
            orden, estacional = elegir_sarima(serie, d, D)
            filas.append(fila(f"SARIMA{orden}{estacional}", serie,
                              modelo_sarima(orden, estacional), detalles))
            x = exogenas(serie)
            ajuste_exog = _ajustar_arima(
                serie, orden, estacional, exog=x.loc[serie.index]
            )
            if "festivos" not in ajuste_exog.params.index:
                raise ValueError("No se encontró el coeficiente de festivos.")
            beta = float(ajuste_exog.params["festivos"]) * ESCALA
            p_festivos = float(ajuste_exog.pvalues["festivos"])
            pd.DataFrame([{
                "variable": "festivos", "beta_pares_por_festivo": beta,
                "valor_p": p_festivos, "AIC_ajuste": float(ajuste_exog.aic),
            }]).to_csv(RESULTADOS / "efecto_festivos.csv", index=False)
            print(f"  Efecto estimado festivos: {beta:+.2f} pares por festivo; "
                  f"p={p_festivos:.6f}")
            filas.append(fila(f"SARIMAX{orden}{estacional} + exógenas", serie,
                              modelo_sarimax(orden, estacional, x), detalles))

        except NotImplementedError as error:
            pendiente("parte 4", error)

    pd.concat(detalles, ignore_index=True).to_csv(
        RESULTADOS / "backtest_por_origen.csv", index=False
    )

    tabla = pd.DataFrame(filas).sort_values("RMSE")
    tabla.to_csv(RESULTADOS / "metricas.csv", index=False)
    # Vista ilustrativa del último origen: pronosticar 2025 desde dic-2024.
    # La línea base estacional no requiere estimación y es libre de fuga.
    real_2025 = serie.iloc[-PERIODO:]
    previsto_2025 = estacional_ingenuo(serie.iloc[:-PERIODO], PERIODO)
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(real_2025.index, real_2025.to_numpy(), marker="o",
            label="Ventas reales 2025")
    ax.plot(real_2025.index, previsto_2025, marker="s", linestyle="--",
            label="Pronóstico estacional ingenuo")
    ax.set_title("Validación: pronóstico del último año con datos hasta 2024")
    ax.set_ylabel("Pares netos")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIGURAS / "validacion_2025.png", dpi=150)
    plt.close(fig)
    print(f"  Último origen: ventas 2025={real_2025.sum():.0f}; "
          f"previsto estacional={sum(previsto_2025):.0f}")
    print(tabla.drop(columns="decision").to_string(index=False))
    print("Mejor modelo por RMSE:", tabla.iloc[0]["modelo"])


if __name__ == "__main__":
    main()
