# CurEnergía Facturas para Home Assistant — Diseño

Fecha: 2026-10-29 · Estado: borrador pendiente de aprobación

Convención: **(usuario)** = decidido por el usuario; **(mío)** = decisión tomada durante el diseño que el usuario puede revisar; **(builder)** = se deja a quien construya.

Las decisiones de planificación D1–D8 están en la cabecera del plan de implementación (`docs/superpowers/plans/2026-10-29-curenergia-integracion-ha.md`); el comportamiento que resulta de ellas y de los dictámenes tomados durante la ejecución está descrito en el `README.md`.

## 1. Intención y porqué

El usuario es cliente de CurEnergía (comercializadora de referencia del grupo Iberdrola) con un contrato de luz (PVPC, peaje 2.0TD) y otro de gas (TUR.1). Ya tiene en Home Assistant la integración **e-data**, que descarga de Datadis el consumo horario de luz.

Quiere **casar lo que le facturan con lo que dice Datadis**: por cada factura, ver periodo, kWh, importe y €/kWh, y al lado lo que Datadis/e-data dicen para las mismas fechas, tanto en kWh como en €. Así detecta si le cobran consumo que no ha hecho (kWh) o a un precio incorrecto (€). El usuario tomó como referencia una tabla hecha a mano por unos amigos (periodo · kWh · importe · €/kWh).

Todo tiene que ser **automático**: el usuario rechazó explícitamente cualquier flujo de importación manual de PDFs **(usuario)**.

## 2. Objetivos

1. Integración personalizada de Home Assistant distribuida por **HACS** como repositorio válido, con versiones (releases) que HACS detecte como actualizaciones **(usuario)**.
2. Obtener las facturas automáticamente desde el **correo** (IMAP + contraseña de aplicación), leyendo el PDF adjunto **(usuario)**.
3. Casar cada factura de luz con Datadis vía e-data en kWh (total y P1/P2/P3) y en € (potencia + energía) **(usuario: kWh y €)**.
4. Mostrar el resultado en una **tarjeta Lovelace propia** y en un **panel en la barra lateral** **(usuario: opciones B y C del boceto)**.
5. Cumplir voluntariamente las **reglas Bronze** del Integration Quality Scale, aunque no se busque entrar en core **(usuario)**.

## 3. No objetivos

- Entrar en Home Assistant core.
- Acceder a la web o a la API de CurEnergía. Investigado y descartado: la web está protegida por Akamai Bot Manager y reCAPTCHA Enterprise. No se intenta eludirlos.
- Acciones ante una discrepancia (avisos, notificaciones, reclamaciones). Solo se **marca** la factura **(usuario: "marcarla y ya, no haremos nada más por ahora")**.
- Comparar el gas con Datadis: Datadis no tiene datos de gas. El gas se muestra sin casar.
- Importar facturas anteriores a lo que haya en el buzón (primera versión) **(mío)**.
- Modificar el buzón: la integración no marca, mueve ni borra correos **(mío)**.

## 4. Anti-objetivos (sería un fracaso aunque "funcione")

- Que acabe pidiendo descargar o subir PDFs a mano.
- Que avise de discrepancias falsas en lecturas estimadas, que son normales y se regularizan en la siguiente factura real.
- Que filtre datos personales (NIF, nombre, dirección, CUPS, número de contrato, correo) en logs, diagnósticos, el repositorio o las fixtures de test.
- Que llene la base de datos de Home Assistant guardando el histórico de facturas en atributos de sensores.

## 5. Restricciones

- Home Assistant actual (2026.x). Versión mínima en `hacs.json` **(builder)**.
- HACS exige un repositorio **público** en GitHub para instalarlo como repositorio personalizado. El repo se crea privado al principio; habrá que hacerlo público antes de instalarlo desde HACS.
- Regla Bronze `dependency-transparency`: la librería que lee los PDFs debe estar publicada en **PyPI**, con código público y publicada por CI desde una release etiquetada. Requiere que el usuario tenga una cuenta en PyPI y configure un *trusted publisher* (es un paso manual del usuario).
- Gmail: IMAP solo funciona con una contraseña de aplicación (requiere verificación en dos pasos). El correo del usuario está en Google Workspace, donde el administrador tiene que permitir IMAP y las contraseñas de aplicación.
- Una contraseña de aplicación da acceso IMAP a **todo** el buzón, no se puede limitar a una etiqueta. Esto se documenta en el README (ver §7.4).

