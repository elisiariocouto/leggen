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
  const [selectedCountry, setSelectedCountry] = useState("");
  const [selectedBank, setSelectedBank] = useState("");
  const [selectedPsuType, setSelectedPsuType] = useState("");

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
    mutationFn: ({
      name,
      country,
      psuType,
    }: {
      name: string;
      country: string;
      psuType: string;
    }) => apiClient.createBankConnection(name, country, psuType),
    onSuccess: (data) => {
      // Redirect to the bank's authorization URL
      if (data.url) {
        window.open(data.url, "_blank");
        setOpen(false);
      }
    },
    onError: (error) => {
      console.error("Failed to create bank connection:", error);
    },
  });

  const selectedBankData = banks?.find((b) => b.name === selectedBank);

  const handleCountryChange = (country: string) => {
    setSelectedCountry(country);
    setSelectedBank("");
    setSelectedPsuType("");
  };

  const handleBankChange = (bank: string) => {
    setSelectedBank(bank);
    const bankData = banks?.find((b) => b.name === bank);
    if (bankData && bankData.psu_types.length === 1) {
      setSelectedPsuType(bankData.psu_types[0]);
    } else {
      setSelectedPsuType("");
    }
  };

  const handleConnect = () => {
    if (selectedBank && selectedCountry && selectedPsuType) {
      connectBankMutation.mutate({
        name: selectedBank,
        country: selectedCountry,
        psuType: selectedPsuType,
      });
    }
  };

  const resetForm = () => {
    setSelectedCountry("");
    setSelectedBank("");
    setSelectedPsuType("");
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
            <Select onValueChange={handleCountryChange}>
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
                <Select
                  key={`bank-${selectedCountry}`}
                  onValueChange={handleBankChange}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select your bank" />
                  </SelectTrigger>
                  <SelectContent>
                    {banks.map((bank) => (
                      <SelectItem key={bank.name} value={bank.name}>
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

          {/* PSU Type Selection */}
          {selectedBankData && selectedBankData.psu_types.length > 1 && (
            <div className="space-y-2">
              <Label htmlFor="psuType">Account Type</Label>
              <Select
                key={`psu-${selectedBank}`}
                onValueChange={setSelectedPsuType}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select account type" />
                </SelectTrigger>
                <SelectContent>
                  {selectedBankData.psu_types.map((psuType) => (
                    <SelectItem key={psuType} value={psuType}>
                      {psuType.charAt(0).toUpperCase() + psuType.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Instructions */}
          {selectedBank && selectedPsuType && (
            <Alert>
              <AlertDescription>
                You&apos;ll be redirected to your bank&apos;s website to
                authorize the connection. After approval, you&apos;ll return to
                Leggen and your account will start syncing.
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
              disabled={
                !selectedBank ||
                !selectedPsuType ||
                connectBankMutation.isPending
              }
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
