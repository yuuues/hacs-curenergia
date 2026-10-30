import { describe, expect, it, vi } from "vitest";
import { fetchInvoices, fetchSummary } from "../src/api";
import type { HomeAssistant } from "../src/types";

function fakeHass(result: unknown = {}) {
  const sendMessagePromise = vi.fn().mockResolvedValue(result);
  const hass = {
    language: "es",
    locale: { language: "es" },
    connection: { sendMessagePromise },
  } as unknown as HomeAssistant;
  return { hass, sendMessagePromise };
}

describe("fetchInvoices", () => {
  it("sends the invoices command without undefined keys", async () => {
    const { hass, sendMessagePromise } = fakeHass({ contracts: [] });
    const response = await fetchInvoices(hass, { supply: "gas", entry_id: undefined });
    expect(sendMessagePromise).toHaveBeenCalledTimes(1);
    expect(sendMessagePromise).toHaveBeenCalledWith({ type: "curenergia/invoices", supply: "gas" });
    expect(Object.keys(sendMessagePromise.mock.calls[0][0])).toEqual(["type", "supply"]);
    expect(response).toEqual({ contracts: [] });
  });

  it("sends only the type when there are no options", async () => {
    const { hass, sendMessagePromise } = fakeHass({ contracts: [] });
    await fetchInvoices(hass);
    expect(sendMessagePromise).toHaveBeenCalledWith({ type: "curenergia/invoices" });
  });

  it("passes entry_id and supply together", async () => {
    const { hass, sendMessagePromise } = fakeHass({ contracts: [] });
    await fetchInvoices(hass, { entry_id: "abc", supply: "electricity" });
    expect(sendMessagePromise).toHaveBeenCalledWith({
      type: "curenergia/invoices",
      entry_id: "abc",
      supply: "electricity",
    });
  });
});

describe("fetchSummary", () => {
  it("sends the summary command with entry_id", async () => {
    const { hass, sendMessagePromise } = fakeHass();
    await fetchSummary(hass, "abc");
    expect(sendMessagePromise).toHaveBeenCalledWith({ type: "curenergia/summary", entry_id: "abc" });
  });

  it("omits entry_id when not given", async () => {
    const { hass, sendMessagePromise } = fakeHass();
    await fetchSummary(hass);
    expect(sendMessagePromise).toHaveBeenCalledWith({ type: "curenergia/summary" });
  });
});
