import { createFileRoute } from "@tanstack/react-router";
import TransactionsTable from "../components/TransactionsTable";

export const Route = createFileRoute("/")({
  component: TransactionsTable,
});
