import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import type { RawTransactionData } from "../types/api";

interface RawTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  rawTransaction: RawTransactionData | undefined;
  transactionId: string;
}

export default function RawTransactionModal({
  isOpen,
  onClose,
  rawTransaction,
  transactionId,
}: RawTransactionModalProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!rawTransaction) return;

    try {
      await navigator.clipboard.writeText(
        JSON.stringify(rawTransaction, null, 2),
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy to clipboard.");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Raw Transaction Data</DialogTitle>
          <DialogDescription>
            Transaction ID:{" "}
            <code className="bg-muted px-2 py-1 rounded text-xs text-foreground">
              {transactionId}
            </code>
          </DialogDescription>
        </DialogHeader>

        {rawTransaction ? (
          <div className="bg-muted rounded-lg p-4 overflow-auto max-h-96">
            <pre className="text-sm text-foreground whitespace-pre-wrap">
              {JSON.stringify(rawTransaction, null, 2)}
            </pre>
          </div>
        ) : (
          <div className="bg-muted rounded-lg p-8 text-center">
            <p className="text-foreground">
              Raw transaction data is not available for this transaction.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Try refreshing the page or check if the transaction was fetched
              with summary_only=false.
            </p>
          </div>
        )}

        <DialogFooter>
          <Button
            onClick={handleCopy}
            disabled={!rawTransaction}
            variant="outline"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4 mr-1 text-green-600 dark:text-green-400" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-4 w-4 mr-1" />
                Copy JSON
              </>
            )}
          </Button>
          <Button onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
