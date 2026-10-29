# CurEnergía Facturas para Home Assistant

> **English summary.** Custom Home Assistant integration (HACS) that reads your
> CurEnergía invoices from an e-mail mailbox over IMAP, extracts the data from
> the PDF (library [`pycurenergia`](lib/)) and compares each electricity invoice
> with the consumption and cost that the **e-data** integration (Datadis)
> stores in Home Assistant. It only **flags** differences; it does nothing else.
> It is **not** an official CurEnergía, Iberdrola or Home Assistant project.
> Install it from HACS as a custom repository (the repository must be public),
> set up a mailbox label, add the integration, and read the status table below.
> Everything is documented in Spanish; the status names (`ok`, `no_cuadra`,
> `estimada`, `sin_datos`, `no_leida`, `gas`) are the same in every language.

## Qué hace

Si eres cliente de CurEnergía y tienes en Home Assistant la integración
[e-data](https://github.com/uvejota/homeassistant-edata), esta integración
**casa lo que te facturan con lo que dice Datadis**:

- Lee automáticamente los correos de facturas de `noresponder@clientescurenergia.es`
  (IMAP, solo lectura) y extrae del PDF adjunto el periodo, los kWh, el importe,
  el €/kWh y el desglose de conceptos.
- Para cada factura de **luz**, compara los kWh (total y P1/P2/P3) y los € con los
  que e-data tiene para las mismas fechas, y la marca como `ok` o `no_cuadra`.
- Las facturas de **gas** se muestran sin casar (Datadis no tiene gas).
- No tienes que descargar ni subir PDFs a mano. No modifica el buzón: no marca,
  mueve ni borra correos.
- No actúa ante una discrepancia (no envía avisos ni reclama): solo la marca.

**No es un proyecto oficial.** No está relacionado con CurEnergía, Iberdrola, Datadis ni Home Assistant.
No accede a la web ni a la API de CurEnergía.

Estado actual: sensores de la última factura de cada contrato, botón para buscar
facturas ahora y API websocket (`curenergia/invoices`, `curenergia/summary`).
La tarjeta Lovelace y el panel lateral llegarán en una versión posterior; la
opción «Mostrar panel lateral» ya existe, pero todavía no hace nada.

## Instalación (HACS)

1. En Home Assistant abre **HACS → ⋮ → Repositorios personalizados**, añade
   `https://github.com/yuuues/hacs-curenergia` con la categoría **Integración**
   e instálala.
2. Reinicia Home Assistant.
3. **Ajustes → Dispositivos y servicios → Añadir integración → CurEnergía Facturas**.

> **Importante:** HACS solo puede instalar repositorios **públicos** de GitHub.
> Si el repositorio todavía es privado, hay que hacerlo público antes de añadirlo a HACS.

Requisitos: Home Assistant 2026.3.0 o superior y, para comparar con Datadis, la
integración e-data instalada y funcionando.

## Preparar el correo

La integración lee una **carpeta** del buzón (en Gmail, una etiqueta es una carpeta).

### Recomendado: filtro + etiqueta

1. En Gmail crea un filtro: **De** `noresponder@clientescurenergia.es` →
   **Aplicar la etiqueta** `CurEnergia` (créala) y marca **Aplicar también a las
   conversaciones existentes**.
2. Al configurar la integración, elige esa etiqueta como carpeta. Solo se leen
   los correos del remitente de CurEnergía aunque la carpeta contenga otros.
3. Crea una **contraseña de aplicación** de Google (requiere la verificación en
   dos pasos) y úsala como contraseña de la integración.

### Alternativa más segura: un buzón dedicado

Reenvía automáticamente esos correos a un buzón creado solo para esto y conecta la
integración a ese buzón. Así Home Assistant no tiene la llave de tu correo principal.

### Aviso importante

**Una contraseña de aplicación da acceso IMAP a todo el buzón**, no se puede
limitar a una etiqueta. Créala solo para esto, no la reutilices y revócala si dejas
de usar la integración. Si no te basta con la etiqueta, usa el buzón dedicado.

### Google Workspace

Si tu correo está en Google Workspace, el **administrador** del dominio tiene que
permitir el acceso IMAP y las contraseñas de aplicación. Si no, el login fallará.
Para otros proveedores, indica su servidor IMAP (puerto 993, SSL) y una contraseña
de aplicación si la exigen.

## Configuración

Al añadir la integración se te pide:

1. Servidor IMAP (`imap.gmail.com`), puerto (`993`), usuario y contraseña de
   aplicación. Se prueba el login antes de crear la entrada.
2. La carpeta donde están los correos. Se preselecciona una cuyo nombre contenga
   «curenergia» si existe; si no, `[Gmail]/All Mail` o `INBOX`.

Solo puede haber una entrada por `usuario@servidor`. Si la contraseña deja de
valer, Home Assistant te pide reautenticarte.

### Opciones

| Opción | Valor por defecto | Para qué sirve |
|---|---|---|
| Carpeta | la elegida | Carpeta del buzón. Cambiarla descarta el estado guardado del buzón y se lee desde cero. |
| Intervalo (horas) | 6 | Cada cuánto se mira el buzón (1–24). |
| Umbral de kWh | 1 | Se marca si la diferencia es **mayor** que este valor. |
| Umbral de importe (%) | 2 | Se marca si la diferencia en € es **mayor** que este porcentaje. |
| Mostrar panel lateral | sí | Reservada para el panel de una versión posterior. |
| Guardar PDF de las facturas | no | Guarda una copia (ver abajo). |
| Entrada de e-data | automático | Con qué entrada de e-data comparar. |

Los umbrales son estrictos: una diferencia **igual** al umbral no se marca.

**Guardar PDFs.** Si se activa, cada factura nueva se guarda como
`config/curenergia/<número de factura>.pdf`. Solo se guardan los números de factura
que son un nombre de fichero seguro (letras, cifras, `_` y `-`), nunca se
sobrescribe un fichero existente y nada se escribe fuera de esa carpeta. Esas
copias contienen tus datos personales: protégelas como tu copia de seguridad.

**Vínculo con e-data.** En modo automático se busca la entrada de e-data con el
mismo CUPS que la factura. Si eliges una entrada a mano, solo se aplica cuando hay
**un único CUPS de luz sin pareja automática**; si hay dos o más sin pareja,
ninguno se vincula (para no comparar dos contadores con el mismo e-data).

## Entidades

Hay un dispositivo por contrato, llamado `CurEnergía luz` o `CurEnergía gas` (si
hay más de uno del mismo tipo se añaden los 4 últimos dígitos del contrato), y un
dispositivo de servicio `CurEnergía` con el botón.

Sensores de la **última factura** de cada contrato: importe, kWh, €/kWh (importe
total ÷ kWh), fecha de emisión, inicio y fin del periodo y estado; en luz, además,
la diferencia en kWh y en €. Los importes no llevan `state_class`, así que no generan
estadísticas ni ensucian el panel de Energía. Todo el histórico va por websocket,
no en atributos.

El botón **Buscar facturas ahora** lee el buzón sin esperar al sondeo.

## Qué significa cada estado

| Estado | Significado |
|---|---|
| `ok` | La factura cuadra con e-data dentro de los umbrales. |
| `no_cuadra` | El total de kWh, algún tramo P1/P2/P3 o el importe difieren de e-data por encima del umbral. |
| `estimada` | La factura es de lectura estimada. **Nunca se marca**: las estimadas son normales y se regularizan en la siguiente factura real. |
| `sin_datos` | No se puede comparar: no hay e-data, Datadis no cubre las fechas de la factura o no se puede cerrar con seguridad el grupo de estimadas (ver más abajo). |
| `no_leida` | La comprobación interna del PDF falló (las sumas no cuadran). Indica un fallo del lector, no de CurEnergía. |
| `gas` | Factura de gas: se muestra sin casar. |

**Cobertura de Datadis.** Las fechas de una factura son `[inicio 00:00, fin + 1 día
00:00)` en la zona horaria de Home Assistant. Se consideran cubiertas si e-data
tiene casi todas las horas (como mucho 2 menos que las de la ventana), la primera
empieza como mucho 2 horas después del inicio y la última empieza como mucho 3
horas antes del final. El cambio de hora (octubre/marzo) se tiene en cuenta. Si no
se cumple, el estado es `sin_datos`.

**Facturas estimadas seguidas de una real.** Una factura real tras una o más
estimadas regulariza lo estimado, así que se compara la suma de todo el grupo
(desde el inicio de la primera estimada hasta el final de la real). El grupo debe
ser contiguo (cada periodo empieza el día después del anterior). La real queda
`sin_datos` si hay un hueco o falta una factura anterior, si el grupo contiene una
factura `no_leida`, o si la primera estimada es la factura más antigua guardada
(no se sabe si había más estimadas antes). Una real ilegible cierra el grupo sin
compararse con él.

## Cómo se comparan los €

e-data calcula `power_cost` y `energy_cost` **con el impuesto eléctrico y el IVA
incluidos**, mientras que en la factura son conceptos sin impuestos. Para
comparar lo equivalente, la factura se lleva a la misma base:

`factura_€ = (potencia + energía) × (1 + impuesto_eléctrico / (potencia + energía + bono_social)) × (1 + IVA / 100)`

y se compara con `power_cost + energy_cost` de e-data: Δ € = factura_€ − e-data_€ y
Δ % = Δ € / e-data_€ × 100. El bono social, el alquiler del contador, los intereses
de demora y otros conceptos no entran.

- **Necesita la facturación activada en e-data.** Sin ella no existen los costes: la
  parte en € no se calcula y no cuenta para el marcado (los kWh sí se comparan).
- **Si cambiaste las fórmulas de coste de e-data** (impuestos, precios), la
  comparación en € pierde sentido.

## Privacidad

- Los **logs** nunca incluyen CUPS, contrato, número de factura, nombre, dirección,
  correo, asunto ni texto del correo o del PDF; se identifica un correo por su UID.
- Los **diagnósticos** ocultan usuario, contraseña, CUPS, contrato y número de factura.
- Las facturas se guardan en el almacenamiento de Home Assistant (`.storage/curenergia.*`)
  de esa entrada, y la contraseña en la propia entrada de configuración. Los PDF solo
  se guardan si lo activas.
- No se envía nada a terceros: la integración solo habla con tu servidor IMAP y
  con el recorder local.
- En este repositorio no hay datos reales: los tests usan fixtures anonimizadas.

### Si el correo falla

Si el servidor IMAP no responde (corte de red, mantenimiento) y ya hay facturas
guardadas, se registra un aviso y **se siguen sirviendo los datos guardados**: los
sensores no pasan a «no disponible». Un login rechazado sí inicia la reautenticación.

### PDFs que no se pueden leer

Si un correo trae un PDF que la librería no entiende, no hay número de factura y,
por tanto, no hay fila. Se recuerda el correo junto con la versión de `pycurenergia`
y se **reintenta cuando esa versión cambia**; mientras tanto se cuenta como correo
ilegible en el resumen (`curenergia/summary`) y en los diagnósticos. Las facturas
rectificativas y los abonos no están soportados: se cuentan aparte y no se reintentan.

## Desinstalación

1. En **Ajustes → Dispositivos y servicios → CurEnergía Facturas**, elimina la entrada
   (esto borra sus dispositivos, entidades y las facturas guardadas).
2. En **HACS**, elimina la integración y reinicia Home Assistant.
3. Si guardabas PDFs, borra la carpeta `config/curenergia/` a mano.
4. **Revoca la contraseña de aplicación** en tu cuenta de correo (y borra el reenvío
   o el buzón dedicado si lo creaste).

## Problemas y contribuciones

Abre un [issue](https://github.com/yuuues/hacs-curenergia/issues) sin datos
personales. Los diagnósticos están pensados para poder adjuntarse, pero revísalos
antes de subirlos. Licencia: MIT.
