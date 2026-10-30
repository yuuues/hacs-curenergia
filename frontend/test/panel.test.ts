import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineFakeHaElements, fakeHass } from "./helpers";
import "../src/panel";
import type { CurenergiaPanel } from "../src/panel";
import type { ContractInvoices, Summary } from "../src/types";

defineFakeHaElements();
if (!customElements.get("ha-menu-button")) {
  customElements.define(
    "ha-menu-button",
    class extends HTMLElement {
      hass?: unknown;
      narrow?: boolean;
    },
  );
}

const REFRESH_MS = 15 * 60 * 1000;

const flush = async () => {
  for (let i = 0; i < 8; i += 1) await Promise.resolve();
};

const SUMMARY: Summary = {
  billed_12m: 1234.5,
  kwh_delta_pct: 1.2,
  estimated_count: 3,
  unreadable_emails: 0,
  unsupported_emails: 0,
  last_mail_check: null,
  mail_error: false,
};

const CONTRACTS: ContractInvoices[] = [
  {
    entry_id: "e1",
    contract: "c1",
    supply: "electricity",
    name: "Casa",
    invoices: [
      {
        number: "F1",
        supply: "electricity",
        issue_date: "2026-08-01",
        period_start: "2026-07-01",
        period_end: "2026-07-31",
        estimated: false,
        status: "ok",
        problems: [],
        total: 40,
        kwh: 100,
        price_kwh: null,
        m3: null,
        energy_price_kwh: null,
        periods: null,
        concepts: [],
        vat: { rate: null, base: null, amount: null },
        in_group_of: null,
        comparison: null,
      },
    ],
  },
];

function api(summary: Partial<Summary> = {}, contracts: ContractInvoices[] = CONTRACTS) {
  return vi.fn(async (msg: { type?: string }) =>
    msg.type === "curenergia/summary" ? { ...SUMMARY, ...summary } : { contracts },
  );
}

async function makePanel(
  send: ReturnType<typeof api>,
  language = "es",
  narrow = false,
): Promise<CurenergiaPanel> {
  const panel = document.createElement("curenergia-panel") as CurenergiaPanel;
  document.body.appendChild(panel);
  panel.narrow = narrow;
  panel.hass = fakeHass(language, send as never);
  await flush();
  await panel.updateComplete;
  return panel;
}

const text = (panel: CurenergiaPanel) => panel.shadowRoot!.textContent ?? "";
const kpis = (panel: CurenergiaPanel) =>
  [...panel.shadowRoot!.querySelectorAll(".kpi")].map((el) => ({
    label: el.querySelector(".label")!.textContent!.trim(),
    value: el.querySelector(".value")!.textContent!.trim(),
  }));

