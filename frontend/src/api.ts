import type { HomeAssistant, InvoicesResponse, Summary, Supply } from "./types";

export interface InvoicesOptions {
  entry_id?: string;
  supply?: Supply;
}

/** Copy of `command` without the keys whose value is `undefined`. */
function compact(command: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(command).filter(([, value]) => value !== undefined));
}

export function fetchInvoices(
  hass: HomeAssistant,
  opts: InvoicesOptions = {},
): Promise<InvoicesResponse> {
  return hass.connection.sendMessagePromise<InvoicesResponse>(
    compact({ type: "curenergia/invoices", entry_id: opts.entry_id, supply: opts.supply }),
  );
}

export function fetchSummary(hass: HomeAssistant, entry_id?: string): Promise<Summary> {
  return hass.connection.sendMessagePromise<Summary>(
    compact({ type: "curenergia/summary", entry_id }),
  );
}
