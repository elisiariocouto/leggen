import { createFileRoute } from "@tanstack/react-router";
import Accounts from "../components/Accounts";

export const Route = createFileRoute("/accounts")({
  component: Accounts,
});
