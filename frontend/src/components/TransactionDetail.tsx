import { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { useIsMobile } from "../hooks/use-mobile";
import { formatCurrency, formatDate } from "../lib/utils";
import { extractRawFields } from "../lib/raw-transaction";
import CategoryBadge from "./CategoryBadge";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { BlurredValue } from "./ui/blurred-value";
import { Separator } from "./ui/separator";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
} from "./ui/drawer";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "./ui/sheet";
import type { Account, Transaction } from "../types/api";

interface TransactionDetailProps {
  transaction: Transaction | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accounts?: Account[];
}

function StatusBadge({ status }: { status: string }) {
  if (status === "pending") {
    return (
      <Badge
        variant="outline"
        className="border-amber-500/50 text-amber-600 dark:text-amber-400"
      >
        Pending
      </Badge>
    );
  }
  if (status === "booked") {
    return <Badge variant="secondary">Booked</Badge>;
  }
  return (
    <Badge variant="secondary">
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}

function DetailRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value?: string;
  mono?: boolean;
}) {
  if (!value) return null;
  return (
    <div className="flex items-start justify-between gap-4 py-1.5">
      <dt className="text-sm text-muted-foreground shrink-0">{label}</dt>
      <dd
        className={`text-right break-all text-foreground ${
          mono ? "font-mono text-xs pt-0.5" : "text-sm"
        }`}
      >
        {value}
      </dd>
    </div>
  );
}

