import { X, Copy, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "./ui/button";
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

  if (!isOpen) return null;

  const handleCopy = async () => {
    if (!rawTransaction) return;

    try {
      await navigator.clipboard.writeText(
        JSON.stringify(rawTransaction, null, 2),
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy to clipboard:", err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-card rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full border">
          <div className="bg-card px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-foreground">
                Raw Transaction Data
              </h3>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={handleCopy}
                  disabled={!rawTransaction}
                  variant="outline"
                  size="sm"
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
                <Button onClick={onClose} variant="ghost" size="sm">
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm text-muted-foreground">
                Transaction ID:{" "}
                <code className="bg-muted px-2 py-1 rounded text-xs text-foreground">
                  {transactionId}
                </code>
              </p>
            </div>

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
                  Try refreshing the page or check if the transaction was
                  fetched with summary_only=false.
                </p>
              </div>
            )}
          </div>

          <div className="bg-muted/50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <Button
              type="button"
              onClick={onClose}
              className="w-full sm:ml-3 sm:w-auto"
            >
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
