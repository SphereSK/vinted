"use client";

import { TableHead } from "@/components/ui/table";
import { ChevronsUpDown, ChevronUp, ChevronDown } from "lucide-react";
import type { ListingSortField } from "@/lib/types";

interface SortableHeadProps {
  label: string;
  field: ListingSortField;
  currentField: ListingSortField;
  sortOrder: "asc" | "desc";
  onSort: (field: ListingSortField) => void;
}

export function SortableHead({
  label,
  field,
  currentField,
  sortOrder,
  onSort,
}: SortableHeadProps) {
  const getSortIcon = () => {
    if (currentField !== field) {
      return <ChevronsUpDown className="size-3 text-muted-foreground" />;
    }
    return sortOrder === "asc" ? (
      <ChevronUp className="size-3 text-muted-foreground" />
    ) : (
      <ChevronDown className="size-3 text-muted-foreground" />
    );
  };

  return (
    <TableHead
      className="cursor-pointer select-none"
      onClick={() => onSort(field)}
    >
      <div className="flex items-center gap-1">
        {label}
        {getSortIcon()}
      </div>
    </TableHead>
  );
}
