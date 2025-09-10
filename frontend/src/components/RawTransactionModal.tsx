import { X, Copy, Check } from "lucide-react";
import { useState } from "react";
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
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Raw Transaction Data
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleCopy}
                  disabled={!rawTransaction}
                  className="inline-flex items-center px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 mr-1 text-green-600" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-1" />
                      Copy JSON
                    </>
                  )}
                </button>
                <button
                  onClick={onClose}
                  className="inline-flex items-center p-1 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Transaction ID:{" "}
                <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                  {transactionId}
                </code>
              </p>
            </div>

            {rawTransaction ? (
              <div className="bg-gray-50 rounded-lg p-4 overflow-auto max-h-96">
                <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                  {JSON.stringify(rawTransaction, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg p-8 text-center">
                <p className="text-gray-600">
                  Raw transaction data is not available for this transaction.
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Try refreshing the page or check if the transaction was
                  fetched with summary_only=false.
                </p>
              </div>
            )}
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={onClose}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
