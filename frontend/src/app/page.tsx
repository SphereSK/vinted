"use client";

import { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, useRouter } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { RefreshCcw, Plus, Loader2 } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { toast } from "sonner";

// Sections
import { DashboardSection } from "./components/dashboard/DashboardSection";
import { ListingsSection } from "./components/listings/ListingsSection";
import { ConfigsSection } from "./components/configs/ConfigsSection";
import { CronSection } from "./components/cron/CronSection";

// Components
import { ConfigDialog } from "./components/configs/ConfigDialog";

// Types and API
import type {
  StatsResponse,
  ListingsPage,
  ScrapeConfigResponse,
  ScrapeConfigWritePayload,
  RuntimeStatusResponse,
  CronJobEntry,
  CronCommandResponse,
  CategoryResponse,
  ConditionResponse,
  SourceResponse,
  ListingsQuery,
  ListingsByPeriodResponse,
  FilterOptionsResponse,
} from "@/lib/types";
import {
  loadListingsToCache,
  listCronJobs,
  listScrapeConfigs,
  listCategories,
  listPlatforms,
  fetchStats,
  syncCron,
  fetchListings,
  runScrapeConfig,
  createScrapeConfig,
  updateScrapeConfig,
  listConditions,
  listSources,
  fetchListingsByPeriod,
  fetchFilterOptions,
} from "@/lib/endpoints";

