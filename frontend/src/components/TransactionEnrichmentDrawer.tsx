import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X, Save, Trash2 } from "lucide-react";
import { apiClient } from "../lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "./ui/drawer";
import type { Transaction, TransactionEnrichmentUpdate } from "../types/api";
import { toast } from "sonner";

interface TransactionEnrichmentDrawerProps {
  transaction: Transaction | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function TransactionEnrichmentDrawer({
  transaction,
  isOpen,
  onClose,
}: TransactionEnrichmentDrawerProps) {
  const queryClient = useQueryClient();

  const [cleanName, setCleanName] = useState("");
  const [category, setCategory] = useState("");
  const [logoUrl, setLogoUrl] = useState("");

  // Reset form when transaction changes or drawer opens
  useEffect(() => {
    if (transaction) {
      setCleanName(transaction.enrichment?.clean_name || "");
      setCategory(transaction.enrichment?.category || "");
      setLogoUrl(transaction.enrichment?.logo_url || "");
    } else {
      setCleanName("");
      setCategory("");
      setLogoUrl("");
    }
  }, [transaction, isOpen]);

  const updateMutation = useMutation({
    mutationFn: async (enrichment: TransactionEnrichmentUpdate) => {
      if (!transaction) throw new Error("No transaction selected");
      await apiClient.updateTransactionEnrichment(
        transaction.account_id,
        transaction.transaction_id,
        enrichment,
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      toast.success("Transaction enrichment updated successfully");
      onClose();
    },
    onError: (error: Error) => {
      toast.error(`Failed to update enrichment: ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!transaction) throw new Error("No transaction selected");
      await apiClient.deleteTransactionEnrichment(
        transaction.account_id,
        transaction.transaction_id,
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      toast.success("Transaction enrichment deleted successfully");
      onClose();
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete enrichment: ${error.message}`);
    },
  });

  const handleSave = () => {
    const enrichment: TransactionEnrichmentUpdate = {
      clean_name: cleanName || undefined,
      category: category || undefined,
      logo_url: logoUrl || undefined,
    };

    // Check if at least one field is filled
    if (!cleanName && !category && !logoUrl) {
      toast.error("Please fill at least one field");
      return;
    }

    updateMutation.mutate(enrichment);
  };

  const handleDelete = () => {
    if (
      window.confirm(
        "Are you sure you want to delete this transaction enrichment?",
      )
    ) {
      deleteMutation.mutate();
    }
  };

  const hasEnrichment = transaction?.enrichment;

  return (
    <Drawer open={isOpen} onOpenChange={onClose}>
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>Enrich Transaction</DrawerTitle>
          <DrawerDescription>
            Add custom information to improve transaction display
          </DrawerDescription>
        </DrawerHeader>

        <div className="px-4 py-4 space-y-4">
          {/* Original transaction info */}
          {transaction && (
            <div className="bg-muted p-3 rounded-md">
              <p className="text-sm text-muted-foreground mb-1">
                Original Description:
              </p>
              <p className="font-medium">{transaction.description}</p>
            </div>
          )}

          {/* Clean Name */}
          <div className="space-y-2">
            <Label htmlFor="cleanName">Clean Name</Label>
            <Input
              id="cleanName"
              type="text"
              value={cleanName}
              onChange={(e) => setCleanName(e.target.value)}
              placeholder="e.g., Starbucks, Amazon, Uber"
            />
            <p className="text-xs text-muted-foreground">
              A cleaner, more readable name for this merchant or counterparty
            </p>
          </div>

          {/* Category */}
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Input
              id="category"
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g., groceries, utilities, entertainment"
            />
            <p className="text-xs text-muted-foreground">
              Categorize this transaction for better organization
            </p>
          </div>

          {/* Logo URL */}
          <div className="space-y-2">
            <Label htmlFor="logoUrl">Logo URL</Label>
            <Input
              id="logoUrl"
              type="text"
              value={logoUrl}
              onChange={(e) => setLogoUrl(e.target.value)}
              placeholder="https://example.com/logo.png"
            />
            <p className="text-xs text-muted-foreground">
              URL to the merchant's logo (for future use)
            </p>
          </div>
        </div>

        <DrawerFooter className="flex flex-row justify-between gap-2">
          <div className="flex gap-2 flex-1">
            <Button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="flex-1"
            >
              <Save className="h-4 w-4 mr-2" />
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
            <Button
              onClick={onClose}
              variant="outline"
              disabled={updateMutation.isPending || deleteMutation.isPending}
              className="flex-1"
            >
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          </div>
          {hasEnrichment && (
            <Button
              onClick={handleDelete}
              variant="destructive"
              disabled={deleteMutation.isPending}
              className="flex-shrink-0"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          )}
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
}
