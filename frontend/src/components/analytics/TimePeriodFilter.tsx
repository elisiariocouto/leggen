import { Calendar } from "lucide-react";
import { Button } from "../ui/button";
import type { TimePeriod } from "../../lib/timePeriods";
import { TIME_PERIODS } from "../../lib/timePeriods";

interface TimePeriodFilterProps {
  selectedPeriod: TimePeriod;
  onPeriodChange: (period: TimePeriod) => void;
  className?: string;
}

export default function TimePeriodFilter({
  selectedPeriod,
  onPeriodChange,
  className = "",
}: TimePeriodFilterProps) {
  return (
    <div
      className={`flex flex-col sm:flex-row sm:items-center gap-4 ${className}`}
    >
      <div className="flex items-center gap-2 text-foreground">
        <Calendar size={20} />
        <span className="font-medium">Time Period:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {TIME_PERIODS.map((period) => (
          <Button
            key={period.value}
            onClick={() => onPeriodChange(period)}
            variant={
              selectedPeriod.value === period.value ? "default" : "outline"
            }
            size="sm"
          >
            {period.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
