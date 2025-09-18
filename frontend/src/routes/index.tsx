import { createFileRoute } from "@tanstack/react-router";
import TransactionsTable from "../components/TransactionsTable";

export const Route = createFileRoute("/")({
  component: TransactionsTable,
  validateSearch: (search) => ({
    accountId: search.accountId as string | undefined,
    startDate: search.startDate as string | undefined,
    endDate: search.endDate as string | undefined,
  }),
});
