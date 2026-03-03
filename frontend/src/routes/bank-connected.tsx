import { useEffect, useRef, useState } from "react";
import { createFileRoute, useSearch } from "@tanstack/react-router";
import { CheckCircle, ArrowLeft, Loader2, AlertCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { apiClient } from "../lib/api";

function BankConnected() {
  const search = useSearch({ from: "/bank-connected" });
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    search?.code ? "loading" : "success",
  );
  const [errorMessage, setErrorMessage] = useState<string>("");
  const exchangedRef = useRef(false);

  useEffect(() => {
    if (search?.code && !exchangedRef.current) {
      exchangedRef.current = true;
      apiClient
        .exchangeAuthCode(search.code)
        .then(() => {
          setStatus("success");
        })
        .catch((err) => {
          setStatus("error");
          setErrorMessage(
            err?.response?.data?.detail || "Failed to complete bank connection",
          );
        });
    }
  }, [search?.code]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto mb-4">
              <Loader2 className="h-16 w-16 text-primary animate-spin" />
            </div>
            <CardTitle className="text-2xl">Connecting Account...</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-muted-foreground">
              Please wait while we complete your bank connection.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto mb-4">
              <AlertCircle className="h-16 w-16 text-destructive" />
            </div>
            <CardTitle className="text-2xl">Connection Failed</CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-muted-foreground">
              {errorMessage || "Something went wrong while connecting your bank account."}
            </p>
            <div className="pt-4">
              <Button
                onClick={() => (window.location.href = "/accounts")}
                className="w-full"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go to Accounts
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

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

          <div className="pt-4">
            <Button
              onClick={() => (window.location.href = "/accounts")}
              className="w-full"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go to Accounts
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
      code: (search.code as string) || undefined,
    };
  },
});
