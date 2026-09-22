import type { ComboboxOption } from "@/components/Combobox";
import type { Category } from "../../types/api";

/** Categories as combobox options, each marked with its colour. */
export function categoryOptions(categories: Category[]): ComboboxOption[] {
  return categories.map((category) => ({
    value: String(category.id),
    label: category.name,
    icon: (
      <span
        className="h-3 w-3 rounded-full shrink-0"
        style={{ backgroundColor: category.color }}
      />
    ),
  }));
}
