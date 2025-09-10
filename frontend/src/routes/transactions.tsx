import { createFileRoute } from "@tanstack/react-router";
import TransactionsList from "../components/TransactionsList";

export const Route = createFileRoute("/transactions")({
  component: TransactionsList,
  validateSearch: (search) => ({
    accountId: search.accountId as string | undefined,
    startDate: search.startDate as string | undefined,
    endDate: search.endDate as string | undefined,
  }),
});
