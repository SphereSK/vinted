"use client";

import { useCallback, useMemo, useState } from "react";
import { QueryClient } from "@tanstack/react-query";
import {
  ChevronLeft,
  ChevronRight,
  Loader2,
  RefreshCcw,
  Filter,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableHeader,
  TableHead,
  TableRow,
  TableBody,
} from "@/components/ui/table";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";

import { SortableHead } from "./SortableHead";
import { ListingRow } from "./ListingRow";
import { FilterPanel } from "../filters/FilterPanel";
import type {
  CategoryResponse,
  ConditionResponse,
  ListingsPage,
  ListingsQuery,
  SourceResponse,
  ListingSortField,
  PlatformResponse,
  FilterRequest,
} from "@/lib/types";

/*───────────────────────────────────────────────
  Constants
───────────────────────────────────────────────*/
const PAGE_SIZE_OPTIONS = [15, 30, 50, 100] as const;

/*───────────────────────────────────────────────
  Main Section
───────────────────────────────────────────────*/
interface ListingsSectionProps {
  platforms?: PlatformResponse[];
  conditions?: ConditionResponse[];
  sources?: SourceResponse[];
  categories?: CategoryResponse[];
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
  categories = [],
  listingsPage,
  isLoading,
  onQueryChange,
  query,
  queryClient,
}: ListingsSectionProps) {
  const [showFilters, setShowFilters] = useState(true);

  // Convert query to filter format
  const filters = useMemo((): FilterRequest => ({
    title: query.search,
    price_min: query.price_min,
    price_max: query.price_max,
    conditions: query.condition ? [query.condition] : [],
    platforms: query.platform ? [query.platform] : [],
    sources: query.source ? [query.source] : [],
    categories: query.category ? [query.category] : [],
  }), [query]);

  const handleFilterChange = useCallback((key: keyof FilterRequest, value: string | number | string[] | undefined) => {
    if (key === "title") {
      onQueryChange({ search: value as string | undefined, page: 1 });
    } else if (key === "price_min" || key === "price_max") {
      onQueryChange({ [key]: value as number | undefined, page: 1 });
    } else if (key === "conditions") {
      const values = value as string[];
      onQueryChange({ condition: values[0] || undefined, page: 1 });
    } else if (key === "platforms") {
      const values = value as string[];
      onQueryChange({ platform: values[0] || undefined, page: 1 });
    } else if (key === "sources") {
      const values = value as string[];
      onQueryChange({ source: values[0] || undefined, page: 1 });
    } else if (key === "categories") {
      const values = value as string[];
      onQueryChange({ category: values[0] || undefined, page: 1 });
    }
  }, [onQueryChange]);

  const handleFiltersChange = useCallback((updates: Partial<FilterRequest>) => {
    const queryUpdates: Partial<ListingsQuery> = { page: 1 };
    if ("title" in updates) queryUpdates.search = updates.title;
    if ("price_min" in updates) queryUpdates.price_min = updates.price_min;
    if ("price_max" in updates) queryUpdates.price_max = updates.price_max;
    if ("conditions" in updates) queryUpdates.condition = updates.conditions?.[0];
    if ("platforms" in updates) queryUpdates.platform = updates.platforms?.[0];
    if ("sources" in updates) queryUpdates.source = updates.sources?.[0];
    if ("categories" in updates) queryUpdates.category = updates.categories?.[0];
    onQueryChange(queryUpdates);
  }, [onQueryChange]);

  const handleClearFilters = useCallback(() => {
    onQueryChange({
      search: undefined,
      price_min: undefined,
      price_max: undefined,
      condition: undefined,
      platform: undefined,
      source: undefined,
      category: undefined,
      currency: undefined,
      is_sold: undefined,
      page: 1,
    });
  }, [onQueryChange]);

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

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="size-4" />
            <span className="ml-1">{showFilters ? "Hide" : "Show"} Filters</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            disabled={isLoading}
            onClick={handleRefresh}
          >
            {isLoading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCcw className="size-4" />
            )}
            <span className="ml-1">Refresh</span>
          </Button>
        </div>
      </div>

      {showFilters && (
        <FilterPanel
          filters={filters}
          onFilterChange={handleFilterChange}
          onFiltersChange={handleFiltersChange}
          onClearFilters={handleClearFilters}
          categories={categories}
          platforms={platforms}
          sources={sources}
          conditions={conditions}
          totalResults={listingsPage?.total_items ?? 0}
          isLoading={isLoading}
          isSold={query.is_sold}
          onSoldChange={(sold) => onQueryChange({ is_sold: sold, page: 1 })}
          currency={query.currency}
          availableCurrencies={
            listingsPage?.items.reduce((acc, item) => {
              if (item.currency && !acc.includes(item.currency)) {
                acc.push(item.currency);
              }
              return acc;
            }, [] as string[]) ?? []
          }
          onCurrencyChange={(currency) => onQueryChange({ currency, page: 1 })}
        />
      )}

      {isLoading ? (
        <div className="flex h-24 items-center justify-center text-muted-foreground">
          <Loader2 className="animate-spin" /> Loading listings…
        </div>
      ) : !hasData ? (
        <div className="flex h-24 items-center justify-center text-muted-foreground">
          No listings found.
        </div>
      ) : (
        <>
          {listingsPage && listingsPage.total_pages > 1 && (
            <div className="flex items-center justify-between border-b p-3">
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
                  Page {query.page} of {listingsPage.total_pages}
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
                  label="Seller"
                  field="seller_name"
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
                <SortableHead
                  label="Change"
                  field="price_change"
                  currentField={query.sort_field}
                  sortOrder={query.sort_order}
                  onSort={toggleSort}
                />
                <SortableHead
                  label="Condition"
                  field="condition"
                  currentField={query.sort_field}
                  sortOrder={query.sort_order}
                  onSort={toggleSort}
                />
                <TableHead>Category</TableHead>
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
                  label="Created"
                  field="first_seen_at"
                  currentField={query.sort_field}
                  sortOrder={query.sort_order}
                  onSort={toggleSort}
                />
                <SortableHead
                  label="Age"
                  field="first_seen_at"
                  currentField={query.sort_field}
                  sortOrder={query.sort_order}
                  onSort={toggleSort}
                />
              </TableRow>
            </TableHeader>

            <TableBody>
              {listingsPage.items.map((listing) => (
                <ListingRow
                  key={listing.id}
                  listing={listing}
                  conditions={conditions}
                  platforms={platforms}
                  sources={sources}
                  categories={categories}
                />
              ))}
            </TableBody>
          </Table>
        </>
      )}

      {listingsPage && listingsPage.total_pages > 1 && (
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
              Page {query.page} of {listingsPage.total_pages}
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