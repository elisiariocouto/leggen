import { useState } from "react";
import { Check, ChevronDown, Building2 } from "lucide-react";

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
import type { Account } from "../../types/api";

export interface AccountComboboxProps {
  accounts?: Account[];
  selectedAccount: string;
  onAccountChange: (accountId: string) => void;
  className?: string;
}

export function AccountCombobox({
  accounts = [],
  selectedAccount,
  onAccountChange,
  className,
}: AccountComboboxProps) {
  const [open, setOpen] = useState(false);

  const selectedAccountData = accounts.find(
    (account) => account.id === selectedAccount,
  );

  const formatAccountName = (account: Account) => {
    const displayName = account.display_name || account.name || "Unnamed Account";
    return `${displayName} (${account.institution_id})`;
  };

  return (
    <div className={className}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="justify-between"
          >
            <div className="flex items-center">
              <Building2 className="mr-2 h-4 w-4" />
              {selectedAccountData
                ? formatAccountName(selectedAccountData)
                : "All accounts"}
            </div>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[300px] p-0">
          <Command>
            <CommandInput placeholder="Search accounts..." className="h-9" />
            <CommandList>
              <CommandEmpty>No accounts found.</CommandEmpty>
              <CommandGroup>
                {/* All accounts option */}
                <CommandItem
                  value="all-accounts"
                  onSelect={() => {
                    onAccountChange("");
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      selectedAccount === "" ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <Building2 className="mr-2 h-4 w-4 text-gray-400" />
                  All accounts
                </CommandItem>

                {/* Individual accounts */}
                {accounts.map((account) => (
                  <CommandItem
                    key={account.id}
                    value={`${account.display_name || account.name} ${account.institution_id}`}
                    onSelect={() => {
                      onAccountChange(account.id);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        selectedAccount === account.id
                          ? "opacity-100"
                          : "opacity-0",
                      )}
                    />
                    <div className="flex flex-col">
                      <span className="font-medium">
                        {account.display_name || account.name || "Unnamed Account"}
                      </span>
                      <span className="text-xs text-gray-500">
                        {account.institution_id}
                        {account.iban && ` • ${account.iban.slice(-4)}`}
                      </span>
                    </div>
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
