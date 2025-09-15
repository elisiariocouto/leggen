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
      <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
        {skeletonRows.map((_, index) => (
          <div key={index} className="p-4 animate-pulse">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-start space-x-3">
                  <div className="p-2 rounded-full bg-gray-200 flex-shrink-0">
                    <div className="h-4 w-4 bg-gray-300 rounded"></div>
                  </div>
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="space-y-1">
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                      <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/3"></div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="text-right ml-3 flex-shrink-0 space-y-2">
                <div className="h-6 bg-gray-200 rounded w-20"></div>
                <div className="h-4 bg-gray-200 rounded w-16 ml-auto"></div>
                <div className="h-6 bg-gray-200 rounded w-12 ml-auto"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left">
                <div className="h-4 bg-gray-200 rounded w-20 animate-pulse"></div>
              </th>
              <th className="px-6 py-3 text-left">
                <div className="h-4 bg-gray-200 rounded w-16 animate-pulse"></div>
              </th>
              <th className="px-6 py-3 text-left">
                <div className="h-4 bg-gray-200 rounded w-12 animate-pulse"></div>
              </th>
              <th className="px-6 py-3 text-left">
                <div className="h-4 bg-gray-200 rounded w-8 animate-pulse"></div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {skeletonRows.map((_, index) => (
              <tr key={index} className="animate-pulse">
                <td className="px-6 py-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 rounded-full bg-gray-200 flex-shrink-0">
                      <div className="h-4 w-4 bg-gray-300 rounded"></div>
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="space-y-1">
                        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-right">
                    <div className="h-6 bg-gray-200 rounded w-24 ml-auto mb-1"></div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="space-y-1">
                    <div className="h-4 bg-gray-200 rounded w-20"></div>
                    <div className="h-3 bg-gray-200 rounded w-16"></div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="h-6 bg-gray-200 rounded w-12"></div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
