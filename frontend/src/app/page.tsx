"use client";

import { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  RuntimeStatusResponse,
  CronJobEntry,
  CronCommandResponse,
  CategoryResponse,
  ConditionResponse,
  SourceResponse,
  ListingsQuery,
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
  listConditions,
  listSources,
} from "@/lib/endpoints";

export default function VintedControlCenter() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const queryClient = useQueryClient();

  const { data: stats, isLoading: statsLoading } = useQuery<StatsResponse>({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });

  const { data: configs = [], isLoading: configsLoading } = useQuery<ScrapeConfigResponse[]>({
    queryKey: ["configs"],
    queryFn: listScrapeConfigs,
  });

  const { data: cronJobs = [], isLoading: cronLoading, error: cronError } = useQuery<CronJobEntry[]>({
    queryKey: ["cronJobs"],
    queryFn: async () => {
      const res = await listCronJobs();
      return res.jobs ?? [];
    },
  });

  const { data: categories = [] } = useQuery<CategoryResponse[]>({
    queryKey: ["categories"],
    queryFn: listCategories,
  });

  const { data: platforms = [] } = useQuery<CategoryResponse[]>({
    queryKey: ["platforms"],
    queryFn: listPlatforms,
  });

  const { data: conditions = [] } = useQuery<ConditionResponse[]>({
    queryKey: ["conditions"],
    queryFn: listConditions,
  });

  const { data: sources = [] } = useQuery<SourceResponse[]>({
    queryKey: ["sources"],
    queryFn: listSources,
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



  const [listingsQuery, setListingsQuery] = useState<ListingsQuery>({
    page: 1,
    page_size: 15,
    sort_field: "last_seen_at",
    sort_order: "desc",
  });

  const { data: listingsPage, isLoading: listingsLoading } = useQuery<ListingsPage>({
    queryKey: ["listings", listingsQuery],
    queryFn: () => fetchListings(listingsQuery),
    keepPreviousData: true,
  });

  useEffect(() => {
    if (listingsPage?.has_next) {
      const nextQuery = { ...listingsQuery, page: listingsQuery.page + 1 };
      queryClient.prefetchQuery({
        queryKey: ["listings", nextQuery],
        queryFn: () => fetchListings(nextQuery),
      });
    }
  }, [listingsPage, listingsQuery, queryClient]);

  const handleListingsQueryChange = (query: Partial<ListingsQuery>) => {
    setListingsQuery((prev) => ({ ...prev, ...query }));
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
          />
        </TabsContent>

        <TabsContent value="listings">
          <ListingsSection
            platforms={platforms}
            conditions={conditions}
            sources={sources}
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
            onEdit={setSelectedConfig}
            onRun={(config) => runConfig(config.id)}
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
        categories={categories}
        platforms={platforms}
      />
    </main>
  );
}
