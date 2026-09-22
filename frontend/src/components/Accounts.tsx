import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CreditCard, Building2 } from "lucide-react";
import { toast } from "sonner";
import { apiClient, getApiErrorMessage } from "../lib/api";
import { accountLabel } from "../lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import QueryErrorAlert from "./QueryErrorAlert";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import AccountsSkeleton from "./AccountsSkeleton";
import AddBankAccountDrawer from "./AddBankAccountDrawer";
import AccountRow from "./accounts/AccountRow";
import BankConnectionRow from "./accounts/BankConnectionRow";
import ConfirmDialog from "./ConfirmDialog";
import { Checkbox } from "./ui/checkbox";
import type { Account, BankConnectionStatus } from "../types/api";
import { queryKeys } from "../lib/queryKeys";
import { useAccounts } from "../hooks/queries";

export default function Accounts() {
  const [deleteDialogAccount, setDeleteDialogAccount] =
    useState<Account | null>(null);
  const [deleteData, setDeleteData] = useState(true);
  const [deleteDialogConnection, setDeleteDialogConnection] =
    useState<BankConnectionStatus | null>(null);
  const [hideDeleted, setHideDeleted] = useState(false);

  const queryClient = useQueryClient();

  const {
    data: accounts,
    isLoading: accountsLoading,
    error: accountsError,
    refetch: refetchAccounts,
  } = useAccounts();

  const { data: bankConnections, isLoading: connectionsLoading } = useQuery({
    queryKey: queryKeys.bankConnections,
    queryFn: apiClient.getBankConnectionsStatus,
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
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts });
      queryClient.invalidateQueries({ queryKey: queryKeys.transactions });
      setDeleteDialogAccount(null);
      setDeleteData(true);
      toast.success("Account deleted successfully.");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to delete account."));
    },
  });

  const deleteBankConnectionMutation = useMutation({
    mutationFn: apiClient.deleteBankConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.accounts });
      queryClient.invalidateQueries({ queryKey: queryKeys.bankConnections });
      setDeleteDialogConnection(null);
      toast.success("Bank connection deleted.");
    },
    onError: (error) => {
      toast.error(
        getApiErrorMessage(error, "Failed to delete bank connection."),
      );
    },
  });

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
      <QueryErrorAlert
        title="Failed to load accounts"
        onRetry={() => refetchAccounts()}
      />
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
              {displayedAccounts.map((account) => (
                <AccountRow
                  key={account.id}
                  account={account}
                  onDelete={(target) => {
                    setDeleteDialogAccount(target);
                    setDeleteData(true);
                  }}
                />
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Delete Account Dialog */}
      <ConfirmDialog
        open={!!deleteDialogAccount}
        onClose={() => {
          setDeleteDialogAccount(null);
          setDeleteData(true);
        }}
        onConfirm={() => {
          if (deleteDialogAccount) {
            deleteAccountMutation.mutate({
              accountId: deleteDialogAccount.id,
              deleteData,
            });
          }
        }}
        isPending={deleteAccountMutation.isPending}
        title="Delete Account"
        description={
          <>
            Are you sure you want to delete{" "}
            <span className="font-medium text-foreground">
              {deleteDialogAccount
                ? accountLabel(deleteDialogAccount)
                : "this account"}
            </span>
            ? This action cannot be undone.
          </>
        }
        confirmLabel="Delete"
      >
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
      </ConfirmDialog>

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
              {bankConnections.map((connection) => (
                <BankConnectionRow
                  key={connection.session_id}
                  connection={connection}
                  onDelete={setDeleteDialogConnection}
                  deleteDisabled={deleteBankConnectionMutation.isPending}
                />
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Delete Bank Connection Dialog */}
      <ConfirmDialog
        open={!!deleteDialogConnection}
        onClose={() => setDeleteDialogConnection(null)}
        onConfirm={() => {
          if (deleteDialogConnection) {
            deleteBankConnectionMutation.mutate(
              deleteDialogConnection.session_id,
            );
          }
        }}
        isPending={deleteBankConnectionMutation.isPending}
        title={
          deleteDialogConnection?.status === "active"
            ? "Disconnect Bank"
            : "Delete Connection"
        }
        description={
          deleteDialogConnection?.status === "active" ? (
            <>
              Are you sure you want to disconnect{" "}
              <span className="font-medium text-foreground">
                {deleteDialogConnection?.aspsp_name}
              </span>
              ? This will stop syncing new transactions but keep your
              existing transaction history.
            </>
          ) : (
            <>
              Delete the connection to{" "}
              <span className="font-medium text-foreground">
                {deleteDialogConnection?.aspsp_name}
              </span>
              ?
            </>
          )
        }
        confirmLabel={
          deleteDialogConnection?.status === "active" ? "Disconnect" : "Delete"
        }
      />
    </div>
  );
}
