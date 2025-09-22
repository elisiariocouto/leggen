import { createFileRoute } from "@tanstack/react-router";
import System from "../components/System";

export const Route = createFileRoute("/system")({
  component: System,
});
