import { LitElement, css, html, nothing } from "lit";
import type { TemplateResult } from "lit";
import { fetchInvoices } from "./api";
import { STRINGS, t } from "./i18n";
import type { ContractInvoices, HomeAssistant, Supply } from "./types";
import "./invoice-table";
import "./card-editor";

export interface CardConfig {
  type?: string;
  title?: string;
  supply?: Supply;
  max_invoices?: number;
  entry_id?: string;
}

const DEFAULT_MAX_INVOICES = 6;
const REFRESH_MS = 15 * 60 * 1000;

function validate(config: unknown): CardConfig {
  if (config === null || typeof config !== "object" || Array.isArray(config)) {
    throw new Error("Invalid configuration");
  }
  const { max_invoices, supply, title, entry_id } = config as Record<string, unknown>;
  if (max_invoices !== undefined) {
    if (
      typeof max_invoices !== "number" ||
      !Number.isInteger(max_invoices) ||
      max_invoices < 1 ||
      max_invoices > 60
    ) {
      throw new Error("max_invoices must be an integer between 1 and 60");
    }
  }
  if (supply !== undefined && supply !== "electricity" && supply !== "gas") {
    throw new Error('supply must be "electricity" or "gas"');
  }
  if (title !== undefined && typeof title !== "string") {
    throw new Error("title must be a string");
  }
  if (entry_id !== undefined && typeof entry_id !== "string") {
    throw new Error("entry_id must be a string");
  }
  return config as CardConfig;
}

export class CurenergiaInvoicesCard extends LitElement {
  static properties = {
    _config: { state: true },
    _data: { state: true },
    _failed: { state: true },
    _supply: { state: true },
  };

  declare _config?: CardConfig;
  declare _data?: ContractInvoices[];
  declare _failed: boolean;
  declare _supply: Supply;

  private _hass?: HomeAssistant;
  private _timer?: ReturnType<typeof setInterval>;
  private _requestId = 0;

  constructor() {
    super();
    this._failed = false;
    this._supply = "electricity";
  }

  static styles = css`
    :host {
      display: block;
    }
    ha-card {
      display: block;
    }
    .body {
      padding: 0 16px 16px;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .message.error {
      color: var(--error-color);
    }
  `;

  static getStubConfig(): CardConfig {
    return { max_invoices: DEFAULT_MAX_INVOICES };
  }

  static getConfigElement(): HTMLElement {
    return document.createElement("curenergia-invoices-card-editor");
  }

  get hass(): HomeAssistant | undefined {
    return this._hass;
  }

  set hass(hass: HomeAssistant | undefined) {
    this._hass = hass;
    this.requestUpdate();
    this._start();
  }

  setConfig(config: CardConfig): void {
    const next = validate(config);
    const previous = this._config;
    this._config = next;
    this._supply = next.supply ?? "electricity";
    if (previous && previous.entry_id !== next.entry_id && this._timer !== undefined) {
      void this._load();
    }
  }

  getCardSize(): number {
    const max = this._config?.max_invoices ?? DEFAULT_MAX_INVOICES;
    const rows = (this._data ?? [])
      .filter((contract) => contract.supply === this._supply)
      .reduce((total, contract) => total + contract.invoices.length, 0);
    return 3 + Math.min(max, rows);
  }

  connectedCallback(): void {
    super.connectedCallback();
    this._start();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._stop();
  }

  /** Fetches now and every 15 minutes, once connected with both `hass` and config. */
  private _start(): void {
    if (this._timer !== undefined || !this.isConnected || !this._hass || !this._config) return;
    this._timer = setInterval(() => void this._load(), REFRESH_MS);
    void this._load();
  }

  private _stop(): void {
    if (this._timer !== undefined) clearInterval(this._timer);
    this._timer = undefined;
    // Late answers of requests in flight are ignored.
    this._requestId += 1;
  }

  private async _load(): Promise<void> {
    const hass = this._hass;
    if (!hass) return;
    this._requestId += 1;
    const requestId = this._requestId;
    try {
      const response = await fetchInvoices(hass, { entry_id: this._config?.entry_id });
      if (requestId !== this._requestId) return;
      this._data = response.contracts ?? [];
      this._failed = false;
    } catch {
      // The error text could contain server details: only a generic message is shown.
      if (requestId !== this._requestId) return;
      this._failed = true;
    }
  }

  private _onSupplyChanged = (event: Event): void => {
    const supply = (event as CustomEvent<{ supply: Supply }>).detail?.supply;
    if (supply === "electricity" || supply === "gas") this._supply = supply;
  };

  protected render(): TemplateResult | typeof nothing {
    const config = this._config;
    const hass = this._hass;
    if (!config || !hass) return nothing;
    return html`
      <ha-card .header=${config.title ?? t(hass, "card_title")}>
        <div class="body">
          ${this._failed
            ? html`<div class="message error">${t(hass, "error")}</div>`
            : nothing}
          ${this._data === undefined
            ? this._failed
              ? nothing
              : html`<div class="message">${t(hass, "loading")}</div>`
            : html`<curenergia-invoice-table
                .hass=${hass}
                .contracts=${this._data}
                .supply=${this._supply}
                .maxInvoices=${config.max_invoices ?? DEFAULT_MAX_INVOICES}
                @supply-changed=${this._onSupplyChanged}
              ></curenergia-invoice-table>`}
        </div>
      </ha-card>
    `;
  }
}

if (!customElements.get("curenergia-invoices-card")) {
  customElements.define("curenergia-invoices-card", CurenergiaInvoicesCard);
}

interface CustomCardEntry {
  type: string;
  name: string;
  description: string;
  preview: boolean;
  documentationURL: string;
}

const cards = ((window as unknown as { customCards?: CustomCardEntry[] }).customCards ??= []);
if (!cards.some((card) => card.type === "curenergia-invoices-card")) {
  cards.push({
    type: "curenergia-invoices-card",
    name: "CurEnergía",
    description: STRINGS.en.card_description,
    preview: false,
    documentationURL: "https://github.com/yuuues/hacs-curenergia#readme",
  });
}
