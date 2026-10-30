import { beforeEach, describe, expect, it } from "vitest";
import { defineFakeHaElements, fakeHass } from "./helpers";
import "../src/card-editor";
import type { CurenergiaInvoicesCardEditor } from "../src/card-editor";

defineFakeHaElements();

type FakeForm = HTMLElement & {
  hass: unknown;
  data: Record<string, unknown>;
  schema: { name: string; selector?: Record<string, unknown> }[];
  computeLabel: (item: { name: string }) => string;
};

async function mount(config: Record<string, unknown>, language = "en") {
  const editor = document.createElement(
    "curenergia-invoices-card-editor",
  ) as CurenergiaInvoicesCardEditor;
  editor.hass = fakeHass(language);
  editor.setConfig({ type: "custom:curenergia-invoices-card", ...config } as never);
  document.body.appendChild(editor);
  await editor.updateComplete;
  const form = editor.shadowRoot!.querySelector("ha-form") as FakeForm;
  return { editor, form };
}

describe("curenergia-invoices-card-editor", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("renders ha-form with the expected schema and data", async () => {
    const { form, editor } = await mount({ title: "T", max_invoices: 5 });
    expect(form).toBeTruthy();
    expect(form.hass).toBe(editor.hass);
    expect(form.data).toMatchObject({ title: "T", max_invoices: 5 });
    expect(form.schema.map((s) => s.name)).toEqual(["title", "supply", "max_invoices", "entry_id"]);
    const byName = Object.fromEntries(form.schema.map((s) => [s.name, s]));
    expect(byName.title.selector).toEqual({ text: {} });
    expect(byName.supply.selector).toMatchObject({
      select: { options: [
        { value: "electricity", label: "Electricity" },
        { value: "gas", label: "Gas" },
      ] },
    });
    expect(byName.max_invoices.selector).toEqual({ number: { min: 1, max: 60, mode: "box" } });
    expect(byName.entry_id.selector).toEqual({ config_entry: { integration: "curenergia" } });
  });

  it("uses translated labels", async () => {
    const { form } = await mount({}, "es");
    expect(form.computeLabel({ name: "title" })).toBe("Título");
    expect(form.computeLabel({ name: "max_invoices" })).toBe("Número máximo de facturas");
    expect(form.computeLabel({ name: "entry_id" })).toBe("Cuenta de correo (opcional)");
    expect(form.computeLabel({ name: "supply" })).toBe("Pestaña inicial");
    expect(form.computeLabel({ name: "other" })).toBe("other");
  });

  it("editor emits config-changed without empty keys", async () => {
    const { editor, form } = await mount({ title: "Old", supply: "gas" });
    const events: CustomEvent[] = [];
    editor.addEventListener("config-changed", (e) => events.push(e as CustomEvent));
    form.dispatchEvent(
      new CustomEvent("value-changed", {
        detail: { value: { title: "", supply: "", max_invoices: 4, entry_id: undefined } },
      }),
    );
    expect(events).toHaveLength(1);
    expect(events[0].detail.config).toEqual({
      type: "custom:curenergia-invoices-card",
      max_invoices: 4,
    });
    expect(events[0].bubbles).toBe(true);
    expect(events[0].composed).toBe(true);
  });

  it("keeps non-empty values", async () => {
    const { editor, form } = await mount({});
    let detail: { config: Record<string, unknown> } | undefined;
    editor.addEventListener("config-changed", (e) => (detail = (e as CustomEvent).detail));
    form.dispatchEvent(
      new CustomEvent("value-changed", {
        detail: { value: { title: "Casa", supply: "gas", max_invoices: 10, entry_id: "abc" } },
      }),
    );
    expect(detail!.config).toEqual({
      type: "custom:curenergia-invoices-card",
      title: "Casa",
      supply: "gas",
      max_invoices: 10,
      entry_id: "abc",
    });
  });
});
