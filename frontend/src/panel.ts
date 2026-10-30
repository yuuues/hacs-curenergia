import { LitElement, css, html, nothing } from "lit";
import type { TemplateResult } from "lit";
import { fetchInvoices, fetchSummary } from "./api";
import { formatEur, formatSignedPct } from "./format";
import { languageOf, t } from "./i18n";
import type { ContractInvoices, HomeAssistant, Summary, Supply } from "./types";
import "./invoice-table";
import "./chart";

const REFRESH_MS = 15 * 60 * 1000;

export class CurenergiaPanel extends LitElement {
  static properties = {
    hass: { attribute: false },
    narrow: { type: Boolean },
    panel: { attribute: false },
    _data: { state: true },
    _summary: { state: true },
    _failed: { state: true },
    _supply: { state: true },
  };

  declare narrow: boolean;
  declare panel?: unknown;
  declare _data?: ContractInvoices[];
  declare _summary?: Summary;
  declare _failed: boolean;
  declare _supply: Supply;

  private _hass?: HomeAssistant;
  private _timer?: ReturnType<typeof setInterval>;
  private _requestId = 0;
  private _inFlight = false;

  constructor() {
    super();
    this.narrow = false;
    this._failed = false;
    this._supply = "electricity";
  }

  static styles = css`
    :host {
      display: block;
      min-height: 100%;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: 56px;
      padding: 0 12px;
      box-sizing: border-box;
      background: var(--app-header-background-color);
      color: var(--app-header-text-color, var(--primary-text-color));
    }
    .toolbar .title {
      font-size: 20px;
      font-weight: 400;
    }
    .content {
      max-width: 1100px;
      margin: 0 auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }
    .kpi,
    .section {
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 16px;
    }
    .kpi .value {
      font-size: 1.8em;
      font-weight: 500;
    }
    .kpi .label {
      margin-top: 4px;
      color: var(--secondary-text-color);
    }
    .warning {
      padding: 8px 12px;
      border-left: 4px solid var(--warning-color);
      background: var(--card-background-color);
      border-radius: 4px;
    }
    .chart-name {
      color: var(--secondary-text-color);
      font-size: 1em;
      font-weight: 500;
      margin: 0 0 4px;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .message.error {
      color: var(--error-color);
    }
  `;

  get hass(): HomeAssistant | undefined {
    return this._hass;
  }

  set hass(hass: HomeAssistant | undefined) {
    this._hass = hass;
    this.requestUpdate();
    this._start();
  }

  connectedCallback(): void {
    super.connectedCallback();
    this._start();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._stop();
  }

  /** Fetches now and every 15 minutes, once connected and with `hass`. */
  private _start(): void {
    if (this._timer !== undefined || !this.isConnected || !this._hass) return;
    this._timer = setInterval(() => void this._load(), REFRESH_MS);
    void this._load();
  }

  private _stop(): void {
    if (this._timer !== undefined) clearInterval(this._timer);
    this._timer = undefined;
    // Late answers of requests in flight are ignored.
    this._requestId += 1;
    this._inFlight = false;
  }

  private async _load(): Promise<void> {
    const hass = this._hass;
    // A tick is skipped while the previous request has not answered yet.
    if (!hass || this._inFlight) return;
    this._inFlight = true;
    this._requestId += 1;
    const requestId = this._requestId;
    try {
      // All entries: no entry_id.
      const [summary, invoices] = await Promise.all([fetchSummary(hass), fetchInvoices(hass)]);
      if (requestId !== this._requestId) return;
      this._summary = summary;
      this._data = invoices.contracts ?? [];
      this._failed = false;
    } catch {
      // The error text could contain server details: only a generic message is shown.
      if (requestId !== this._requestId) return;
      this._failed = true;
    } finally {
      if (requestId === this._requestId) this._inFlight = false;
    }
  }

  private _onSupplyChanged = (event: Event): void => {
    const supply = (event as CustomEvent<{ supply: Supply }>).detail?.supply;
    if (supply === "electricity" || supply === "gas") this._supply = supply;
  };

  private _renderKpis(hass: HomeAssistant): TemplateResult {
    const lang = languageOf(hass);
    const summary = this._summary;
    const kpi = (label: string, value: string) =>
      html`<div class="kpi">
        <div class="value">${value}</div>
        <div class="label">${label}</div>
      </div>`;
    return html`<div class="kpis">
      ${kpi(t(hass, "panel_billed_12m"), formatEur(lang, summary?.billed_12m ?? null))}
      ${kpi(t(hass, "panel_kwh_delta"), formatSignedPct(lang, summary?.kwh_delta_pct ?? null))}
      ${kpi(
        t(hass, "panel_estimated_count"),
        summary ? new Intl.NumberFormat(lang).format(summary.estimated_count) : "—",
      )}
    </div>`;
  }

  private _renderBody(hass: HomeAssistant): TemplateResult {
    if (this._data === undefined) {
      return this._failed
        ? html``
        : html`<div class="message">${t(hass, "loading")}</div>`;
    }
    if (this._data.length === 0) {
      return html`<div class="message">${t(hass, "empty")}</div>`;
    }
    // One chart per electricity contract, each with its own most recent invoices.
    const electricity = this._data.filter((contract) => contract.supply === "electricity");
    const named = electricity.length > 1;
    return html`
      ${electricity.map(
        (contract) => html`
          <div class="section">
            ${named ? html`<h3 class="chart-name">${contract.name}</h3>` : nothing}
            <curenergia-bar-chart
              .hass=${hass}
              .invoices=${contract.invoices}
            ></curenergia-bar-chart>
          </div>
        `,
      )}
      <div class="section">
        <curenergia-invoice-table
          .hass=${hass}
          .contracts=${this._data}
          .supply=${this._supply}
          @supply-changed=${this._onSupplyChanged}
        ></curenergia-invoice-table>
      </div>
    `;
  }

  protected render(): TemplateResult | typeof nothing {
    const hass = this._hass;
    if (!hass) return nothing;
    const summary = this._summary;
    return html`
      <div class="toolbar">
        <ha-menu-button .hass=${hass} .narrow=${this.narrow}></ha-menu-button>
        <div class="title">${t(hass, "panel_title")}</div>
      </div>
      <div class="content">
        ${this._failed ? html`<div class="message error">${t(hass, "error")}</div>` : nothing}
        ${this._renderKpis(hass)}
        ${summary?.mail_error
          ? html`<div class="warning">${t(hass, "panel_mail_error")}</div>`
          : nothing}
        ${summary && summary.unreadable_emails > 0
          ? html`<div class="warning">
              ${t(hass, "panel_unreadable", { n: summary.unreadable_emails })}
            </div>`
          : nothing}
        ${summary && summary.unsupported_emails > 0
          ? html`<div class="warning">
              ${t(hass, "panel_unsupported", { n: summary.unsupported_emails })}
            </div>`
          : nothing}
        ${this._renderBody(hass)}
      </div>
    `;
  }
}

if (!customElements.get("curenergia-panel")) {
  customElements.define("curenergia-panel", CurenergiaPanel);
}
