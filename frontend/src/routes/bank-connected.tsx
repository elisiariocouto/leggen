import { createFileRoute, useSearch } from "@tanstack/react-router";
import { CheckCircle, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";

function BankConnected() {
  const search = useSearch({ from: "/bank-connected" });

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4">
            <CheckCircle className="h-16 w-16 text-green-500" />
          </div>
          <CardTitle className="text-2xl">Account Connected!</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <p className="text-muted-foreground">
            Your bank account has been successfully connected to Leggen. We'll
            start syncing your transactions shortly.
          </p>

          {search?.bank && (
            <p className="text-sm text-muted-foreground">
              Connected to: <strong>{search.bank}</strong>
            </p>
          )}

          <div className="pt-4">
            <Button
              onClick={() => (window.location.href = "/settings")}
              className="w-full"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go to Settings
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export const Route = createFileRoute("/bank-connected")({
  component: BankConnected,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      bank: (search.bank as string) || undefined,
    };
  },
});
