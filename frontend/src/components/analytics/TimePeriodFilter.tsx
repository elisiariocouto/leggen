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
    <div className={`flex flex-wrap gap-2 ${className}`}>
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
  );
}