export default function VintedControlCenter() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedPeriod, setSelectedPeriod] = useState<"daily" | "weekly" | "monthly">("daily");

  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Initialize query from URL params
  const initializeQueryFromURL = (): ListingsQuery => {
    const params = new URLSearchParams(searchParams.toString());
    return {
      page: parseInt(params.get("page") || "1", 10),
      page_size: parseInt(params.get("page_size") || "15", 10),
      sort_field: (params.get("sort_field") || "last_seen_at") as string,
      sort_order: (params.get("sort_order") || "desc") as "asc" | "desc",
      search: params.get("search") || undefined,
      price_min: params.get("price_min") ? Number(params.get("price_min")) : undefined,
      price_max: params.get("price_max") ? Number(params.get("price_max")) : undefined,
      condition_id: params.get("condition_id") ? Number(params.get("condition_id")) : undefined,
      platform_id: params.get("platform_id") ? Number(params.get("platform_id")) : undefined,
      source_id: params.get("source_id") ? Number(params.get("source_id")) : undefined,
      category_id: params.get("category_id") ? Number(params.get("category_id")) : undefined,
      currency: params.get("currency") || undefined,
      is_sold: params.get("is_sold") ? params.get("is_sold") === "true" : undefined,
    };
  };

  const { data: stats, isLoading: statsLoading } = useQuery<StatsResponse>({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });

  const { data: configs = [], isLoading: configsLoading } = useQuery<ScrapeConfigResponse[]>({
    queryKey: ["configs"],
    queryFn: () => listScrapeConfigs(undefined),
  });

  const { data: cronJobs = [], isLoading: cronLoading, error: cronError } = useQuery<CronJobEntry[]>({
    queryKey: ["cronJobs"],
    queryFn: async () => {
      const res = await listCronJobs();
      return res.jobs ?? [];
    },
  });

  // Fetch all categories/platforms for ConfigDialog (includes inactive)
  const { data: allCategories = [] } = useQuery<CategoryResponse[]>({
    queryKey: ["categories"],
    queryFn: listCategories,
  });

  const { data: allPlatforms = [] } = useQuery<CategoryResponse[]>({
    queryKey: ["platforms"],
    queryFn: listPlatforms,
  });

  // Fetch filter options based on active listings only
  const { data: filterOptions } = useQuery<FilterOptionsResponse>({
    queryKey: ["filterOptions"],
    queryFn: fetchFilterOptions,
  });

  const { data: listingsByPeriod, isLoading: listingsByPeriodLoading } = useQuery<ListingsByPeriodResponse>({
    queryKey: ["listingsByPeriod", selectedPeriod],
    queryFn: () => fetchListingsByPeriod(selectedPeriod),
  });

  const { mutate: runConfig } = useMutation({
    mutationFn: runScrapeConfig,
    onSuccess: (data, variables) => {
      toast.success(`Scrape queued for config #${variables}`);
      queryClient.invalidateQueries({ queryKey: ["configs"] });
    },
    onError: (error) => {
      toast.error("Failed to queue scrape", { description: error.message });
    },
  });

  const { mutate: syncCronJobs, isLoading: isSyncingCron } = useMutation({
    mutationFn: syncCron,
    onSuccess: (data) => {
      toast.success(data.message ?? "Crontab synced successfully");
      queryClient.invalidateQueries({ queryKey: ["cronJobs"] });
    },
    onError: (error) => {
      toast.error("Failed to sync cron", { description: error.message });
    },
  });

  const { mutate: reloadCache, isLoading: isReloadingCache } = useMutation({
    mutationFn: loadListingsToCache,
    onSuccess: () => {
      toast.success("Listings cache reloaded");
      queryClient.invalidateQueries({ queryKey: ["listings"] });
    },
    onError: (error) => {
      toast.error("Failed to reload listings cache", { description: error.message });
    },
  });

  const [isConfigDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<ScrapeConfigResponse | null>(null);

  const handleRefreshAll = () => {
    queryClient.invalidateQueries();
  };

  const [listingsQuery, setListingsQuery] = useState<ListingsQuery>(() => initializeQueryFromURL());

  // Sync URL with query changes
  useEffect(() => {
    const params = new URLSearchParams();

    // Add all non-empty query params to URL
    if (listingsQuery.page > 1) params.set("page", listingsQuery.page.toString());
    if (listingsQuery.page_size !== 15) params.set("page_size", listingsQuery.page_size.toString());
    if (listingsQuery.sort_field !== "last_seen_at") params.set("sort_field", listingsQuery.sort_field);
    if (listingsQuery.sort_order !== "desc") params.set("sort_order", listingsQuery.sort_order);
    if (listingsQuery.search) params.set("search", listingsQuery.search);
    if (listingsQuery.price_min !== undefined) params.set("price_min", listingsQuery.price_min.toString());
    if (listingsQuery.price_max !== undefined) params.set("price_max", listingsQuery.price_max.toString());
    if (listingsQuery.condition_id !== undefined) params.set("condition_id", listingsQuery.condition_id.toString());
    if (listingsQuery.platform_id !== undefined) params.set("platform_id", listingsQuery.platform_id.toString());
    if (listingsQuery.source_id !== undefined) params.set("source_id", listingsQuery.source_id.toString());
    if (listingsQuery.category_id !== undefined) params.set("category_id", listingsQuery.category_id.toString());
    if (listingsQuery.currency) params.set("currency", listingsQuery.currency);
    if (listingsQuery.is_sold !== undefined) params.set("is_sold", listingsQuery.is_sold.toString());

    const newURL = params.toString() ? `?${params.toString()}` : window.location.pathname;
    router.replace(newURL, { scroll: false });
  }, [listingsQuery, router]);

  const { data: listingsPage, isLoading: listingsLoading } = useQuery<ListingsPage>({
    queryKey: ["listings", listingsQuery],
    queryFn: () => fetchListings(listingsQuery),
    keepPreviousData: true,
  });

  const handleListingsQueryChange = (query: Partial<ListingsQuery>) => {
    setListingsQuery((prev) => ({ ...prev, ...query }));
  };

  const handleEditConfig = (config: ScrapeConfigResponse) => {
    setSelectedConfig(config);
    setConfigDialogOpen(true);
  };

  const handleCopyConfig = (config: ScrapeConfigResponse) => {
    // Create a copy with only the fields that are valid for creation
    // Exclude: id, url, created_at, last_run_at, last_run_status, last_run_items, last_health_status, last_health_check_at
    const copiedConfig: Partial<ScrapeConfigResponse> = {
      name: `Copy of ${config.name}`,
      search_text: config.search_text,
      categories: config.categories,
      platform_ids: config.platform_ids,
      order: config.order,
      extra_filters: config.extra_filters,
      locales: config.locales,
      extra_args: config.extra_args,
      max_pages: config.max_pages,
      per_page: config.per_page,
      delay: config.delay,
      fetch_details: config.fetch_details,
      details_for_new_only: config.details_for_new_only,
      use_proxy: config.use_proxy,
      error_wait_minutes: config.error_wait_minutes,
      max_retries: config.max_retries,
      base_url: config.base_url,
      details_strategy: config.details_strategy,
      details_concurrency: config.details_concurrency,
      cron_schedule: config.cron_schedule,
      is_active: config.is_active,
      healthcheck_ping_url: config.healthcheck_ping_url,
    };
    setSelectedConfig(copiedConfig as ScrapeConfigResponse);
    setConfigDialogOpen(true);
  };

  const handleSaveConfig = async (payload: ScrapeConfigWritePayload) => {
    try {
      if (selectedConfig?.id) {
        // Update existing config
        await updateScrapeConfig(selectedConfig.id, payload);
        toast.success("Configuration updated successfully");
      } else {
        // Create new config
        await createScrapeConfig(payload);
        toast.success("Configuration created successfully");
      }
      // Refresh configs list
      queryClient.invalidateQueries({ queryKey: ["configs"] });
      setConfigDialogOpen(false);
    } catch (error) {
      console.error("Failed to save config:", error);
      toast.error("Failed to save configuration", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
      throw error; // Re-throw to let ConfigDialog handle it
    }
  };

  const handleToggleActive = async (config: ScrapeConfigResponse, newActiveState: boolean) => {
    try {
      await updateScrapeConfig(config.id, { is_active: newActiveState });
      toast.success(
        newActiveState
          ? `Configuration "${config.name}" enabled`
          : `Configuration "${config.name}" disabled`
      );
      queryClient.invalidateQueries({ queryKey: ["configs"] });
    } catch (error) {
      console.error("Failed to toggle config:", error);
      toast.error("Failed to update configuration", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    }
  };

  return (
    <main className="mx-auto flex w-full flex-col gap-6 p-6">
      <header className="flex flex-col gap-2 border-b pb-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Vinted Control Center</h1>
          <p className="text-sm text-muted-foreground">
            Monitor scrape performance, manage configurations, and track cron schedules.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshAll}
            disabled={isReloadingCache}
          >
            {isReloadingCache ? <Loader2 className="animate-spin" /> : <RefreshCcw className="size-4" />}
            Refresh
          </Button>
          <Button size="sm" onClick={() => setConfigDialogOpen(true)}>
            <Plus className="size-4" /> New config
          </Button>
        </div>
      </header>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="listings">Listings</TabsTrigger>
          <TabsTrigger value="configs">Configs</TabsTrigger>
          <TabsTrigger value="cron">Cron jobs</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <DashboardSection
            stats={stats}
            statsLoading={statsLoading}
            configs={configs}
            cronJobs={cronJobs}
            cronError={cronError as Error | null}
            cronLoading={cronLoading}
            listingsByPeriod={listingsByPeriod?.items ?? []}
            listingsByPeriodLoading={listingsByPeriodLoading}
            selectedPeriod={selectedPeriod}
            setSelectedPeriod={setSelectedPeriod}
          />
        </TabsContent>

        <TabsContent value="listings">
          <ListingsSection
            platforms={filterOptions?.platforms ?? []}
            conditions={filterOptions?.conditions ?? []}
            sources={filterOptions?.sources ?? []}
            categories={filterOptions?.categories ?? []}
            availableCurrencies={filterOptions?.currencies ?? []}
            soldStatuses={filterOptions?.sold_statuses ?? []}
            priceMin={filterOptions?.price_min ?? null}
            priceMax={filterOptions?.price_max ?? null}
            listingsPage={listingsPage}
            isLoading={listingsLoading}
            onQueryChange={handleListingsQueryChange}
            query={listingsQuery}
            queryClient={queryClient}
          />
        </TabsContent>

        <TabsContent value="configs">
          <ConfigsSection
            configs={configs}
            statuses={{}}
            onEdit={handleEditConfig}
            onCopy={handleCopyConfig}
            onRun={(config) => runConfig(config.id)}
            onToggleActive={handleToggleActive}
          />
        </TabsContent>

        <TabsContent value="cron">
          <CronSection
            jobs={cronJobs}
            configs={configs}
            loading={cronLoading}
            syncing={isSyncingCron}
            error={cronError as Error | null}
            onReload={() => queryClient.invalidateQueries({ queryKey: ["cronJobs"] })}
            onSync={syncCronJobs}
          />
        </TabsContent>
      </Tabs>

      <ConfigDialog
        open={isConfigDialogOpen}
        onOpenChange={setConfigDialogOpen}
        config={selectedConfig}
        categories={allCategories}
        platforms={allPlatforms}
        onSave={handleSaveConfig}
      />
    </main>
  );
}