## 6. Arquitectura

Un único repositorio `hacs-curenergia` **(mío)** con:

```
custom_components/curenergia/   ← integración (dominio: curenergia)
  frontend/                     ← JS ya compilado de la tarjeta y del panel
lib/                            ← librería Python del lector de PDF (se publica en PyPI)
frontend/                       ← código fuente de la tarjeta y del panel
docs/
hacs.json, README.md, LICENSE (MIT, mío)
.github/workflows/              ← hassfest, HACS action, tests, publicación en PyPI, build del frontend
```

Nombre en PyPI de la librería **(builder)**, por ejemplo `pycurenergia`. Que la librería viva en el mismo repo **(mío)** es por sencillez. Separarla más adelante no cambia la integración.

Flujo de datos:

```
Gmail (IMAP, carpeta/etiqueta elegida, solo lectura)
  → correos de noresponder@clientescurenergia.es con PDF adjunto
  → librería: PDF → texto → Invoice (modelo tipado)
  → integración: guarda las facturas (Store), deduplicadas por nº de factura
  → casación: suma las estadísticas largas de e-data en el periodo de la factura
  → sensores (última factura) + API websocket → tarjeta y panel
```

## 7. Ingesta por correo (IMAP)

### 7.1 Configuración (config flow)

1. Servidor (por defecto `imap.gmail.com`), puerto (993, SSL), usuario, contraseña de aplicación. Se prueba el login antes de crear la entrada (`test-before-configure`).
2. Se listan las carpetas IMAP de la cuenta (en Gmail, las etiquetas son carpetas) y el usuario elige una en un desplegable **(usuario: ir solo a una etiqueta)**. Por defecto se preselecciona una carpeta cuyo nombre contenga "curenergia" si existe; si no, `[Gmail]/All Mail` o `INBOX` **(mío)**. Los nombres de carpeta en IMAP van en UTF-7 modificado (acentos, espacios); hay que decodificarlos para mostrarlos y codificarlos para hacer `SELECT`.
3. `unique_id` de la entrada = `usuario@servidor` en minúsculas (`unique-config-entry`).
4. Reautenticación si el login falla después (contraseña revocada) **(mío; es regla Silver, pero se incluye)**.
5. Opciones (options flow): carpeta, intervalo de sondeo, umbrales de casación (§9.4), panel lateral sí/no (§11.2), guardar PDFs sí/no (§8.3), vínculo manual con e-data (§9.2).

### 7.2 Búsqueda

- La carpeta se abre en **solo lectura** (`EXAMINE` / `SELECT` readonly) **(mío)**: así no se marcan como leídos.
- Filtro: `FROM "noresponder@clientescurenergia.es"`, **aunque** la carpeta ya sea una etiqueta filtrada, como segunda barrera **(mío)**.
- Asuntos conocidos (sirven para saber si es luz o gas antes de leer el PDF):
  - `Ya tienes disponible tu factura de electricidad de Curenergía`
  - `Ya tienes disponible tu factura de gas de Curenergía`
  Se aceptan correos del remitente aunque el asunto cambie; el tipo se decide en último término por el contenido del PDF **(mío)**.
- Adjunto: PDF llamado `{contrato}_{id-factura}.pdf`. No se depende del nombre del fichero.
- El cuerpo del correo trae también el importe. Si se puede extraer, se usa para comprobar el total leído del PDF (§8.2) **(mío)**.
- Se recuerdan `UIDVALIDITY` + UIDs ya procesados para no volver a descargar adjuntos. Si cambia `UIDVALIDITY`, se reprocesa todo y la deduplicación por número de factura evita duplicados.

### 7.3 Frecuencia

