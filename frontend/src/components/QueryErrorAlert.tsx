import { AlertCircle, RefreshCw } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Button } from "./ui/button";

interface QueryErrorAlertProps {
  title: string;
  onRetry: () => void;
}

/** A query that could not reach the API, with a button to try again. */
export default function QueryErrorAlert({ title, onRetry }: QueryErrorAlertProps) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="space-y-3">
        <p>
          Unable to connect to the Leggen API. Please check your configuration
          and ensure the API server is running.
        </p>
        <Button onClick={onRetry} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </AlertDescription>
    </Alert>
  );
}
