import { beforeEach, describe, expect, it } from "vitest";
import { fakeHass } from "./helpers";
import "../src/chart";
import type { CurenergiaBarChart } from "../src/chart";
import type { InvoiceRow } from "../src/types";

function invoice(
  n: number,
  periodEnd: string,
  kwh: number | null,
  edata: number | null,
  supply: "electricity" | "gas" = "electricity",
): InvoiceRow {
  return {
    number: `F${n}`,
    supply,
    issue_date: periodEnd,
    period_start: periodEnd,
    period_end: periodEnd,
    estimated: false,
    status: "ok",
    problems: [],
    total: 50,
    kwh,
    price_kwh: null,
    m3: null,
    energy_price_kwh: null,
    periods: null,
    concepts: [],
    vat: { rate: null, base: null, amount: null },
    in_group_of: null,
    comparison:
      edata === null
        ? null
        : ({
            group: [`F${n}`],
            invoice_kwh: kwh,
            edata_kwh: edata,
          } as never),
  };
}

async function makeChart(invoices: InvoiceRow[], language = "es"): Promise<CurenergiaBarChart> {
  const chart = document.createElement("curenergia-bar-chart") as CurenergiaBarChart;
  chart.hass = fakeHass(language);
  chart.invoices = invoices;
  document.body.appendChild(chart);
  await chart.updateComplete;
  return chart;
}

const labels = (chart: CurenergiaBarChart) =>
  [...chart.shadowRoot!.querySelectorAll("text.x-label")].map((el) => el.textContent);