function RawJsonSection({ transaction }: { transaction: Transaction }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!transaction.raw_transaction) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(
        JSON.stringify(transaction.raw_transaction, null, 2),
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy to clipboard.");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 text-muted-foreground"
          onClick={() => setExpanded((prev) => !prev)}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4 mr-1" />
          ) : (
            <ChevronRight className="h-4 w-4 mr-1" />
          )}
          Raw data
        </Button>
        {expanded && (
          <Button variant="ghost" size="sm" onClick={handleCopy}>
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
        )}
      </div>
      {expanded && (
        <div className="bg-muted rounded-lg p-4 overflow-auto max-h-96 mt-2">
          <pre className="text-xs text-foreground whitespace-pre-wrap">
            {JSON.stringify(transaction.raw_transaction, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function TransactionDetailContent({
  transaction,
  account,
}: {
  transaction: Transaction;
  account?: Account;
}) {
  const raw = extractRawFields(transaction.raw_transaction);
  const isPositive = transaction.transaction_value > 0;
  const iban = transaction.iban && transaction.iban !== "N/A" ? transaction.iban : undefined;
  const showEntryReference =
    raw.entryReference && raw.entryReference !== transaction.internal_transaction_id;

  return (
    <div className="space-y-4">
      {/* Header: description, amount, status */}
      <div className="flex items-start space-x-3">
        <div
          className={`p-2 rounded-full shrink-0 ${
            isPositive
              ? "bg-green-100 dark:bg-green-900/20"
              : "bg-red-100 dark:bg-red-900/20"
          }`}
        >
          {isPositive ? (
            <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-foreground break-words">
            {transaction.description}
          </h3>
          <p
            className={`text-2xl font-semibold mt-1 ${
              isPositive
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            <BlurredValue>
              {isPositive ? "+" : ""}
              {formatCurrency(
                transaction.transaction_value,
                transaction.transaction_currency,
              )}
            </BlurredValue>
          </p>
          <div className="flex items-center gap-2 mt-2">
            <StatusBadge status={transaction.transaction_status} />
            <span className="text-sm text-muted-foreground">
              {transaction.transaction_date
                ? formatDate(transaction.transaction_date)
                : "No date"}
            </span>
          </div>
        </div>
      </div>

      <Separator />

      {/* Details */}
      <dl>
        <DetailRow
          label="Booking date"
          value={raw.bookingDate ? formatDate(raw.bookingDate) : undefined}
        />
        <DetailRow
          label="Value date"
          value={raw.valueDate ? formatDate(raw.valueDate) : undefined}
        />
        <DetailRow
          label="Account"
          value={account ? account.display_name || "Unnamed Account" : undefined}
        />
        <DetailRow label="Account IBAN" value={iban} mono />
        <DetailRow label="To" value={raw.creditorName} />
        <DetailRow label="To IBAN" value={raw.creditorIban} mono />
        <DetailRow label="From" value={raw.debtorName} />
        <DetailRow label="From IBAN" value={raw.debtorIban} mono />
        <DetailRow label="Bank transaction code" value={raw.bankTransactionCode} />
      </dl>

      {raw.currencyExchange && (
        <>
          <Separator />
          <dl>
            <DetailRow
              label="Currency exchange"
              value={
                raw.currencyExchange.sourceCurrency &&
                raw.currencyExchange.targetCurrency
                  ? `${raw.currencyExchange.sourceCurrency} → ${raw.currencyExchange.targetCurrency}`
                  : undefined
              }
            />
            <DetailRow label="Exchange rate" value={raw.currencyExchange.exchangeRate} />
            <DetailRow
              label="Instructed amount"
              value={
                raw.currencyExchange.instructedAmount
                  ? formatCurrency(
                      Number.parseFloat(
                        raw.currencyExchange.instructedAmount.amount,
                      ),
                      raw.currencyExchange.instructedAmount.currency,
                    )
                  : undefined
              }
            />
          </dl>
        </>
      )}

      {raw.balanceAfter && (
        <div className="flex items-start justify-between gap-4 py-1.5">
          <dt className="text-sm text-muted-foreground shrink-0">
            Balance after
          </dt>
          <dd className="text-sm text-right text-foreground">
            <BlurredValue>
              {formatCurrency(raw.balanceAfter.amount, raw.balanceAfter.currency)}
            </BlurredValue>
          </dd>
        </div>
      )}

      <Separator />

      {/* Category */}
      <div className="flex items-center justify-between gap-4">
        <span className="text-sm text-muted-foreground">Category</span>
        <CategoryBadge
          accountId={transaction.account_id}
          transactionId={transaction.transaction_id}
          categoryId={transaction.category_id}
          categoryName={transaction.category_name}
          categoryColor={transaction.category_color}
          description={transaction.description}
        />
      </div>

      <Separator />

      {/* References */}
      <dl>
        <DetailRow label="Transaction ID" value={transaction.transaction_id} mono />
        <DetailRow
          label="Internal ID"
          value={transaction.internal_transaction_id ?? undefined}
          mono
        />
        {showEntryReference && (
          <DetailRow label="Entry reference" value={raw.entryReference} mono />
        )}
      </dl>

      <RawJsonSection transaction={transaction} />
    </div>
  );
}

export default function TransactionDetail({
  transaction,
  open,
  onOpenChange,
  accounts,
}: TransactionDetailProps) {
  const isMobile = useIsMobile();

  if (!transaction) return null;

  const account = accounts?.find((acc) => acc.id === transaction.account_id);

  if (isMobile) {
    return (
      <Drawer open={open} onOpenChange={onOpenChange}>
        <DrawerContent className="max-h-[90dvh]">
          <DrawerHeader className="pb-0">
            <DrawerTitle>Transaction details</DrawerTitle>
            <DrawerDescription className="sr-only">
              Details for transaction {transaction.description}
            </DrawerDescription>
          </DrawerHeader>
          <div className="overflow-y-auto px-4 pb-6 pt-4">
            <TransactionDetailContent transaction={transaction} account={account} />
          </div>
        </DrawerContent>
      </Drawer>
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Transaction details</SheetTitle>
          <SheetDescription className="sr-only">
            Details for transaction {transaction.description}
          </SheetDescription>
        </SheetHeader>
        <div className="mt-4">
          <TransactionDetailContent transaction={transaction} account={account} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
