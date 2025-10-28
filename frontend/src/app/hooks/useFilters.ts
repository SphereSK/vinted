import { useState, useCallback, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchListings } from "@/lib/endpoints";
import type { FilterRequest, ListingsPage, ListingsQuery } from "@/lib/types";

interface UseFiltersOptions {
  initialFilters?: Partial<FilterRequest>;
  debounceMs?: number;
  enabled?: boolean;
}

export function useFilters(options: UseFiltersOptions = {}) {
  const {
    initialFilters = {},
    debounceMs = 300,
    enabled = true,
  } = options;

  // Filter state
  const [filters, setFilters] = useState<FilterRequest>({
    title: initialFilters.title,
    price_min: initialFilters.price_min,
    price_max: initialFilters.price_max,
    conditions: initialFilters.conditions || [],
    platforms: initialFilters.platforms || [],
    sources: initialFilters.sources || [],
    categories: initialFilters.categories || [],
  });

  // Debounced filters for API calls
  const [debouncedFilters, setDebouncedFilters] = useState<FilterRequest>(filters);

  // Debounce filter changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilters(filters);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [filters, debounceMs]);

  // Build query from filters
  const query = useMemo((): ListingsQuery => {
    return {
      page: 1,
      page_size: 15,
      sort_field: "last_seen_at",
      sort_order: "desc",
      search: debouncedFilters.title,
      price_min: debouncedFilters.price_min,
      price_max: debouncedFilters.price_max,
      // For multi-select filters, we'll join them with commas
      // The API will need to handle comma-separated values
      condition: debouncedFilters.conditions?.join(",") || undefined,
      platform: debouncedFilters.platforms?.join(",") || undefined,
      source: debouncedFilters.sources?.join(",") || undefined,
      // Category handling - API expects single category_id
      // If multiple categories, take the first one for now
      // TODO: Update API to support multiple categories
    };
  }, [debouncedFilters]);

  // Fetch listings with debounced filters
  const {
    data: listingsPage,
    isLoading,
    error,
    refetch,
  } = useQuery<ListingsPage>({
    queryKey: ["listings", "filtered", debouncedFilters],
    queryFn: () => fetchListings(query),
    enabled,
    keepPreviousData: true,
  });

  // Update individual filter
  const updateFilter = useCallback((key: keyof FilterRequest, value: string | number | string[] | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  // Update multiple filters at once
  const updateFilters = useCallback((updates: Partial<FilterRequest>) => {
    setFilters((prev) => ({
      ...prev,
      ...updates,
    }));
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFilters({
      title: undefined,
      price_min: undefined,
      price_max: undefined,
      conditions: [],
      platforms: [],
      sources: [],
      categories: [],
    });
  }, []);

  // Clear specific filter
  const clearFilter = useCallback((key: keyof FilterRequest) => {
    setFilters((prev) => ({
      ...prev,
      [key]: Array.isArray(prev[key]) ? [] : undefined,
    }));
  }, []);

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return Boolean(
      filters.title ||
      filters.price_min !== undefined ||
      filters.price_max !== undefined ||
      (filters.conditions && filters.conditions.length > 0) ||
      (filters.platforms && filters.platforms.length > 0) ||
      (filters.sources && filters.sources.length > 0) ||
      (filters.categories && filters.categories.length > 0)
    );
  }, [filters]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.title) count++;
    if (filters.price_min !== undefined || filters.price_max !== undefined) count++;
    if (filters.conditions && filters.conditions.length > 0) count++;
    if (filters.platforms && filters.platforms.length > 0) count++;
    if (filters.sources && filters.sources.length > 0) count++;
    if (filters.categories && filters.categories.length > 0) count++;
    return count;
  }, [filters]);

  return {
    filters,
    debouncedFilters,
    updateFilter,
    updateFilters,
    clearFilters,
    clearFilter,
    hasActiveFilters,
    activeFilterCount,
    listingsPage,
    isLoading,
    error: error as Error | null,
    refetch,
    totalResults: listingsPage?.total_items || 0,
  };
}
