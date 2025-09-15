import { Skeleton } from "./ui/skeleton";
import { Card } from "./ui/card";

interface TransactionSkeletonProps {
  rows?: number;
  view?: "table" | "mobile";
}

export default function TransactionSkeleton({
  rows = 5,
  view = "table",
}: TransactionSkeletonProps) {
  const skeletonRows = Array.from({ length: rows }, (_, index) => index);

  if (view === "mobile") {
    return (
      <Card className="divide-y divide-border">
        {skeletonRows.map((_, index) => (
          <div key={index} className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-start space-x-3">
                  <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
                  <div className="flex-1 min-w-0 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <div className="space-y-1">
                      <Skeleton className="h-3 w-1/2" />
                      <Skeleton className="h-3 w-2/3" />
                      <Skeleton className="h-3 w-1/3" />
                    </div>
                  </div>
                </div>
              </div>
              <div className="text-right ml-3 flex-shrink-0 space-y-2">
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-4 w-16 ml-auto" />
                <Skeleton className="h-6 w-12 ml-auto" />
              </div>
            </div>
          </div>
        ))}
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-6 py-3 text-left">
                <Skeleton className="h-4 w-20" />
              </th>
              <th className="px-6 py-3 text-left">
                <Skeleton className="h-4 w-16" />
              </th>
              <th className="px-6 py-3 text-left">
                <Skeleton className="h-4 w-12" />
              </th>
              <th className="px-6 py-3 text-left">
                <Skeleton className="h-4 w-8" />
              </th>
            </tr>
          </thead>
          <tbody className="bg-card divide-y divide-border">
            {skeletonRows.map((_, index) => (
              <tr key={index}>
                <td className="px-6 py-4">
                  <div className="flex items-start space-x-3">
                    <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <div className="space-y-1">
                        <Skeleton className="h-3 w-1/2" />
                        <Skeleton className="h-3 w-2/3" />
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-right">
                    <Skeleton className="h-6 w-24 ml-auto mb-1" />
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                </td>
                <td className="px-6 py-4">
                  <Skeleton className="h-6 w-12" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
