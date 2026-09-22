import { AlertTriangle, Building2, Trash2 } from "lucide-react";
import { formatDate } from "../../lib/utils";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip";
import type { BankConnectionStatus } from "../../types/api";

interface BankConnectionRowProps {
  connection: BankConnectionStatus;
  onDelete: (connection: BankConnectionStatus) => void;
  deleteDisabled: boolean;
}

/** One bank authorization: its status, time left and the button to end it. */
export default function BankConnectionRow({
  connection,
  onDelete,
  deleteDisabled,
}: BankConnectionRowProps) {
  const isExpiring =
    connection.status === "active" &&
    connection.days_until_expiry != null &&
    connection.days_until_expiry <= 7;
  const statusColor = isExpiring
    ? "bg-amber-500"
    : connection.status === "active"
      ? "bg-green-500"
      : connection.status === "expired"
        ? "bg-red-500"
        : "bg-muted-foreground";

  return (
    <div className="p-4 sm:p-6 hover:bg-accent transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 min-w-0 flex-1">
          <div className="shrink-0 w-10 h-10 rounded-full bg-muted flex items-center justify-center">
            <Building2 className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <h4 className="text-base font-medium text-foreground truncate">
                {connection.aspsp_name}
              </h4>
              {/* Colour echoes the status spelled out below, so it is
                  decorative to a screen reader. */}
              <div
                className={`w-3 h-3 rounded-full ${statusColor}`}
                aria-hidden="true"
              />
              {connection.status === "expired" && (
                <Badge
                  variant="outline"
                  className="shrink-0 text-xs border-red-500 text-negative"
                >
                  Expired
                </Badge>
              )}
              {connection.days_until_expiry != null && (
                <Badge
                  variant="outline"
                  className={`shrink-0 text-xs ${isExpiring ? "border-amber-500 text-amber-600 dark:text-amber-400" : "border-border text-muted-foreground"}`}
                >
                  {isExpiring && <AlertTriangle className="h-3 w-3 mr-1" />}
                  {connection.days_until_expiry} day
                  {connection.days_until_expiry !== 1 ? "s" : ""} left
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {connection.aspsp_country} • {connection.status} •{" "}
              {connection.accounts_count} account
              {connection.accounts_count !== 1 ? "s" : ""}
            </p>
            <p className="text-xs text-muted-foreground font-mono">
              ID: {connection.session_id}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <div className="text-right">
            <p className="text-xs text-muted-foreground">
              Created {formatDate(connection.created_at)}
            </p>
          </div>
          <Tooltip>
            <TooltipTrigger
              render={
                <Button
                  onClick={() => onDelete(connection)}
                  disabled={deleteDisabled}
                  size="icon"
                  variant="ghost"
                  aria-label="Delete connection"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              }
            />
            <TooltipContent>Delete connection</TooltipContent>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}
