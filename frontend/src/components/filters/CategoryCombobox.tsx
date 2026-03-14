import { useState } from "react";
import { Check, ChevronDown, Tag } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { apiClient } from "../../lib/api";
import type { Category } from "../../types/api";

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
  const [open, setOpen] = useState(false);

  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ["categories"],
    queryFn: apiClient.getCategories,
  });

  const selectedCategoryData = categories.find(
    (cat) => String(cat.id) === selectedCategory,
  );

  const getDisplayLabel = () => {
    if (selectedCategory === "uncategorized") return "Uncategorized";
    if (selectedCategoryData) return selectedCategoryData.name;
    return "All categories";
  };

  return (
    <div className={className}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between"
          >
            <div className="flex items-center">
              {selectedCategoryData ? (
                <span
                  className="mr-2 h-3 w-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: selectedCategoryData.color }}
                />
              ) : (
                <Tag className="mr-2 h-4 w-4" />
              )}
              {getDisplayLabel()}
            </div>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[220px] p-0">
          <Command>
            <CommandInput
              placeholder="Search categories..."
              className="h-9"
            />
            <CommandList>
              <CommandEmpty>No categories found.</CommandEmpty>
              <CommandGroup>
                {/* All categories option */}
                <CommandItem
                  value="all-categories"
                  onSelect={() => {
                    onCategoryChange("");
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      selectedCategory === "" ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <Tag className="mr-2 h-4 w-4 text-muted-foreground" />
                  All categories
                </CommandItem>

                {/* Uncategorized option */}
                <CommandItem
                  value="uncategorized"
                  onSelect={() => {
                    onCategoryChange("uncategorized");
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      selectedCategory === "uncategorized"
                        ? "opacity-100"
                        : "opacity-0",
                    )}
                  />
                  <span className="mr-2 h-3 w-3 rounded-full flex-shrink-0 border border-dashed border-muted-foreground" />
                  Uncategorized
                </CommandItem>

                {/* Individual categories */}
                {categories.map((cat) => (
                  <CommandItem
                    key={cat.id}
                    value={cat.name}
                    onSelect={() => {
                      onCategoryChange(String(cat.id));
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        selectedCategory === String(cat.id)
                          ? "opacity-100"
                          : "opacity-0",
                      )}
                    />
                    <span
                      className="mr-2 h-3 w-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: cat.color }}
                    />
                    {cat.name}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
