import { beforeEach, describe, expect, it } from "vitest";
import "../src/invoice-table";
import type { CurenergiaInvoiceTable } from "../src/invoice-table";
import type {
  Comparison,
  ContractInvoices,
  HomeAssistant,
  InvoiceRow,
  Status,
  Supply,
} from "../src/types";

const hassWith = (language: string) =>
  ({
    language,
    locale: { language },
    connection: { sendMessagePromise: async () => ({}) },
  }) as unknown as HomeAssistant;

const periods = (p1: number | null, p2: number | null, p3: number | null) => ({ p1, p2, p3 });

function comparison(overrides: Partial<Comparison> = {}): Comparison {
  return {
    group: ["F-1"],
    window_start: "2026-07-01",
    window_end: "2026-07-31",
    invoice_kwh: 300,
    invoice_periods: periods(100, 120, 80),
    invoice_eur: 50,
    edata_kwh: 298,
    edata_periods: periods(99, 120, 79),
    edata_eur: 49.5,
    delta_kwh: 2,
    delta_periods: periods(1, 0, 1),
    delta_eur: 0.5,
    delta_pct: 1.0,
    ...overrides,
  };
}

function row(number: string, end: string, overrides: Partial<InvoiceRow> = {}): InvoiceRow {
  return {
    number,
    supply: "electricity",
    issue_date: end,
    period_start: `${end.slice(0, 7)}-01`,
    period_end: end,
    estimated: false,
    status: "ok",
    problems: [],
    total: 61.2,
    kwh: 300,
    price_kwh: 0.204,
    m3: null,
    energy_price_kwh: 0.1234,
    periods: periods(100, 120, 80),
    concepts: [
      { key: "power", label: "Término de potencia", amount: 20 },
      { key: "energy", label: "Término de energía", amount: 30 },
    ],
    vat: { rate: 21, base: 52, amount: 10.92 },
    in_group_of: null,
    comparison: comparison(),
    ...overrides,
  };
}

function contract(
  supply: Supply,
  invoices: InvoiceRow[],
  name = "Casa",
  id = "C1",
): ContractInvoices {
  return { entry_id: "e1", contract: id, supply, name, invoices };
}

const gasRow = (number: string, end: string, overrides: Partial<InvoiceRow> = {}) =>
  row(number, end, {
    supply: "gas",
    status: "gas",
    comparison: null,
    periods: null,
    energy_price_kwh: null,
    kwh: 150,
    m3: 14.25,
    price_kwh: 0.1,
    total: 15,
    ...overrides,
  });

async function mount(props: Partial<CurenergiaInvoiceTable> = {}) {
  const el = document.createElement("curenergia-invoice-table") as CurenergiaInvoiceTable;
  el.hass = hassWith("es");
  el.contracts = [];
  el.supply = "electricity";
  Object.assign(el, props);
  document.body.append(el);
  await el.updateComplete;
  return el;
}

const root = (el: HTMLElement) => el.shadowRoot as ShadowRoot;
const headers = (el: HTMLElement) =>
  [...root(el).querySelectorAll("thead th")].map((th) => th.textContent?.trim());
const bodyRows = (el: HTMLElement) =>
  [...root(el).querySelectorAll<HTMLElement>("tbody tr.row")];
const toggleOf = (tr: Element) =>
  tr.querySelector("td:first-child button.toggle") as HTMLButtonElement;
const cells = (tr: Element) => [...tr.querySelectorAll("td")].map((td) => td.textContent?.trim());

beforeEach(() => {
  document.body.innerHTML = "";
});

