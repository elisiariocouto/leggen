import { createFileRoute } from "@tanstack/react-router";
import CategoryRules from "../components/CategoryRules";

export const Route = createFileRoute("/rules")({
  component: CategoryRules,
});
