import type { Status } from "./types";

const DASH = "—";
const MINUS = "−";

/** Intl uses no-break spaces; replace them with plain ones. */
function plain(text: string): string {
  return text.replace(/[  ]/g, " ");
}

function number(lang: string, value: number, min: number, max: number): string {
  const options = { minimumFractionDigits: min, maximumFractionDigits: max };
  let formatter: Intl.NumberFormat;
  try {
    formatter = new Intl.NumberFormat(lang, options);
  } catch (error) {
    if (!(error instanceof RangeError)) throw error;
    formatter = new Intl.NumberFormat("en", options);
  }
  return plain(formatter.format(value));
}

/** `2026-08-29` -> `29/08/2026`, built from the text so no timezone shift can happen. */
export function formatDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : iso;
}

/** `29/08 – 28/09/2026`; with different years `29/12/2025 – 28/01/2026`. */
export function formatPeriod(start: string, end: string): string {
  const from = formatDate(start);
  const to = formatDate(end);
  if (start.slice(0, 4) === end.slice(0, 4)) {
    return `${from.slice(0, 5)} – ${to}`;
  }
  return `${from} – ${to}`;
}

export function formatKwh(lang: string, value: number | null): string {
  return value === null ? DASH : `${number(lang, value, 0, 2)} kWh`;
}

export function formatEur(lang: string, value: number | null): string {
  return value === null ? DASH : `${number(lang, value, 2, 2)} €`;
}

export function formatPricePerKwh(lang: string, value: number | null): string {
  return value === null ? DASH : `${number(lang, value, 4, 4)} €/kWh`;
}

export function formatPct(lang: string, value: number | null): string {
  return value === null ? DASH : `${number(lang, value, 1, 1)} %`;
}

/** Signed difference: `+5 kWh`, `−1,82 €`, and `0` without sign. */
export function formatDelta(lang: string, value: number | null, kind: "kwh" | "eur"): string {
  if (value === null) return DASH;
  const unit = kind === "kwh" ? "kWh" : "€";
  const digits: [number, number] = kind === "kwh" ? [0, 2] : [2, 2];
  const magnitude = number(lang, Math.abs(value), ...digits);
  // A value that rounds to zero is shown as plain zero, never as "+0" or "−0".
  const isZero = Number(Math.abs(value).toFixed(digits[1])) === 0;
  const sign = isZero ? "" : value < 0 ? MINUS : "+";
  return `${sign}${magnitude} ${unit}`;
}

/** Name of the HA theme variable that colours a delta for each status. */
export function deltaColorVar(status: Status): string {
  switch (status) {
    case "ok":
      return "--success-color";
    case "no_cuadra":
      return "--warning-color";
    case "no_leida":
      return "--error-color";
    default:
      return "--secondary-text-color";
  }
}
