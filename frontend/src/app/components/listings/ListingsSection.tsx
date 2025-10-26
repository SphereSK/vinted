"use client";

import { useMemo, useCallback } from "react";
import { useQueryClient, QueryClient } from "@tanstack/react-query";
import {
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Loader2,
  RefreshCcw,
} from "lucide-react";

import { cn } from "@/lib/utils";
import {
  formatCurrency,
  formatDate,
  formatActiveDuration,
} from "@/lib/format";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableHeader,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
} from "@/components/ui/table";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Badge, BadgeProps } from "@/components/ui/badge";

function getConditionBadgeVariant(condition: string | null): BadgeProps["variant"] {
  if (!condition) return "secondary";
  const lower = condition.toLowerCase();
  if (lower.includes("new")) return "success";
  if (lower.includes("good")) return "default";
  if (lower.includes("satisfactory")) return "outline";
  return "secondary";
}

function getPlatformBadgeVariant(platform: string | null): BadgeProps["variant"] {
  if (!platform) return "secondary";
  const lower = platform.toLowerCase();
  if (lower.includes("vinted")) return "success";
  if (lower.includes("depop")) return "destructive";
  return "secondary";
}

import { SortableHead } from "./SortableHead";
import { ListingRow } from "./ListingRow";
import type {
  CategoryResponse,
  ConditionResponse,
  ListingResponse,
  ListingsPage,
  ListingsQuery,
  SourceResponse,
  ListingSortField,
} from "@/lib/types";

import { ListingAvatar } from "../common/ListingAvatar";
import { PriceChangeBadge } from "../common/PriceChangeBadge";

/*───────────────────────────────────────────────
  Constants
───────────────────────────────────────────────*/
const PAGE_SIZE_OPTIONS = [15, 30, 50, 100] as const;

/*───────────────────────────────────────────────
  Main Section
───────────────────────────────────────────────*/
interface ListingsSectionProps {
  platforms?: CategoryResponse[];
  conditions?: ConditionResponse[];
  sources?: SourceResponse[];
  listingsPage: ListingsPage | null;
  isLoading: boolean;
  onQueryChange: (query: Partial<ListingsQuery>) => void;
  query: ListingsQuery;
  queryClient: QueryClient;
}

