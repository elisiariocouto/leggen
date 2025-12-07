import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { useBalanceVisibility } from "../../contexts/BalanceVisibilityContext";
import { BlurredValue } from "../ui/blurred-value";
import type { Account } from "../../types/api";

interface TransactionDistributionProps {
  accounts: Account[];
  className?: string;
}

interface PieDataPoint {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: PieDataPoint;
  }>;
}

export default function TransactionDistribution({
  accounts,
  className,
}: TransactionDistributionProps) {
  const { isBalanceVisible } = useBalanceVisibility();

  // Helper function to get bank name from institution_id
  const getBankName = (institutionId: string): string => {
    const bankMapping: Record<string, string> = {
      REVOLUT_REVOLT21: "Revolut",
      NUBANK_NUPBBR25: "Nu Pagamentos",
      BANCOBPI_BBPIPTPL: "Banco BPI",
      // TODO: Add more bank mappings as needed
    };
    return bankMapping[institutionId] || institutionId.split("_")[0];
  };

  // Helper function to create display name for account
  const getAccountDisplayName = (account: Account): string => {
    const bankName = getBankName(account.institution_id);
    const accountName = account.name || `Account ${account.id.split("-")[1]}`;
    return `${bankName} - ${accountName}`;
  };

  // Create pie chart data from account balances
  const pieData: PieDataPoint[] = accounts.map((account, index) => {
    const primaryBalance = account.balances?.[0]?.amount || 0;

    const colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];

    return {
      name: getAccountDisplayName(account),
      value: primaryBalance,
      color: colors[index % colors.length],
    };
  });

  const totalBalance = pieData.reduce((sum, item) => sum + item.value, 0);

  if (pieData.length === 0 || totalBalance === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-medium text-foreground mb-4">
          Account Distribution
        </h3>
        <div className="h-80 flex items-center justify-center text-muted-foreground">
          No account data available
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: TooltipProps) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const percentage = ((data.value / totalBalance) * 100).toFixed(1);
      return (
        <div className="bg-card p-3 border rounded shadow-lg">
          <p className="font-medium text-foreground">{data.name}</p>
          <p className="text-primary">
            Balance:{" "}
            <BlurredValue>€{data.value.toLocaleString()}</BlurredValue>
          </p>
          <p className="text-muted-foreground">{percentage}% of total</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-foreground mb-4">
        Account Balance Distribution
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              outerRadius={100}
              innerRadius={40}
              paddingAngle={2}
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              formatter={(value, entry: { color?: string }) => (
                <span style={{ color: entry.color }}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-2">
        {pieData.map((item, index) => (
          <div
            key={index}
            className="flex items-center justify-between text-sm"
          >
            <div className="flex items-center">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-foreground">{item.name}</span>
            </div>
            <span className="font-medium text-foreground">
              <BlurredValue>€{item.value.toLocaleString()}</BlurredValue>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
