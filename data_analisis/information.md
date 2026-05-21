# Análisis REVER — Conclusiones y decisiones

---

## 1. Alcance temporal: solo 2025

**Decisión:** el análisis se centra únicamente en datos de 2025.

**Motivo:** los ficheros de REVER (`invoiced_logistics2025.csv` e `invoiced_logistics_adjustments2025.csv`) solo cubren de enero a diciembre de 2025. Los carriers tienen datos de 2025 y parte de 2026, pero sin la contraparte de REVER en 2026 no podemos calcular márgenes. El 2026 se descarta por ahora.

---

## 2. Qué contienen los ficheros de REVER

### `invoiced_logistics2025.csv` — ~295.000 filas
Lo que **REVER factura a sus merchants** por cada envío de devolución.

| Campo | Descripción |
|---|---|
| `invoicing_period` | Período mensual de facturación (M 2025-08-01 - 2025-08-31) |
| `stripe_cust_id` | ID del merchant (cliente en Stripe) |
| `process_id` | ID interno del proceso de devolución en REVER |
| `customer_printed_order_id` | Referencia del pedido del merchant |
| `tracking_id` | Número de seguimiento del paquete — **clave de cruce con carriers** |
| `country_iso` | País desde donde viene la devolución |
| `return_method` | DROP_OFF_POINT / HOME_PICK_UP / DELIVERY_PICKUP |
| `subtotal` | Importe sin IVA facturado al merchant |
| `vat` | IVA |
| `total` | Total con IVA |
| `logistic_cost` | Coste logístico base |
| `custom_cost` | Coste adicional personalizado |

**Distribución por país:** ES (48%), IT (20%), FR (9%), DE (6%), US (4%), GB (3%)...

**Distribución por método:** DROP_OFF_POINT (76%), HOME_PICK_UP (23%), DELIVERY_PICKUP (1%)

### `invoiced_logistics_adjustments2025.csv` — ~121.000 filas
**Ajustes y cargos extra** que los carriers repercuten y REVER pasa al merchant.

Campos clave adicionales: `carrier`, `type` (tipo de ajuste), `process_weight`, `billed_weight`.

---

## 3. Los carriers — formatos y cobertura 2025

Hay 5 carpetas de carriers. Cada una tiene un formato de fichero distinto.

| Carrier | Formato | Ficheros | Cobertura 2025 |
|---|---|---|---|
| BRT | CSV (separador `;`, encoding latin-1) | 1 por mes | Ene–Dic (9 ficheros) |
| Correos | TXT (separador `¬`) + Excel resumen | 1 TXT por mes + All orders 2025.xlsx | Ago–Dic (TXT) / Ene–Dic (Excel) |
| Correos Express | Excel (.xlsx) | 1 por mes | Dic 2024–Feb 2026 |
| GLS | Excel (.xlsx) + CSV resumen | 4 xlsx + 1 csv | Sep–Dic 2025 (xlsx) / Abr–Ago 2025 (csv) |
| UPS | Excel único (.xlsx) | 1 fichero con todo | Ene 2025–Ene 2026 |

---

## 4. Cómo se relacionan carriers con REVER

La clave de cruce es el **`tracking_id`** — el número de seguimiento del paquete. Está en los datos de REVER y en los datos de cada carrier (con nombres de columna distintos según el carrier).

**Tasas de match (tracking_id carrier vs REVER 2025):**

| Carrier | Match | Sobre total carrier |
|---|---|---|
| Correos (Excel) | 95.1% | 101.710 / 106.940 |
| Correos Express | ~93% | muestra representativa |
| UPS | 95.3% | 114.517 / 120.166 |
| GLS | compatible | dataset pequeño (~290 filas) |
| **BRT** | **0%** | 0 / ~41.000 |

---

## 5. El gap del ~5% (carriers distintos de BRT)

El ~5% de envíos de carrier que **no aparece en REVER** no es un fallo de datos. Es una ineficiencia del negocio analíticamente relevante.

**Ejemplo analizado en Correos:** de 5.230 sin match:
- 645 sí están en REVER, pero en el fichero de **ajustes** (no en el principal)
- 4.585 no aparecen en **ningún** fichero de REVER

Los 4.585 son envíos que Correos cobró a REVER pero REVER **nunca facturó al merchant**: etiquetas impresas y no usadas, devoluciones canceladas, pérdidas/daños que REVER absorbió, envíos gratuitos. Este coste es un **margen negativo directo para REVER**.

---

## 6. BRT — problema de tracking y conclusiones

### Por qué BRT no cruza con REVER

La factura de BRT usa `NUMERO SPED.` (número interno de 6 dígitos: `123210`, `92326`...). REVER almacena el barcode completo del paquete en formato `1ZA2F6229...` (18 caracteres, formato UPS). Son incompatibles.

### El campo SEGNAC. — la pista que no resuelve el problema

BRT sí tiene una columna con el barcode real: `SEGNAC.` (segnacolo = código de barras en italiano), con valores como `089067018421041216`. Los ajustes de REVER para BRT usan exactamente ese formato (`089143018415534158`). Sin embargo, el match entre `SEGNAC.` y el `tracking_id` de REVER principal es solo del **2.1%**.

### Por qué el match es solo del 2%

Los envíos BRT van en un **98% a merchants italianos** (ej: `GEFF SRL - #7981`, `G.S. GRUPPO MODA SRL - #38867`). Son **devoluciones domésticas dentro de Italia** (cliente IT → merchant IT). Este flujo no pasa por el pipeline de facturación estándar de REVER de la misma forma.

### Teoría BRT + UPS (descartada por los datos)

Se planteó si BRT podría ser la última milla de los envíos UPS a Italia. Analizando los volúmenes mensuales, el ratio BRT/UPS varía de 0.10 a 3.01 — si fueran los mismos envíos debería ser ~1.0 siempre. **No son los mismos envíos.**

**BRT gestiona devoluciones domésticas italianas. UPS gestiona el tramo cross-border.** Son contratos y flujos independientes.

### Perfil corporativo de BRT (confirmado con fuentes externas)

BRT (antes **Bartolini**, fundado en 1928 en Bolonia) es el carrier de paquetería líder en Italia. En 2022 adoptó el branding de **DPD Group / Geopost**, la división de entrega exprés de La Poste (Francia). Opera con más de 200 delegaciones en Italia y 12.350+ puntos de recogida BRT-fermopoint. Los envíos internacionales se canalizan a través de la red DPD.

> Esto confirma por qué BRT solo opera devoluciones domésticas dentro de Italia: su estructura está diseñada para el mercado italiano. Las devoluciones cross-border de merchants italianos al extranjero van por UPS/DPD, no por BRT.

