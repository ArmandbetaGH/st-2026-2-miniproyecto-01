# Ficha de datos — ventas mensuales netas de calzado (V2)

| Campo | Información |
|---|---|
| Archivo | `ventas_calzado_mensual_V2.csv` |
| Qué mide | Cantidad **mensual de pares netos** vendidos, incluyendo devoluciones con signo negativo en la consolidación de origen |
| Origen | Dataset empresarial anonimizado `ventas_consolidadas_2022_2025_V2.xlsx`, hoja `Detalle`, aportado por el grupo |
| Fuente y enlace | La empresa autorizó divulgar los datos mensuales agregados en este repositorio académico. No se ha declarado una licencia abierta que permita su reutilización por terceros. La autorización del profesor para usar 48 observaciones corresponde al requisito de extensión de la serie.|
| Autorización | Según confirmación del grupo, la empresa **autorizó la publicación pública** de los datos mensuales agregados para el miniproyecto; no se publican registros individuales ni identificadores de clientes |
| Licencia y reutilización | Existe autorización empresarial para divulgar estos agregados en el repositorio académico; **no se ha informado una licencia abierta para su reutilización por terceros**. La aceptación de este régimen frente a la rúbrica está pendiente de confirmación del docente |
| Enlace público | `https://github.com/ArmandbetaGH/st-2026-2-miniproyecto-01/blob/main/datos/ventas_calzado_mensual_V2.csv` |
| Frecuencia | Mensual (`MS`, primer día del mes como etiqueta) |
| Periodo | Enero 2022 a diciembre 2025 (48 observaciones consecutivas) |
| Columna de fecha | `mes` |
| Columna objetivo | `pares_netos` |
| Tratamiento | Suma mensual de `Pares`; devoluciones negativas conservadas; sin imputación ni eliminación de meses |
| Autorización académica | Se confirmó que es válido utilizar la serie de 48 observaciones mensuales para el desarrollo del Miniproyecto 1. |

## Calidad y decisiones

La serie comprende 48 meses consecutivos, sin valores nulos y con **93.411 pares netos** acumulados. La inspección global con el método IQR (1,5 × rango intercuartílico) no señala meses fuera de sus límites; esto **no descarta** comportamientos comerciales atípicos. Los valores bajos de mayo y diciembre de 2025 merecen interpretación de negocio y se conservan mientras no exista soporte que justifique corregirlos.

**Estado de publicación:** los datos mensuales agregados están publicados en el repositorio académico con autorización empresarial. Se confirma que es válido trabajar con 48 observaciones para este miniproyecto, según correo electrónico del 30 de octubre de 2026. La información no dispone de una licencia abierta de reutilización por terceros.
