import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CreditCard,
  TrendingUp,
  TrendingDown,
  Building2,
  RefreshCw,
  AlertCircle,
  Edit2,
  Check,
  X,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "../lib/api";
import { formatCurrency, formatDate } from "../lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Badge } from "./ui/badge";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { BlurredValue } from "./ui/blurred-value";
import AccountsSkeleton from "./AccountsSkeleton";
import AddBankAccountDrawer from "./AddBankAccountDrawer";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "./ui/tooltip";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";
import { Checkbox } from "./ui/checkbox";
import type { Account, Balance } from "../types/api";

const getStatusIndicator = (status: string) => {
  const statusLower = status.toLowerCase();

  switch (statusLower) {
    case "ready":
      return { color: "bg-green-500", tooltip: "Ready" };
    case "pending":
      return { color: "bg-amber-500", tooltip: "Pending" };
    case "error":
    case "failed":
      return { color: "bg-destructive", tooltip: "Error" };
    case "inactive":
      return { color: "bg-muted-foreground", tooltip: "Inactive" };
    case "deleted":
      return { color: "bg-muted-foreground/50", tooltip: "Deleted" };
    default:
      return { color: "bg-primary", tooltip: status };
  }
};

export default function Accounts() {
  const [editingAccountId, setEditingAccountId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [failedImages, setFailedImages] = useState<Set<string>>(new Set());
  const [deleteDialogAccount, setDeleteDialogAccount] =
    useState<Account | null>(null);
  const [deleteData, setDeleteData] = useState(true);
  const [hideDeleted, setHideDeleted] = useState(false);

  const queryClient = useQueryClient();

  const {
    data: accounts,
    isLoading: accountsLoading,
    error: accountsError,
    refetch: refetchAccounts,
  } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: apiClient.getAccounts,
  });

  const { data: balances } = useQuery<Balance[]>({
    queryKey: ["balances"],
    queryFn: () => apiClient.getBalances(),
  });

  const { data: bankConnections, isLoading: connectionsLoading } = useQuery({
    queryKey: ["bankConnections"],
    queryFn: apiClient.getBankConnectionsStatus,
  });

  const updateAccountMutation = useMutation({
    mutationFn: ({ id, display_name }: { id: string; display_name: string }) =>
      apiClient.updateAccount(id, { display_name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["balances"] });
      setEditingAccountId(null);
      setEditingName("");
    },
    onError: () => {
      toast.error("Failed to update account name.");
    },
  });

  const deleteAccountMutation = useMutation({
    mutationFn: ({
      accountId,
      deleteData,
    }: {
      accountId: string;
      deleteData: boolean;
    }) => apiClient.deleteAccount(accountId, deleteData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["balances"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      setDeleteDialogAccount(null);
      setDeleteData(true);
      toast.success("Account deleted successfully.");
    },
    onError: () => {
      toast.error("Failed to delete account.");
    },
  });

  const deleteBankConnectionMutation = useMutation({
    mutationFn: apiClient.deleteBankConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["bankConnections"] });
      queryClient.invalidateQueries({ queryKey: ["balances"] });
    },
    onError: () => {
      toast.error("Failed to delete bank connection.");
    },
  });

  const handleEditStart = (account: Account) => {
    setEditingAccountId(account.id);
    setEditingName(account.display_name || account.name || "");
  };

  const handleEditSave = () => {
    if (editingAccountId && editingName.trim()) {
      updateAccountMutation.mutate({
        id: editingAccountId,
        display_name: editingName.trim(),
      });
    }
  };

  const handleEditCancel = () => {
    setEditingAccountId(null);
    setEditingName("");
  };

  const isLoading = accountsLoading || connectionsLoading;

  if (isLoading) {
    return <AccountsSkeleton />;
  }

  const hasDeletedAccounts = accounts?.some(
    (a) => a.status.toLowerCase() === "deleted",
  );
  const displayedAccounts = (
    hideDeleted
      ? accounts?.filter((a) => a.status.toLowerCase() !== "deleted")
      : accounts
  )
    ?.slice()
    .sort((a, b) => {
      const aDeleted = a.status.toLowerCase() === "deleted" ? 1 : 0;
      const bDeleted = b.status.toLowerCase() === "deleted" ? 1 : 0;
      return aDeleted - bDeleted;
    });

  if (accountsError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Failed to load accounts</AlertTitle>
        <AlertDescription className="space-y-3">
          <p>
            Unable to connect to the Leggen API. Please check your configuration
            and ensure the API server is running.
          </p>
          <Button
            onClick={() => refetchAccounts()}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Account Management Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Account Management</CardTitle>
              <CardDescription>
                Manage your connected bank accounts and customize their display
                names
              </CardDescription>
            </div>
            {hasDeletedAccounts && (
              <div className="flex items-center space-x-2">
                <Switch
                  id="hide-deleted"
                  checked={hideDeleted}
                  onCheckedChange={setHideDeleted}
                />
                <Label
                  htmlFor="hide-deleted"
                  className="text-sm text-muted-foreground whitespace-nowrap"
                >
                  Hide deleted
                </Label>
              </div>
            )}
          </div>
        </CardHeader>

        {!displayedAccounts || displayedAccounts.length === 0 ? (
          <CardContent className="p-6 text-center">
            <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No accounts found
            </h3>
            <p className="text-muted-foreground mb-4">
              Connect your first bank account to get started with Leggen.
            </p>
          </CardContent>
        ) : (
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {displayedAccounts.map((account) => {
                const accountBalance = account.balances?.[0];
                const fallbackBalance = balances?.find(
                  (b) => b.account_id === account.id,
                );
                const balance =
                  accountBalance?.amount ||
                  fallbackBalance?.balance_amount ||
                  0;
                const currency =
                  accountBalance?.currency ||
                  fallbackBalance?.currency ||
                  account.currency ||
                  "EUR";
                const isPositive = balance >= 0;
                const isDeleted =
                  account.status.toLowerCase() === "deleted";

                return (
                  <div
                    key={account.id}
                    className={`p-4 sm:p-6 hover:bg-accent transition-colors ${isDeleted ? "opacity-60" : ""}`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
                      <div className="flex items-start sm:items-center space-x-3 sm:space-x-4 min-w-0 flex-1">
                        <div className="flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-full overflow-hidden bg-muted flex items-center justify-center">
                          {account.logo && !failedImages.has(account.id) ? (
                            <img
                              src={account.logo}
                              alt={`${account.institution_id} logo`}
                              className="w-6 h-6 sm:w-8 sm:h-8 object-contain"
                              onError={() => {
                                setFailedImages(
                                  (prev) => new Set([...prev, account.id]),
                                );
                              }}
                            />
                          ) : (
                            <Building2 className="h-5 w-5 sm:h-6 sm:w-6 text-muted-foreground" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          {editingAccountId === account.id ? (
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <input
                                  type="text"
                                  value={editingName}
                                  onChange={(e) =>
                                    setEditingName(e.target.value)
                                  }
                                  className="flex-1 px-3 py-1 text-base sm:text-lg font-medium border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
                                  placeholder="Custom account name"
                                  name="account-name"
                                  autoComplete="off"
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") handleEditSave();
                                    if (e.key === "Escape")
                                      handleEditCancel();
                                  }}
                                  autoFocus
                                />
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      onClick={handleEditSave}
                                      disabled={
                                        !editingName.trim() ||
                                        updateAccountMutation.isPending
                                      }
                                      size="icon"
                                      variant="ghost"
                                      className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-100"
                                    >
                                      <Check className="h-4 w-4" />
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Save changes</TooltipContent>
                                </Tooltip>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      onClick={handleEditCancel}
                                      size="icon"
                                      variant="ghost"
                                      className="h-8 w-8"
                                    >
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Cancel editing</TooltipContent>
                                </Tooltip>
                              </div>
                              <p className="text-sm text-muted-foreground truncate">
                                {account.institution_id}
                              </p>
                            </div>
                          ) : (
                            <div>
                              <div className="flex items-center space-x-2 min-w-0">
                                <h4 className="text-base sm:text-lg font-medium text-foreground truncate">
                                  {account.display_name ||
                                    account.name ||
                                    "Unnamed Account"}
                                </h4>
                                {isDeleted && (
                                  <Badge
                                    variant="secondary"
                                    className="flex-shrink-0 text-xs"
                                  >
                                    Deleted
                                  </Badge>
                                )}
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      onClick={() => handleEditStart(account)}
                                      size="icon"
                                      variant="ghost"
                                      className="h-8 w-8 flex-shrink-0"
                                    >
                                      <Edit2 className="h-4 w-4" />
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Edit account name</TooltipContent>
                                </Tooltip>
                                {!isDeleted && (
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        onClick={() => {
                                          setDeleteDialogAccount(account);
                                          setDeleteData(true);
                                        }}
                                        disabled={
                                          deleteAccountMutation.isPending
                                        }
                                        size="icon"
                                        variant="ghost"
                                        className="h-8 w-8 flex-shrink-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                      >
                                        <Trash2 className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      Delete account
                                    </TooltipContent>
                                  </Tooltip>
                                )}
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

                      <div className="flex items-center justify-between sm:flex-col sm:items-end sm:text-right flex-shrink-0">
                        <div className="flex items-center space-x-2 order-1 sm:order-2">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <div
                                className={`w-3 h-3 rounded-full ${getStatusIndicator(account.status).color} cursor-help`}
                                role="img"
                                aria-label={`Account status: ${getStatusIndicator(account.status).tooltip}`}
                              />
                            </TooltipTrigger>
                            <TooltipContent>
                              {getStatusIndicator(account.status).tooltip}
                            </TooltipContent>
                          </Tooltip>
                          <p className="text-xs sm:text-sm text-muted-foreground whitespace-nowrap">
                            Updated{" "}
                            {formatDate(
                              account.last_accessed || account.created,
                            )}
                          </p>
                        </div>

                        <div className="flex items-center space-x-2 order-2 sm:order-1">
                          {isPositive ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                          <BlurredValue
                            className={`text-base sm:text-lg font-semibold ${
                              isPositive ? "text-green-600" : "text-red-600"
                            }`}
                          >
                            {formatCurrency(balance, currency)}
                          </BlurredValue>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Delete Account Dialog */}
      <AlertDialog
        open={!!deleteDialogAccount}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteDialogAccount(null);
            setDeleteData(true);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Account</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete{" "}
              <span className="font-medium text-foreground">
                {deleteDialogAccount?.display_name ||
                  deleteDialogAccount?.name ||
                  "this account"}
              </span>
              ? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex items-center space-x-2 py-2">
            <Checkbox
              id="delete-data"
              checked={deleteData}
              onCheckedChange={(checked) => setDeleteData(checked === true)}
            />
            <label
              htmlFor="delete-data"
              className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Also delete all transactions and balance history
            </label>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteDialogAccount) {
                  deleteAccountMutation.mutate({
                    accountId: deleteDialogAccount.id,
                    deleteData,
                  });
                }
              }}
              disabled={deleteAccountMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Bank Connections Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Bank Connections</CardTitle>
              <CardDescription>
                Status of all bank connection requests and their authorization
                state
              </CardDescription>
            </div>
            <AddBankAccountDrawer />
          </div>
        </CardHeader>

        {!bankConnections || bankConnections.length === 0 ? (
          <CardContent className="p-6 text-center">
            <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No bank connections found
            </h3>
            <p className="text-muted-foreground">
              Bank connection requests will appear here after you connect
              accounts.
            </p>
          </CardContent>
        ) : (
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {bankConnections.map((connection) => {
                const statusColor =
                  connection.status === "active"
                    ? "bg-green-500"
                    : connection.status === "expired"
                      ? "bg-red-500"
                      : "bg-muted-foreground";

                return (
                  <div
                    key={connection.session_id}
                    className="p-4 sm:p-6 hover:bg-accent transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 min-w-0 flex-1">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                          <Building2 className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <h4 className="text-base font-medium text-foreground truncate">
                              {connection.aspsp_name}
                            </h4>
                            <div
                              className={`w-3 h-3 rounded-full ${statusColor}`}
                              title={connection.status}
                            />
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {connection.aspsp_country} •{" "}
                            {connection.status} •{" "}
                            {connection.accounts_count} account
                            {connection.accounts_count !== 1 ? "s" : ""}
                          </p>
                          <p className="text-xs text-muted-foreground font-mono">
                            ID: {connection.session_id}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 flex-shrink-0">
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">
                            Created {formatDate(connection.created_at)}
                          </p>
                        </div>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              onClick={() => {
                                const isActive = connection.status === "active";
                                const message = isActive
                                  ? `Are you sure you want to disconnect "${connection.aspsp_name}"? This will stop syncing new transactions but keep your existing transaction history.`
                                  : `Delete connection to ${connection.aspsp_name}?`;

                                if (confirm(message)) {
                                  deleteBankConnectionMutation.mutate(
                                    connection.session_id,
                                  );
                                }
                              }}
                              disabled={deleteBankConnectionMutation.isPending}
                              size="icon"
                              variant="ghost"
                              className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Delete connection</TooltipContent>
                        </Tooltip>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
