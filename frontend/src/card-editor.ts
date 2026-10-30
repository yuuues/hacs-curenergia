import { LitElement, html, nothing } from "lit";
import type { TemplateResult } from "lit";
import { t } from "./i18n";
import type { StringKey } from "./i18n";
import type { CardConfig } from "./card";
import type { HomeAssistant } from "./types";

const LABELS: Record<string, StringKey> = {
  title: "editor_title",
  supply: "editor_supply",
  max_invoices: "editor_max_invoices",
  entry_id: "editor_entry_id",
};

export class CurenergiaInvoicesCardEditor extends LitElement {
  static properties = {
    hass: { attribute: false },
    _config: { state: true },
  };

  declare hass?: HomeAssistant;
  declare _config?: CardConfig;

  setConfig(config: CardConfig): void {
    this._config = config;
  }

  private _schema() {
    const hass = this.hass as HomeAssistant;
    return [
      { name: "title", selector: { text: {} } },
      {
        name: "supply",
        selector: {
          select: {
            mode: "dropdown",
            options: [
              { value: "electricity", label: t(hass, "tab_electricity") },
              { value: "gas", label: t(hass, "tab_gas") },
            ],
          },
        },
      },
      { name: "max_invoices", selector: { number: { min: 1, max: 60, mode: "box" } } },
      { name: "entry_id", selector: { config_entry: { integration: "curenergia" } } },
    ];
  }

  private _computeLabel = (item: { name: string }): string => {
    const key = LABELS[item.name];
    return key && this.hass ? t(this.hass, key) : item.name;
  };

  private _valueChanged = (event: Event): void => {
    event.stopPropagation();
    const value = (event as CustomEvent<{ value: Record<string, unknown> }>).detail.value;
    const config: Record<string, unknown> = { type: this._config?.type };
    for (const [key, entry] of Object.entries(value)) {
      if (entry === undefined || entry === null || entry === "") continue;
      config[key] = entry;
    }
    if (config.type === undefined) delete config.type;
    this._config = config as CardConfig;
    this.dispatchEvent(
      new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }),
    );
  };

  protected render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) return nothing;
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${this._schema()}
        .computeLabel=${this._computeLabel}
        @value-changed=${this._valueChanged}
      ></ha-form>
    `;
  }
}

if (!customElements.get("curenergia-invoices-card-editor")) {
  customElements.define("curenergia-invoices-card-editor", CurenergiaInvoicesCardEditor);
}
