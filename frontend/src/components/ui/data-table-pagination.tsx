import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface DataTablePaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  total: number;
  hasNext: boolean;
  hasPrev: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

export function DataTablePagination({
  currentPage,
  totalPages,
  pageSize,
  total,
  hasNext,
  hasPrev,
  onPageChange,
  onPageSizeChange,
}: DataTablePaginationProps) {
  return (
    <div className="flex items-center justify-between px-2 py-4">
      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div className="flex items-center space-x-6 lg:space-x-8">
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium text-foreground">Rows per page</p>
            <Select
              value={`${pageSize}`}
              onValueChange={(value) => {
                onPageSizeChange(Number(value));
                onPageChange(1); // Reset to first page when changing page size
              }}
            >
              <SelectTrigger className="h-8 w-[70px]">
                <SelectValue placeholder={pageSize} />
              </SelectTrigger>
              <SelectContent side="top">
                {[10, 25, 50, 100].map((pageSize) => (
                  <SelectItem key={pageSize} value={`${pageSize}`}>
                    {pageSize}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex w-[100px] items-center justify-center text-sm font-medium text-foreground">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              className="hidden h-8 w-8 p-0 lg:flex"
              onClick={() => onPageChange(1)}
              disabled={currentPage === 1}
            >
              <span className="sr-only">Go to first page</span>
              <ChevronsLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!hasPrev}
            >
              <span className="sr-only">Go to previous page</span>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!hasNext}
            >
              <span className="sr-only">Go to next page</span>
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="hidden h-8 w-8 p-0 lg:flex"
              onClick={() => onPageChange(totalPages)}
              disabled={currentPage === totalPages}
            >
              <span className="sr-only">Go to last page</span>
              <ChevronsRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="text-sm text-muted-foreground">
          Showing {(currentPage - 1) * pageSize + 1} to{" "}
          {Math.min(currentPage * pageSize, total)} of {total} entries
        </div>
      </div>

      {/* Mobile view */}
      <div className="flex w-full items-center justify-between space-x-4 sm:hidden">
        <div className="text-sm text-muted-foreground">
          Page {currentPage} of {totalPages}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={!hasPrev}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={!hasNext}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
