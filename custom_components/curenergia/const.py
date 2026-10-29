"""Constantes de la integración CurEnergía."""

DOMAIN = "curenergia"

# Remitente fijo de las facturas.
SENDER = "noresponder@clientescurenergia.es"

# Claves de las opciones.
CONF_FOLDER = "folder"
CONF_SCAN_HOURS = "scan_hours"
CONF_KWH_THRESHOLD = "kwh_threshold"
CONF_EUR_THRESHOLD_PCT = "eur_threshold_pct"
CONF_SHOW_PANEL = "show_panel"
CONF_SAVE_PDFS = "save_pdfs"
CONF_EDATA_ENTRY = "edata_entry"

# Valor de ``CONF_EDATA_ENTRY`` que significa vínculo automático con e-data.
EDATA_AUTO = "auto"

# Valores por defecto.
DEFAULT_HOST = "imap.gmail.com"
DEFAULT_PORT = 993
DEFAULT_SCAN_HOURS = 6
DEFAULT_KWH_THRESHOLD = 1.0
DEFAULT_EUR_THRESHOLD_PCT = 2.0
