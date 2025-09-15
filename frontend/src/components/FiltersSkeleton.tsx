import { Skeleton } from "./ui/skeleton";
import { Card, CardContent } from "./ui/card";

export default function FiltersSkeleton() {
  return (
    <Card>
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-32" />
          <div className="flex items-center space-x-2">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-8 w-20" />
          </div>
        </div>
      </div>

      <CardContent className="px-6 py-4 border-b border-border bg-muted/30">
        {/* Quick Date Filters Skeleton */}
        <div className="mb-6">
          <Skeleton className="h-4 w-32 mb-3" />
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-10 w-24 rounded-lg" />
              <Skeleton className="h-10 w-20 rounded-lg" />
              <Skeleton className="h-10 w-28 rounded-lg" />
            </div>
            <div className="flex flex-wrap gap-2">
              <Skeleton className="h-10 w-24 rounded-lg" />
              <Skeleton className="h-10 w-20 rounded-lg" />
            </div>
          </div>
        </div>

        {/* Filter Fields Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="sm:col-span-2 lg:col-span-1">
            <Skeleton className="h-4 w-16 mb-1" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div>
            <Skeleton className="h-4 w-16 mb-1" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div>
            <Skeleton className="h-4 w-20 mb-1" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div>
            <Skeleton className="h-4 w-16 mb-1" />
            <Skeleton className="h-10 w-full" />
          </div>
        </div>

        {/* Amount Range Filters Skeleton */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          <div>
            <Skeleton className="h-4 w-20 mb-1" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div>
            <Skeleton className="h-4 w-20 mb-1" />
            <Skeleton className="h-10 w-full" />
          </div>
        </div>
      </CardContent>

      {/* Results Summary Skeleton */}
      <CardContent className="px-6 py-3 bg-muted/30 border-b border-border">
        <Skeleton className="h-4 w-48" />
      </CardContent>
    </Card>
  );
}
