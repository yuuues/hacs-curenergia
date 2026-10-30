import { describe, expect, it } from "vitest";
import { STRINGS, t } from "../src/i18n";
import type { HomeAssistant } from "../src/types";

const hassWith = (language: string) =>
  ({ language, locale: { language } }) as unknown as HomeAssistant;

describe("i18n", () => {
  it("has the same keys in es and en", () => {
    expect(Object.keys(STRINGS.es).sort()).toEqual(Object.keys(STRINGS.en).sort());
  });

  it("has no empty strings", () => {
    for (const lang of ["es", "en"] as const) {
      for (const [key, value] of Object.entries(STRINGS[lang])) {
        expect(value, `${lang}.${key}`).not.toBe("");
      }
    }
  });

  it("picks Spanish for es-ES and English otherwise", () => {
    expect(t(hassWith("es-ES"), "tab_electricity")).toBe("Luz");
    expect(t(hassWith("es"), "tab_electricity")).toBe("Luz");
    expect(t(hassWith("de"), "tab_electricity")).toBe("Electricity");
    expect(t(hassWith("en"), "tab_electricity")).toBe("Electricity");
  });

  it("falls back to hass.language when locale is missing", () => {
    expect(t({ language: "es" } as unknown as HomeAssistant, "tab_electricity")).toBe("Luz");
  });

  it("translates the plan 2 status texts", () => {
    const es = hassWith("es");
    expect(t(es, "status_ok")).toBe("Cuadra");
    expect(t(es, "status_mismatch")).toBe("No cuadra");
    expect(t(es, "status_estimated")).toBe("Lectura estimada");
    expect(t(es, "status_no_data")).toBe("Sin datos suficientes");
    expect(t(es, "status_unreadable")).toBe("No se pudo leer");
    expect(t(es, "status_gas")).toBe("Gas (sin casar)");
  });

  it("replaces {placeholders}", () => {
    expect(t(hassWith("en"), "detail_power_energy", { invoice: "10 €", edata: "9 €" })).toBe(
      "Power + energy: invoice 10 € / e-data 9 €",
    );
  });
});