- Sondeo cada **6 horas** (`appropriate-polling`). Las facturas son mensuales y no hace falta más **(mío)**.
- Botón (entidad `button`) "Buscar facturas ahora" para forzarlo **(mío; se prefiere a una acción de servicio)**.
- Primera ejecución: procesa todos los correos que haya en la carpeta (aproximadamente un año de facturas en el caso del usuario).

### 7.4 Documentación del correo en el README

- **Recomendado:** un filtro de Gmail (remitente `noresponder@clientescurenergia.es` → aplicar una etiqueta, por ejemplo `CurEnergia`, y marcar "aplicar también a las conversaciones existentes"), y elegir esa etiqueta en la configuración.
- **Alternativa más segura:** reenviar esos correos a un buzón dedicado y conectar la integración a ese buzón. Así Home Assistant no tiene llave del correo principal.
- Explicar claramente que la contraseña de aplicación da acceso a todo el buzón.

## 8. Lectura de los PDF (librería)

### 8.1 Formato

Los PDF de CurEnergía tienen **texto extraíble** (no son escaneos), 4 páginas. Se han analizado una factura de luz y una de gas reales del usuario. La librería usa `pypdf` (Python puro) para extraer el texto **(mío; builder puede elegir otra si es necesario)** y después lo interpreta con expresiones regulares por campo.

**Material de partida (mío):** los PDF reales del usuario se dejan en `private/invoices/` dentro del repo, carpeta excluida por `.gitignore` y que nunca se sube. Al principio hay una factura de luz y una de gas; el usuario puede descargar de su correo el resto (unas 12 de luz), entre ellas alguna estimada y alguna con intereses de demora. Un script del repo (`scripts/anonymize.py` o similar) extrae el texto con la misma librería y sustituye los datos personales por valores inventados con el mismo formato. Las fixtures que salen de ahí son las únicas que se suben. Las expresiones regulares se escriben sobre la salida real de `pypdf`, no sobre texto inventado.

Se recomienda separar dos capas **(mío)**: PDF → texto, y texto → `Invoice`. La segunda capa se puede probar con fixtures de texto anonimizado.

Formato de números: español (`1.234,56`). Fechas: `dd/mm/aaaa` y también en texto (`5 de agosto de 2026`).

**Luz** (campos encontrados):

| Dato | Dónde |
|---|---|
| Nº de factura, fecha de emisión, fecha límite de pago | cabecera |
| Periodo | `Periodo de consumo: D de mes de AAAA a D de mes de AAAA` |
| Importe total | `IMPORTE FACTURA` / `TOTAL IMPORTE FACTURA` |
| Resumen | `Por potencia contratada`, `Por energía consumida`, `Por financiación del bono social`, `Impuesto electricidad`, `Otros` (intereses de demora), `Alquiler del contador`, `IVA NN % s/BASE € IMPORTE €` |
| Contrato | `TIPO DE CONTRATO` (PVPC), peaje 2.0TD, potencia punta/valle (kW), CUPS (`ES 0031 …`) |
| Consumo total | `Su consumo en el periodo facturado ha sido: N kWh` |
| Lecturas | `Lectura actual (real|estimada) (fecha)`; `Lectura en P1 (punta): … kWh Consumo en P1: … kWh` (P2 llano, P3 valle) |
| Desglose (pág. 2) | peajes y cargos por periodo, `Coste de la energía: N kWh x P €/kWh`, `Margen de comercialización fijo`, `Intereses de demora (*)` |

**Gas** (campos encontrados):

| Dato | Dónde |
|---|---|
| Periodo | `Periodo de facturación dd/mm/aaaa - dd/mm/aaaa` |
| Nº de factura, fecha de emisión, nº de contrato | cabecera |
| Lectura estimada | texto `Factura con lectura estimada` |
| Contrato | CUPS (`ES 0217 …`), distribuidora, tarifa (TUR.1) |
| Conceptos | `Término fijo mensual N meses x P €/mes`, `Energía facturada (real|estimada) N kWh x P €/kWh`, `Impuesto sobre gas natural`, `Alquiler equipos de medida`, IVA, TOTAL |
| Lecturas | m³ (real/estimada), `Factor de corrección`, `PCS`, `Consumo kWh` |