describe("curenergia-panel", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("fetches summary and invoices once on first hass, without entry_id", async () => {
    const send = api();
    const panel = await makePanel(send);
    expect(send).toHaveBeenCalledTimes(2);
    expect(send).toHaveBeenCalledWith({ type: "curenergia/summary" });
    expect(send).toHaveBeenCalledWith({ type: "curenergia/invoices" });
    panel.hass = fakeHass("es", send as never);
    await flush();
    expect(send).toHaveBeenCalledTimes(2);
  });

  it("renders the top bar with the menu button and the translated title", async () => {
    const panel = await makePanel(api(), "es", true);
    const button = panel.shadowRoot!.querySelector("ha-menu-button") as unknown as {
      hass: unknown;
      narrow: boolean;
    };
    expect(button).not.toBeNull();
    expect(button.narrow).toBe(true);
    expect(button.hass).toBe(panel.hass);
    expect(panel.shadowRoot!.querySelector(".toolbar")!.textContent).toContain("Facturas");
  });

  it("renders KPIs from the summary", async () => {
    const panel = await makePanel(api());
    expect(kpis(panel)).toEqual([
      { label: "Facturado en 12 meses", value: "1234,50 €" },
      { label: "kWh factura vs Datadis", value: "+1,2 %" },
      { label: "Lecturas estimadas", value: "3" },
    ]);
  });

  it("shows a dash for a null summary figure", async () => {
    const panel = await makePanel(api({ billed_12m: null, kwh_delta_pct: null }));
    expect(kpis(panel).map((k) => k.value)).toEqual(["—", "—", "3"]);
  });

  it("shows a minus sign for a negative difference", async () => {
    const panel = await makePanel(api({ kwh_delta_pct: -0.8 }), "en");
    expect(kpis(panel)[1].value).toBe("−0.8 %");
  });

  it("shows mail error and unreadable warnings", async () => {
    const panel = await makePanel(api({ mail_error: true, unreadable_emails: 2 }));
    expect(text(panel)).toContain("No se pudo leer el correo; se muestran las facturas guardadas");
    expect(text(panel)).toContain("2 correos con factura que no se pudo leer");
  });

  it("warns about unsupported e-mails with their count", async () => {
    const es = await makePanel(api({ unsupported_emails: 3 }));
    expect(text(es)).toContain(
      "Correos con factura no soportada (rectificativa o abono): 3",
    );
    const en = await makePanel(api({ unsupported_emails: 1 }), "en");
    expect(text(en)).toContain(
      "E-mails with an unsupported invoice (corrective or credit note): 1",
    );
  });

  it("shows no warnings when there is nothing to warn about", async () => {
    const panel = await makePanel(api());
    expect(panel.shadowRoot!.querySelectorAll(".warning")).toHaveLength(0);
  });

  it("shows the chart and the table without a row limit", async () => {
    const panel = await makePanel(api());
    const chart = panel.shadowRoot!.querySelector("curenergia-bar-chart") as unknown as {
      invoices: { number: string }[];
    };
    const table = panel.shadowRoot!.querySelector("curenergia-invoice-table") as unknown as {
      contracts: ContractInvoices[];
      maxInvoices?: number;
    };
    expect(chart.invoices.map((i) => i.number)).toEqual(["F1"]);
    expect(table.contracts).toEqual(CONTRACTS);
    expect(table.maxInvoices).toBeUndefined();
    // A single electricity contract: no contract subtitle over the chart.
    expect(panel.shadowRoot!.querySelector(".chart-name")).toBeNull();
  });

  it("draws one chart per electricity contract, named when there are several", async () => {
    const invoice = CONTRACTS[0].invoices[0];
    const contracts: ContractInvoices[] = [
      CONTRACTS[0],
      {
        entry_id: "e1",
        contract: "c2",
        supply: "electricity",
        name: "Garaje",
        invoices: [{ ...invoice, number: "G1" }, { ...invoice, number: "G2" }],
      },
      {
        entry_id: "e1",
        contract: "c3",
        supply: "gas",
        name: "Gas casa",
        invoices: [{ ...invoice, number: "GAS1", supply: "gas" }],
      },
    ];
    const panel = await makePanel(api({}, contracts));
    const charts = [
      ...panel.shadowRoot!.querySelectorAll("curenergia-bar-chart"),
    ] as unknown as { invoices: { number: string }[] }[];
    expect(charts.map((chart) => chart.invoices.map((i) => i.number))).toEqual([
      ["F1"],
      ["G1", "G2"],
    ]);
    const names = [...panel.shadowRoot!.querySelectorAll(".chart-name")].map((el) =>
      el.textContent!.trim(),
    );
    expect(names).toEqual(["Casa", "Garaje"]);
  });

  it("shows the empty text with no contracts", async () => {
    const panel = await makePanel(api({}, []), "en");
    expect(text(panel)).toContain("No invoices yet");
    expect(panel.shadowRoot!.querySelector("curenergia-invoice-table")).toBeNull();
    expect(panel.shadowRoot!.querySelector("curenergia-bar-chart")).toBeNull();
  });

  it("shows a generic error without details", async () => {
    const send = vi.fn().mockRejectedValue(new Error("secret"));
    const panel = await makePanel(send as never, "en");
    expect(text(panel)).toContain("Could not load the invoices");
    expect(text(panel)).not.toContain("secret");
  });

  it("refreshes every 15 minutes, skips a tick while a request is in flight and stops on disconnect", async () => {
    vi.useFakeTimers();
    const releases: (() => void)[] = [];
    let hold = false;
    const send = vi.fn(async (msg: { type?: string }) => {
      if (hold) await new Promise<void>((resolve) => releases.push(resolve));
      return msg.type === "curenergia/summary" ? SUMMARY : { contracts: CONTRACTS };
    });
    const panel = document.createElement("curenergia-panel") as CurenergiaPanel;
    document.body.appendChild(panel);
    panel.hass = fakeHass("en", send as never);
    await vi.advanceTimersByTimeAsync(0);
    expect(send).toHaveBeenCalledTimes(2);

    hold = true;
    await vi.advanceTimersByTimeAsync(REFRESH_MS);
    expect(send).toHaveBeenCalledTimes(4);
    // Still in flight: the next tick does not start another pair of requests.
    await vi.advanceTimersByTimeAsync(REFRESH_MS);
    expect(send).toHaveBeenCalledTimes(4);

    hold = false;
    releases.forEach((release) => release());
    await vi.advanceTimersByTimeAsync(0);
    await vi.advanceTimersByTimeAsync(REFRESH_MS);
    expect(send).toHaveBeenCalledTimes(6);

    panel.remove();
    await vi.advanceTimersByTimeAsync(REFRESH_MS * 3);
    expect(send).toHaveBeenCalledTimes(6);
  });

  it("ignores a late answer after disconnect and fetches again on reconnect", async () => {
    let resolveSummary: ((value: Summary) => void) | undefined;
    const send = vi.fn(async (msg: { type?: string }) =>
      msg.type === "curenergia/summary"
        ? new Promise<Summary>((resolve) => (resolveSummary = resolve))
        : { contracts: CONTRACTS },
    );
    const panel = document.createElement("curenergia-panel") as CurenergiaPanel;
    document.body.appendChild(panel);
    panel.hass = fakeHass("en", send as never);
    await flush();
    panel.remove();
    resolveSummary?.(SUMMARY);
    await flush();
    expect((panel as unknown as { _summary?: Summary })._summary).toBeUndefined();
    document.body.appendChild(panel);
    await flush();
    expect(send).toHaveBeenCalledTimes(4);
  });
});