describe("curenergia-bar-chart", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("draws one pair of bars per electricity invoice, max 12, oldest first", async () => {
    // 14 monthly invoices, Jan 2026 .. Feb 2027, given newest first, plus a gas one.
    const rows: InvoiceRow[] = [];
    for (let i = 13; i >= 0; i -= 1) {
      const year = 2026 + Math.floor(i / 12);
      const month = String((i % 12) + 1).padStart(2, "0");
      rows.push(invoice(i, `${year}-${month}-28`, 100, 98));
    }
    rows.push(invoice(99, "2027-03-28", 5, null, "gas"));
    const chart = await makeChart(rows);
    const root = chart.shadowRoot!;
    expect(root.querySelectorAll("rect.bar.invoice")).toHaveLength(12);
    expect(root.querySelectorAll("rect.bar.datadis")).toHaveLength(12);
    // The 12 most recent (Jan and Feb 2026 dropped), oldest first.
    expect(labels(chart)).toEqual([
      "03/26",
      "04/26",
      "05/26",
      "06/26",
      "07/26",
      "08/26",
      "09/26",
      "10/26",
      "11/26",
      "12/26",
      "01/27",
      "02/27",
    ]);
  });

  it("uses mm/aa from period_end without timezone shifts", async () => {
    const chart = await makeChart([
      invoice(1, "2026-08-01", 10, 9),
      invoice(2, "2026-12-31", 20, 18),
    ]);
    expect(labels(chart)).toEqual(["08/26", "12/26"]);
  });

  it("scales bars to the maximum and takes the colours from theme variables", async () => {
    const chart = await makeChart([
      invoice(1, "2026-07-31", 200, 100),
      invoice(2, "2026-08-31", 50, null),
    ]);
    const root = chart.shadowRoot!;
    const heights = (selector: string) =>
      [...root.querySelectorAll(selector)].map((el) => Number(el.getAttribute("height")));
    const [first, second] = heights("rect.bar.invoice");
    const [datadis] = heights("rect.bar.datadis");
    expect(first).toBeGreaterThan(0);
    expect(second).toBeCloseTo(first / 4, 5);
    expect(datadis).toBeCloseTo(first / 2, 5);
    const css = (chart.constructor as unknown as { styles: { cssText: string } }).styles.cssText;
    expect(css).toContain("var(--primary-color)");
    expect(css).toContain("var(--secondary-text-color)");
  });

  it("draws only the invoice bar when comparison is null", async () => {
    const chart = await makeChart([invoice(1, "2026-07-31", 100, null)]);
    const root = chart.shadowRoot!;
    expect(root.querySelectorAll("rect.bar.invoice")).toHaveLength(1);
    expect(root.querySelectorAll("rect.bar.datadis")).toHaveLength(0);
  });

  it("puts the formatted value in a <title> of each bar", async () => {
    const chart = await makeChart([invoice(1, "2026-07-31", 1234.5, 1200)], "es");
    const titles = [...chart.shadowRoot!.querySelectorAll("rect.bar title")].map(
      (el) => el.textContent,
    );
    expect(titles).toHaveLength(2);
    expect(titles[0]).toContain("1234,5 kWh");
    expect(titles[1]).toContain("1200 kWh");
  });

  it("has a translated legend", async () => {
    const es = await makeChart([invoice(1, "2026-07-31", 10, 9)], "es");
    const text = es.shadowRoot!.querySelector(".legend")!.textContent!;
    expect(text).toContain("Factura");
    expect(text).toContain("Datadis");
    document.body.innerHTML = "";
    const en = await makeChart([invoice(1, "2026-07-31", 10, 9)], "en");
    expect(en.shadowRoot!.querySelector(".legend")!.textContent).toContain("Invoice");
  });

  it("shows the empty text when there is nothing to draw", async () => {
    const cases = [
      [],
      [invoice(1, "2026-07-31", 5, null, "gas")],
      [invoice(2, "2026-07-31", null, null)],
    ];
    for (const rows of cases) {
      document.body.innerHTML = "";
      const chart = await makeChart(rows, "en");
      expect(chart.shadowRoot!.querySelector("svg")).toBeNull();
      expect(chart.shadowRoot!.textContent).toContain("No data for the chart");
    }
  });

  describe("per-invoice figures", () => {
    // E1 is estimated and settled by R; R's comparison covers both.
    function group(memberComparison: boolean): InvoiceRow[] {
      const e1: InvoiceRow = {
        ...invoice(1, "2026-06-30", 300, memberComparison ? 310 : null),
        number: "E1",
        estimated: true,
        status: "estimada",
        in_group_of: "R",
      };
      if (e1.comparison) e1.comparison = { ...e1.comparison, group: ["E1"] };
      const r: InvoiceRow = {
        ...invoice(2, "2026-07-31", 900, 1200),
        number: "R",
        comparison: { group: ["E1", "R"], invoice_kwh: 1200, edata_kwh: 1200 } as never,
      };
      return [r, e1];
    }

    const titles = (chart: CurenergiaBarChart, kind: "invoice" | "datadis") =>
      [...chart.shadowRoot!.querySelectorAll(`rect.bar.${kind} title`)].map(
        (el) => el.textContent ?? "",
      );

    it("draws each invoice's own kWh and the Datadis share of its own period", async () => {
      const chart = await makeChart(group(true));
      const invoiceTitles = titles(chart, "invoice");
      const datadisTitles = titles(chart, "datadis");
      expect(invoiceTitles).toHaveLength(2);
      expect(invoiceTitles[0]).toContain("300 kWh");
      expect(invoiceTitles[1]).toContain("900 kWh");
      expect(datadisTitles).toHaveLength(2);
      expect(datadisTitles[0]).toContain("310 kWh");
      expect(datadisTitles[1]).toContain("890 kWh");
    });

    it("omits the Datadis bar of a group whose member has no comparison", async () => {
      const chart = await makeChart(group(false));
      expect(titles(chart, "invoice")).toHaveLength(2);
      expect(titles(chart, "datadis")).toHaveLength(0);
    });

    it("draws estimated and unreadable invoices with their own style and tooltip", async () => {
      const unreadable: InvoiceRow = {
        ...invoice(3, "2026-08-31", 100, 98),
        status: "no_leida",
      };
      const chart = await makeChart([...group(true), unreadable]);
      const bars = [...chart.shadowRoot!.querySelectorAll("rect.bar.invoice")];
      expect(bars[0].classList.contains("estimated")).toBe(true);
      expect(bars[0].querySelector("title")!.textContent).toContain("estimada");
      expect(bars[1].classList.contains("estimated")).toBe(false);
      expect(bars[1].classList.contains("unreadable")).toBe(false);
      expect(bars[2].classList.contains("unreadable")).toBe(true);
      expect(bars[2].querySelector("title")!.textContent).toContain("no se pudo leer");
      const css = (chart.constructor as unknown as { styles: { cssText: string } }).styles
        .cssText;
      expect(css).toMatch(/\.bar\.invoice\.estimated[^}]*stroke-dasharray/);
    });
  });

  it("does not fail with all-zero values", async () => {
    const chart = await makeChart([invoice(1, "2026-07-31", 0, 0)]);
    const bars = [...chart.shadowRoot!.querySelectorAll("rect.bar")];
    expect(bars).toHaveLength(2);
    for (const bar of bars) expect(Number(bar.getAttribute("height"))).toBe(0);
  });
});
