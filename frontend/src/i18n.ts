import type { HomeAssistant } from "./types";

const ES = {
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
  detail_delta_pct: "Δ {pct}",
  detail_group: "Comparada junto con: {numbers}",
  detail_in_group_of: "Regularizada en la factura {number}",
  detail_vat: "IVA {rate} sobre {base}: {amount}",
  detail_energy_price: "Precio de la energía: {price}",
  detail_period_row: "{period}: factura {invoice} / Datadis {edata}",
  row_covers: "abarca {n} facturas",
  detail_own_kwh: "Esta factura: {kwh}",
  detail_group_heading: "Comparación del grupo ({n} facturas)",
  // Card states
  card_title: "Facturas",
  loading: "Cargando…",
  empty: "Todavía no hay facturas",
  error: "No se pudieron cargar las facturas",
  card_description: "Facturas de CurEnergía comparadas con los datos de Datadis",
  // Chart
  chart_title: "kWh por factura",
  chart_empty: "Sin datos para el gráfico",
  chart_invoice: "Factura",
  chart_datadis: "Datadis",
  // Panel
  panel_title: "Facturas",
  panel_menu: "Menú",
  panel_billed_12m: "Facturado en 12 meses",
  panel_kwh_delta: "kWh factura vs Datadis",
  panel_estimated_count: "Lecturas estimadas",
  panel_unreadable: "{n} correos con factura que no se pudo leer",
  panel_unsupported: "Correos con factura no soportada (rectificativa o abono): {n}",
  panel_mail_error: "No se pudo leer el correo; se muestran las facturas guardadas",
  // Card editor
  editor_title: "Título",
  editor_supply: "Pestaña inicial",
  editor_max_invoices: "Número máximo de facturas",
  editor_entry_id: "Cuenta de correo (opcional)",
} as const;

export type StringKey = keyof typeof ES;

const EN: Record<StringKey, string> = {
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
  detail_delta_pct: "Δ {pct}",
  detail_group: "Compared together with: {numbers}",
  detail_in_group_of: "Settled by invoice {number}",
  detail_vat: "VAT {rate} on {base}: {amount}",
  detail_energy_price: "Energy price: {price}",
  detail_period_row: "{period}: invoice {invoice} / Datadis {edata}",
  row_covers: "covers {n} invoices",
  detail_own_kwh: "This invoice: {kwh}",
  detail_group_heading: "Group comparison ({n} invoices)",
  card_title: "Invoices",
  loading: "Loading…",
  empty: "No invoices yet",
  error: "Could not load the invoices",
  card_description: "CurEnergía invoices compared with Datadis data",
  chart_title: "kWh per invoice",
  chart_empty: "No data for the chart",
  chart_invoice: "Invoice",
  chart_datadis: "Datadis",
  panel_title: "Invoices",
  panel_menu: "Menu",
  panel_billed_12m: "Billed in 12 months",
  panel_kwh_delta: "Invoice kWh vs Datadis",
  panel_estimated_count: "Estimated readings",
  panel_unreadable: "{n} e-mails with an invoice could not be read",
  panel_unsupported: "E-mails with an unsupported invoice (corrective or credit note): {n}",
  panel_mail_error: "Could not read the mailbox; showing the saved invoices",
  editor_title: "Title",
  editor_supply: "Initial tab",
  editor_max_invoices: "Maximum number of invoices",
  editor_entry_id: "Mail account (optional)",
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
