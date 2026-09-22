import { Tag } from "lucide-react";

import Combobox from "@/components/Combobox";
import { useCategories } from "@/hooks/queries";
import { categoryOptions } from "./categoryOptions";

export interface CategoryComboboxProps {
  selectedCategory: string;
  onCategoryChange: (categoryId: string) => void;
  className?: string;
}

export function CategoryCombobox({
  selectedCategory,
  onCategoryChange,
  className,
}: CategoryComboboxProps) {
  const { data: categories = [] } = useCategories();

  const options = [
    {
      value: "",
      label: "All categories",
      icon: <Tag className="h-4 w-4 text-muted-foreground" />,
    },
    {
      value: "uncategorized",
      label: "Uncategorized",
      icon: (
        <span className="h-3 w-3 rounded-full shrink-0 border border-dashed border-muted-foreground" />
      ),
    },
    ...categoryOptions(categories),
  ];

  return (
    <Combobox
      className={className}
      options={options}
      value={selectedCategory}
      onChange={onCategoryChange}
      placeholder="All categories"
      icon={<Tag className="h-4 w-4" />}
      searchPlaceholder="Search categories..."
      emptyText="No categories found."
      popoverClassName="w-[220px]"
    />
  );
}