describe("curenergia-invoice-table", () => {
  it("is registered once", () => {
    expect(customElements.get("curenergia-invoice-table")).toBeDefined();
  });

  it("renders electricity columns in order", async () => {
    const el = await mount({ contracts: [contract("electricity", [row("F-1", "2026-07-31")])] });
    expect(headers(el)).toEqual([
      "Periodo",
      "kWh factura",
      "kWh Datadis",
      "Δ kWh",
      "Importe",
      "Δ €",
    ]);
    const c = cells(bodyRows(el)[0]);
    expect(c[0]).toContain("01/07 – 31/07/2026");
    expect(c[1]).toBe("300 kWh");
    expect(c[2]).toBe("298 kWh");
    expect(c[3]).toBe("+2 kWh");
    expect(c[4].replace(/\s/g, " ")).toBe("61,20 €");
    expect(c[5].replace(/\s/g, " ")).toBe("+0,50 €");
  });

  it("renders gas columns in order", async () => {
    const el = await mount({
      supply: "gas",
      contracts: [contract("gas", [gasRow("G-1", "2026-07-31")], "Gas casa", "G1")],
    });
    expect(headers(el)).toEqual(["Periodo", "kWh", "m³", "Importe", "€/kWh"]);
    const c = cells(bodyRows(el)[0]);
    expect(c[1]).toBe("150 kWh");
    expect(c[2]).toBe("14,25 m³");
    expect(c[3].replace(/\s/g, " ")).toBe("15,00 €");
    expect(c[4].replace(/\s/g, " ")).toBe("0,1000 €/kWh");
  });

  it("shows dashes for null comparison values", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-1", "2026-07-31", { comparison: null, status: "sin_datos", kwh: null }),
        ]),
      ],
    });
    const c = cells(bodyRows(el)[0]);
    expect(c[1]).toBe("—");
    expect(c[2]).toBe("—");
    expect(c[3]).toBe("—");
    expect(c[5]).toBe("—");
    const text = root(el).textContent ?? "";
    expect(text).not.toContain("NaN");
    expect(text).not.toContain("null");
    expect(text).not.toContain("undefined");
  });

  it("shows dashes in the detail when everything is null", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-1", "2026-07-31", {
            comparison: comparison({
              edata_kwh: null,
              edata_eur: null,
              delta_pct: null,
              delta_kwh: null,
              delta_eur: null,
              edata_periods: periods(null, null, null),
            }),
            energy_price_kwh: null,
            periods: null,
            total: null,
            vat: { rate: null, base: null, amount: null },
            concepts: [{ key: "other", label: "Otros", amount: null }],
          }),
        ]),
      ],
    });
    toggleOf(bodyRows(el)[0]).click();
    await el.updateComplete;
    const text = root(el).textContent ?? "";
    expect(text).not.toContain("NaN");
    expect(text).not.toContain("null");
    expect(text).not.toContain("undefined");
  });

  it("colours deltas by status", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-2", "2026-08-31", { status: "no_cuadra" }),
          row("F-1", "2026-07-31", { status: "ok" }),
        ]),
      ],
    });
    const [mismatch, ok] = bodyRows(el);
    const style = (tr: Element, index: number) =>
      tr.querySelectorAll("td")[index].getAttribute("style") ?? "";
    expect(style(ok, 3)).toContain("var(--success-color)");
    expect(style(mismatch, 3)).toContain("var(--warning-color)");
  });

  it("always colours the Δ € cell as secondary (informational)", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-2", "2026-08-31", { status: "no_cuadra" }),
          row("F-1", "2026-07-31", { status: "ok" }),
        ]),
      ],
    });
    const [mismatch, ok] = bodyRows(el);
    const style = (tr: Element, index: number) =>
      tr.querySelectorAll("td")[index].getAttribute("style") ?? "";
    expect(style(ok, 5)).toContain("var(--secondary-text-color)");
    expect(style(mismatch, 5)).toContain("var(--secondary-text-color)");
  });

  it("colours the dash of a missing delta as secondary whatever the status", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-2", "2026-08-31", { status: "no_cuadra", comparison: null }),
          row("F-1", "2026-07-31", { status: "ok", comparison: null }),
        ]),
      ],
    });
    for (const tr of bodyRows(el)) {
      const cells = tr.querySelectorAll("td");
      for (const index of [3, 5]) {
        expect(cells[index].textContent?.trim()).toBe("—");
        expect(cells[index].getAttribute("style")).toContain("var(--secondary-text-color)");
      }
    }
  });

  it("labels estimated and unreadable rows", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-3", "2026-09-30", { estimated: true, status: "estimada" }),
          row("F-2", "2026-08-31", { status: "no_leida", comparison: null }),
          row("F-1", "2026-07-31"),
        ]),
      ],
    });
    const [estimated, unreadable, plain] = bodyRows(el);
    expect(estimated.textContent).toContain("estimada");
    expect(estimated.classList.contains("estimated")).toBe(true);
    expect(estimated.querySelectorAll("td")[3].getAttribute("style")).toContain(
      "var(--secondary-text-color)",
    );
    expect(unreadable.textContent).toContain("no se pudo leer");
    expect(unreadable.textContent).not.toContain("estimada");
    expect(plain.textContent).not.toContain("estimada");
    expect(plain.textContent).not.toContain("no se pudo leer");
  });

  it("says when a row covers several invoices", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-2", "2026-08-31", { comparison: comparison({ group: ["F-1", "F-2"] }) }),
        ]),
      ],
    });
    expect(bodyRows(el)[0].textContent).toContain("abarca 2 facturas");
    expect(root(el).textContent).not.toContain("abarca 1");
  });

  it("shows group sums in the columns and own values in the detail", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-2", "2026-08-31", {
            kwh: 200,
            comparison: comparison({
              group: ["F-1", "F-2"],
              invoice_kwh: 500,
              edata_kwh: 495,
              delta_kwh: 5,
              invoice_periods: periods(250, 150, 100),
              edata_periods: periods(248, 149, 98),
            }),
          }),
        ]),
      ],
    });
    const c = cells(bodyRows(el)[0]);
    expect(c[1]).toBe("500 kWh");
    expect(c[2]).toBe("495 kWh");
    expect(c[3]).toBe("+5 kWh");

    toggleOf(bodyRows(el)[0]).click();
    await el.updateComplete;
    const detail = ((root(el).querySelector("tr.detail") as HTMLElement).textContent ?? "")
      .replace(/\s+/g, " ");
    expect(detail).toContain("Esta factura: 200 kWh");
    expect(detail).toContain("Comparación del grupo (2 facturas)");
    expect(detail).toContain("P1: factura 250 kWh / Datadis 248 kWh");
    expect(detail.indexOf("Esta factura")).toBeLessThan(detail.indexOf("Comparación del grupo"));
    expect(detail.indexOf("Comparación del grupo")).toBeLessThan(detail.indexOf("P1:"));
  });

  it("does not show the own-kWh line or group heading for a single invoice", async () => {
    const el = await mount({ contracts: [contract("electricity", [row("F-1", "2026-07-31")])] });
    toggleOf(bodyRows(el)[0]).click();
    await el.updateComplete;
    const detail = (root(el).querySelector("tr.detail") as HTMLElement).textContent ?? "";
    expect(detail).not.toContain("Esta factura");
    expect(detail).not.toContain("Comparación del grupo");
  });

  it("toggles a row with a native button in its first cell (Enter/Space for free)", async () => {
    const el = await mount({ contracts: [contract("electricity", [row("F-1", "2026-07-31")])] });
    const tr = bodyRows(el)[0];
    const button = toggleOf(tr);
    expect(button.localName).toBe("button");
    expect(button.getAttribute("type")).toBe("button");
    expect(button.closest("td")).toBe(tr.querySelector("td"));
    expect(button.textContent).toContain("01/07 – 31/07/2026");
    // The row itself is no longer a focus stop nor carries the state.
    expect(tr.hasAttribute("tabindex")).toBe(false);
    expect(tr.hasAttribute("aria-expanded")).toBe(false);
    button.click();
    await el.updateComplete;
    expect(toggleOf(bodyRows(el)[0]).getAttribute("aria-expanded")).toBe("true");
    toggleOf(bodyRows(el)[0]).click();
    await el.updateComplete;
    expect(toggleOf(bodyRows(el)[0]).getAttribute("aria-expanded")).toBe("false");
  });

  it("colours unreadable deltas as error and missing-data deltas as secondary", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-2", "2026-08-31", { status: "no_leida" }),
          row("F-1", "2026-07-31", { status: "sin_datos" }),
        ]),
      ],
    });
    const [unreadable, noData] = bodyRows(el);
    const style = (tr: Element, i: number) => tr.querySelectorAll("td")[i].getAttribute("style");
    expect(style(unreadable, 3)).toContain("var(--error-color)");
    expect(style(unreadable, 5)).toContain("var(--secondary-text-color)");
    expect(style(noData, 3)).toContain("var(--secondary-text-color)");
    expect(style(noData, 5)).toContain("var(--secondary-text-color)");
  });

  it("uses English when the locale is not Spanish", async () => {
    const el = await mount({
      hass: hassWith("en"),
      contracts: [
        contract("electricity", [
          row("F-2", "2026-08-31", {
            estimated: true,
            status: "estimada",
            comparison: comparison({ group: ["F-1", "F-2"] }),
          }),
        ]),
      ],
    });
    expect(headers(el)[0]).toBe("Period");
    expect(bodyRows(el)[0].textContent).toContain("estimated");
    expect(bodyRows(el)[0].textContent).toContain("covers 2 invoices");
  });

  it("expands a row on a click anywhere on it and on its toggle button", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [
          row("F-1", "2026-07-31", { comparison: comparison({ group: ["F-0", "F-1"] }) }),
          row("F-0", "2026-06-30", { in_group_of: "F-1", comparison: null }),
        ]),
      ],
    });
    const [first, second] = bodyRows(el);
    expect(toggleOf(first).getAttribute("aria-expanded")).toBe("false");
    expect(root(el).querySelector("tr.detail")).toBeNull();

    (first.querySelectorAll("td")[2] as HTMLElement).click();
    await el.updateComplete;
    expect(toggleOf(first).getAttribute("aria-expanded")).toBe("true");
    const detail = (root(el).querySelector("tr.detail") as HTMLElement).textContent ?? "";
    const normalised = detail.replace(/\s/g, " ");
    expect(normalised).toContain("Término de potencia");
    expect(normalised).toContain("20,00 €");
    expect(normalised).toContain("IVA 21 % sobre 52,00 €: 10,92 €");
    expect(normalised).toContain("P1: factura 100 kWh / Datadis 99 kWh");
    expect(normalised).toContain("P3: factura 80 kWh / Datadis 79 kWh");
    expect(normalised).toContain("Potencia + energía: factura 50,00 € / e-data 49,50 €");
    expect(normalised).toContain("(Δ 1,0 %)");
    expect(normalised).toContain("0,1234 €/kWh");
    expect(normalised).toContain("F-0");

    first.click();
    await el.updateComplete;
    expect(toggleOf(first).getAttribute("aria-expanded")).toBe("false");
    expect(root(el).querySelector("tr.detail")).toBeNull();

    toggleOf(second).click();
    await el.updateComplete;
    expect(toggleOf(bodyRows(el)[1]).getAttribute("aria-expanded")).toBe("true");
    expect((root(el).querySelector("tr.detail") as HTMLElement).textContent).toContain(
      "Regularizada en la factura F-1",
    );
  });

  it("limits rows to maxInvoices, newest first", async () => {
    const el = await mount({
      maxInvoices: 2,
      contracts: [
        contract("electricity", [
          row("F-1", "2026-05-31"),
          row("F-3", "2026-07-31"),
          row("F-2", "2026-06-30"),
        ]),
      ],
    });
    const rows = bodyRows(el);
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain("31/07/2026");
    expect(rows[1].textContent).toContain("30/06/2026");

    el.maxInvoices = undefined;
    await el.updateComplete;
    expect(bodyRows(el)).toHaveLength(3);
  });

  it("shows a header per contract when there are two of the same supply", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [row("F-1", "2026-07-31")], "Casa", "C1"),
        contract("electricity", [row("F-9", "2026-07-31")], "Trastero", "C2"),
        contract("gas", [gasRow("G-1", "2026-07-31")], "Gas", "G1"),
      ],
    });
    const titles = [...root(el).querySelectorAll(".contract-name")].map((n) => n.textContent);
    expect(titles).toEqual(["Casa", "Trastero"]);
    expect(root(el).querySelectorAll("table")).toHaveLength(2);
  });

  it("shows no contract header when there is a single contract", async () => {
    const el = await mount({ contracts: [contract("electricity", [row("F-1", "2026-07-31")])] });
    expect(root(el).querySelector(".contract-name")).toBeNull();
  });

  it("shows the empty text when there are no contracts", async () => {
    const el = await mount({ contracts: [] });
    expect(root(el).textContent).toContain("Todavía no hay facturas");
    expect(root(el).querySelectorAll("[role=tab]")).toHaveLength(2);
    expect(root(el).querySelector("table")).toBeNull();
  });

  it("shows the empty text for a tab whose supply has no contracts", async () => {
    const el = await mount({
      supply: "gas",
      contracts: [contract("electricity", [row("F-1", "2026-07-31")])],
    });
    expect(root(el).textContent).toContain("Todavía no hay facturas");
    expect(root(el).querySelector("table")).toBeNull();
  });

  it("switches tab and emits supply-changed", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [row("F-1", "2026-07-31")]),
        contract("gas", [gasRow("G-1", "2026-07-31")], "Gas", "G1"),
      ],
    });
    const events: Supply[] = [];
    el.addEventListener("supply-changed", (event) =>
      events.push((event as CustomEvent<{ supply: Supply }>).detail.supply),
    );
    const tabs = [...root(el).querySelectorAll<HTMLElement>("[role=tab]")];
    expect(tabs.map((tab) => tab.textContent?.trim())).toEqual(["Luz", "Gas"]);
    expect(tabs[0].getAttribute("aria-selected")).toBe("true");

    tabs[1].click();
    await el.updateComplete;
    expect(el.supply).toBe("gas");
    expect(events).toEqual(["gas"]);
    expect(headers(el)).toEqual(["Periodo", "kWh", "m³", "Importe", "€/kWh"]);
    expect(
      [...root(el).querySelectorAll<HTMLElement>("[role=tab]")][1].getAttribute("aria-selected"),
    ).toBe("true");
  });

  it("does not emit when the active tab is clicked again", async () => {
    const el = await mount({ contracts: [] });
    let count = 0;
    el.addEventListener("supply-changed", () => (count += 1));
    root(el).querySelectorAll<HTMLElement>("[role=tab]")[0].click();
    await el.updateComplete;
    expect(count).toBe(0);
  });

  it("collapses expanded rows when the tab changes", async () => {
    const el = await mount({
      contracts: [
        contract("electricity", [row("F-1", "2026-07-31")]),
        contract("gas", [gasRow("F-1", "2026-07-31")], "Gas", "G1"),
      ],
    });
    toggleOf(bodyRows(el)[0]).click();
    await el.updateComplete;
    root(el).querySelectorAll<HTMLElement>("[role=tab]")[1].click();
    await el.updateComplete;
    expect(toggleOf(bodyRows(el)[0]).getAttribute("aria-expanded")).toBe("false");
  });
});

// Keep the Status import used for readers of the file: every status renders without throwing.
describe("every status renders", () => {
  const statuses: Status[] = ["ok", "no_cuadra", "estimada", "sin_datos", "no_leida", "gas"];
  it.each(statuses)("renders status %s", async (status) => {
    const el = await mount({
      contracts: [contract("electricity", [row("F-1", "2026-07-31", { status })])],
    });
    expect(bodyRows(el)).toHaveLength(1);
  });
});
