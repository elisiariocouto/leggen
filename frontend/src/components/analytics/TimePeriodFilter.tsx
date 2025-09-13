import { Calendar } from "lucide-react";
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
    <div className={`flex items-center gap-4 ${className}`}>
      <div className="flex items-center gap-2 text-gray-700">
        <Calendar size={20} />
        <span className="font-medium">Time Period:</span>
      </div>
      <div className="flex gap-2">
        {TIME_PERIODS.map((period) => (
          <button
            key={period.value}
            onClick={() => onPeriodChange(period)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              selectedPeriod.value === period.value
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {period.label}
          </button>
        ))}
      </div>
    </div>
  );
}