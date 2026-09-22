import { useState, type FormEvent, type ReactNode } from "react";
import {
  useMutation,
  useQueryClient,
  type QueryKey,
} from "@tanstack/react-query";
import { TestTube, type LucideIcon } from "lucide-react";
import { toast } from "sonner";
import { getApiErrorMessage } from "../../lib/api";
import { cn } from "../../lib/utils";
import { Button } from "../ui/button";
import { EditButton } from "../ui/edit-button";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "../ui/drawer";

export interface SettingsDrawerState {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  close: () => void;
}

/**
 * Open state for a settings drawer. `seed` fills the form from the saved
 * settings each time the drawer opens, rather than mirroring props into state
 * with an effect — that ran on every settings refetch and could overwrite
 * what the user was typing.
 */
export function useSettingsDrawer(seed: () => void): SettingsDrawerState {
  const [open, setOpen] = useState(false);
  return {
    open,
    onOpenChange: (next) => {
      if (next) seed();
      setOpen(next);
    },
    close: () => setOpen(false),
  };
}

/**
 * A settings save: on success it refreshes what the change affects, closes
 * the drawer and confirms; on failure it shows the API's reason.
 */
export function useSettingsMutation<TVariables>({
  mutationFn,
  invalidates,
  successMessage,
  errorMessage,
  onSuccess,
}: {
  mutationFn: (variables: TVariables) => Promise<unknown>;
  invalidates: QueryKey[];
  successMessage: string;
  errorMessage: string;
  onSuccess?: () => void;
}) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      for (const queryKey of invalidates) {
        queryClient.invalidateQueries({ queryKey });
      }
      onSuccess?.();
      toast.success(successMessage);
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, errorMessage));
    },
  });
}

const WIDTHS = {
  sm: "max-w-sm",
  md: "max-w-md",
  "2xl": "max-w-2xl",
} as const;

interface SettingsDrawerProps {
  drawer: SettingsDrawerState;
  title: string;
  description: string;
  icon?: LucideIcon;
  width?: keyof typeof WIDTHS;
  onSubmit: () => void;
  isSaving: boolean;
  saveLabel: string;
  /** Skip the browser's own field validation, for forms that show their own. */
  noValidate?: boolean;
  /** Buttons beside Save, such as Test. */
  actions?: ReactNode;
  /** Controls under the button row, above Cancel. */
  footer?: ReactNode;
  children: ReactNode;
}

/** The Edit trigger, drawer chrome and Save/Cancel footer of a settings form. */
export default function SettingsDrawer({
  drawer,
  title,
  description,
  icon: Icon,
  width = "md",
  onSubmit,
  isSaving,
  saveLabel,
  noValidate,
  actions,
  footer,
  children,
}: SettingsDrawerProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <Drawer open={drawer.open} onOpenChange={drawer.onOpenChange}>
      <DrawerTrigger render={<EditButton />} />
      <DrawerContent>
        <div className={cn("mx-auto w-full", WIDTHS[width])}>
          <DrawerHeader>
            <DrawerTitle className="flex items-center space-x-2">
              {Icon && <Icon className="h-5 w-5 text-primary" />}
              <span>{title}</span>
            </DrawerTitle>
            <DrawerDescription>{description}</DrawerDescription>
          </DrawerHeader>

          <form
            onSubmit={handleSubmit}
            noValidate={noValidate}
            className="p-4 space-y-6"
          >
            {children}

            <DrawerFooter className="px-0">
              <div className="flex space-x-2">
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? "Saving..." : saveLabel}
                </Button>
                {actions}
              </div>
              {footer}
              <DrawerClose render={<Button variant="ghost">Cancel</Button>} />
            </DrawerFooter>
          </form>
        </div>
      </DrawerContent>
    </Drawer>
  );
}

/** Sends a test through the configuration in the form. */
export function TestButton({
  onClick,
  isPending,
}: {
  onClick: () => void;
  isPending: boolean;
}) {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      disabled={isPending}
    >
      <TestTube className={cn("h-4 w-4 mr-2", isPending && "animate-spin")} />
      {isPending ? "Testing..." : "Test"}
    </Button>
  );
}
