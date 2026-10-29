# Ficha de datos — ventas mensuales netas de calzado (V2)

| Campo | Información |
|---|---|
| Archivo | `ventas_calzado_mensual_V2.csv` |
| Qué mide | Cantidad **mensual de pares netos** vendidos, incluyendo devoluciones con signo negativo en la consolidación de origen |
| Origen | Dataset empresarial anonimizado `ventas_consolidadas_2022_2025_V2.xlsx`, hoja `Detalle`, aportado por el grupo |
| Fuente y enlace | Fuente empresarial original no publicada; la serie **mensual agregada y anonimizada** se hará pública en este repositorio: `datos/ventas_calzado_mensual_V2.csv` |
| Autorización | Según confirmación del grupo, la empresa **autorizó la publicación pública** de los datos mensuales agregados para el miniproyecto; no se publican registros individuales ni identificadores de clientes |
| Licencia y reutilización | Existe autorización empresarial para divulgar estos agregados en el repositorio académico; **no se ha informado una licencia abierta para su reutilización por terceros**. La aceptación de este régimen frente a la rúbrica está pendiente de confirmación del docente |
| Enlace público previsto | `https://github.com/ArmandbetaGH/st-2026-2-miniproyecto-01/blob/main/datos/ventas_calzado_mensual_V2.csv` (estará disponible cuando la rama se integre a `main`) |
| Frecuencia | Mensual (`MS`, primer día del mes como etiqueta) |
| Periodo | Enero 2022 a diciembre 2025 (48 observaciones consecutivas) |
| Columna de fecha | `mes` |
| Columna objetivo | `pares_netos` |
| Tratamiento | Suma mensual de `Pares`; devoluciones negativas conservadas; sin imputación ni eliminación de meses |
| Limitación académica | 48 meses disponibles frente al mínimo de 60 solicitado; pendiente respuesta del profesor |

## Calidad y decisiones

La serie comprende 48 meses consecutivos, sin valores nulos y con **93.411 pares netos** acumulados. La inspección global con el método IQR (1,5 × rango intercuartílico) no señala meses fuera de sus límites; esto **no descarta** comportamientos comerciales atípicos. Los valores bajos de mayo y diciembre de 2025 merecen interpretación de negocio y se conservan mientras no exista soporte que justifique corregirlos.

**Estado de publicación:** el grupo ha confirmado autorización empresarial para divulgar los agregados mensuales; persiste la consulta al docente por los 48 meses (frente a 60) y por la ausencia de una licencia abierta de reutilización.