Los intereses de demora ("Otros") son un concepto propio, no se mezclan con la energía **(mío)**.

### 8.2 Modelo y comprobación interna

`Invoice` (tipado, inmutable): tipo (luz/gas), nº de factura, nº de contrato, CUPS, fecha de emisión, periodo inicio/fin, lectura estimada (bool), kWh total, kWh P1/P2/P3 (luz), m³ (gas), lista de conceptos (nombre normalizado + importe), base imponible, tipo de IVA, IVA, total, y para luz la potencia contratada y la tarifa. Incluye también `energy_price_kwh` (precio del término de energía en €/kWh, `None` si la factura no lo indica) **(mío)**.

Comprobación interna **(mío)**: suma de conceptos = total (±0,01 €), IVA = tipo leído × base (±0,01 €), P1+P2+P3 = total kWh, y total = importe del cuerpo del correo cuando esté disponible. Si falla, la factura se guarda con estado **"no se pudo leer bien"**. Ese estado es distinto de "no cuadra" y significa que el lector tiene un fallo, no CurEnergía. Se registra un aviso en el log sin datos personales.

Errores de la librería **(mío)**: `InvoiceParseError` (no se pudo leer un campo), `UnsupportedInvoiceError` (el PDF no es un tipo soportado, por ejemplo una rectificativa o un abono) e `InvoiceReadError` (el PDF está dañado, cifrado, vacío o es demasiado grande; su mensaje nunca lleva texto del PDF). Sin número de factura no se puede guardar una fila, así que la integración guarda el UID del correo junto con la versión de la librería, reintenta ese correo cuando la versión cambia y lo cuenta en el resumen; los no soportados se guardan aparte y no se reintentan.

### 8.3 Almacenamiento

- Facturas en `helpers.storage.Store` por entrada de configuración, con versión de esquema y deduplicadas por número de factura.
- Los PDF **no** se guardan por defecto. Opción para guardarlos en una carpeta de `config/` **(mío)**.

## 9. Casación con e-data (solo luz)

### 9.1 Fuente

Se leen las **estadísticas largas** del recorder que publica e-data **(mío; no se tocan sus tablas internas ni su SQLite)**:

- consumo: `edata:<id>_consumption`, `edata:<id>_p1_consumption`, `_p2_consumption`, `_p3_consumption`
- coste: `edata:<id>_power_cost`, `edata:<id>_energy_cost` (solo existen si el usuario tiene activada la facturación en e-data; para PVPC, e-data usa precios horarios)

Se suman los valores horarios (`state`, que en e-data es el valor de esa hora) en la ventana de la factura **(mío)**. Cada fila de e-data lleva como `start` el **inicio** de la hora.

### 9.2 Vínculo factura ↔ e-data

- Automático por **CUPS**: buscar la entrada de configuración de e-data cuyo CUPS coincida con el de la factura y obtener `<id>` igual que lo construye e-data. Verificado en `uvejota/homeassistant-edata` 2026.10.4 (dominio `edata`): la entrada guarda `data["cups"]` (CUPS completo, que además es su `unique_id` en mayúsculas) y `data["scups"]` (sufijo corto), y el `<id>` de las estadísticas es `data["scups"].lower()`.
- Si no se encuentra, en opciones se puede elegir la entrada de e-data a mano. Ese vínculo manual solo se aplica cuando hay un único CUPS de luz sin pareja automática: con dos o más, ninguno se vincula, para no comparar dos contadores con el mismo e-data **(mío)**.
- Sin e-data, la integración funciona igual y muestra las facturas sin casar.

### 9.3 Ventana temporal

