import { Edit3 } from "lucide-react";
import { Button } from "./button";
import { cn } from "../../lib/utils";

interface EditButtonProps {
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  size?: "default" | "sm" | "lg" | "icon";
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  children?: React.ReactNode;
}

export function EditButton({
  onClick,
  disabled = false,
  className,
  size = "sm",
  variant = "outline",
  children,
  ...props
}: EditButtonProps) {
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      size={size}
      variant={variant}
      className={cn(
        "h-8 px-3 text-muted-foreground hover:text-foreground transition-colors",
        className,
      )}
      {...props}
    >
      <Edit3 className="h-4 w-4" />
      <span className="ml-2">{children || "Edit"}</span>
    </Button>
  );
}
