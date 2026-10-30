import type { HomeAssistant } from "./types";

const ES = {
  // Statuses (plan 2 texts)
  status_ok: "Cuadra",
  status_mismatch: "No cuadra",
  status_estimated: "Lectura estimada",
  status_no_data: "Sin datos suficientes",
  status_unreadable: "No se pudo leer",
  status_gas: "Gas (sin casar)",
  // Pills next to the period
  pill_estimated: "estimada",
  pill_unreadable: "no se pudo leer",
  // Tabs
  tab_electricity: "Luz",
  tab_gas: "Gas",
  // Electricity columns
  col_period: "Periodo",
  col_kwh_invoice: "kWh factura",
  col_kwh_edata: "kWh Datadis",
  col_delta_kwh: "Δ kWh",
  col_amount: "Importe",
  col_delta_eur: "Δ €",
  // Gas columns
  col_kwh: "kWh",
  col_m3: "m³",
  col_price_kwh: "€/kWh",
  // Expandable row
  detail_power_energy: "Potencia + energía: factura {invoice} / e-data {edata}",
  detail_delta_pct: "Diferencia: {pct}",
  detail_number: "Nº de factura",
  detail_issued: "Emitida el {date}",
  detail_window: "Ventana e-data: {period}",
  detail_group: "Comparada junto con: {numbers}",
  detail_in_group_of: "Incluida en la comparación de {number}",
  detail_periods: "kWh por periodo (P1 / P2 / P3)",
  detail_concepts: "Conceptos",
  detail_vat: "IVA {rate} sobre {base}: {amount}",
  detail_energy_price: "Precio de la energía: {price}",
  detail_problems: "Avisos de lectura",
  // Card states
  card_title: "Facturas",
  loading: "Cargando…",
  empty: "Todavía no hay facturas",
  error: "No se pudieron cargar las facturas",
  retry: "Reintentar",
  // Chart
  chart_title: "Importe por factura",
  chart_empty: "Sin datos para el gráfico",
  // Panel
  panel_title: "Facturas",
  panel_billed_12m: "Facturado en 12 meses",
  panel_kwh_delta: "Diferencia de kWh",
  panel_estimated_count: "Facturas con lectura estimada",
  panel_unreadable: "Correos que no se pudieron leer",
  panel_unsupported: "Correos no soportados",
  panel_last_check: "Último correo comprobado",
  panel_never: "Nunca",
  panel_mail_error: "No se pudo acceder al buzón",
  panel_all_entries: "Todas las cuentas",
  panel_entry: "Cuenta",
  // Card editor
  editor_title: "Título",
  editor_supply: "Pestaña inicial",
  editor_max_invoices: "Número máximo de facturas",
  editor_entry_id: "Cuenta de correo (opcional)",
  editor_entry_all: "Todas",
} as const;

export type StringKey = keyof typeof ES;

const EN: Record<StringKey, string> = {
  status_ok: "Matches",
  status_mismatch: "Does not match",
  status_estimated: "Estimated reading",
  status_no_data: "Not enough data",
  status_unreadable: "Could not be read",
  status_gas: "Gas (not matched)",
  pill_estimated: "estimated",
  pill_unreadable: "could not be read",
  tab_electricity: "Electricity",
  tab_gas: "Gas",
  col_period: "Period",
  col_kwh_invoice: "Invoice kWh",
  col_kwh_edata: "Datadis kWh",
  col_delta_kwh: "Δ kWh",
  col_amount: "Amount",
  col_delta_eur: "Δ €",
  col_kwh: "kWh",
  col_m3: "m³",
  col_price_kwh: "€/kWh",
  detail_power_energy: "Power + energy: invoice {invoice} / e-data {edata}",
  detail_delta_pct: "Difference: {pct}",
  detail_number: "Invoice no.",
  detail_issued: "Issued on {date}",
  detail_window: "e-data window: {period}",
  detail_group: "Compared together with: {numbers}",
  detail_in_group_of: "Included in the comparison of {number}",
  detail_periods: "kWh by period (P1 / P2 / P3)",
  detail_concepts: "Line items",
  detail_vat: "VAT {rate} on {base}: {amount}",
  detail_energy_price: "Energy price: {price}",
  detail_problems: "Reading warnings",
  card_title: "Invoices",
  loading: "Loading…",
  empty: "No invoices yet",
  error: "Could not load the invoices",
  retry: "Retry",
  chart_title: "Amount per invoice",
  chart_empty: "No data for the chart",
  panel_title: "Invoices",
  panel_billed_12m: "Billed in 12 months",
  panel_kwh_delta: "kWh difference",
  panel_estimated_count: "Invoices with estimated reading",
  panel_unreadable: "E-mails that could not be read",
  panel_unsupported: "Unsupported e-mails",
  panel_last_check: "Last e-mail checked",
  panel_never: "Never",
  panel_mail_error: "Could not access the mailbox",
  panel_all_entries: "All accounts",
  panel_entry: "Account",
  editor_title: "Title",
  editor_supply: "Initial tab",
  editor_max_invoices: "Maximum number of invoices",
  editor_entry_id: "Mail account (optional)",
  editor_entry_all: "All",
};

export const STRINGS: { es: Record<StringKey, string>; en: Record<StringKey, string> } = {
  es: ES,
  en: EN,
};

/** Language tag to feed `Intl`: the user's locale, falling back to HA's language. */
export function languageOf(hass: HomeAssistant): string {
  return hass.locale?.language || hass.language || "en";
}

/** Spanish when the locale starts with `es`; English otherwise. */
export function t(
  hass: HomeAssistant,
  key: StringKey,
  vars?: Record<string, string | number>,
): string {
  const table = languageOf(hass).toLowerCase().startsWith("es") ? STRINGS.es : STRINGS.en;
  const text = table[key];
  if (!vars) return text;
  return text.replace(/\{(\w+)\}/g, (placeholder, name: string) =>
    name in vars ? String(vars[name]) : placeholder,
  );
}
