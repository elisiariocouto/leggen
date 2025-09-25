import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Plus, Building2, ExternalLink } from "lucide-react";
import { apiClient } from "../lib/api";
import { Button } from "./ui/button";
import { Label } from "./ui/label";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "./ui/drawer";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Alert, AlertDescription } from "./ui/alert";

export default function AddBankAccountDrawer() {
  const [open, setOpen] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [selectedBank, setSelectedBank] = useState<string>("");

  const { data: countries } = useQuery({
    queryKey: ["supportedCountries"],
    queryFn: apiClient.getSupportedCountries,
  });

  const { data: banks, isLoading: banksLoading } = useQuery({
    queryKey: ["bankInstitutions", selectedCountry],
    queryFn: () => apiClient.getBankInstitutions(selectedCountry),
    enabled: !!selectedCountry,
  });

  const connectBankMutation = useMutation({
    mutationFn: (institutionId: string) =>
      apiClient.createBankConnection(institutionId),
    onSuccess: (data) => {
      // Redirect to the bank's authorization link
      if (data.link) {
        window.open(data.link, "_blank");
        setOpen(false);
      }
    },
    onError: (error) => {
      console.error("Failed to create bank connection:", error);
    },
  });

  const handleCountryChange = (country: string) => {
    setSelectedCountry(country);
    setSelectedBank("");
  };

  const handleConnect = () => {
    if (selectedBank) {
      connectBankMutation.mutate(selectedBank);
    }
  };

  const resetForm = () => {
    setSelectedCountry("");
    setSelectedBank("");
  };

  return (
    <Drawer
      open={open}
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (!isOpen) {
          resetForm();
        }
      }}
    >
      <DrawerTrigger asChild>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Add New Account
        </Button>
      </DrawerTrigger>
      <DrawerContent className="max-h-[80vh]">
        <DrawerHeader>
          <DrawerTitle>Connect Bank Account</DrawerTitle>
          <DrawerDescription>
            Select your country and bank to connect your account to Leggen
          </DrawerDescription>
        </DrawerHeader>

        <div className="px-6 space-y-6 overflow-y-auto">
          {/* Country Selection */}
          <div className="space-y-2">
            <Label htmlFor="country">Country</Label>
            <Select value={selectedCountry} onValueChange={handleCountryChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select your country" />
              </SelectTrigger>
              <SelectContent>
                {countries?.map((country) => (
                  <SelectItem key={country.code} value={country.code}>
                    {country.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Bank Selection */}
          {selectedCountry && (
            <div className="space-y-2">
              <Label htmlFor="bank">Bank</Label>
              {banksLoading ? (
                <div className="p-4 text-center text-muted-foreground">
                  Loading banks...
                </div>
              ) : banks && banks.length > 0 ? (
                <Select value={selectedBank} onValueChange={setSelectedBank}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your bank" />
                  </SelectTrigger>
                  <SelectContent>
                    {banks.map((bank) => (
                      <SelectItem key={bank.id} value={bank.id}>
                        <div className="flex items-center space-x-2">
                          {bank.logo ? (
                            <img
                              src={bank.logo}
                              alt={`${bank.name} logo`}
                              className="w-4 h-4 object-contain"
                            />
                          ) : (
                            <Building2 className="w-4 h-4" />
                          )}
                          <span>{bank.name}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Alert>
                  <AlertDescription>
                    No banks available for the selected country.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          {/* Instructions */}
          {selectedBank && (
            <Alert>
              <AlertDescription>
                You'll be redirected to your bank's website to authorize the
                connection. After approval, you'll return to Leggen and your
                account will start syncing.
              </AlertDescription>
            </Alert>
          )}

          {/* Error Display */}
          {connectBankMutation.isError && (
            <Alert variant="destructive">
              <AlertDescription>
                Failed to create bank connection. Please try again.
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DrawerFooter>
          <div className="flex space-x-2">
            <Button
              onClick={handleConnect}
              disabled={!selectedBank || connectBankMutation.isPending}
              className="flex-1"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              {connectBankMutation.isPending
                ? "Connecting..."
                : "Open Bank Authorization"}
            </Button>
            <DrawerClose asChild>
              <Button
                variant="outline"
                disabled={connectBankMutation.isPending}
              >
                Cancel
              </Button>
            </DrawerClose>
          </div>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
}
