import { useState, type ReactNode } from "react";
import { Check, ChevronDown } from "lucide-react";

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

export interface ComboboxOption {
  value: string;
  label: string;
  /** Shown on the trigger when selected; defaults to the label. */
  triggerLabel?: string;
  /** Extra words the search matches besides the label. */
  keywords?: string[];
  icon?: ReactNode;
  /** A second, muted line under the label in the list. */
  description?: ReactNode;
}

interface ComboboxProps {
  options: ComboboxOption[];
  value: string;
  onChange: (value: string) => void;
  /** Trigger text when no option matches `value`. */
  placeholder: string;
  /** Trigger icon when the selected option has none of its own. */
  icon: ReactNode;
  searchPlaceholder: string;
  emptyText: string;
  popoverClassName?: string;
  className?: string;
}

/** A searchable single-choice picker: a button that opens a filtered list. */
export default function Combobox({
  options,
  value,
  onChange,
  placeholder,
  icon,
  searchPlaceholder,
  emptyText,
  popoverClassName = "w-[240px]",
  className,
}: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const selected = options.find((option) => option.value === value);

  return (
    <div className={className}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger
          render={
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={open}
              className="w-full justify-between"
            >
              <span className="flex min-w-0 items-center">
                <span className="mr-2 flex shrink-0 items-center">
                  {selected?.icon ?? icon}
                </span>
                <span className="truncate">
                  {selected
                    ? (selected.triggerLabel ?? selected.label)
                    : placeholder}
                </span>
              </span>
              <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          }
        />
        <PopoverContent className={cn("p-0", popoverClassName)} align="start">
          <Command>
            <CommandInput placeholder={searchPlaceholder} className="h-9" />
            <CommandList>
              <CommandEmpty>{emptyText}</CommandEmpty>
              <CommandGroup>
                {options.map((option) => (
                  <CommandItem
                    key={option.value}
                    // cmdk identifies items by this string, so it carries the
                    // id to keep two options with the same label apart.
                    value={`${option.label} ${option.value}`}
                    keywords={option.keywords}
                    onSelect={() => {
                      onChange(option.value);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        option.value === value ? "opacity-100" : "opacity-0",
                      )}
                    />
                    {option.icon && (
                      <span className="mr-2 flex shrink-0 items-center">
                        {option.icon}
                      </span>
                    )}
                    {option.description ? (
                      <div className="flex flex-col">
                        <span className="font-medium">{option.label}</span>
                        <span className="text-xs text-muted-foreground">
                          {option.description}
                        </span>
                      </div>
                    ) : (
                      option.label
                    )}
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
