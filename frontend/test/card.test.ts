import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineFakeHaElements, fakeHass } from "./helpers";
import "../src/card";
import type { CurenergiaInvoicesCard } from "../src/card";
import type { ContractInvoices } from "../src/types";

defineFakeHaElements();

const REFRESH_MS = 15 * 60 * 1000;

function makeCard(config: Record<string, unknown> = {}): CurenergiaInvoicesCard {
  const card = document.createElement("curenergia-invoices-card") as CurenergiaInvoicesCard;
  card.setConfig(config as never);
  return card;
}

const flush = async () => {
  for (let i = 0; i < 5; i += 1) await Promise.resolve();
};

const headerOf = (card: CurenergiaInvoicesCard) =>
  (card.shadowRoot!.querySelector("ha-card") as unknown as { header: string }).header;

describe("curenergia-invoices-card", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("rejects invalid max_invoices and supply", () => {
    const card = document.createElement("curenergia-invoices-card") as CurenergiaInvoicesCard;
    for (const bad of [0, 61, 1.5, "6", null, Number.NaN]) {
      expect(() => card.setConfig({ max_invoices: bad } as never), String(bad)).toThrow(
        /max_invoices/,
      );
    }
    expect(() => card.setConfig({ supply: "water" } as never)).toThrow(/supply/);
    expect(() => card.setConfig(undefined as never)).toThrow();
    expect(() => card.setConfig({ max_invoices: 1 })).not.toThrow();
    expect(() => card.setConfig({ max_invoices: 60, supply: "gas" })).not.toThrow();
    expect(() => card.setConfig({})).not.toThrow();
  });

  it("returns a stub config", () => {
    const ctor = customElements.get("curenergia-invoices-card") as unknown as {
      getStubConfig(): unknown;
    };
    expect(ctor.getStubConfig()).toEqual({ max_invoices: 6 });
  });

  describe("native config form", () => {
    type Form = {
      schema: { name: string; selector: Record<string, unknown> }[];
      computeLabel: (item: { name: string }) => string | undefined;
    };
    const ctor = () =>
      customElements.get("curenergia-invoices-card") as unknown as {
        getConfigForm(): Form;
        getConfigElement?: unknown;
      };
    const previousLang = document.documentElement.lang;

    afterEach(() => {
      document.documentElement.lang = previousLang;
    });

    it("has no custom editor element", () => {
      expect(ctor().getConfigElement).toBeUndefined();
      expect(customElements.get("curenergia-invoices-card-editor")).toBeUndefined();
    });

    it("describes the four fields with HA selectors", () => {
      document.documentElement.lang = "en";
      const { schema } = ctor().getConfigForm();
      expect(schema.map((s) => s.name)).toEqual(["title", "supply", "max_invoices", "entry_id"]);
      const byName = Object.fromEntries(schema.map((s) => [s.name, s.selector]));
      expect(byName.title).toEqual({ text: {} });
      expect(byName.supply).toEqual({
        select: {
          mode: "dropdown",
          options: [
            { value: "electricity", label: "Electricity" },
            { value: "gas", label: "Gas" },
          ],
        },
      });
      expect(byName.max_invoices).toEqual({ number: { min: 1, max: 60, mode: "box" } });
      expect(byName.entry_id).toEqual({ config_entry: { integration: "curenergia" } });
    });

    it("labels the fields in Spanish or English", () => {
      document.documentElement.lang = "es-ES";
      const es = ctor().getConfigForm();
      expect(es.computeLabel({ name: "title" })).toBe("Título");
      expect(es.computeLabel({ name: "supply" })).toBe("Pestaña inicial");
      expect(es.computeLabel({ name: "max_invoices" })).toBe("Número máximo de facturas");
      expect(es.computeLabel({ name: "entry_id" })).toBe("Cuenta de correo (opcional)");
      expect(es.computeLabel({ name: "other" })).toBeUndefined();
      const supply = es.schema.find((s) => s.name === "supply")!.selector as {
        select: { options: { label: string }[] };
      };
      expect(supply.select.options.map((o) => o.label)).toEqual(["Luz", "Gas"]);

      document.documentElement.lang = "en";
      const en = ctor().getConfigForm();
      expect(en.computeLabel({ name: "title" })).toBe("Title");
      expect(en.computeLabel({ name: "supply" })).toBe("Initial tab");
      expect(en.computeLabel({ name: "max_invoices" })).toBe("Maximum number of invoices");
      expect(en.computeLabel({ name: "entry_id" })).toBe("Mail account (optional)");
    });
  });

  it("treats empty strings from the form as unset", async () => {
    const send = vi.fn().mockResolvedValue({ contracts: [] });
    const card = makeCard({ title: "", supply: "", entry_id: "" });
    document.body.appendChild(card);
    card.hass = fakeHass("es", send);
    await flush();
    await card.updateComplete;
    expect(headerOf(card)).toBe("Facturas");
    expect(send).toHaveBeenCalledWith({ type: "curenergia/invoices" });
  });

  it("fetches once on first hass and every 15 minutes", async () => {
    vi.useFakeTimers();
    const send = vi.fn().mockResolvedValue({ contracts: [] });
    const card = makeCard();
    document.body.appendChild(card);
    card.hass = fakeHass("en", send);
    await flush();
    expect(send).toHaveBeenCalledTimes(1);
    // New hass objects (HA sends one on every state change) do not trigger fetches.
    card.hass = fakeHass("en", send);
    expect(send).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(REFRESH_MS);
    expect(send).toHaveBeenCalledTimes(2);

    card.remove();
    await vi.advanceTimersByTimeAsync(REFRESH_MS * 3);
    expect(send).toHaveBeenCalledTimes(2);
  });

  it("fetches when connected after hass was set", async () => {
    const send = vi.fn().mockResolvedValue({ contracts: [] });
    const card = makeCard();
    card.hass = fakeHass("en", send);
    expect(send).not.toHaveBeenCalled();
    document.body.appendChild(card);
    await flush();
    expect(send).toHaveBeenCalledTimes(1);
  });

  it("passes entry_id to the API", async () => {
    const send = vi.fn().mockResolvedValue({ contracts: [] });
    const card = makeCard({ entry_id: "abc123" });
    document.body.appendChild(card);
    card.hass = fakeHass("en", send);
    await flush();
    expect(send).toHaveBeenCalledWith({ type: "curenergia/invoices", entry_id: "abc123" });
  });

  it("omits entry_id when not configured", async () => {
    const send = vi.fn().mockResolvedValue({ contracts: [] });
    const card = makeCard();
    document.body.appendChild(card);
    card.hass = fakeHass("en", send);
    await flush();
    expect(send).toHaveBeenCalledWith({ type: "curenergia/invoices" });
  });

  it("shows a load error without details", async () => {
    const send = vi.fn().mockRejectedValue(new Error("secret"));
    const card = makeCard();
    document.body.appendChild(card);
    card.hass = fakeHass("en", send);
    await flush();
    await card.updateComplete;
    const text = card.shadowRoot!.textContent ?? "";
    expect(text).toContain("Could not load the invoices");
    expect(text).not.toContain("secret");
  });

  it("uses the configured title or the translated default", async () => {
    const card = makeCard({ title: "Mis facturas" });
    document.body.appendChild(card);
    card.hass = fakeHass("en");
    await card.updateComplete;
    expect(headerOf(card)).toBe("Mis facturas");

    const plain = makeCard();
    document.body.appendChild(plain);
    plain.hass = fakeHass("es");
    await plain.updateComplete;
    expect(headerOf(plain)).toBe("Facturas");
  });

  it("shows the table with the configured supply and max_invoices", async () => {
    const card = makeCard({ supply: "gas", max_invoices: 3 });
    document.body.appendChild(card);
    card.hass = fakeHass("en");
    await flush();
    await card.updateComplete;
    const table = card.shadowRoot!.querySelector("curenergia-invoice-table") as unknown as {
      supply: string;
      maxInvoices: number;
    };
    expect(table.supply).toBe("gas");
    expect(table.maxInvoices).toBe(3);
  });

  it("keeps the chosen tab across re-renders", async () => {
    const card = makeCard();
    document.body.appendChild(card);
    card.hass = fakeHass("en");
    await flush();
    await card.updateComplete;
    const table = card.shadowRoot!.querySelector("curenergia-invoice-table")!;
    table.dispatchEvent(
      new CustomEvent("supply-changed", {
        detail: { supply: "gas" },
        bubbles: true,
        composed: true,
      }),
    );
    card.hass = fakeHass("es");
    await card.updateComplete;
    const again = card.shadowRoot!.querySelector("curenergia-invoice-table") as unknown as {
      supply: string;
    };
    expect(again.supply).toBe("gas");
  });

  it("computes the card size from the rows", async () => {
    const contracts: ContractInvoices[] = [
      {
        entry_id: "e",
        contract: "c",
        supply: "electricity",
        name: "n",
        invoices: Array.from(
          { length: 10 },
          (_, i) =>
            ({
              number: `F${i}`,
              period_end: "2026-07-31",
              issue_date: "2026-08-01",
              period_start: "2026-07-01",
              supply: "electricity",
              status: "gas",
              estimated: false,
              problems: [],
              concepts: [],
              vat: { rate: null, base: null, amount: null },
              periods: null,
              comparison: null,
              in_group_of: null,
            }) as never,
        ),
      },
    ];
    const card = makeCard({ max_invoices: 4 });
    expect(card.getCardSize()).toBe(3);
    document.body.appendChild(card);
    card.hass = fakeHass("en", async () => ({ contracts }));
    await flush();
    expect(card.getCardSize()).toBe(7);
    card.setConfig({ max_invoices: 20 });
    expect(card.getCardSize()).toBe(13);
  });

  it("refetches when entry_id changes while connected", async () => {
    const send = vi.fn().mockResolvedValue({ contracts: [] });
    const card = makeCard({ entry_id: "a" });
    document.body.appendChild(card);
    card.hass = fakeHass("en", send);
    await flush();
    card.setConfig({ entry_id: "b" });
    await flush();
    expect(send).toHaveBeenCalledTimes(2);
    expect(send).toHaveBeenLastCalledWith({ type: "curenergia/invoices", entry_id: "b" });
    card.setConfig({ entry_id: "b", title: "x" });
    await flush();
    expect(send).toHaveBeenCalledTimes(2);
  });

  it("registers in window.customCards once", () => {
    const cards = (window as unknown as { customCards: { type: string }[] }).customCards;
    const mine = cards.filter((c) => c.type === "curenergia-invoices-card");
    expect(mine).toHaveLength(1);
    expect(mine[0]).toEqual({
      type: "curenergia-invoices-card",
      name: "CurEnergía",
      description: expect.any(String),
      preview: false,
      documentationURL: "https://github.com/yuuues/hacs-curenergia#readme",
    });
  });
});
