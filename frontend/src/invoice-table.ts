import { LitElement, css, html, nothing } from "lit";
import type { TemplateResult } from "lit";
import {
  deltaColorVar,
  formatDelta,
  formatEur,
  formatKwh,
  formatM3,
  formatPct,
  formatPeriod,
  formatPricePerKwh,
  formatRate,
} from "./format";
import { languageOf, t } from "./i18n";
import type { StringKey } from "./i18n";
import type {
  Comparison,
  ContractInvoices,
  HomeAssistant,
  InvoiceRow,
  PeriodValues,
  Supply,
} from "./types";

const SUPPLIES: { supply: Supply; label: StringKey }[] = [
  { supply: "electricity", label: "tab_electricity" },
  { supply: "gas", label: "tab_gas" },
];

const PERIOD_KEYS: { key: keyof PeriodValues; name: string }[] = [
  { key: "p1", name: "P1" },
  { key: "p2", name: "P2" },
  { key: "p3", name: "P3" },
];

/** Newest first: by period end, then issue date, then number. */
function newestFirst(a: InvoiceRow, b: InvoiceRow): number {
  return (
    b.period_end.localeCompare(a.period_end) ||
    b.issue_date.localeCompare(a.issue_date) ||
    b.number.localeCompare(a.number)
  );
}

export class CurenergiaInvoiceTable extends LitElement {
  static properties = {
    hass: { attribute: false },
    contracts: { attribute: false },
    supply: { type: String },
    maxInvoices: { type: Number, attribute: "max-invoices" },
    _expanded: { state: true },
  };

  declare hass: HomeAssistant;
  declare contracts: ContractInvoices[];
  declare supply: Supply;
  declare maxInvoices?: number;
  declare _expanded: ReadonlySet<string>;

  constructor() {
    super();
    this.contracts = [];
    this.supply = "electricity";
    this._expanded = new Set();
  }

  static styles = css`
    :host {
      display: block;
      color: var(--primary-text-color);
    }
    .tabs {
      display: flex;
      gap: 4px;
      border-bottom: 1px solid var(--divider-color);
      margin-bottom: 8px;
    }
    .tab {
      appearance: none;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--secondary-text-color);
      cursor: pointer;
      font: inherit;
      padding: 8px 12px;
    }
    .tab[aria-selected="true"] {
      border-bottom-color: var(--primary-color);
      color: var(--primary-text-color);
      font-weight: 500;
    }
    .contract-name {
      color: var(--secondary-text-color);
      font-size: 1em;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      padding: 8px 6px;
      text-align: right;
      white-space: nowrap;
    }
    th:first-child,
    td:first-child {
      text-align: left;
    }
    th {
      border-bottom: 1px solid var(--divider-color);
      color: var(--secondary-text-color);
      font-weight: 500;
    }
    tr.row {
      cursor: pointer;
    }
    tr.row:hover,
    tr.row:focus-visible {
      background: var(--secondary-background-color, transparent);
    }
    tr.row:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: -2px;
    }
    tr.row td {
      border-bottom: 1px solid var(--divider-color);
    }
    tr.row.estimated {
      color: var(--secondary-text-color);
    }
    .pill {
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      color: var(--secondary-text-color);
      font-size: 0.8em;
      margin-left: 6px;
      padding: 1px 6px;
    }
    .pill.error {
      border-color: var(--error-color);
      color: var(--error-color);
    }
    .note {
      color: var(--secondary-text-color);
      display: block;
      font-size: 0.85em;
    }
    tr.detail td {
      background: var(--secondary-background-color, transparent);
      border-bottom: 1px solid var(--divider-color);
      text-align: left;
      white-space: normal;
    }
    .detail-body {
      display: grid;
      gap: 6px;
      padding: 4px 0;
    }
    .detail-body ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .detail-body li {
      display: flex;
      gap: 12px;
      justify-content: space-between;
    }
    .empty {
      color: var(--secondary-text-color);
      padding: 16px 0;
      text-align: center;
    }
    @media (max-width: 450px) {
      th,
      td {
        padding: 6px 4px;
      }
    }
  `;

