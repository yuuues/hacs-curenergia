# CurEnergía Facturas para Home Assistant

> **English summary.** Custom Home Assistant integration (HACS) that reads your
> CurEnergía invoices from an e-mail mailbox over IMAP, extracts the data from
> the PDF (library [`pycurenergia`](https://github.com/yuuues/hacs-curenergia/tree/main/lib)) and compares each electricity invoice
> with the consumption and cost that the **e-data** integration (Datadis)
> stores in Home Assistant. It only **flags** differences; it does nothing else.
> It is **not** an official CurEnergía, Iberdrola or Home Assistant project.
> Install it from HACS as a custom repository (the repository must be public),
> set up a mailbox label, add the integration, and read the status table below.
> The integration also serves its own Lovelace card (`custom:curenergia-invoices-card`,
> edited with Home Assistant's native visual editor: title, initial tab, maximum number
> of invoices, mail account) and an optional admin-only sidebar panel "Facturas" (KPIs,
> one kWh chart per electricity contract showing each invoice's own figures against
> Datadis, and the same invoice table); no extra resources or HACS frontend installs are needed. Both follow
> the Home Assistant theme and language (Spanish or English).
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

Estado actual (0.2.0): sensores de la última factura de cada contrato, botón para
buscar facturas ahora, API websocket (`curenergia/invoices`, `curenergia/summary`),
una **tarjeta Lovelace** con editor visual (el nativo de Home Assistant) y un **panel lateral** «Facturas» (solo
administradores) que se puede activar o desactivar con la opción «Mostrar panel
lateral». Ver [Tarjeta y panel](#tarjeta-y-panel).

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
| Intervalo de revisión (horas) | 6 | Cada cuánto se mira el buzón (1–24). |
| Umbral de kWh | 1 | Se marca si la diferencia es **mayor** que este valor. |
| Umbral de importe (%) | 2 | Se marca si la diferencia en € es **mayor** que este porcentaje. |
| Mostrar panel lateral | sí | Muestra el panel «Facturas» en la barra lateral (solo administradores). Ver [Tarjeta y panel](#tarjeta-y-panel). |
| Guardar los PDF de las facturas | no | Guarda una copia (ver abajo). |
| Entrada de e-data | automático | Con qué entrada de e-data comparar. |

Los umbrales son estrictos: una diferencia **igual** al umbral no se marca.

**Guardar PDFs.** Si se activa, cada factura nueva se guarda como
`config/curenergia/<número de factura>.pdf`. Solo se guardan los números de factura
que son un nombre de fichero seguro (letras, cifras, `_` y `-`), nunca se
sobrescribe un fichero existente y nada se escribe fuera de esa carpeta. Esas
copias contienen tus datos personales: protégelas como tu copia de seguridad.

**Vínculo con e-data.** En modo automático se busca la entrada de e-data con el
mismo CUPS que la factura (se comparan los 20 primeros caracteres, sin distinguir
mayúsculas, porque el CUPS puede llevar 2 caracteres más). Si eliges una entrada a
mano, solo se aplica cuando hay **un único CUPS de luz sin pareja automática** y
esa entrada no está ya vinculada automáticamente a otro CUPS de luz; si hay dos o
más sin pareja, ninguno se vincula (para no comparar dos contadores con el mismo
e-data).

## Tarjeta y panel

La propia integración sirve el JavaScript de la tarjeta y del panel (ruta
`/curenergia_static/curenergia.js`) y lo carga en todas las vistas de Home Assistant:
**no hay que añadir recursos de Lovelace ni instalar nada más en HACS**. Tras
actualizar a esta versión reinicia Home Assistant y recarga el navegador (Ctrl+F5)
para que se cargue el módulo nuevo. Ambos usan solo las variables del tema de Home
Assistant y el idioma de tu perfil (español si empieza por `es`; si no, inglés).

### Tabla de facturas

La tarjeta y el panel comparten la misma tabla, con pestañas **Luz** y **Gas**:

- **Luz:** Periodo · kWh factura · kWh Datadis · Δ kWh · Importe · Δ €.
  *Importe* es el total de la factura (con impuestos, bono social, alquiler, etc.).
  *Δ €* es la diferencia de la parte comparable, **potencia + energía**, entre la
  factura y e-data (ver [Cómo se comparan los €](#cómo-se-comparan-los-)); por eso no
  hay una columna «€ e-data»: no se puede restar del total.
- **Gas:** Periodo · kWh · m³ · Importe · €/kWh. No se casa con Datadis.
- Los valores que faltan se muestran como «—».
- El color de la diferencia sigue el estado: verde `ok`, ámbar `no_cuadra`, gris
  `estimada`, `sin_datos` y `gas`, rojo `no_leida`. Las facturas estimadas y las
  ilegibles llevan una pastilla «estimada» / «no se pudo leer».
- **Fila desplegable** (pulsa una fila o el periodo, también con el teclado): conceptos de la
  factura e IVA y, solo en las de **luz**, kWh por periodo P1/P2/P3 (factura / Datadis),
  «Potencia + energía: factura X € / e-data Y €» con la diferencia en % y precio de la
  energía. Si la factura se compara en grupo con otras (una real tras
  estimadas), el detalle separa **«Esta factura»** de **«Comparación del grupo»**.
- Si hay dos contratos del mismo suministro, cada uno lleva su subtítulo con el
  nombre del contrato. Sin facturas se muestra «Todavía no hay facturas».

### Tarjeta Lovelace

Añádela desde el selector de tarjetas («CurEnergía») o en YAML:

```yaml
type: custom:curenergia-invoices-card
title: Facturas de la luz
supply: electricity
max_invoices: 6
```

El **editor visual** es el formulario nativo de Home Assistant y muestra los mismos campos:

| Opción (YAML) | Editor | Valor por defecto | Para qué sirve |
|---|---|---|---|
| `title` | Título | «Facturas» | Título de la tarjeta. |
| `supply` | Pestaña inicial | `electricity` | Pestaña que se abre primero: `electricity` (luz) o `gas`. |
| `max_invoices` | Número máximo de facturas | 6 | Cuántas facturas se listan (de 1 a 60). |
| `entry_id` | Cuenta de correo (opcional) | todas | Limita la tarjeta a una entrada de la integración (solo útil con varias cuentas de correo). |

La tarjeta recarga los datos al mostrarse y después cada 15 minutos.

### Panel lateral «Facturas»

Aparece en la barra lateral (icono `mdi:receipt-text`) para los **administradores**;
los demás usuarios no lo ven. Muestra:

- **Cabecera:** facturado en los últimos 12 meses, diferencia % de kWh entre factura
  y Datadis y número de lecturas estimadas.
- Un **gráfico de barras** por cada contrato **de luz** (con su nombre si hay más de uno),
  con sus 12 facturas más recientes: los **kWh** propios de cada factura frente a los de
  Datadis en su propio periodo (en una factura comparada en grupo, el valor del grupo
  menos el de las estimadas que regulariza). Las estimadas y las ilegibles se dibujan
  más claras, con borde discontinuo.
- La tabla de arriba, con las facturas de todas las entradas de la integración.
- Avisos si hay correos con factura que no se pudieron leer, correos con facturas no
  soportadas (rectificativas o abonos) o demasiado grandes (más de 15 MB) o un error al
  leer el correo (en ese caso se siguen mostrando las facturas guardadas).

Para quitarlo, desactiva la opción **Mostrar panel lateral** en las opciones de la
integración (si hay varias entradas basta con que una lo tenga activado para que
aparezca). El título del panel en la barra lateral es «Facturas» en todos los
idiomas, porque Home Assistant no traduce el título de los paneles personalizados.

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
| `sin_datos` | No se puede comparar: no hay e-data, Datadis no cubre las fechas de la factura, falta la factura anterior o no se puede cerrar con seguridad el grupo de estimadas (ver más abajo). También cuando habría una diferencia pero a e-data le faltan horas. |
| `no_leida` | La comprobación interna del PDF falló (las sumas no cuadran). Indica un fallo del lector, no de CurEnergía. |
| `gas` | Factura de gas: se muestra sin casar. |

**Qué horas abarca una factura.** CurEnergía factura de lectura a lectura: una
factura «del 29 de agosto al 28 de septiembre» va de la lectura del día 29 a la del
día 28, y la siguiente empieza el mismo 28 de septiembre (dos facturas seguidas
comparten esa fecha). La lectura del primer día cierra la factura anterior, así que
la factura `inicio a fin` se compara con e-data en `[inicio + 1 día 00:00, fin + 1 día
00:00)`, en la zona horaria de Home Assistant. Esta regla sale de comparar facturas
reales con Datadis.

**Cobertura de Datadis.** Esa ventana se considera cubierta si e-data tiene casi
todas sus horas (como mucho 2 menos), la primera empieza antes de que pasen 2 horas
desde el inicio de la ventana y la última empieza como mucho 3 horas antes de su
final. El cambio de hora (octubre/marzo) se tiene en cuenta. Si no se cumple, el
estado es `sin_datos`.

**Datos incompletos nunca dan `no_cuadra`.** Si a e-data le falta alguna hora
dentro de la ventana (aunque esté cubierta), una diferencia por encima del umbral
se muestra como `sin_datos`, porque puede deberse a esas horas; si la diferencia
está dentro del umbral, queda `ok`. Los costes de e-data solo se usan si
`power_cost` y `energy_cost` cumplen la misma regla de cobertura; si no, la parte en
€ no se calcula.

**Falta la factura anterior.** Una factura real cuyo periodo no empieza el mismo
día en que acaba la factura anterior guardada de ese contrato (porque falta una
factura o porque se solapan) queda `sin_datos`: la que falta pudo regularizar
parte de esta. La factura más antigua guardada sí se compara.

**Facturas estimadas seguidas de una real.** Una factura real tras una o más
estimadas regulariza lo estimado, así que se compara la suma de todo el grupo
(del día siguiente al inicio de la primera estimada al día siguiente al final de la
real). El grupo debe ser contiguo (cada periodo empieza el día en que acaba el
anterior). La real queda `sin_datos` si hay un hueco o falta una factura anterior,
si el grupo contiene una factura `no_leida`, o si la primera estimada es la factura
más antigua guardada (no se sabe si había más estimadas antes). Una real ilegible
cierra el grupo sin compararse con él.

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
- Los **diagnósticos** ocultan servidor IMAP, usuario, contraseña, carpeta, CUPS,
  contrato y número de factura. Del buzón solo dan contadores: correos de
  CurEnergía en la carpeta, si la última revisión la leyó entera y el tipo del
  último error (sin su mensaje).
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

### Primera sincronización y correos grandes

La primera vez se descargan todos los correos de facturas de la carpeta, **por
lotes de 20**; tras cada lote se guarda lo leído, así que si la conexión se corta
la siguiente revisión sigue donde se quedó. En cada revisión se leen como mucho
unos 1000 correos; el resto, en las siguientes. Los correos de **más de 15 MB** no se
descargan: se cuentan como no soportados (`unsupported_emails`) y no se reintentan.

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
