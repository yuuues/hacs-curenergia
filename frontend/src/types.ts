/**
 * Types mirroring the websocket contract of the integration
 * (custom_components/curenergia/websocket.py) plus the minimal
 * subset of Home Assistant objects the frontend needs.
 */

export type Supply = "electricity" | "gas";

export type Status = "ok" | "no_cuadra" | "estimada" | "sin_datos" | "no_leida" | "gas";

export type ConceptKey =
  | "power"
  | "energy"
  | "social_bonus"
  | "electricity_tax"
  | "meter_rental"
  | "gas_fixed_term"
  | "gas_energy"
  | "gas_tax"
  | "other";

/** kWh or € split by tariff period. */
export interface PeriodValues {
  p1: number | null;
  p2: number | null;
  p3: number | null;
}

export interface Concept {
  key: ConceptKey;
  label: string;
  amount: number | null;
}

export interface Vat {
  rate: number | null;
  base: number | null;
  amount: number | null;
}

export interface Comparison {
  group: string[];
  window_start: string;
  window_end: string;
  invoice_kwh: number | null;
  invoice_periods: PeriodValues;
  invoice_eur: number | null;
  edata_kwh: number | null;
  edata_periods: PeriodValues;
  edata_eur: number | null;
  delta_kwh: number | null;
  delta_periods: PeriodValues;
  delta_eur: number | null;
  delta_pct: number | null;
}

/** Meter readings of an invoice: m³ for gas, one value per period for electricity. */
export interface MeterReadings {
  read_on: string;
  estimated: boolean;
  m3: number | null;
  periods: PeriodValues | null;
  previous: { read_on: string; estimated: boolean; m3: number | null } | null;
}

export interface InvoiceRow {
  number: string;
  supply: Supply;
  issue_date: string;
  period_start: string;
  period_end: string;
  estimated: boolean;
  status: Status;
  problems: string[];
  total: number | null;
  kwh: number | null;
  price_kwh: number | null;
  m3: number | null;
  energy_price_kwh: number | null;
  periods: PeriodValues | null;
  meter: MeterReadings | null;
  concepts: Concept[];
  vat: Vat;
  in_group_of: string | null;
  comparison: Comparison | null;
}

export interface ContractInvoices {
  entry_id: string;
  contract: string;
  supply: Supply;
  name: string;
  invoices: InvoiceRow[];
}

export interface InvoicesResponse {
  contracts: ContractInvoices[];
}

export interface Summary {
  billed_12m: number | null;
  kwh_delta_pct: number | null;
  estimated_count: number;
  unreadable_emails: number;
  unsupported_emails: number;
  last_mail_check: string | null;
  mail_error: boolean;
}

/** Minimal subset of Home Assistant's `hass` object. */
export interface HomeAssistant {
  language: string;
  locale: { language: string };
  connection: {
    sendMessagePromise<T>(msg: object): Promise<T>;
  };
}