  protected render(): TemplateResult {
    const contracts = (this.contracts ?? []).filter((c) => c.supply === this.supply);
    return html`
      <div class="tabs" role="tablist">
        ${SUPPLIES.map(
          ({ supply, label }) => html`
            <button
              class="tab"
              role="tab"
              type="button"
              aria-selected=${supply === this.supply ? "true" : "false"}
              @click=${() => this._selectSupply(supply)}
            >
              ${t(this.hass, label)}
            </button>
          `,
        )}
      </div>
      ${contracts.length === 0
        ? html`<div class="empty">${t(this.hass, "empty")}</div>`
        : contracts.map((contract) => this._renderContract(contract, contracts.length > 1))}
    `;
  }

  private _renderContract(contract: ContractInvoices, withName: boolean): TemplateResult {
    const rows = [...contract.invoices].sort(newestFirst);
    const limit = this.maxInvoices;
    const shown = limit && limit > 0 ? rows.slice(0, limit) : rows;
    const gas = this.supply === "gas";
    const headers: StringKey[] = gas
      ? ["col_period", "col_kwh", "col_m3", "col_amount", "col_price_kwh"]
      : [
          "col_period",
          "col_kwh_invoice",
          "col_kwh_edata",
          "col_delta_kwh",
          "col_amount",
          "col_delta_eur",
        ];
    return html`
      ${withName ? html`<h3 class="contract-name">${contract.name}</h3>` : nothing}
      <div class="scroll">
        <table>
          <thead>
            <tr>
              ${headers.map((key) => html`<th>${t(this.hass, key)}</th>`)}
            </tr>
          </thead>
          <tbody>
            ${shown.map((invoice) => this._renderRow(contract, invoice, headers.length))}
          </tbody>
        </table>
      </div>
    `;
  }

