import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Check,
  Edit2,
  RefreshCw,
  Trash2,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { apiClient, getApiErrorMessage } from "../../lib/api";
import { invalidateSyncedData, queryKeys } from "../../lib/queryKeys";
import { accountLabel, cn, formatCurrency, formatDate } from "../../lib/utils";
import { Badge } from "../ui/badge";
import { BlurredValue } from "../ui/blurred-value";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip";
import type { Account } from "../../types/api";

const STATUS_INDICATORS: Record<string, { color: string; label: string }> = {
  ready: { color: "bg-green-500", label: "Ready" },
  pending: { color: "bg-amber-500", label: "Pending" },
  error: { color: "bg-destructive", label: "Error" },
  failed: { color: "bg-destructive", label: "Error" },
  inactive: { color: "bg-muted-foreground", label: "Inactive" },
  deleted: { color: "bg-muted-foreground/50", label: "Deleted" },
};

function statusIndicator(status: string) {
  return (
    STATUS_INDICATORS[status.toLowerCase()] ?? {
      color: "bg-primary",
      label: status,
    }
  );
}

/** An icon-only button with its tooltip; the tooltip text is also its name. */
function IconAction({
  label,
  onClick,
  disabled,
  className,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Button
            onClick={onClick}
            disabled={disabled}
            size="icon"
            variant="ghost"
            aria-label={label}
            className={cn("h-8 w-8 shrink-0", className)}
          >
            {children}
          </Button>
        }
      />
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}

interface AccountRowProps {
  account: Account;
  onDelete: (account: Account) => void;
}

/** One account: logo, name (editable in place), balance, status and actions. */
export default function AccountRow({ account, onDelete }: AccountRowProps) {
  const [editingName, setEditingName] = useState<string | null>(null);
  const [logoFailed, setLogoFailed] = useState(false);
  const queryClient = useQueryClient();

  const rename = useMutation({
    mutationFn: (display_name: string) =>
      apiClient.updateAccount(account.id, { display_name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts });
      setEditingName(null);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to update account name."));
    },
  });

  const sync = useMutation({
    mutationFn: () => apiClient.triggerSync({ account_ids: [account.id] }),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(
          `Account synced: ${result.transactions_added} new transactions.`,
        );
      } else {
        toast.error(
          `Sync finished with errors: ${result.errors.join(", ") || "Unknown error"}`,
        );
      }
      invalidateSyncedData(queryClient);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to sync account."));
    },
  });

  const saveName = () => {
    if (editingName?.trim()) rename.mutate(editingName.trim());
  };

  const accountBalance = account.balances?.[0];
  const balance = accountBalance?.amount ?? 0;
  const currency = accountBalance?.currency || account.currency || "EUR";
  const isPositive = balance >= 0;
  const isDeleted = account.status.toLowerCase() === "deleted";
  const status = statusIndicator(account.status);

  return (
    <div
      className={`p-4 sm:p-6 hover:bg-accent transition-colors ${isDeleted ? "opacity-60" : ""}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div className="flex items-start sm:items-center space-x-3 sm:space-x-4 min-w-0 flex-1">
          <div className="shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-full overflow-hidden bg-muted flex items-center justify-center">
            {account.logo && !logoFailed ? (
              <img
                src={account.logo}
                alt={`${account.institution_id} logo`}
                className="w-6 h-6 sm:w-8 sm:h-8 object-contain"
                onError={() => setLogoFailed(true)}
              />
            ) : (
              <Building2 className="h-5 w-5 sm:h-6 sm:w-6 text-muted-foreground" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            {editingName !== null ? (
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Input
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    className="flex-1 text-base sm:text-lg font-medium"
                    placeholder="Custom account name"
                    aria-label="Account name"
                    name="account-name"
                    autoComplete="off"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") saveName();
                      if (e.key === "Escape") setEditingName(null);
                    }}
                    autoFocus
                  />
                  <IconAction
                    label="Save changes"
                    onClick={saveName}
                    disabled={!editingName.trim() || rename.isPending}
                    className="text-positive hover:text-positive"
                  >
                    <Check className="h-4 w-4" />
                  </IconAction>
                  <IconAction
                    label="Cancel editing"
                    onClick={() => setEditingName(null)}
                  >
                    <X className="h-4 w-4" />
                  </IconAction>
                </div>
                <p className="text-sm text-muted-foreground truncate">
                  {account.institution_id}
                </p>
              </div>
            ) : (
              <div>
                <div className="flex items-center space-x-2 min-w-0">
                  <h4 className="text-base sm:text-lg font-medium text-foreground truncate">
                    {accountLabel(account)}
                  </h4>
                  {isDeleted && (
                    <Badge variant="secondary" className="shrink-0 text-xs">
                      Deleted
                    </Badge>
                  )}
                  <div className="ml-auto flex items-center shrink-0">
                    {!isDeleted && (
                      <IconAction
                        label="Sync this account"
                        onClick={() => sync.mutate()}
                        disabled={sync.isPending}
                      >
                        <RefreshCw
                          className={cn(
                            "h-4 w-4",
                            sync.isPending && "animate-spin",
                          )}
                        />
                      </IconAction>
                    )}
                    <IconAction
                      label="Edit account name"
                      onClick={() =>
                        setEditingName(account.display_name || account.name || "")
                      }
                    >
                      <Edit2 className="h-4 w-4" />
                    </IconAction>
                    {!isDeleted && (
                      <IconAction
                        label="Delete account"
                        onClick={() => onDelete(account)}
                        className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </IconAction>
                    )}
                  </div>
                </div>
                <p className="text-sm text-muted-foreground truncate">
                  {account.institution_id}
                </p>
                {account.iban && (
                  <p className="text-xs text-muted-foreground mt-1 font-mono break-all sm:break-normal">
                    IBAN: {account.iban}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between sm:flex-col sm:items-end sm:text-right shrink-0">
          <div className="flex items-center space-x-2 order-1 sm:order-2">
            <Tooltip>
              <TooltipTrigger
                render={
                  <div
                    className={`w-3 h-3 rounded-full ${status.color} cursor-help`}
                    role="img"
                    aria-label={`Account status: ${status.label}`}
                  />
                }
              />
              <TooltipContent>{status.label}</TooltipContent>
            </Tooltip>
            <p className="text-xs sm:text-sm text-muted-foreground whitespace-nowrap">
              Updated {formatDate(account.last_accessed || account.created)}
            </p>
          </div>

          <div className="flex items-center space-x-2 order-2 sm:order-1">
            {isPositive ? (
              <TrendingUp className="h-4 w-4 text-positive" />
            ) : (
              <TrendingDown className="h-4 w-4 text-negative" />
            )}
            <BlurredValue
              className={`text-base sm:text-lg font-semibold ${
                isPositive ? "text-positive" : "text-negative"
              }`}
            >
              {formatCurrency(balance, currency)}
            </BlurredValue>
          </div>
        </div>
      </div>
    </div>
  );
}