Se usa el periodo **del PDF**, no el de la lista web, que muestra otro periodo para la misma factura. **Regla fijada con datos reales (v0.1.1):** el periodo `D1 a D2` corresponde a `[D1+1 00:00, D2+1 00:00)` (hora local de España). Las facturas van de lectura a lectura y la lectura del día `D1` cierra la factura anterior, así que el consumo de esta empieza el día siguiente. Por eso **dos facturas consecutivas comparten la fecha frontera**: a `D1 a D2` le sigue `D2 a D3` (pasa igual en gas). Cómo se fijó: la v0.1.0 usaba por defecto `[D1 00:00, D2+1 00:00)`, y sus diagnósticos daban, para cada factura con lectura real, la Δ kWh con las fronteras alternativas (un día antes y un día después en cada extremo). Con los diagnósticos de la instalación del usuario, desplazar el inicio un día dejaba todas las facturas reales en Δ ≈ 0,00 kWh (±0,02), frente a −6…−18 kWh con la regla anterior. Los diagnósticos siguen dando esas cinco Δ, ahora relativas a la regla nueva. Si Datadis no cubre todas las horas de la ventana, la factura queda como **"sin datos suficientes"** y no se marca.

**Cobertura de Datadis (mío):** la ventana se considera cubierta si `edata:<id>_consumption` tiene al menos `horas − 2` filas horarias, la primera empieza antes de `inicio + 2 h` y la última empieza en `fin − 3 h` o después. Las horas se cuentan como horas reales transcurridas, de modo que el cambio de hora (745 h en octubre, 743 h en marzo) no produce un `sin_datos` falso. Si no se cumple, el estado es `sin_datos`. Los costes de e-data solo se usan si `power_cost` y `energy_cost` cumplen esa misma regla, y si a la ventana le falta alguna hora de consumo, una diferencia por encima del umbral queda `sin_datos` en vez de `no_cuadra` (una dentro del umbral sigue `ok`) **(mío)**.

### 9.4 Reglas de marcado **(usuario aprobó estos valores por defecto)**

- **kWh:** se marca si el total o algún tramo P1/P2/P3 difiere en **más de 1 kWh**.
- **€:** se compara solo **potencia + energía** de la factura (`Por potencia contratada` + `Por energía consumida`) con `power_cost` + `energy_cost` de e-data. Se marca si difieren en **más de un 2 %**. El resto de conceptos (bono social, impuestos, alquiler, intereses, IVA) solo se muestran **(usuario aceptó)**. Verificado: `power_term` y `energy_term` de e-data **incluyen el impuesto eléctrico y el IVA** con sus fórmulas por defecto (`electricity_tax * iva_tax * …`, con `electricity_tax = 1,0511300560` e `iva_tax = 1,21`). Por eso la factura se lleva a la misma base **(mío)**: `factura_€ = (potencia + energía) × (1 + impuesto_eléctrico / (potencia + energía + bono_social)) × (1 + IVA / 100)`, y se compara con `power_cost + energy_cost`. Δ € = factura_€ − e-data_€ y Δ % = Δ € / e-data_€ × 100. Si el usuario cambió las fórmulas de e-data, la comparación pierde sentido; se documenta en el README.
- Si no hay costes de e-data: la columna en € muestra "—" y no cuenta para el marcado.
- **Lecturas estimadas:** nunca se marcan como discrepancia, solo llevan la etiqueta "estimada", y su diferencia se muestra en gris.
- **Factura real después de estimadas (ventana combinada) (usuario):** una factura con lectura real que llega tras una o más estimadas consecutivas del mismo contrato regulariza lo estimado. Por eso no se compara solo con su propio periodo. Se toma la ventana desde el inicio de la primera estimada del grupo hasta el final de la real (con la regla de §9.3: del día siguiente a su `period_start` al día siguiente al `period_end` de la real), y se compara la suma de lo facturado (kWh total, P1/P2/P3, y potencia + energía en €) con Datadis/e-data en esa ventana, con los mismos umbrales. El estado resultante es el de la factura real. Las estimadas del grupo mantienen la etiqueta "estimada" y quedan vinculadas al grupo. En la tabla, la fila de la factura real indica que la comparación abarca N facturas, y el desplegable muestra cuáles. Si la estimada más antigua del grupo empieza antes de la primera factura disponible, o Datadis no cubre la ventana, el estado es `sin_datos`. Mientras la última factura sea estimada, solo lleva la etiqueta, a la espera de la real. Reglas añadidas durante la ejecución **(mío)**: el grupo tiene que ser contiguo (cada `period_start` es igual al `period_end` anterior, porque las facturas consecutivas comparten la fecha frontera, §9.3; si empieza después hay un hueco y si empieza antes, un solape), y la real queda `sin_datos` si hay un hueco, si el grupo contiene una factura `no_leida` o si la primera estimada es la factura más antigua guardada del contrato, porque no se sabe si había estimadas anteriores.
- **Factura ilegible dentro de un grupo:** una factura real `no_leida` cierra el grupo pero no se compara con él (la siguiente real empieza un grupo nuevo), y una estimada `no_leida` se une al grupo pendiente y hace que la real que lo cierra quede `sin_datos`.
- **Hueco antes del grupo:** si la primera estimada del grupo no es contigua con la factura anterior guardada del contrato (no empieza el día en que acaba esa factura: falta una), la real que lo cierra queda `sin_datos`: la que falta pudo ser también una estimada y una discrepancia falsa es un anti-objetivo (§4).
- **Hueco antes de una real sin estimadas (mío):** una real que no es contigua con la factura anterior guardada del contrato (su `period_start` no es el `period_end` de esa factura, aunque sea `no_leida`) también queda `sin_datos`, porque la que falta pudo regularizar parte de ella; la factura más antigua guardada sí se compara.
- Umbrales configurables en opciones.