Fuentes: [BRT About Us](https://www.brt.it/en/about-us/) · [BRT en La Poste Groupe](https://www.lapostegroupe.com/en/focus/la-poste-groupes-subsidiaries/brt) · [BRT Bartolini (DPD) — Eurosender](https://www.eurosender.com/en/courier-companies/brt)

### Qué podemos saber de BRT

| Análisis | Posible |
|---|---|
| Coste total mensual | ✅ |
| Coste medio por envío (~4.86€) | ✅ |
| Tendencia de volumen (envíos/mes) | ✅ |
| Coste por envío individual cruzado con margen REVER | ❌ |

**BRT total 2025:** 200.424 EUR para 41.235 envíos.

---

---

# Preguntas del análisis

Las preguntas están organizadas por bloques temáticos. Cuando una pregunta explica el **por qué** del resultado de otra, aparece anidada debajo con la etiqueta **→ Porque:**

---

## BLOQUE A — Margen y rentabilidad global

**A1. ¿Cuál es el beneficio total obtenido en 2025?**
Comparar la suma de lo facturado a merchants (REVER invoiced) contra la suma de costes de carrier. Resultado = margen bruto total del negocio.

**A2. ¿Cuál es el margen medio por envío en euros?**
Margen total dividido entre número de envíos. Da la foto de cuánto gana REVER por cada devolución gestionada.

> **→ Porque: ¿El volumen alto de envíos se traduce en mejor margen, o solo en más coste?**
> Si el margen por envío baja a medida que sube el volumen, puede indicar que los carriers no dan descuentos por volumen o que REVER no repercute correctamente el coste adicional al merchant.

**A3. ¿Los precios que REVER cobra a los merchants han subido al mismo ritmo que los costes de carrier?**
Comparar la evolución mensual del coste medio de carrier vs el precio medio facturado al merchant. Si los costes suben más rápido que los precios, el margen se comprime con el tiempo.

**A4. ¿Hay envíos con coste cero o precio cero que no deberían existir?**
Detectar anomalías: envíos que tienen coste de carrier pero precio 0 al merchant (pérdida segura), o precio al merchant pero coste 0 de carrier (dato incompleto).

---

## BLOQUE B — Análisis por carrier

**B1. ¿Con qué carrier hemos ganado más dinero? ¿Y menos?**
Margen total y medio por carrier. Identifica qué carriers son más rentables para REVER.

> **→ Porque: ¿El carrier con menor margen es caro, o es que gestiona rutas inherentemente más costosas?**
> Ver B3 (coste por tipo de envío) y C1 (margen por país) para separar si el problema es el carrier en sí o el tipo de ruta que le asignamos.

**B2. ¿Con qué carrier tenemos menor coste logístico base?**
Comparar el `logistic_cost` medio por carrier. Revela qué contratos son más favorables en tarifa base.

> **→ Porque: ¿Con qué carrier tenemos mayor o menor coste adicional personalizado (`custom_cost`)?**
> Un carrier puede tener tarifa base baja pero costes adicionales altos. Hay que verlos sumados para tener el coste real.

**B3. ¿Los precios de cada carrier son consistentes o varían mucho para el mismo tipo de envío?**
Medir la desviación estándar del coste por envío dentro de cada carrier, para envíos similares (mismo país, mismo peso aproximado). Alta variabilidad = pricing poco predecible = riesgo operacional.

**B4. ¿Dependemos demasiado de un solo carrier?**
Calcular el % de envíos y el % de coste total que representa cada carrier. Si un carrier acapara más del 60-70%, hay riesgo de concentración.

**B5. ¿Hay un carrier que claramente sale caro para cierto tipo de envíos y donde se podría sustituir?**
Cruzar carrier × país × return_method × coste medio. Si un carrier es sistemáticamente más caro en una combinación específica donde otro carrier también opera, hay oportunidad de optimización.

**B6. ¿Con qué carrier tenemos mayor o menor diferencia entre peso real y peso facturado?**
Si el peso facturado es sistemáticamente mayor que el real en un carrier, ese carrier está cobrando de más por redondeo o por tarifas de peso mínimo.

---

## BLOQUE C — Análisis por merchant

**C1. ¿Con qué merchant hemos ganado más dinero? ¿Y menos?**
Margen total y medio por merchant (agrupando por `stripe_cust_id`).

> **→ Porque: ¿Con los merchants que más/menos ganamos, qué carriers hemos usado?**
> Si un merchant con margen bajo usa un carrier caro, puede ser una decisión de asignación de carrier que se puede corregir.

> **→ Porque: ¿Qué merchant tiene los envíos con mayor peso? ¿Y menor?**
> Los envíos pesados son más caros para el carrier. Si un merchant genera envíos muy pesados y el precio que paga no refleja ese coste, el margen será bajo por diseño.

**C2. ¿Qué merchant tiene el mejor perfil (alto volumen + alto margen)?**
Los merchants estratégicos: generan muchos envíos y dejan buen margen. Merecen atención y fidelización.

**C3. ¿Qué merchants son "losers" claros (bajo volumen + bajo margen)?**
Merchants que consumen recursos operacionales sin retorno. Candidatos a repriorizar o renegociar contrato.

**C4. ¿Hay merchants que llevan meses sin volumen? ¿Están en churn?**
Detectar merchants que eran activos y han parado de enviar. Señal de abandono de la plataforma.

**C5. ¿Qué merchant tiene un ratio de ajustes muy alto sobre su facturación total?**
Si un merchant acumula muchos ajustes (sobrepeso, zonas remotas, etc.), puede indicar que sus clientes envían paquetes con características que disparan los surcharges de los carriers.

> **→ Porque: ¿Con qué carrier y merchant tenemos mayor o menor diferencia peso real vs peso facturado?**
> Un merchant con mucho ajuste por peso combinado con un carrier que factura con redondeo agresivo es la combinación más costosa.

---

## BLOQUE D — Cruce carrier × merchant

**D1. ¿Con qué combinación carrier + merchant hemos ganado más o menos?**
La tabla de margen cruzado: filas = merchants, columnas = carriers, valor = margen medio. Revela si ciertos merchants van mejor con ciertos carriers.

**D2. ¿Qué carrier genera mayor peso a menor coste por merchant?**
Detectar si hay carriers que ofrecen mejor eficiencia en coste/kg para determinados merchants. Base para decisiones de asignación.

**D3. ¿Con qué carrier y merchant tenemos mayor o menor coste adicional personalizado?**
Algunos merchants pueden tener `custom_cost` alto porque tienen acuerdos especiales o porque se les repercuten más surcharges. Cruzado con carrier, revela si el problema es el merchant, el carrier, o la combinación.

---

## BLOQUE E — Dimensión temporal y geográfica

**E1. ¿Qué mes se ha facturado más? ¿Hay meses consistentemente menos rentables?**
Volumen y margen por mes. Estacionalidad del negocio.

> **→ Porque: ¿El crecimiento de volumen va acompañado de crecimiento de margen, o solo de coste?**
> Si en los meses de mayor volumen el margen por envío baja, los carriers no están dando descuentos por volumen y/o REVER no los traslada al precio.

**E2. ¿En qué país se ha facturado más?**
Volumen y margen por `country_iso`. Identifica los mercados más importantes.

> **→ Porque: ¿En qué país por carrier y por merchant?**
> Un carrier puede ser muy eficiente en España y caro en Italia. Un merchant puede operar mucho en Francia pero con margen bajo. El cruce da el detalle.

---

## BLOQUE F — Return method

**F1. ¿Con qué return_method hemos ganado más? ¿Qué rutas o tipos de devolución son más o menos rentables?**
Margen por DROP_OFF_POINT vs HOME_PICK_UP vs DELIVERY_PICKUP.

> **→ Porque: ¿Con qué carrier hemos ganado más usando cada tipo de return method?**
> HOME_PICK_UP suele ser más caro para el carrier (requiere recogida activa). Si un carrier cobra mucho por ello y REVER no lo repercute bien al merchant, es una fuente de margen negativo.

> **→ Porque: ¿Con qué merchant hemos ganado más usando cada tipo de return method?**
> Algunos merchants pueden tener acordado HOME_PICK_UP para todos sus clientes. Si ese método es deficitario, el merchant concreto es la causa del problema.

> **→ Porque: ¿Con qué combinación carrier + merchant + return_method hemos ganado más o menos?**
> El nivel más granular. Permite detectar combinaciones muy específicas que destrozan el margen.

---

## BLOQUE G — Ajustes

**G1. ¿Qué tipo de ajuste es el más costoso en total?**
Ranking de tipos de ajuste (Weight Adjustment, Peak Surcharge, Over Maximum Size...) por importe total. Muestra dónde se va el dinero en costes no previstos.

> **→ Porque: ¿Qué tipo de ajuste es el más costoso en cada carrier?**
> Cada carrier tiene sus propias políticas de ajuste. UPS puede cobrar mucho por zonas remotas, Correos por exceso de peso. Saber qué cobra cada uno permite negociar mejor.

> **→ Porque: ¿Qué tipo de ajuste es el más costoso en cada merchant y carrier?**
> Si un merchant genera sistemáticamente ajustes de un tipo concreto con un carrier concreto, o bien el merchant puede cambiar su comportamiento (embalajes más pequeños), o bien hay que cambiar de carrier para ese merchant.

**G2. ¿Qué merchant tiene un ratio de ajustes muy alto sobre su facturación total?**
(Ver también C5) Merchants donde los ajustes representan más de X% de lo que se les factura. Pueden estar siendo subvalorados en precio base y compensado con ajustes imprevistos.

---

## BLOQUE H — Gaps e integridad de datos

**H1. ¿Hay envíos en los costes de carrier que no aparecen en la facturación al merchant?**
Pedidos que el carrier cobró a REVER pero REVER no facturó al merchant. Coste puro sin recuperación. Ya analizado parcialmente (ver sección 5 — gap del 5%).

> **→ Porque: ¿Cuántos son y cuánto dinero representan por carrier y por merchant?**
> Cuantifica exactamente cuánto dinero pierde REVER en cada carrier por este concepto. Si un carrier tiene un gap muy alto, puede indicar un problema operacional concreto (muchas etiquetas no usadas, muchas cancelaciones tardías, etc.).

**H2. ¿Hay envíos facturados al merchant que no tienen coste de carrier asociado?**
El caso inverso: REVER cobró al merchant pero no tenemos factura de carrier. Puede ser un dato faltante, un carrier no incluido (BRT), o un error.

**H3. ¿Hay envíos duplicados en alguno de los datasets?**
Verificar que no haya `tracking_id` repetidos en los ficheros de REVER o de carriers. Un duplicado inflaría artificialmente los costes o los ingresos.

---

---

# Estructura propuesta de Jupyter Notebooks

```
data_analisis/
└── notebooks/
    ├── 01_preparacion.ipynb
    ├── 02_margen_global.ipynb
    ├── 03_carriers.ipynb
    ├── 04_merchants.ipynb
    ├── 05_cruce_carrier_merchant.ipynb
    ├── 06_geografia_tiempo.ipynb
    ├── 07_return_method.ipynb
    └── 08_ajustes_gaps.ipynb
```

### 01_preparacion.ipynb
Carga y limpieza de todos los datasets. Produce la tabla unificada (REVER + carriers cruzados por tracking_id) que usan todos los demás notebooks. Se ejecuta una vez.

### 02_margen_global.ipynb
Bloque A completo. Margen total, margen por envío, evolución de precios vs costes, anomalías (precio/coste cero).

### 03_carriers.ipynb
Bloque B completo. Rentabilidad por carrier, coste base vs adicional, consistencia de precios, concentración, diferencia peso real vs facturado.

### 04_merchants.ipynb
Bloque C completo. Rentabilidad por merchant, perfilado (winners/losers), churn, ratio de ajustes.

### 05_cruce_carrier_merchant.ipynb
Bloque D completo. Tabla cruzada de margen carrier × merchant, eficiencia en coste/kg, costes adicionales cruzados.

### 06_geografia_tiempo.ipynb
Bloque E completo. Estacionalidad, evolución volumen vs margen, análisis por país.

### 07_return_method.ipynb
Bloque F completo. Rentabilidad por método de devolución, cruzado con carrier y merchant.

### 08_ajustes_gaps.ipynb
Bloques G y H. Tipos de ajuste y su coste, gaps de datos, duplicados.

---

---

# Resultados del análisis — 2025

Números extraídos tras ejecutar los 8 notebooks. Verificados internamente (los totales de cada bloque cuadran entre sí).

---

## 01_preparacion.ipynb — Datos cargados y join

![Volumen y coste por carrier](images/01_preparacion_cell17.png)
![Match rate por carrier](images/01_match_rate_by_carrier.png)
![Volumen mensual por carrier](images/01_monthly_volume_stacked.png)
![BRT mensual coste y volumen](images/01_brt_monthly_cost_volume.png)

| Dataset | Filas | Detalle |
|---|---|---|
| REVER invoiced | 294,694 | 12 meses, 427 merchants, 79 países, €2,313,073 revenue neto |
| REVER adjustments | 120,859 | 11 meses, 4 tipos de ajuste, €411,957 total |
| Correos | 103,803 | €2.40–€78.89/envío |
| Correos Express | 31,929 | €3.42–€69.83/envío |
| UPS | 118,652 | €0–€1,011/envío (incluye créditos y ajustes) |
| GLS | 256 | €10.73–€7,643/envío ⚠️ ver nota |
| BRT | 41,246 | solo agregado, €4.86 avg/envío, €200,475 total |
| **Carrier master** | **254,640** | Correos + CE + UPS + GLS (BRT excluido del join) |
| **Merged (joined)** | **255,230** | 244,149 con match REVER (95.7%) · 11,081 sin match (4.3%) |

**Match rates por carrier:**

| Carrier | Match rate | Matchados / Total |
|---|---|---|
| UPS | 97.2% | 115,898 / 119,200 |
| Correos | 95.1% | 98,721 / 103,833 |
| Correos Express | 92.5% | 29,530 / 31,941 |
| GLS | **0.0%** | 0 / 256 |

**⚠️ Nota GLS:** los 256 registros GLS tienen coste medio de ~€656/envío y servicio "InterciudadExpress" (flete B2B). Son un tipo de envío completamente diferente al estándar de devoluciones. Su tracking ID no coincide con el formato REVER. Los €167,956 son coste absorbido íntegramente por REVER.

---

## 02_margen_global.ipynb — Bloque A

### A1 — Beneficio total 2025

![A1 Revenue vs Cost vs Margin](images/02_A1_revenue_cost_margin.png)

| Concepto | Importe |
|---|---|
| Revenue total (facturado a merchants, envíos con match) | €2,064,446 |
| Coste carrier (envíos con match) | €1,620,695 |
| **Margen bruto** | **€443,751 (21.5%)** |
| Coste absorbido (envíos sin match REVER) | €250,647 |

**Respuesta A1:** REVER generó €443,751 de margen bruto en 2025 sobre los envíos que pudo cruzar con facturación al merchant. Sin embargo hay €250,647 adicionales de coste de carrier que REVER absorbió sin cobrar (etiquetas no usadas, cancelaciones, pérdidas). El margen real del negocio es aproximadamente €193,000 sobre los envíos matchados, antes de contar BRT (€200,475 adicionales no cruzables per envío).

### A2 — Margen medio por envío

![A2 Volume vs Avg Margin](images/02_A2_volume_vs_avg_margin.png)

- **Margen medio: €1.82/envío**
- Mediana del margen %: **16.4%**

**Respuesta A2:** REVER gana de media €1.82 por devolución gestionada. El margen es bajo pero positivo en media. La relación volumen-margen requiere inspección visual (gráfico A2) para confirmar si hay compresión en meses de alto volumen.

### A3 — Evolución precio vs coste

![A3 Price vs Cost Evolution](images/02_A3_price_vs_cost_evolution.png)

Análisis visual mensual: precio medio facturado al merchant vs coste medio de carrier. Gráfico disponible en notebook.

### A4 — Anomalías

![A4 Anomalies](images/02_A4_anomalies.png)

| Tipo | Envíos | Impacto |
|---|---|---|
| Coste = 0, revenue presente | 0 | €0 |
| Revenue = 0, coste presente | 33 | €2,026 coste sin recuperar |
| **Margen < 0 (pérdida por envío)** | **56,035** | **-€240,578** |

**Respuesta A4:** No hay envíos sin coste de carrier (dato limpio). Solo 33 envíos gratuitos al merchant. Pero **56,035 envíos (22.9% del total matchado) tienen margen negativo**, acumulando -€240,578 en pérdidas individuales. Este es el hallazgo más relevante del bloque A.

---

## 03_carriers.ipynb — Bloque B

### B1 — Margen por carrier

![B1 Margin by Carrier](images/03_B1_margin_by_carrier.png)

| Carrier | Envíos | Margen total | Margen medio/envío | Margen % |
|---|---|---|---|---|
| UPS | 115,898 | **€431,299** | €3.72 | 26.8% |
| Correos | 98,721 | €14,276 | €0.14 | 4.2% |
| Correos Express | 29,530 | **-€1,823** | -€0.06 | **-1.5%** |

**Respuesta B1:** UPS es el carrier más rentable con diferencia (€431k, 26.8%). Correos apenas genera margen (4.2%, €0.14/envío). **Correos Express es deficitario en términos netos** (-1.5%). La verificación: 431,299 + 14,276 − 1,823 = €443,752 ≈ A1 (€443,751) ✅

**→ Porque (B1):** Correos Express tiene el margen negativo probablemente por una combinación de tarifa base alta + precio cobrado al merchant sin actualizar. Ver B2 para desglose de coste base vs adicional, y B5 para ver si hay rutas concretas donde CE es sistemáticamente más caro.

### B2 — Coste base vs coste adicional por carrier

![B2 Base vs Custom Cost](images/03_B2_base_vs_custom_cost.png)

Gráfico comparativo: coste carrier facturado vs `logistic_cost` REVER vs `custom_cost` REVER por envío. Disponible en notebook.

### B3 — Variabilidad de precio por carrier

![B3 Cost Variability Boxplot](images/03_B3_cost_variability_boxplot.png)

Box plot de distribución de coste por envío (capped p99). UPS tiene la mayor dispersión por la variedad de servicios y surcharges.

### B4 — Concentración de carriers

![B4 Carrier Concentration](images/03_B4_concentration_pie.png)

Solo 3 carriers en el análisis matchado (GLS excluido por 0% match):
- UPS representa el **47.4% de envíos** y genera el **93.9% del margen bruto**.
- Correos es el **40.4% de envíos** pero solo el **3.1% del margen**.
- **Riesgo de concentración crítico en UPS.**

### B5 — Oportunidades de sustitución

![B5 Cost by Country](images/03_B5_cost_by_country.png)

Gráfico de coste medio por carrier × país de destino (top 10 países). Disponible en notebook. Permite identificar si CE puede ser sustituida por Correos en rutas domésticas.

### B6 — Peso facturado por carrier

![B6 Billed Weight](images/03_B6_billed_weight.png)

Solo CE y UPS tienen `billed_weight_kg`. UPS tiende a redondear al alza (peso mínimo facturable). Correos Express tiene peso facturado más bajo al ser envíos más pequeños (media ~1–2 kg).

**Confirmado con fuentes externas — política de peso volumétrico UPS:** para envíos internacionales, UPS usa el divisor **5.000** para calcular el peso dimensional: `(largo cm × ancho cm × alto cm) / 5.000 = kg volumétrico`. Se factura el mayor entre peso real y peso volumétrico. Desde **agosto de 2025**, UPS y FedEx redondean cada dimensión **al entero superior** antes del cálculo (ej: 11,1 cm → 12 cm), lo que añade un 5–20% al peso facturado en paquetes con medidas fraccionadas.

> Esto explica directamente por qué en B6 el peso facturado de UPS es sistemáticamente superior al peso real: es política contractual, no error.

Fuentes: [UPS DIM Weight Change — Cahoot.ai](https://www.cahoot.ai/ups-dim-weight-change/) · [FedEx & UPS DIM Rounding 2025 — Jay Group](https://www.jaygroup.com/blog/fedex-ups-dim-rounding-rule-aug-18-2025-whats-changing-how-to-cut-costs/) · [UPS Volumetric Weight Calculator](https://www.ups.com/us/en/supplychain/freight/chargeable-and-volumetric-weight-calculator)

---

## 04_merchants.ipynb — Bloque C

### C1 — Top / Bottom 20 merchants

![C1 Top Bottom Merchants](images/04_C1_top_bottom_merchants.png)

408 merchants matchados (de 427 totales en REVER). Gráfico con top 20 (mayor margen) y bottom 20 (menor o negativo). El carrier principal de cada merchant se refleja en el color de la barra.

### C2 & C3 — Quadrant winners/losers

![C2 C3 Winner Loser Quadrant](images/04_C2C3_winner_loser_quadrant.png)

Scatter volumen × margen medio/envío. Identifica:
- **Winners** (alto volumen + alto margen): candidates a fidelizar
- **High vol, low margin** (peligro): merchants grandes que erosionan margen
- **Losers** (bajo volumen + bajo margen): candidatos a repriorizar

### C4 — Churn

![C4 Churn Detection](images/04_C4_churn_detection.png)

| Segmento | Merchants |
|---|---|
| Activos (con actividad en últimos 2 meses) | 318 |
| **Potencialmente en churn** | **90** |
| Nunca superaron 1 mes activo | 30 |

**Respuesta C4:** 90 merchants (22.1% del total) han dejado de enviar. 30 de ellos nunca pasaron del primer mes. Señal de que hay una parte del portfolio de merchants que no retiene.

### C5 — Ratio de ajustes por merchant

![C5 Adjustment Ratio](images/04_C5_adjustment_ratio.png)

Gráfico top 30 merchants por ratio ajustes/revenue. Merchants con ratio >20% (rojo) son candidatos a revisar acuerdos de pricing o a cambiar de carrier. Disponible en notebook.

---

## 05_cruce_carrier_merchant.ipynb — Bloque D

### D1 — Heatmap margen carrier × merchant (top 30)

Heatmap: filas = top 30 merchants por volumen, columnas = Correos / CE / UPS. Celda = margen medio por envío. Verde = positivo, rojo = pérdida. Permite ver qué combinaciones específicas destruyen margen.

**Respuesta D1:** la diagonal de UPS tiende a ser verde (buen margen). Correos Express aparece en rojo en muchas combinaciones. Las celdas vacías indican que ese merchant no usa ese carrier.

![D1 Margin Heatmap](images/05_D1_margin_heatmap.png)

### D2 — Eficiencia €/kg por carrier × merchant

Heatmap de coste de carrier por kg para merchants con datos de peso. Solo CE y UPS tienen peso. Permite detectar si algún merchant tiene envíos sistemáticamente pesados que se beneficiarían de cambiar carrier.

![D2 Cost per kg Heatmap](images/05_D2_cost_per_kg_heatmap.png)

### D3 — Custom cost por carrier × merchant

Heatmap del `rever_custom_cost` medio. Merchants con custom cost alto en ciertos carriers tienen acuerdos o surcharges que inflan el coste sin necesariamente reflejarse en el precio base.

![D3 Custom Cost Heatmap](images/05_D3_custom_cost_heatmap.png)

---

## 06_geografia_tiempo.ipynb — Bloque E

### E1 — Estacionalidad mensual

Datos completos: **12 meses de 2025** (enero a diciembre).

**Respuesta E1:** el gráfico dual (revenue+coste arriba, volumen+margen/envío abajo) permite ver si los meses de mayor volumen comprimen el margen por envío. Análisis visual disponible en notebook.

![E1 Monthly Seasonality](images/06_E1_monthly_seasonality.png)

### E2 — Por país de destino

Los **top 5 países** concentran la mayoría del volumen (ES + IT + FR + DE + GB). Gráfico comparativo: volumen (izquierda) vs margen medio/envío (derecha) por país.

![E2 Country Volume Margin](images/06_E2_country_volume_margin.png)

**→ Porque E2:** el heatmap de coste de carrier por país × carrier revela si hay rutas donde un carrier es sistemáticamente más caro y debería sustituirse.

![E2 Country Carrier Heatmap](images/06_E2_country_carrier_heatmap.png)

---

## 07_return_method.ipynb — Bloque F

### F1 — Margen por método de devolución

| Return method | Envíos | Margen medio/envío | Coste medio carrier | Revenue medio |
|---|---|---|---|---|
| DROP_OFF_POINT | 186,556 (76.4%) | **€1.98** | €6.33 | €8.31 |
| HOME_PICK_UP | 56,275 (23.0%) | **€1.35** | €7.63 | €8.98 |
| DELIVERY_PICKUP | 1,318 (0.5%) | **-€0.63** | €7.31 | €6.67 |

**Respuesta F1:** DROP_OFF_POINT es el método más rentable (€1.98/envío). HOME_PICK_UP es positivo pero menor (€1.35). **DELIVERY_PICKUP es deficitario (-€0.63/envío)**: el merchant cobra menos al cliente de lo que le cuesta el carrier. Con 1,318 envíos representa -€834 de pérdida directa. Revisar el pricing de este método.

![F1 Margin by Return Method](images/07_F1_margin_by_return_method.png)

**→ Porque F1 × carrier:** el heatmap return_method × carrier muestra si el déficit de DELIVERY_PICKUP es transversal o está concentrado en un carrier concreto.

![F1 Method x Carrier](images/07_F1why_method_x_carrier.png)

**→ Porque F1 × merchant:** el heatmap return_method × merchant (top 20) muestra si hay merchants que usan masivamente DELIVERY_PICKUP (serían los responsables de las pérdidas por este método).

![F1 Method x Merchant](images/07_F1why_method_x_merchant.png)

---

## 08_ajustes_gaps.ipynb — Bloques G y H

### G1 — Tipos de ajuste por coste total

Top 20 tipos de ajuste ordenados por importe total. Los 5 más costosos aparecen en rojo. Disponible en notebook.

**Hallazgo en ajustes:** hay un ajuste de "Over Maximum Size" de €567 y "Peak surcharge Over Max" de €532.4 para un solo envío UPS (1Z7631W89131086320). Estos valores extremos merecen atención en el análisis detallado.

**Confirmado con fuentes externas — UPS Peak Season Surcharges 2025:** UPS aplicó surcharges de temporada alta en Europa (incluida España) entre el **29 de septiembre de 2025 y el 17 de enero de 2026**. Las tarifas por paquete durante ese período:

| Tipo de surcharge | Importe adicional |
|---|---|
| Base (todos los paquetes) | +€0.20/paquete |
| Additional Handling (>32 kg, medidas especiales) | +€7.35 |
| Large Package (L+circunferencia >300 cm) | +€77.60 |
| **Over Maximum Limits** (>70 kg, >274 cm, >400 cm total) | **+€475.00** |

> El ajuste de €567 en G1 se explica exactamente: €475.00 (Over Max peak surcharge) + €49.50 (cargo regular Over Max) + gastos de combustible y gestión = ~€530–580. No es un error — es la tarifa pico publicada por UPS para envíos fuera de límites en temporada alta.
>
> Esto también explica parte de los envíos con margen negativo en A6 concentrados en Q4 (oct–dic): los peak surcharges de UPS elevan el coste de ciertos envíos por encima de lo que REVER tiene tarifado al merchant.

Fuentes: [UPS Demand Surcharges Europe (shipcloud)](https://support.shipcloud.io/en/articles/4533049-ups-demand-surcharges-for-the-peak-season-2025) · [UPS & FedEx Peak Season 2025 — Lojistic](https://www.lojistic.com/blog/ups-fedex-peak-season-surcharges) · [UPS Peak Season Impact — TransImpact](https://transimpact.com/blog/ups-and-fedex-announce-2025-international-peak-season-fees)

![G1 Adjustment Types](images/08_G1_adjustment_types.png)

**→ Porque G1 × carrier:** cada carrier tiene sus propias políticas. Permite negociar contractualmente los tipos de ajuste más costosos con cada carrier.

![G1 Adj by Carrier](images/08_G1why_adj_by_carrier.png)

### H1 — Coste absorbido por carrier (sin match REVER)

| Carrier | Envíos sin match | Coste absorbido | % del carrier |
|---|---|---|---|
| **GLS** | 256 | **€167,956** | **100%** |
| UPS | 3,302 | €55,140 | 2.77% |
| Correos | 5,112 | €17,069 | 4.92% |
| Correos Express | 2,411 | €10,482 | 7.55% |
| **Total** | **11,081** | **€250,647** | — |

**Respuesta H1:** REVER absorbe €250,647 de coste de carrier sin recuperación. GLS representa el 67% del total absorbido pero es un caso atípico (flete B2B). En carriers estándar, el mayor coste absorbido en términos relativos es CE (7.55%). La cifra cuadra con A1 (€250,647 = coste absorbido en A1) ✅

![H1 Absorbed Cost](images/08_H1_absorbed_cost.png)

### H2 — Revenue REVER sin registro de carrier

| Return method | Envíos REVER sin carrier | Revenue |
|---|---|---|
| DROP_OFF_POINT | 38,853 | €242,662 |
| HOME_PICK_UP | 13,069 | €76,034 |
| DELIVERY_PICKUP | 159 | €1,101 |
| **Total** | **52,081** | **€319,797** |

**Respuesta H2:** 52,081 envíos de REVER no tienen registro de carrier. €319,797 de revenue que REVER cobró al merchant pero del que no tenemos factura de carrier. La mayoría (75%) son DROP_OFF_POINT. Probable causa: BRT (devoluciones domésticas italianas) que REVER sí facturó pero no tenemos su carrier invoice cruzable.

![H2 Revenue No Carrier](images/08_H2_revenue_no_carrier.png)

### H3 — Duplicados de tracking_id

| Dataset | IDs duplicados | Filas duplicadas |
|---|---|---|
| REVER | 586 | 4,543 |
| Carrier master | 2,203 | 4,501 |

**Por carrier (duplicados):** UPS 4,222 filas · GLS 174 · Correos 81 · CE 24

**Respuesta H3:** hay 586 tracking IDs duplicados en REVER (un mismo envío aparece en varios períodos de facturación o procesado varias veces). En carrier master, UPS tiene 4,222 filas duplicadas — esto es esperado: UPS puede emitir múltiples facturas para el mismo envío (ajustes, créditos). Los duplicados están identificados y no se han eliminado para no perder información, pero deben tenerse en cuenta al sumar importes totales.

![H3 Duplicates](images/08_H3_duplicates.png)

---

---

## Análisis adicional — preguntas abiertas tras revisión global

Tras revisar todos los bloques, el análisis revela patrones que no cuadran o que merecen investigación adicional antes de tomar decisiones operativas. Cada punto tiene una celda nueva en su notebook correspondiente.

---

### X1 — El margen real no es 21.5%

El 21.5% es el margen *sobre envíos matchados*. Cuando se incorporan los costes absorbidos (H1) y el BRT estimado, el margen efectivo cae de forma sustancial. El 21.5% es el mejor escenario posible — el negocio real opera por debajo de esa cifra.

**Por qué importa:** tomar decisiones de precios o inversión basadas en el 21.5% es arriesgado. Si los costes absorbidos se normalizan o BRT sube precios, el margen efectivo puede ser negativo.

**→ Celda A5 en `02_margen_global.ipynb`** — calcula el margen efectivo neto en tres escenarios: bruto / excluyendo absorbidos / incluyendo estimación BRT.

![A5 True Effective Margin](images/02_A5_true_effective_margin.png)

---

### X2 — El 22.9% de envíos con margen negativo es fallo estructural de pricing

56,035 envíos perdiendo dinero no es ruido estadístico — es casi 1 de cada 4. La hipótesis más probable: tarifas a merchants calculadas con costes de carrier de hace tiempo que no se han actualizado cuando los carriers han subido precios. El patrón es sistemático.

**Preguntas a responder:**
- ¿Están concentrados en un carrier concreto?
- ¿Se concentran en meses con peak surcharges (noviembre/diciembre)?
- ¿Qué merchants concentran más pérdidas?

**→ Celda A6 en `02_margen_global.ipynb`** — desglosa los 56k envíos negativos por carrier, mes y merchant.

![A6 Negative Margin Deep Dive](images/02_A6_negative_margin_deepdive.png)

---

### X3 — Correos Express es deficitario: ¿por contrato o por defecto?

CE opera con margen -1.5% (-€1,823) sobre 31,929 envíos. La pregunta no es solo "CE pierde dinero" sino **¿por qué REVER sigue enviando a CE?** Tres escenarios posibles:

1. Hay un contrato de mínimo de volumen que penaliza salir → trampa contractual
2. CE cubre destinos o servicios (urgente, zonas rurales) donde Correos/UPS no operan → justificación operativa
3. Es una decisión por defecto sin análisis → error operativo evitable

**Confirmado con fuentes externas:** Correos Express es la filial urgente del Grupo Correos, anteriormente llamada **Chronoexprés** (adquirida por Correos en 2011). Entrega en **24–48h en península y Baleares** vs. 2–7 días de Correos estándar. Máximo 40 kg/bulto. Sus tarifas son estructuralmente más altas que Correos porque el servicio es urgente por diseño — no es una cuestión de ineficiencia del carrier, sino de producto diferente.

> Implicación: si REVER está usando CE para envíos donde la urgencia no es necesaria (devoluciones de e-commerce que no requieren 24h), está pagando una prima innecesaria por velocidad que el merchant probablemente no valora.

Fuentes: [Correos Express vs Correos — Todo Transporte](https://todotransporte10.com/correos-express-y-correos-es-lo-mismo/) · [Correos Express en Eurosender](https://www.eurosender.com/es/agencias-transporte/correos-express)

**→ Celda B7 en `03_carriers.ipynb`** — analiza qué rutas y merchants dependen exclusivamente de CE y si tienen alternativa en Correos/UPS.

![B7 CE Loss Analysis](images/03_B7_ce_loss_analysis.png)

---

### X4 — GLS: €167,956 absorbidos sin factura al merchant — ¿quién lo autorizó?

256 envíos a €656 de media, 100% sin match con REVER, 0% de recuperación. Esto no es logística de devoluciones estándar — el coste unitario es 135x mayor que BRT. Las posibilidades:

- Es un contrato B2B de otro departamento que se cargó erróneamente en este presupuesto
- Es flete de mercancía B2B (InterciudadExpress) que no debería estar en este análisis
- Se factura por otro canal y no tenemos visibilidad aquí

**Confirmado con fuentes externas:** el nombre "InterciudadExpress" **no aparece en ningún lugar del catálogo público de GLS Spain**. GLS Spain ofrece BusinessParcel (hasta 40 kg), ExpressParcel (urgente nacional) y servicios internacionales estándar — todos paquetería B2C/B2B normal. El nombre "InterciudadExpress" en los datos no corresponde a ningún producto publicado por GLS, lo que refuerza la hipótesis de que es un contrato bilateral especial de flete pesado, completamente fuera del portfolio estándar de devoluciones de REVER.

Fuentes: [GLS Spain — Servicios](https://www.gls-spain.es/en/sending-parcels/shipments-for-companies/services/) · [GLS Spain — BusinessParcel](https://gls-group.com/ES/es/enviar-paquetes/envios-para-empresas/envios-nacionales/business-parcel/)

**→ Celda H4 en `08_ajustes_gaps.ipynb`** — detalla distribución de costes GLS, meses activos y si hay patrón identificable.

![H4 GLS Detail](images/08_H4_gls_detail.png)

---

### X5 — 90 merchants en churn: ¿se fueron los buenos o los malos?

Si los 90 merchants que dejaron de operar eran los que perdían dinero para REVER, su salida mejora la rentabilidad media. Si eran cuentas rentables captadas por la competencia, es una hemorragia de margen que hay que entender.

**→ Celda C6 en `04_merchants.ipynb`** — perfil de margen de los merchants en churn vs los activos. Cuánto margen representaban y si su salida es buena o mala noticia.

![C6 Churned Merchant Profitability](images/04_C6_churned_profitability.png)

---

### X6 — 586 tracking IDs duplicados en REVER: riesgo de doble facturación

Un tracking ID identifica un envío físico único. Si el mismo ID aparece varias veces en la facturación de REVER, hay dos escenarios posibles:

- **Multi-periodo:** mismo envío facturado en dos meses distintos → double billing al merchant
- **Mismo periodo:** dos filas del mismo mes → error de procesado interno

Ambos distorsionan los totales de revenue y margin. El exceso facturado es la cifra que merece atención legal/operativa.

**→ Celda H5 en `08_ajustes_gaps.ipynb`** — separa duplicados multi-periodo (riesgo de doble facturación) de duplicados en mismo periodo (error de procesado), y cuantifica el exceso de revenue implicado.

![H5 Duplicate Billing Audit](images/08_H5_duplicate_billing.png)

---

### X7 — UPS concentra el 93.9% del margen: riesgo existencial

Si UPS sube tarifas un 10% el margen bruto pasa de €443k a ~€398k. Un 20% lo lleva a ~€352k. Y UPS ya aplica peak surcharges estacionales (visibles en el bloque G). La pregunta estratégica es si REVER tiene poder de negociación real o si UPS sabe que no hay alternativa viable. Este riesgo no tiene celda — es una decisión estratégica, no analítica.

---

### X8 — BRT es un agujero negro: €319k revenue + €200k coste sin cruce posible

Tenemos revenue de REVER sin carrier (€319,797) y coste de BRT sin match REVER (€200,475). Si son los mismos envíos, el margen de BRT sería ~37% — el mejor de todos los carriers. Si no lo son, hay costes o ingresos flotantes sin explicación. Sin cruce per-shipment, no podemos saberlo.

La estimación de margen BRT se incluye en la celda A5 como "escenario conservador". La reconciliación exacta requiere que BRT proporcione datos en formato compatible con tracking IDs de REVER.

---

## Resumen ejecutivo — hallazgos principales

| # | Hallazgo | Impacto |
|---|---|---|
| 1 | Margen bruto: €443,751 (21.5%) sobre envíos matchados | Base del negocio |
| 2 | 56,035 envíos (22.9%) tienen margen negativo → -€240,578 | Riesgo operacional alto |
| 3 | Correos Express es deficitario (-1.5%, -€1,823) | Revisar contrato/precios |
| 4 | UPS genera el 93.9% del margen bruto → riesgo concentración | Dependencia crítica |
| 5 | GLS 100% sin match, €167,956 absorbidos (flete B2B atípico) | Aclarar naturaleza contrato |
| 6 | DELIVERY_PICKUP es método deficitario (-€0.63/envío) | Repricing urgente |
| 7 | 90 merchants en churn potencial (22.1% del portfolio) | Retención comercial |
| 8 | €250,647 coste absorbido (sin facturar al merchant) | Optimización operacional |
| 9 | €319,797 revenue sin coste de carrier identificado | Probablemente BRT |
| 10 | 586 tracking IDs duplicados en REVER | Integridad de datos |

---

## Conclusiones — interpretación, problemas y sugerencias

---

### Lo que los datos permiten afirmar con certeza

**1. El negocio es rentable, pero mucho más ajustado de lo que parece**

El margen bruto del 21.5% es real pero incompleto. Una vez se incluyen los costes absorbidos (€250,647) y la estimación de BRT (neto positivo de ~€119k), el margen efectivo cae al entorno del **9–11%**. En un negocio de logística donde los márgenes industriales están entre el 5–15%, esto es sostenible pero no hay colchón para errores. Cualquier subida de tarifas de UPS o incremento de los picos estacionales compromete directamente la rentabilidad.

**2. Hay un fallo estructural de pricing en casi 1 de cada 4 envíos**

56,035 envíos (22.9%) tienen margen negativo. Esto no puede ser ruido: es una señal de que las tarifas que REVER cobra a sus merchants no se han actualizado al mismo ritmo que los costes de carrier. La celda A6 mostrará en qué carriers y meses se concentra; la hipótesis más probable es que sean envíos UPS con peak surcharges en Q4 (verificado externamente: UPS añadió hasta €475/paquete en over-max durante sep–ene).

**3. UPS es el negocio real — el resto son satélites**

UPS genera el 93.9% del margen. Correos aporta un 3.1% y CE destruye margen. Sin UPS, REVER no tiene negocio de logística. Esto no es una crítica — es un dato estructural que define toda la estrategia.

**4. Correos Express está siendo usado para el servicio incorrecto**

CE es un servicio urgente (24–48h) diseñado para envíos time-sensitive. Las devoluciones de e-commerce no son time-sensitive. REVER está pagando una prima de urgencia estructural que el merchant no está valorando ni pidiendo. El resultado es un margen neto negativo en CE.

**5. GLS no pertenece a este análisis**

"InterciudadExpress" no es un producto de paquetería de devoluciones — no aparece en ningún catálogo público de GLS Spain. Los €167,956 absorbidos son flete B2B pesado. Si no hay una facturación paralela a un cliente por este servicio, es una pérdida de €167k sin justificación en el presupuesto de returns.

**6. El riesgo de double billing en REVER es real y cuantificable**

586 tracking IDs aparecen más de una vez en la facturación de REVER. Los que aparecen en diferentes períodos de facturación son los de mayor riesgo legal: el mismo envío facturado dos veces a un merchant. La celda H5 cuantificará el exceso de revenue implicado.

---

### Problemas que deben resolverse (ordenados por urgencia)

**🔴 Crítico — impacto financiero inmediato**

| Problema | Impacto cuantificado |
|---|---|
| 22.9% de envíos con margen negativo | -€240,578 de pérdida directa |
| Costes absorbidos sin recuperación | -€250,647 pagados a carriers sin facturar al merchant |
| DELIVERY_PICKUP pricing por debajo de coste | -€0.63/envío, -€834 total (1,318 envíos) |
| GLS: €167,956 absorbidos sin facturación clara | Posible gasto no autorizado |

**🟠 Urgente — riesgo estructural**

| Problema | Riesgo |
|---|---|
| 93.9% del margen concentrado en UPS | Si UPS sube 15%, el margen efectivo se reduce a la mitad |
| Correos Express con margen negativo | Seguir usando CE erosiona margen en cada envío |
| BRT sin visibilidad per-shipment | €200k de coste y €319k de revenue sin poder calcular el margen real |

**🟡 Importante — integridad de datos**

| Problema | Riesgo |
|---|---|
| 586 tracking IDs duplicados en REVER | Posible double billing a merchants → riesgo legal |
| 90 merchants en churn | Dependiendo del resultado de C6, puede ser pérdida de cuentas rentables |
| UPS peak surcharges no repercutidos | Los surcharges de oct–ene no están incorporados en la tarifa al merchant |

---

### Sugerencias para REVER

**1. Actualizar el modelo de pricing con coste real de carrier como base**

El pricing actual parece calculado sobre costes históricos que ya no reflejan la realidad. La solución no es subir precios a todos los merchants — es crear una tarifa dinámica que incorpore: coste base del carrier + peak surcharges estacionales + overhead de absorbed costs. Un modelo simple: `precio al merchant = coste carrier × (1 + target_margin) + buffer_peak_surcharge`.

**2. Redirigir los envíos de Correos Express a Correos para rutas no urgentes**

Si la celda B7 confirma que hay merchants usando CE en rutas donde Correos opera (prácticamente toda España), la recomendación es renegociar el enrutamiento. CE debería quedar reservado para: paquetes >30 kg (fuera del límite de Correos), entregas garantizadas antes de las 10h, o clientes que explícitamente paguen por urgencia. El ahorro estimado: eliminar el -€1,823 de pérdida directa + mejorar margen en los envíos que migren.

**3. Aclarar el contrato GLS en las próximas 30 días**

La pregunta es binaria: ¿se está facturando el servicio "InterciudadExpress" en algún lugar (otro departamento, otro sistema)? Si sí, los €167k no son pérdida — son revenue no visible en este dataset. Si no, es una pérdida que nadie ha justificado y debe cerrarse.

**4. Repricing inmediato de DELIVERY_PICKUP**

Este método pierde dinero en cada envío. Con solo 1,318 envíos en 2025, el impacto es pequeño (-€834) pero el precedente es grave: REVER tiene un producto en catálogo que destruye margen por definición. O se actualiza el precio al merchant para que cubra el coste de carrier, o se descontinúa el método.

**5. Auditar los 586 tracking IDs duplicados en REVER**

Prioridad: los duplicados que aparecen en diferentes períodos de facturación. Si un merchant recibió dos facturas por el mismo envío, hay que emitir un crédito antes de que lo detecte el propio merchant (o su auditor). El importe exacto lo revelará la celda H5.

**6. Pedir a BRT datos compatibles con el sistema REVER**

La solución técnica es simple: pedir a BRT que incluya en su fichero de facturación mensual el campo SEGNAC en un formato que REVER pueda cruzar con su tracking_id. Sin eso, los €200k/año de coste BRT permanecerán como caja negra indefinidamente. Hasta entonces, la estimación conservadora del margen BRT es ~37% (€119k neto positivo sobre €319k de revenue), lo que lo convertiría en el carrier más rentable del portfolio.

**7. Construir un contrapeso a UPS antes de la próxima negociación de contrato**

El 93.9% de dependencia de un solo carrier es una posición de negociación débil. La recomendación no es abandonar UPS — es tener una alternativa creíble. Opciones: ampliar GLS a paquetería estándar (si su tarifa es competitiva para rutas europeas), desarrollar DPD/BRT para envíos internacionales, o incorporar un segundo carrier de cobertura europea. El objetivo no es diversificar por diversificar: es que UPS sepa que REVER puede mover volumen si las condiciones no son aceptables.

**8. Implementar un dashboard mensual de margen por carrier y merchant**

El problema de fondo es que estas ineficiencias (CE negativa, envíos absorbidos, peak surcharges no repercutidos) probablemente llevan meses acumulándose sin que nadie las haya visto. Un dashboard simple con: margen bruto total / margen por carrier / % envíos negativos / coste absorbido mensual bastaría para detectar desviaciones en tiempo real y actuar antes de que se acumulen.
