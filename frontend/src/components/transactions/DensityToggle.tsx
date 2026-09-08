import { Rows2, Rows3 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { Density } from "@/lib/density";

/**
 * Compact/cosy row-height switch for the table.
 *
 * A single toggle rather than a menu — there are two states, and the icon
 * shows which one a click leads to.
 */
export default function DensityToggle({
  density,
  onDensityChange,
}: {
  density: Density;
  onDensityChange: (density: Density) => void;
}) {
  const next: Density = density === "compact" ? "cosy" : "compact";
  const label = next === "cosy" ? "Use cosy rows" : "Use compact rows";

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-2 px-2 text-muted-foreground"
            aria-label={label}
            onClick={() => onDensityChange(next)}
          >
            {density === "compact" ? (
              <Rows3 className="h-4 w-4" />
            ) : (
              <Rows2 className="h-4 w-4" />
            )}
          </Button>
        }
      />
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