  private _renderRow(contract: ContractInvoices, invoice: InvoiceRow, columns: number) {
    const lang = languageOf(this.hass);
    const key = `${contract.entry_id}|${contract.contract}|${invoice.number}`;
    const open = this._expanded.has(key);
    const group = invoice.comparison?.group.length ?? 0;
    const color = `color: var(${deltaColorVar(invoice.status)})`;
    const toggle = () => this._toggle(key);
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
    };
    const period = html`
      <td>
        ${formatPeriod(invoice.period_start, invoice.period_end)}
        ${invoice.estimated
          ? html`<span class="pill">${t(this.hass, "pill_estimated")}</span>`
          : nothing}
        ${invoice.status === "no_leida"
          ? html`<span class="pill error">${t(this.hass, "pill_unreadable")}</span>`
          : nothing}
        ${group > 1
          ? html`<span class="note">${t(this.hass, "row_covers", { n: group })}</span>`
          : nothing}
      </td>
    `;
    const comparison = invoice.comparison;
    const cellsForSupply =
      invoice.supply === "gas"
        ? html`
            <td>${formatKwh(lang, invoice.kwh)}</td>
            <td>${formatM3(lang, invoice.m3)}</td>
            <td>${formatEur(lang, invoice.total)}</td>
            <td>${formatPricePerKwh(lang, invoice.price_kwh)}</td>
          `
        : html`
            <td>${formatKwh(lang, comparison?.invoice_kwh ?? invoice.kwh)}</td>
            <td>${formatKwh(lang, comparison?.edata_kwh ?? null)}</td>
            <td style=${color}>${formatDelta(lang, comparison?.delta_kwh ?? null, "kwh")}</td>
            <td>${formatEur(lang, invoice.total)}</td>
            <td style=${color}>${formatDelta(lang, comparison?.delta_eur ?? null, "eur")}</td>
          `;
    return html`
      <tr
        class="row ${invoice.estimated ? "estimated" : ""}"
        tabindex="0"
        aria-expanded=${open ? "true" : "false"}
        @click=${toggle}
        @keydown=${onKey}
      >
        ${period} ${cellsForSupply}
      </tr>
      ${open
        ? html`<tr class="detail">
            <td colspan=${columns}>${this._renderDetail(invoice)}</td>
          </tr>`
        : nothing}
    `;
  }

  private _renderDetail(invoice: InvoiceRow): TemplateResult {
    const lang = languageOf(this.hass);
    const electricity = invoice.supply !== "gas";
    const comparison = invoice.comparison;
    return html`
      <div class="detail-body">
        <ul>
          ${invoice.concepts.map(
            (concept) =>
              html`<li><span>${concept.label}</span><span>${formatEur(lang, concept.amount)}</span></li>`,
          )}
        </ul>
        <div>
          ${t(this.hass, "detail_vat", {
            rate: formatRate(lang, invoice.vat.rate),
            base: formatEur(lang, invoice.vat.base),
            amount: formatEur(lang, invoice.vat.amount),
          })}
        </div>
        ${electricity ? this._renderElectricityDetail(invoice, comparison) : nothing}
        ${invoice.in_group_of
          ? html`<div>
              ${t(this.hass, "detail_in_group_of", { number: invoice.in_group_of })}
            </div>`
          : nothing}
        ${comparison && comparison.group.length > 1
          ? html`<div>
              ${t(this.hass, "detail_group", { numbers: comparison.group.join(", ") })}
            </div>`
          : nothing}
      </div>
    `;
  }

  private _renderElectricityDetail(invoice: InvoiceRow, comparison: Comparison | null) {
    const lang = languageOf(this.hass);
    const invoicePeriods = comparison?.invoice_periods ?? invoice.periods;
    const edataPeriods = comparison?.edata_periods ?? null;
    const showPeriods = invoicePeriods !== null || edataPeriods !== null;
    const grouped = (comparison?.group.length ?? 0) > 1;
    return html`
      ${grouped
        ? html`<div>${t(this.hass, "detail_own_kwh", { kwh: formatKwh(lang, invoice.kwh) })}</div>
            <strong>
              ${t(this.hass, "detail_group_heading", { n: comparison?.group.length ?? 0 })}
            </strong>`
        : nothing}
      ${showPeriods
        ? html`<ul>
            ${PERIOD_KEYS.map(
              ({ key, name }) =>
                html`<li>
                  ${t(this.hass, "detail_period_row", {
                    period: name,
                    invoice: formatKwh(lang, invoicePeriods?.[key] ?? null),
                    edata: formatKwh(lang, edataPeriods?.[key] ?? null),
                  })}
                </li>`,
            )}
          </ul>`
        : nothing}
      ${comparison
        ? html`<div>
            ${t(this.hass, "detail_power_energy", {
              invoice: formatEur(lang, comparison.invoice_eur),
              edata: formatEur(lang, comparison.edata_eur),
            })}
            (${t(this.hass, "detail_delta_pct", { pct: formatPct(lang, comparison.delta_pct) })})
          </div>`
        : nothing}
      <div>
        ${t(this.hass, "detail_energy_price", {
          price: formatPricePerKwh(lang, invoice.energy_price_kwh),
        })}
      </div>
    `;
  }

  private _toggle(key: string): void {
    const next = new Set(this._expanded);
    if (!next.delete(key)) next.add(key);
    this._expanded = next;
  }

  private _selectSupply(supply: Supply): void {
    if (supply === this.supply) return;
    this.supply = supply;
    this._expanded = new Set();
    this.dispatchEvent(
      new CustomEvent("supply-changed", { detail: { supply }, bubbles: true, composed: true }),
    );
  }
}

if (!customElements.get("curenergia-invoice-table")) {
  customElements.define("curenergia-invoice-table", CurenergiaInvoiceTable);
}

declare global {
  interface HTMLElementTagNameMap {
    "curenergia-invoice-table": CurenergiaInvoiceTable;
  }
}
