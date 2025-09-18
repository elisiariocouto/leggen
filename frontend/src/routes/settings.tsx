import { createFileRoute } from "@tanstack/react-router";
import AccountSettings from "../components/AccountSettings";

export const Route = createFileRoute("/settings")({
  component: AccountSettings,
});