Estados de una factura: `ok`, `no_cuadra`, `estimada`, `sin_datos` (sin e-data o fuera del rango de Datadis), `no_leida` (falló la comprobación interna), y `gas` (sin casación) **(mío)**.

## 10. Entidades

Un **dispositivo por contrato** (luz y gas por separado; uno nuevo aparece solo) **(mío)**. `has_entity_name`, `unique_id` estables (basados en contrato y clave), `runtime_data`, coordinador en `coordinator.py`, entidad base en `entity.py`.

**€/kWh (mío):** es el **importe total de la factura ÷ kWh facturados**, es decir, lo que de verdad pagas por kWh, como en la tabla de referencia. El precio del término de energía (€/kWh del desglose) se muestra en la fila desplegable.

Sensores de la **última factura** de cada contrato **(mío; lista ajustable por el builder)**: importe (€), kWh, €/kWh, fecha de emisión, periodo (inicio/fin), estado (sensor `enum`), y en luz la diferencia en kWh y en €. Sin `state_class` en los importes de factura, para que no generen estadísticas que confundan al panel de Energía. Botón "Buscar facturas ahora".

El histórico **no** va en atributos (anti-objetivo §4); la tarjeta y el panel lo piden por websocket.

## 11. Interfaz

### 11.1 API websocket **(mío)**

- `curenergia/invoices` → facturas de una entrada/contrato con su casación (valores factura, valores e-data, diferencias, estado, desglose de conceptos y P1/P2/P3).
- `curenergia/summary` → los datos de la cabecera del panel.

Los nombres concretos y el formato quedan al builder.

### 11.2 Tarjeta y panel (ver el boceto: opciones B y C)

Boceto con datos inventados: [`2026-10-29-curenergia-boceto.html`](2026-10-29-curenergia-boceto.html) (opción A descartada). Es orientativo: indica la estructura y la información que se muestra, no el estilo exacto. Debe respetar el tema de Home Assistant.

Un único componente de tabla compartido por la tarjeta y el panel **(mío)**:

