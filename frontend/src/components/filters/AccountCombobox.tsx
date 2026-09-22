import { Building2 } from "lucide-react";

import { accountLabel } from "@/lib/utils";
import Combobox from "@/components/Combobox";
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
  const options = [
    {
      value: "",
      label: "All accounts",
      icon: <Building2 className="h-4 w-4 text-muted-foreground" />,
    },
    ...accounts.map((account) => ({
      value: account.id,
      label: accountLabel(account),
      triggerLabel: `${accountLabel(account)} (${account.institution_id})`,
      keywords: [account.institution_id],
      description: (
        <>
          {account.institution_id}
          {account.iban && ` • ${account.iban.slice(-4)}`}
        </>
      ),
    })),
  ];

  return (
    <Combobox
      className={className}
      options={options}
      value={selectedAccount}
      onChange={onAccountChange}
      placeholder="All accounts"
      icon={<Building2 className="h-4 w-4" />}
      searchPlaceholder="Search accounts..."
      emptyText="No accounts found."
      popoverClassName="w-[300px]"
    />
  );
}
