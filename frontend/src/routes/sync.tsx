import { createFileRoute } from "@tanstack/react-router";
import Sync from "../components/Sync";

export const Route = createFileRoute("/sync")({
  component: Sync,
});
