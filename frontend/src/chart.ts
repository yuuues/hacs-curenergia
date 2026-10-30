import { LitElement, css, html, nothing, svg } from "lit";
import type { SVGTemplateResult, TemplateResult } from "lit";
import { formatKwh } from "./format";
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

interface Point {
  label: string;
  invoice: number | null;
  datadis: number | null;
}

/** `2026-08-28` -> `08/26`, built from the text (no `Date`, so no timezone shift). */
function monthLabel(iso: string): string {
  const match = /^(\d{4})-(\d{2})/.exec(iso);
  return match ? `${match[2]}/${match[1].slice(2)}` : iso;
}

function oldestFirst(a: InvoiceRow, b: InvoiceRow): number {
  return (
    a.period_end.localeCompare(b.period_end) ||
    a.issue_date.localeCompare(b.issue_date) ||
    a.number.localeCompare(b.number)
  );
}

/** Bar chart of kWh per electricity invoice: invoice against Datadis. */
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
  `;

  /** The 12 most recent electricity invoices, oldest first. */
  private _points(): Point[] {
    return this.invoices
      .filter((invoice) => invoice.supply === "electricity")
      .sort(oldestFirst)
      .slice(-MAX_INVOICES)
      .map((invoice) => ({
        label: monthLabel(invoice.period_end),
        // Same figures as the table: the comparison's, when there is one.
        invoice: invoice.comparison?.invoice_kwh ?? invoice.kwh,
        datadis: invoice.comparison?.edata_kwh ?? null,
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

    const bar = (
      kind: "invoice" | "datadis",
      x: number,
      value: number,
      period: string,
    ): SVGTemplateResult => {
      const height = heightOf(value);
      const name = kind === "invoice" ? invoiceLabel : datadisLabel;
      return svg`<rect
        class="bar ${kind}"
        x=${x}
        y=${BASELINE - height}
        width=${barWidth}
        height=${height}
        rx="2"
      ><title>${name} ${period}: ${formatKwh(lang, value)}</title></rect>`;
    };

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
                  point.label,
                )
              : nothing}
            ${point.datadis !== null
              ? bar(
                  "datadis",
                  point.invoice !== null ? center + 1 : center - barWidth / 2,
                  point.datadis,
                  point.label,
                )
              : nothing}
            <text class="x-label" x=${center} y=${HEIGHT - 8} text-anchor="middle">${point.label}</text>
          `;
        })}
      </svg>
      <div class="legend">
        <span><i class="swatch invoice"></i>${invoiceLabel}</span>
        <span><i class="swatch datadis"></i>${datadisLabel}</span>
      </div>
    `;
  }
}

if (!customElements.get("curenergia-bar-chart")) {
  customElements.define("curenergia-bar-chart", CurenergiaBarChart);
}