- Pestañas **Luz / Gas**.
- Columnas de luz: periodo · kWh factura · kWh Datadis · Δ kWh · importe · Δ €. Columnas de gas: periodo · kWh · m³ · importe · €/kWh. **Decisión del usuario sobre las columnas de luz:** no hay columna «€ e-data», porque no se puede restar del importe total de la factura; «Importe» es el total de la factura y «Δ €» es la diferencia en potencia + energía, que es la parte de la factura que se puede comparar con e-data (§9). El detalle desplegable muestra «Potencia + energía: factura X € / e-data Y €» y el Δ %.
- Color de la diferencia según el estado: verde ok, ámbar no cuadra, gris estimada, sin datos y gas, rojo no leída. Etiqueta "estimada" y "no se pudo leer".
- Fila desplegable con el desglose de conceptos de la factura y P1/P2/P3 (factura / Datadis). Si la factura se compara en grupo (una real tras estimadas), el detalle separa «Esta factura» de «Comparación del grupo».

**Tarjeta** `custom:curenergia-invoices-card`: el JS lo sirve y registra la propia integración (rutas estáticas + `add_extra_js_url`), sin añadir recursos a mano ni instalar nada aparte en HACS **(mío)**. La tarjeta tiene **editor visual** (decisión del usuario): título, pestaña inicial, número máximo de facturas (1–60, por defecto 6) y cuenta de correo opcional.

**Panel** en la barra lateral ("Facturas", `mdi:receipt-text`), registrado por la integración con `panel_custom`, activable en opciones y **solo para administradores** por defecto **(mío)**. Muestra:

- cabecera con: total facturado en los últimos 12 meses, diferencia % de kWh entre factura y Datadis, número de lecturas estimadas;
- gráfico de barras por factura (factura frente a Datadis) que representa los **kWh**;
- la tabla compartida.

Tecnología del frontend **(mío)**: TypeScript + Lit, empaquetado con Rollup; el JS compilado se incluye en la release dentro de `custom_components/curenergia/frontend/`. El tipo de gráfico (SVG propio u otra librería) queda al builder.

## 12. Idiomas

Textos en inglés (obligatorio en `strings.json`) y español en `translations/es.json` **(mío)**. La tarjeta y el panel también en los dos idiomas, según el idioma de Home Assistant.

## 13. Calidad (Bronze voluntario)

`quality_scale.yaml` en la integración con todas las reglas Bronze vigentes marcadas como `done` o `exempt` con motivo (por ejemplo, `action-setup`: exenta porque no hay acciones; se usa un botón). CI en GitHub Actions: `hassfest`, validación de HACS, tests con `pytest-homeassistant-custom-component`, cobertura del config flow al 100 % (`config-flow-test-coverage`), tests de la librería y publicación en PyPI desde releases etiquetadas. Logo/brand **(builder)**: usar lo que HA/HACS admita en ese momento para integraciones personalizadas.

## 14. Privacidad y seguridad

- Diagnósticos con datos ocultos: CUPS, NIF, nombre, dirección, contrato, correo y contraseña.
- Logs sin datos personales ni contenido de los correos.
- **Fixtures de test:** se generan a partir de las facturas reales sustituyendo todos los datos personales por valores inventados con el mismo formato. Nunca se suben al repositorio los PDF ni el texto real. El usuario puede aportar más facturas (hay unas 12 de luz en su correo) para ampliar las fixtures; conviene cubrir varias, incluida alguna con lectura estimada y alguna con intereses de demora.
- `.gitignore` excluye `*.pdf` fuera de las fixtures anonimizadas.

## 15. Riesgos

- **Cambio de formato del PDF** o del correo de CurEnergía: mitigado con la comprobación interna (§8.2), que hace visible el fallo como "no se pudo leer" en lugar de dar datos falsos, y con tests sobre fixtures.
- **Frontera del periodo** mal elegida: dará diferencias en todas las facturas. Se valida con datos reales (§9.3).
- **e-data cambia sus estadísticas o su forma de calcular el coste**: la casación en € es opcional y degrada a "—".
- **Google Workspace** bloquea IMAP o las contraseñas de aplicación: se documenta.

## 16. Queda al builder

Nombre del paquete en PyPI, versión mínima de HA, nombres de la API websocket y su formato, elección de librería del gráfico, lista final de sensores, logo, y la verificación de la frontera del periodo (§9.3) con los datos reales del usuario. Los puntos **(builder)** de §9.2 y §9.4 ya están verificados.
