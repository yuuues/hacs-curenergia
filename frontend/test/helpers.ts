import type { HomeAssistant } from "../src/types";

/** Minimal stand-ins for the HA elements that only exist inside Home Assistant. */
export function defineFakeHaElements(): void {
  if (!customElements.get("ha-card")) {
    customElements.define(
      "ha-card",
      class extends HTMLElement {
        header?: string;
      },
    );
  }
  if (!customElements.get("ha-form")) {
    customElements.define(
      "ha-form",
      class extends HTMLElement {
        hass?: unknown;
        data?: unknown;
        schema?: unknown;
        computeLabel?: unknown;
      },
    );
  }
}

export function fakeHass(
  language = "en",
  sendMessagePromise: (msg: object) => Promise<unknown> = async () => ({ contracts: [] }),
): HomeAssistant {
  return {
    language,
    locale: { language },
    connection: { sendMessagePromise },
  } as unknown as HomeAssistant;
}
