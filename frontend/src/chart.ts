import { LitElement, css, html, nothing, svg } from "lit";
import type { SVGTemplateResult, TemplateResult } from "lit";
import { formatKwh, formatPeriod } from "./format";
import { languageOf, t } from "./i18n";
import type { HomeAssistant, InvoiceRow } from "./types";

const MAX_INVOICES = 12;

const WIDTH = 640;
const HEIGHT = 236;
const PAD_LEFT = 64;
const PAD_RIGHT = 8;
const PAD_TOP = 16;
const PAD_BOTTOM = 24;
const BASELINE = HEIGHT - PAD_BOTTOM;
const PLOT_HEIGHT = BASELINE - PAD_TOP;
const PLOT_WIDTH = WIDTH - PAD_LEFT - PAD_RIGHT;
const MAX_BAR_WIDTH = 26;

type Mark = "estimated" | "unreadable" | null;

interface Point {
  /** X-axis label. */
  label: string;
  /** Full period, for the tooltip. */
  period: string;
  invoice: number | null;
  datadis: number | null;
  mark: Mark;
}

/**
 * `2026-08-28` -> `28/08` (`28/08/26` with `withYear`), built from the text
 * (no `Date`, so no timezone shift).
 */
function dayLabel(iso: string, withYear: boolean): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return iso;
  const day = `${match[3]}/${match[2]}`;
  return withYear ? `${day}/${match[1].slice(2)}` : day;
}

/**
 * Datadis kWh of the invoice's own period.
 *
 * A row whose comparison covers a group (a real invoice after estimated ones)
 * holds the Datadis figure of the whole group: the own share is that figure
 * minus the own Datadis figures of the other members (the rows settled by this
 * one). If any of them is missing, the share cannot be known: `null`.
 */
function ownDatadis(invoice: InvoiceRow, all: InvoiceRow[]): number | null {
  const comparison = invoice.comparison;
  if (!comparison || comparison.edata_kwh === null) return null;
  if (comparison.group.length <= 1) return comparison.edata_kwh;
  const members = all.filter((row) => row.in_group_of === invoice.number);
  const others = comparison.group.filter((number) => number !== invoice.number);
  let share = comparison.edata_kwh;
  for (const number of others) {
    const member = members.find((row) => row.number === number);
    const edata = member?.comparison?.edata_kwh ?? null;
    if (edata === null) return null;
    share -= edata;
  }
  // Same rounding as the websocket figures (2 decimals), without float noise.
  return Math.round(share * 100) / 100;
}

function markOf(invoice: InvoiceRow): Mark {
  if (invoice.status === "no_leida") return "unreadable";
  return invoice.estimated ? "estimated" : null;
}

function oldestFirst(a: InvoiceRow, b: InvoiceRow): number {
  return (
    a.period_end.localeCompare(b.period_end) ||
    a.issue_date.localeCompare(b.issue_date) ||
    a.number.localeCompare(b.number)
  );
}

/**
 * Bar chart of kWh per electricity invoice of one contract: the invoice's own
 * kWh against Datadis for its own period.
 */
export class CurenergiaBarChart extends LitElement {
  static properties = {
    hass: { attribute: false },
    invoices: { attribute: false },
  };

  declare hass?: HomeAssistant;
  declare invoices: InvoiceRow[];

  constructor() {
    super();
    this.invoices = [];
  }

  static styles = css`
    :host {
      display: block;
      color: var(--primary-text-color);
    }
    .title {
      font-weight: 500;
      margin: 8px 0;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    svg {
      display: block;
      width: 100%;
      height: auto;
    }
    .axis {
      stroke: var(--divider-color);
      stroke-width: 1;
    }
    .grid {
      stroke: var(--divider-color);
      stroke-width: 1;
      stroke-dasharray: 3 3;
    }
    text {
      fill: var(--secondary-text-color);
      font-size: 11px;
    }
    .bar.invoice {
      fill: var(--primary-color);
    }
    .bar.datadis {
      fill: var(--secondary-text-color);
    }
    /* Estimated or unreadable invoice figure: lighter fill and dashed outline. */
    .bar.invoice.estimated,
    .bar.invoice.unreadable {
      fill-opacity: 0.35;
      stroke: var(--primary-color);
      stroke-width: 1.5;
      stroke-dasharray: 3 2;
    }
    .bar.invoice.unreadable {
      stroke: var(--error-color);
    }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin: 4px 0 8px;
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .swatch {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 2px;
    }
    .swatch.invoice {
      background: var(--primary-color);
    }
    .swatch.datadis {
      background: var(--secondary-text-color);
    }
    .swatch.invoice.estimated,
    .swatch.invoice.unreadable {
      background: transparent;
      border: 1.5px dashed var(--primary-color);
      box-sizing: border-box;
    }
    .swatch.invoice.unreadable {
      border-color: var(--error-color);
    }
  `;

