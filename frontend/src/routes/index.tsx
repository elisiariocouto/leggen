import { createFileRoute } from "@tanstack/react-router";
import AccountsOverview from "../components/AccountsOverview";

export const Route = createFileRoute("/")({
  component: AccountsOverview,
});