export function ListingsSection({
  platforms = [],
  conditions = [],
  sources = [],
  listingsPage,
  isLoading,
  onQueryChange,
  query,
  queryClient,
}: ListingsSectionProps) {
  const platformLookup = useMemo(
    () => new Map(platforms.map((p) => [p.id, p.name])),
    [platforms],
  );

  const handlePageChange = useCallback((newPage: number) => {
    onQueryChange({ page: newPage });
  }, [onQueryChange]);

  const handlePageSizeChange = useCallback((newPageSize: string) => {
    onQueryChange({ page_size: Number(newPageSize), page: 1 });
  }, [onQueryChange]);

  function toggleSort(field: ListingSortField) {
    if (query.sort_field === field) {
      onQueryChange({ sort_order: query.sort_order === "asc" ? "desc" : "asc" });
    } else {
      onQueryChange({ sort_field: field, sort_order: "desc" });
    }
  }

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["listings"] });
  };

  const hasData = listingsPage && listingsPage.items.length > 0;

  const has_next = listingsPage?.has_next ?? false;

  return (
    <section className="flex flex-col gap-4 pt-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Listings</h1>
          <p className="text-sm text-muted-foreground">
            All tracked items with price history and timestamps.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Input
            placeholder="Search by title..."
            value={query.search ?? ''}
            onChange={(e) => onQueryChange({ search: e.target.value })}
            className="w-[200px]"
          />

          <Input
            placeholder="Min price..."
            value={query.price_min_cents ? query.price_min_cents / 100 : ""}
            onChange={(e) => onQueryChange({ price_min_cents: e.target.value ? Math.round(parseFloat(e.target.value) * 100) : undefined })}
            className="w-[120px]"
            type="number"
            step="0.01"
          />
          <Input
            placeholder="Max price..."
            value={query.price_max_cents ? query.price_max_cents / 100 : ""}
            onChange={(e) => onQueryChange({ price_max_cents: e.target.value ? Math.round(parseFloat(e.target.value) * 100) : undefined })}
            className="w-[120px]"
            type="number"
            step="0.01"
          />

          <Select value={query.condition ?? "ALL"} onValueChange={(value) => onQueryChange({ condition: value === "ALL" ? undefined : value })}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Condition" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Conditions</SelectItem>
              {conditions.map((cond) => (
                <SelectItem key={cond.id} value={cond.code}>
                  {cond.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={query.platform_id?.toString() ?? "ALL"} onValueChange={(value) => onQueryChange({ platform_id: value === "ALL" ? undefined : parseInt(value) })}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Platform" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Platforms</SelectItem>
              {platforms.map((plat) => (
                <SelectItem key={plat.id} value={plat.id.toString()}>
                  {plat.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={query.source ?? "ALL"} onValueChange={(value) => onQueryChange({ source: value === "ALL" ? undefined : value })}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Sources</SelectItem>
              {sources.map((src) => (
                <SelectItem key={src.id} value={src.code}>
                  {src.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={query.currency ?? "ALL"} onValueChange={(value) => onQueryChange({ currency: value === "ALL" ? undefined : value })}>
            <SelectTrigger className="w-[100px]">
              <SelectValue placeholder="Currency" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All</SelectItem>
              {(listingsPage?.available_currencies ?? []).map((cur) => (
                <SelectItem key={cur} value={cur}>
                  {cur}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            disabled={isLoading}
            onClick={handleRefresh}>
            {isLoading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCcw className="size-4" />
            )}
            <span className="ml-1">Refresh</span>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-24 items-center justify-center text-muted-foreground">
          <Loader2 className="animate-spin" /> Loading listings…
        </div>
      ) : !hasData ? (
        <div className="flex h-24 items-center justify-center text-muted-foreground">
          No listings found.
        </div>
      ) : (
        <Table className="w-full">
          <TableHeader>
            <TableRow>
              <SortableHead
                label="Title"
                field="title"
                currentField={query.sort_field}
                sortOrder={query.sort_order}
                onSort={toggleSort}
              />
              <SortableHead
                label="Price"
                field="price"
                currentField={query.sort_field}
                sortOrder={query.sort_order}
                onSort={toggleSort}
              />
              <TableHead>Change</TableHead>
              <SortableHead
                label="Condition"
                field="condition"
                currentField={query.sort_field}
                sortOrder={query.sort_order}
                onSort={toggleSort}
              />
              <TableHead>Platform</TableHead>
              <TableHead>Source</TableHead>
              <SortableHead
                label="Last seen"
                field="last_seen_at"
                currentField={query.sort_field}
                sortOrder={query.sort_order}
                onSort={toggleSort}
              />
              <SortableHead
                label="First seen"
                field="first_seen_at"
                currentField={query.sort_field}
                sortOrder={query.sort_order}
                onSort={toggleSort}
              />
              <TableHead>Active for</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {listingsPage.items.map((listing) => (
              <ListingRow
                key={listing.id}
                listing={listing}
                platformLookup={platformLookup}
                getConditionBadgeVariant={getConditionBadgeVariant}
                getPlatformBadgeVariant={getPlatformBadgeVariant}
              />
            ))}
          </TableBody>
        </Table>
      )}

      {listingsPage && listingsPage.total > 0 && (
        <div className="flex items-center justify-between border-t p-3">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePageChange(query.page - 1)}
              disabled={query.page <= 1 || isLoading}
            >
              <ChevronLeft className="size-4" /> Prev
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {query.page} of {Math.ceil(listingsPage.total / query.page_size)}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePageChange(query.page + 1)}
              disabled={!has_next || isLoading}
            >
              Next <ChevronRight className="size-4" />
            </Button>
          </div>
          <Select value={query.page_size.toString()} onValueChange={handlePageSizeChange}>
            <SelectTrigger className="w-[100px]">
              <SelectValue placeholder="Page Size" />
            </SelectTrigger>
            <SelectContent>
              {PAGE_SIZE_OPTIONS.map((size) => (
                <SelectItem key={size} value={size.toString()}>
                  {size} per page
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
    </section>
  );
}