  /** The 12 most recent electricity invoices, oldest first. */
  private _points(): Point[] {
    const electricity = this.invoices.filter((invoice) => invoice.supply === "electricity");
    const shown = [...electricity].sort(oldestFirst).slice(-MAX_INVOICES);
    // Add the year only when the drawn invoices span more than one.
    const withYear = new Set(shown.map((invoice) => invoice.period_end.slice(0, 4))).size > 1;
    return shown.map((invoice) => ({
      label: dayLabel(invoice.period_end, withYear),
      period: formatPeriod(invoice.period_start, invoice.period_end),
      // Own figures, not the group's (the table shows the group's).
      invoice: invoice.kwh,
      datadis: ownDatadis(invoice, electricity),
      mark: markOf(invoice),
    }));
  }

  protected render(): TemplateResult | typeof nothing {
    const hass = this.hass;
    if (!hass) return nothing;
    const lang = languageOf(hass);
    const points = this._points();
    const values = points.flatMap((point) =>
      [point.invoice, point.datadis].filter((value): value is number => value !== null),
    );
    if (values.length === 0) {
      return html`<div class="message">${t(hass, "chart_empty")}</div>`;
    }
    const max = Math.max(...values, 0);
    const slot = PLOT_WIDTH / points.length;
    const barWidth = Math.min(slot * 0.36, MAX_BAR_WIDTH);
    const heightOf = (value: number): number =>
      max > 0 ? (Math.max(value, 0) / max) * PLOT_HEIGHT : 0;
    const invoiceLabel = t(hass, "chart_invoice");
    const datadisLabel = t(hass, "chart_datadis");

    const markLabel = (mark: Mark): string =>
      mark === "estimated"
        ? ` (${t(hass, "pill_estimated")})`
        : mark === "unreadable"
          ? ` (${t(hass, "pill_unreadable")})`
          : "";

    const bar = (
      kind: "invoice" | "datadis",
      x: number,
      value: number,
      point: Point,
    ): SVGTemplateResult => {
      const height = heightOf(value);
      const name = kind === "invoice" ? invoiceLabel : datadisLabel;
      // Only the invoice figure is estimated or unreadable; Datadis is measured.
      const mark = kind === "invoice" ? point.mark : null;
      return svg`<rect
        class="bar ${kind} ${mark ?? ""}"
        x=${x}
        y=${BASELINE - height}
        width=${barWidth}
        height=${height}
        rx="2"
      ><title>${name} ${point.period}: ${formatKwh(lang, value)}${markLabel(mark)}</title></rect>`;
    };
    const marks = new Set(points.map((point) => point.mark));

    return html`
      <div class="title">${t(hass, "chart_title")}</div>
      <svg
        viewBox="0 0 ${WIDTH} ${HEIGHT}"
        role="img"
        aria-label=${t(hass, "chart_title")}
        preserveAspectRatio="xMidYMid meet"
      >
        <line class="grid" x1=${PAD_LEFT} x2=${WIDTH - PAD_RIGHT} y1=${PAD_TOP} y2=${PAD_TOP} />
        <line
          class="axis"
          x1=${PAD_LEFT}
          x2=${WIDTH - PAD_RIGHT}
          y1=${BASELINE}
          y2=${BASELINE}
        />
        <text class="y-label" x=${PAD_LEFT - 6} y=${PAD_TOP + 4} text-anchor="end">${formatKwh(lang, max)}</text>
        ${points.map((point, index) => {
          const center = PAD_LEFT + slot * index + slot / 2;
          const paired = point.invoice !== null && point.datadis !== null;
          return svg`
            ${point.invoice !== null
              ? bar(
                  "invoice",
                  paired ? center - barWidth - 1 : center - barWidth / 2,
                  point.invoice,
                  point,
                )
              : nothing}
            ${point.datadis !== null
              ? bar(
                  "datadis",
                  point.invoice !== null ? center + 1 : center - barWidth / 2,
                  point.datadis,
                  point,
                )
              : nothing}
            <text class="x-label" x=${center} y=${HEIGHT - 8} text-anchor="middle">${point.label}</text>
          `;
        })}
      </svg>
      <div class="legend">
        <span><i class="swatch invoice"></i>${invoiceLabel}</span>
        <span><i class="swatch datadis"></i>${datadisLabel}</span>
        ${marks.has("estimated")
          ? html`<span><i class="swatch invoice estimated"></i>${t(hass, "pill_estimated")}</span>`
          : nothing}
        ${marks.has("unreadable")
          ? html`<span><i class="swatch invoice unreadable"></i>${t(hass, "pill_unreadable")}</span>`
          : nothing}
      </div>
    `;
  }
}

if (!customElements.get("curenergia-bar-chart")) {
  customElements.define("curenergia-bar-chart", CurenergiaBarChart);
}
