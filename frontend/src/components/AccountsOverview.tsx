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
} from "lucide-react";
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
import LoadingSpinner from "./LoadingSpinner";
import type { Account, Balance } from "../types/api";

// Helper function to get status indicator color and styles
const getStatusIndicator = (status: string) => {
  const statusLower = status.toLowerCase();

  switch (statusLower) {
    case "ready":
      return {
        color: "bg-green-500",
        tooltip: "Ready",
      };
    case "pending":
      return {
        color: "bg-yellow-500",
        tooltip: "Pending",
      };
    case "error":
    case "failed":
      return {
        color: "bg-red-500",
        tooltip: "Error",
      };
    case "inactive":
      return {
        color: "bg-gray-500",
        tooltip: "Inactive",
      };
    default:
      return {
        color: "bg-blue-500",
        tooltip: status,
      };
  }
};

export default function AccountsOverview() {
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

  const [editingAccountId, setEditingAccountId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");

  const queryClient = useQueryClient();

  const updateAccountMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      apiClient.updateAccount(id, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setEditingAccountId(null);
      setEditingName("");
    },
    onError: (error) => {
      console.error("Failed to update account:", error);
    },
  });

  const handleEditStart = (account: Account) => {
    setEditingAccountId(account.id);
    setEditingName(account.name || "");
  };

  const handleEditSave = () => {
    if (editingAccountId && editingName.trim()) {
      updateAccountMutation.mutate({
        id: editingAccountId,
        name: editingName.trim(),
      });
    }
  };

  const handleEditCancel = () => {
    setEditingAccountId(null);
    setEditingName("");
  };

  if (accountsLoading) {
    return (
      <Card>
        <LoadingSpinner message="Loading accounts..." />
      </Card>
    );
  }

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
          <Button onClick={() => refetchAccounts()} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  const totalBalance =
    accounts?.reduce((sum, account) => {
      // Get the first available balance from the balances array
      const primaryBalance = account.balances?.[0]?.amount || 0;
      return sum + primaryBalance;
    }, 0) || 0;
  const totalAccounts = accounts?.length || 0;
  const uniqueBanks = new Set(accounts?.map((acc) => acc.institution_id) || [])
    .size;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Total Balance
                </p>
                <p className="text-2xl font-bold text-foreground">
                  {formatCurrency(totalBalance)}
                </p>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/20 rounded-full">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Total Accounts
                </p>
                <p className="text-2xl font-bold text-foreground">
                  {totalAccounts}
                </p>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-full">
                <CreditCard className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Connected Banks
                </p>
                <p className="text-2xl font-bold text-foreground">
                  {uniqueBanks}
                </p>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-full">
                <Building2 className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Accounts List */}
      <Card>
        <CardHeader>
          <CardTitle>Bank Accounts</CardTitle>
          <CardDescription>Manage your connected bank accounts</CardDescription>
        </CardHeader>

        {!accounts || accounts.length === 0 ? (
          <CardContent className="p-6 text-center">
            <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No accounts found
            </h3>
            <p className="text-muted-foreground">
              Connect your first bank account to get started with Leggen.
            </p>
          </CardContent>
        ) : (
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {accounts.map((account) => {
                // Get balance from account's balances array or fallback to balances query
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

                return (
                  <div
                    key={account.id}
                    className="p-4 sm:p-6 hover:bg-accent transition-colors"
                  >
                    {/* Mobile layout - stack vertically */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
                      <div className="flex items-start sm:items-center space-x-3 sm:space-x-4 min-w-0 flex-1">
                        <div className="flex-shrink-0 p-2 sm:p-3 bg-muted rounded-full">
                          <Building2 className="h-5 w-5 sm:h-6 sm:w-6 text-muted-foreground" />
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
                                  placeholder="Account name"
                                  name="search"
                                  autoComplete="off"
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") handleEditSave();
                                    if (e.key === "Escape") handleEditCancel();
                                  }}
                                  autoFocus
                                />
                                <button
                                  onClick={handleEditSave}
                                  disabled={
                                    !editingName.trim() ||
                                    updateAccountMutation.isPending
                                  }
                                  className="p-1 text-green-600 hover:text-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                  title="Save changes"
                                >
                                  <Check className="h-4 w-4" />
                                </button>
                                <button
                                  onClick={handleEditCancel}
                                  className="p-1 text-gray-600 hover:text-gray-700"
                                  title="Cancel editing"
                                >
                                  <X className="h-4 w-4" />
                                </button>
                              </div>
                              <p className="text-sm text-muted-foreground truncate">
                                {account.institution_id}
                              </p>
                            </div>
                          ) : (
                            <div>
                              <div className="flex items-center space-x-2 min-w-0">
                                <h4 className="text-base sm:text-lg font-medium text-foreground truncate">
                                  {account.name || "Unnamed Account"}
                                </h4>
                                <button
                                  onClick={() => handleEditStart(account)}
                                  className="flex-shrink-0 p-1 text-muted-foreground hover:text-foreground transition-colors"
                                  title="Edit account name"
                                >
                                  <Edit2 className="h-4 w-4" />
                                </button>
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

                      {/* Balance and date section */}
                      <div className="flex items-center justify-between sm:flex-col sm:items-end sm:text-right flex-shrink-0">
                        {/* Mobile: date/status on left, balance on right */}
                        {/* Desktop: balance on top, date/status on bottom */}

                        {/* Date and status indicator - left on mobile, bottom on desktop */}
                        <div className="flex items-center space-x-2 order-1 sm:order-2">
                          <div
                            className={`w-3 h-3 rounded-full ${getStatusIndicator(account.status).color} relative group cursor-help`}
                            role="img"
                            aria-label={`Account status: ${getStatusIndicator(account.status).tooltip}`}
                          >
                            {/* Tooltip */}
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap z-10">
                              {getStatusIndicator(account.status).tooltip}
                              <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-2 border-transparent border-t-gray-900"></div>
                            </div>
                          </div>
                          <p className="text-xs sm:text-sm text-muted-foreground whitespace-nowrap">
                            Updated{" "}
                            {formatDate(
                              account.last_accessed || account.created,
                            )}
                          </p>
                        </div>

                        {/* Balance - right on mobile, top on desktop */}
                        <div className="flex items-center space-x-2 order-2 sm:order-1">
                          {isPositive ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                          <p
                            className={`text-base sm:text-lg font-semibold ${
                              isPositive ? "text-green-600" : "text-red-600"
                            }`}
                          >
                            {formatCurrency(balance, currency)}
                          </p>
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
    </div>
  );
}
