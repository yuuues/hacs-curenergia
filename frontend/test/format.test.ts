import { describe, expect, it } from "vitest";
import {
  deltaColorVar,
  formatCount,
  formatDate,
  formatDelta,
  formatEur,
  formatKwh,
  formatM3,
  formatPct,
  formatPeriod,
  formatPricePerKwh,
  formatRate,
  formatSignedPct,
} from "../src/format";

// Intl inserts no-break spaces; the implementation normalises them to plain ones.
const plain = (text: string) => text.replace(/[  ]/g, " ");

describe("dates", () => {
  it("formats ISO dates without timezone shift", () => {
    const previous = process.env.TZ;
    process.env.TZ = "America/Los_Angeles";
    try {
      expect(formatDate("2026-08-29")).toBe("29/08/2026");
      expect(formatDate("2026-01-01")).toBe("01/01/2026");
    } finally {
      if (previous === undefined) delete process.env.TZ;
      else process.env.TZ = previous;
    }
  });

  it("formats periods", () => {
    expect(formatPeriod("2026-08-29", "2026-09-28")).toBe("29/08 – 28/09/2026");
    expect(formatPeriod("2025-12-28", "2026-01-31")).toBe("28/12/2025 – 31/01/2026");
  });
});

describe("numbers", () => {
  it("formats numbers per locale and nulls as dash", () => {
    expect(plain(formatEur("es", 102.55))).toBe("102,55 €");
    expect(plain(formatKwh("en", 380.06))).toBe("380.06 kWh");
    expect(plain(formatPricePerKwh("es", 0.2698))).toBe("0,2698 €/kWh");
    expect(formatEur("es", null)).toBe("—");
    expect(formatKwh("es", null)).toBe("—");
    expect(formatPricePerKwh("en", null)).toBe("—");
    expect(formatPct("es", null)).toBe("—");
  });

  it("uses 0-2 decimals for kWh, 2 for euros and 1 for percentages", () => {
    expect(plain(formatKwh("es", 380))).toBe("380 kWh");
    expect(plain(formatKwh("es", 380.1))).toBe("380,1 kWh");
    expect(plain(formatEur("en", 5))).toBe("5.00 €");
    expect(plain(formatPct("es", 3.456))).toBe("3,5 %");
  });

  it("formats cubic metres (0-2 decimals) and VAT rates", () => {
    expect(plain(formatM3("es", 34.5))).toBe("34,5 m³");
    expect(plain(formatM3("en", 34))).toBe("34 m³");
    expect(formatM3("es", null)).toBe("—");
    expect(plain(formatRate("es", 21))).toBe("21 %");
    expect(plain(formatRate("es", 10.5))).toBe("10,5 %");
    expect(formatRate("es", null)).toBe("—");
  });

  it("falls back to English for an invalid language tag", () => {
    expect(plain(formatEur("not a tag", 1.5))).toBe("1.50 €");
    expect(plain(formatCount("not a tag", 1234))).toBe("1,234");
  });

  it("formats counts as integers per locale", () => {
    expect(plain(formatCount("en", 3))).toBe("3");
    expect(plain(formatCount("en", 1234))).toBe("1,234");
  });
});

describe("deltas", () => {
  it("signs deltas", () => {
    expect(plain(formatDelta("es", -1.82, "eur"))).toBe("−1,82 €");
    expect(plain(formatDelta("es", 5, "kwh"))).toBe("+5 kWh");
    expect(plain(formatDelta("es", 0, "kwh"))).toBe("0 kWh");
    expect(plain(formatDelta("es", 0, "eur"))).toBe("0,00 €");
    expect(formatDelta("es", null, "eur")).toBe("—");
  });
});

describe("colours", () => {
  it("maps status to theme colour variables", () => {
    expect(deltaColorVar("ok")).toBe("--success-color");
    expect(deltaColorVar("no_cuadra")).toBe("--warning-color");
    expect(deltaColorVar("estimada")).toBe("--secondary-text-color");
    expect(deltaColorVar("sin_datos")).toBe("--secondary-text-color");
    expect(deltaColorVar("gas")).toBe("--secondary-text-color");
    expect(deltaColorVar("no_leida")).toBe("--error-color");
  });
});

describe("signed percentages", () => {
  it("adds the sign, and shows zero and null plainly", () => {
    expect(plain(formatSignedPct("es", 1.2))).toBe("+1,2 %");
    expect(plain(formatSignedPct("en", -0.84))).toBe("−0.8 %");
    expect(plain(formatSignedPct("es", 0))).toBe("0,0 %");
    expect(plain(formatSignedPct("es", 0.04))).toBe("0,0 %");
    expect(formatSignedPct("es", null)).toBe("—");
  });
});
