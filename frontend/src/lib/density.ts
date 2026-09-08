/**
 * Row density for the transaction table.
 *
 * A ledger is read by scanning down a column, so how many rows fit on screen
 * matters more here than breathing room. "Compact" is the default; "cosy"
 * keeps the roomier spacing for anyone who prefers it.
 */
const DENSITIES = ["compact", "cosy"] as const;

export type Density = (typeof DENSITIES)[number];

export const DEFAULT_DENSITY: Density = "compact";

export function asDensity(value: unknown): Density | undefined {
  if (typeof value !== "string") return undefined;
  const text = value.trim().toLowerCase();
  return DENSITIES.find((density) => density === text);
}

/** Vertical cell padding per density, applied to every body cell. */
export const DENSITY_CELL_CLASS: Record<Density, string> = {
  compact: "py-2",
  cosy: "py-4",
};

const STORAGE_KEY = "leggen:transaction-density";

/**
 * Density is a per-device display preference rather than part of the view, so
 * it lives in localStorage instead of the URL — a shared link should not
 * impose the sender's row height on the recipient.
 */
export function readStoredDensity(): Density {
  try {
    return asDensity(localStorage.getItem(STORAGE_KEY)) ?? DEFAULT_DENSITY;
  } catch {
    // Private-mode browsers throw on access rather than returning null.
    return DEFAULT_DENSITY;
  }
}

export function writeStoredDensity(density: Density): void {
  try {
    localStorage.setItem(STORAGE_KEY, density);
  } catch {
    // A preference that cannot be persisted still applies for this session.
  }
}
