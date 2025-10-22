"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronsUpDown,
  Copy,
  Loader2,
  Pencil,
  Play,
  Plus,
  Repeat,
  RefreshCcw,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogClose,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { cn } from "@/lib/utils";
import { formatCurrency, formatDate } from "@/lib/format";
import {
  createScrapeConfig,
  deleteScrapeConfig,
  fetchListings,
  fetchStats,
  getScrapeConfigStatus,
  listCronJobs,
  buildCronCommand,
  listScrapeConfigs,
  runScrapeConfig,
  updateScrapeConfig,
  listCategories,
  listPlatforms,
  syncCron,
} from "@/lib/endpoints";
import { appConfig } from "@/lib/config";
import type {
  CategoryResponse,
  CronJobEntry,
  ListingResponse,
  ListingsPage,
  RuntimeStatusResponse,
  ScrapeConfigResponse,
  ScrapeConfigWritePayload,
  StatsResponse,
  CronCommandResponse,
} from "@/lib/types";

const DEFAULT_PAGE_SIZE = 15;
const PAGE_SIZE_OPTIONS = [15, 30, 50, 100] as const;
const DEFAULT_FORM: ConfigFormState = {
  id: undefined,
  name: "",
  search_text: "",
  categories: "",
  platform_ids: "",
  order: "",
  extra_filters: "",
  locales: "",
  extra_args: "",
  max_pages: 5,
  per_page: 24,
  delay: 1,
  fetch_details: false,
  details_for_new_only: false,
  use_proxy: true,
  error_wait_minutes: 30,
  max_retries: 3,
  base_url: "",
  details_strategy: "browser",
  details_concurrency: 2,
  cron_schedule: "",
  is_active: true,
  healthcheck_ping_url: "",
};

const ORDER_OPTIONS = [
  { value: "newest_first", label: "Newest first" },
  { value: "price_low_to_high", label: "Price low -> high" },
  { value: "price_high_to_low", label: "Price high -> low" },
] as const;

const DETAIL_STRATEGY_OPTIONS = [
  { value: "browser" as const, label: "Browser (Chromium)" },
  { value: "http" as const, label: "HTTP requests" },
];

const CRON_PRESETS = [
  { value: "0 * * * *", label: "Hourly" },
  { value: "0 */6 * * *", label: "Every 6 hours" },
  { value: "0 0 * * *", label: "Daily at midnight" },
  { value: "0 9 * * *", label: "Daily at 09:00" },
  { value: "0 18 * * 1-5", label: "Weekdays at 18:00" },
  { value: "*/30 * * * *", label: "Every 30 minutes" },
];

type TabValue = "dashboard" | "listings" | "configs" | "cron";

interface ConfigFormState {
  id: number | undefined;
  name: string;
  search_text: string;
  categories: string;
  platform_ids: string;
  order: string;
  extra_filters: string;
  locales: string;
  extra_args: string;
  max_pages: number;
  per_page: number;
  delay: number;
  fetch_details: boolean;
  details_for_new_only: boolean;
  use_proxy: boolean;
  error_wait_minutes: number;
  max_retries: number;
  base_url: string;
  details_strategy: "browser" | "http";
  details_concurrency: number;
  cron_schedule: string;
  is_active: boolean;
  healthcheck_ping_url: string;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabValue>("dashboard");
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const [listingPage, setListingPage] = useState<ListingsPage>({
    items: [],
    total: 0,
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    has_next: false,
    available_currencies: [],
  });
  const [listingPageNumber, setListingPageNumber] = useState(1);
  const [listingPageSize, setListingPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [listingActiveOnly, setListingActiveOnly] = useState(true);
  const [listingSortField, setListingSortField] = useState<"last_seen_at" | "first_seen_at" | "price" | "title">("last_seen_at");
  const [listingSortOrder, setListingSortOrder] = useState<"asc" | "desc">("desc");
  const [listingCurrency, setListingCurrency] = useState("");
  const [listingsLoading, setListingsLoading] = useState(true);
  const [listingsError, setListingsError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  const [configs, setConfigs] = useState<ScrapeConfigResponse[]>([]);
  const [configStatuses, setConfigStatuses] = useState<
    Record<number, RuntimeStatusResponse | null>
  >({});
  const [cronJobs, setCronJobs] = useState<CronJobEntry[]>([]);
  const [cronLoading, setCronLoading] = useState(true);
  const [cronError, setCronError] = useState<string | null>(null);
  const [cronSyncing, setCronSyncing] = useState(false);
  const [categories, setCategories] = useState<CategoryResponse[]>([]);
  const [platforms, setPlatforms] = useState<CategoryResponse[]>([]);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isConfigDialogOpen, setConfigDialogOpen] = useState(false);
  const [isSavingConfig, setSavingConfig] = useState(false);
  const [configForm, setConfigForm] = useState<ConfigFormState>(DEFAULT_FORM);
  const [cronPreview, setCronPreview] = useState<CronCommandResponse | null>(null);
  const [cronPreviewLoading, setCronPreviewLoading] = useState(false);
  const [cronPreviewError, setCronPreviewError] = useState<string | null>(null);

  function resetCronPreview() {
    setCronPreview(null);
    setCronPreviewError(null);
    setCronPreviewLoading(false);
  }

  function handleFormUpdate(updated: ConfigFormState) {
    setConfigForm(updated);
    setCronPreview(null);
    setCronPreviewError(null);
    setCronPreviewLoading(false);
  }

  function handleConfigDialogOpenChange(open: boolean) {
    setConfigDialogOpen(open);
    if (!open) {
      resetCronPreview();
      setConfigForm(DEFAULT_FORM);
      setSavingConfig(false);
    }
  }

  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedSearch(searchTerm.trim());
    }, 400);
    return () => clearTimeout(timeout);
  }, [searchTerm]);

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setListingPageNumber(1);
    void loadListings(
      1,
      listingPageSize,
      listingActiveOnly,
      listingSortField,
      listingSortOrder,
      listingCurrency,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  useEffect(() => {
    if (!configs.length) return;

    const interval = setInterval(() => {
      refreshStatuses(configs.map((cfg) => cfg.id)).catch((error) => {
        console.warn("Status polling failed", error);
      });
    }, appConfig.statusPollInterval);

    return () => clearInterval(interval);
  }, [configs]);

  async function refreshAll() {
    setIsRefreshing(true);
    try {
      await Promise.all([
        loadStats(),
        loadListings(listingPageNumber, listingPageSize, listingActiveOnly),
        loadConfigs(),
        loadCronJobs(),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  }

  async function loadStats() {
    setStatsLoading(true);
    try {
      const data = await fetchStats();
      setStats(data);
    } catch (error) {
      toast.error("Failed to load dashboard stats");
      console.error(error);
    } finally {
      setStatsLoading(false);
    }
  }

  async function loadListings(
    pageArg = listingPageNumber,
    pageSizeArg = listingPageSize,
    activeOnlyArg = listingActiveOnly,
    sortFieldArg = listingSortField,
    sortOrderArg = listingSortOrder,
    currencyArg = listingCurrency,
  ) {
    setListingsLoading(true);
    setListingsError(null);
    try {
      const data = await fetchListings({
        page: pageArg,
        page_size: pageSizeArg,
        search: debouncedSearch || undefined,
        active_only: activeOnlyArg,
        sort_field: sortFieldArg,
        sort_order: sortOrderArg,
        currency: currencyArg || undefined,
      });
      setListingPage(data);
      setListingPageNumber(data.page);
      setListingPageSize(data.page_size);
      setListingActiveOnly(activeOnlyArg);
      setListingSortField(sortFieldArg);
      setListingSortOrder(sortOrderArg);
      setListingCurrency(currencyArg);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown error occurred";
      setListingsError(message);
      toast.error("Unable to load listings", {
        description: message,
      });
    } finally {
      setListingsLoading(false);
    }
  }

  function handleListingsPageChange(nextPage: number) {
    const target = Math.max(1, nextPage);
    setListingPageNumber(target);
    void loadListings(
      target,
      listingPageSize,
      listingActiveOnly,
      listingSortField,
      listingSortOrder,
      listingCurrency,
    );
  }

  function handleListingsPageSizeChange(size: number) {
    const normalized = Math.max(1, size);
    setListingPageSize(normalized);
    setListingPageNumber(1);
    void loadListings(
      1,
      normalized,
      listingActiveOnly,
      listingSortField,
      listingSortOrder,
      listingCurrency,
    );
  }

  function handleListingActiveToggle(value: boolean) {
    setListingActiveOnly(value);
    setListingPageNumber(1);
    void loadListings(
      1,
      listingPageSize,
      value,
      listingSortField,
      listingSortOrder,
      listingCurrency,
    );
  }

  function handleListingsSortChange(field: "last_seen_at" | "first_seen_at" | "price" | "title") {
    const nextOrder: "asc" | "desc" =
      listingSortField === field && listingSortOrder === "desc" ? "asc" : "desc";
    setListingSortField(field);
    setListingSortOrder(nextOrder);
    setListingPageNumber(1);
    void loadListings(1, listingPageSize, listingActiveOnly, field, nextOrder, listingCurrency);
  }

  function handleListingsCurrencyChange(value: string) {
    const normalized = value === "ALL" ? "" : value;
    setListingCurrency(normalized);
    setListingPageNumber(1);
    void loadListings(
      1,
      listingPageSize,
      listingActiveOnly,
      listingSortField,
      listingSortOrder,
      normalized,
    );
  }

  async function loadConfigs() {
    try {
      const [configsData, categoriesData, platformsData] = await Promise.all([
        listScrapeConfigs(),
        listCategories(),
        listPlatforms(),
      ]);
      setConfigs(configsData);
      setCategories(categoriesData);
      setPlatforms(platformsData);

      await refreshStatuses(configsData.map((cfg) => cfg.id));
    } catch (error) {
      console.warn("Failed to load config metadata", error);
    }
  }

  async function loadCronJobs(showToast = false) {
    setCronLoading(true);
    setCronError(null);
    try {
      const data = await listCronJobs();
      const jobs = Array.isArray(data.jobs) ? data.jobs : [];
      setCronJobs(jobs);
      if (showToast) {
        toast.success(
          `Loaded ${jobs.length} cron job${jobs.length === 1 ? "" : "s"}`,
        );
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to load cron jobs";
      setCronError(message);
      if (showToast) {
        toast.error("Failed to load cron jobs", { description: message });
      }
      console.warn("Failed to load cron jobs", error);
    } finally {
      setCronLoading(false);
    }
  }

  async function handleSyncCron() {
    if (cronSyncing) return;
    setCronSyncing(true);
    try {
      const response = await syncCron();
      toast.success(response.message ?? "Crontab synced successfully");
      await loadCronJobs();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to sync cron jobs";
      setCronError(message);
      toast.error("Failed to sync cron jobs", { description: message });
      console.warn("Failed to sync cron jobs", error);
    } finally {
      setCronSyncing(false);
    }
  }

  async function refreshStatuses(configIds: number[]) {
    const results = await Promise.all(
      configIds.map(async (id) => {
        try {
          const status = await getScrapeConfigStatus(id);
          return [id, status] as const;
        } catch (error) {
          console.warn(`Failed to fetch status for config ${id}`, error);
          return [id, null] as const;
        }
      }),
    );

    setConfigStatuses((prev) => {
      const next = { ...prev };
      results.forEach(([id, status]) => {
        next[id] = status;
      });
      return next;
    });
  }

  async function handleRun(config: ScrapeConfigResponse) {
    try {
      await runScrapeConfig(config.id);
      toast.success(`Scrape queued for "${config.name}"`);
      await refreshStatuses([config.id]);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to start scrape";
      toast.error("Failed to queue scrape", { description: message });
    }
  }

  async function handlePreviewCron() {
    if (cronPreviewLoading) return;
    setCronPreviewLoading(true);
    setCronPreviewError(null);
    setCronPreview(null);

    try {
      const payload = buildConfigPayload(configForm);

      if (!payload.name) {
        throw new Error("Name is required before previewing the cron command.");
      }

      if (!payload.search_text) {
        throw new Error("Search text is required before previewing the cron command.");
      }

      const cronPayload = {
        schedule: configForm.cron_schedule.trim() || null,
        search_text: payload.search_text,
        categories: payload.categories,
        platform_ids: payload.platform_ids,
        order: payload.order,
        extra_filters: payload.extra_filters,
        locales: payload.locales,
        extra_args: payload.extra_args,
        max_pages: payload.max_pages,
        per_page: payload.per_page,
        delay: payload.delay,
        fetch_details: payload.fetch_details,
        details_for_new_only: payload.details_for_new_only,
        use_proxy: payload.use_proxy,
        error_wait_minutes: payload.error_wait_minutes,
        max_retries: payload.max_retries,
        base_url: payload.base_url,
        details_strategy: payload.details_strategy,
        details_concurrency: payload.details_concurrency,
        healthcheck_ping_url: payload.healthcheck_ping_url,
      };

      const previewResponse = await buildCronCommand(cronPayload);
      setCronPreview(previewResponse);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to build cron command";
      setCronPreviewError(message);
      toast.error("Failed to build cron command", { description: message });
    } finally {
      setCronPreviewLoading(false);
    }
  }

  async function handleDelete(config: ScrapeConfigResponse) {
    if (
      !window.confirm(
        `Delete configuration "${config.name}"? This cannot be undone.`,
      )
    ) {
      return;
    }

    try {
      await deleteScrapeConfig(config.id);
      toast.success(`Deleted "${config.name}"`);
      await loadConfigs();
      await loadCronJobs();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to delete config";
      toast.error("Failed to delete configuration", { description: message });
    }
  }

  function openCreateDialog() {
    resetCronPreview();
    setConfigForm(DEFAULT_FORM);
    handleConfigDialogOpenChange(true);
  }

  function openEditDialog(config: ScrapeConfigResponse) {
    resetCronPreview();
    setConfigForm({
      id: config.id,
      name: config.name,
      search_text: config.search_text,
      categories: formatIdList(config.categories),
      platform_ids: formatIdList(config.platform_ids),
      order: config.order ?? "",
      extra_filters: formatStringList(config.extra_filters ?? config.extra ?? null, "\n"),
      locales: formatStringList(config.locales ?? null),
      extra_args: formatStringList(config.extra_args ?? null, "\n"),
      max_pages: config.max_pages,
      per_page: config.per_page,
      delay: Number(config.delay ?? 1),
      fetch_details: !!config.fetch_details,
      details_for_new_only: !!config.details_for_new_only,
      use_proxy: config.use_proxy ?? true,
      error_wait_minutes: config.error_wait_minutes ?? 30,
      max_retries: config.max_retries ?? 3,
      base_url: config.base_url ?? "",
      details_strategy: (config.details_strategy ?? "browser") as "browser" | "http",
      details_concurrency: config.details_concurrency ?? 2,
      cron_schedule: config.cron_schedule ?? "",
      is_active: config.is_active ?? true,
      healthcheck_ping_url: config.healthcheck_ping_url ?? "",
    });
    handleConfigDialogOpenChange(true);
  }

  async function handleSaveConfig(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingConfig(true);

    try {
      const payload = buildConfigPayload(configForm);

      if (!payload.name) {
        throw new Error("Configuration name is required.");
      }

      if (!payload.search_text) {
        throw new Error("Search text is required.");
      }

      if (configForm.id) {
        await updateScrapeConfig(configForm.id, payload);
        toast.success(`Updated "${payload.name}"`);
      } else {
        await createScrapeConfig(payload);
        toast.success(`Created "${payload.name}"`);
      }

      handleConfigDialogOpenChange(false);
      await loadConfigs();
      await loadCronJobs();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to save configuration";
      toast.error("Failed to save configuration", { description: message });
    } finally {
      setSavingConfig(false);
    }
  }

  const priceChangeSummary = useMemo(() => {
    const summary = { up: 0, down: 0, same: 0 };
    listingPage.items.forEach((listing) => {
      if (!listing.price_change) return;
      if (listing.price_change === "up") summary.up += 1;
      if (listing.price_change === "down") summary.down += 1;
      if (listing.price_change === "same") summary.same += 1;
    });
    return summary;
  }, [listingPage.items]);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 p-6">
      <header className="flex flex-col gap-2 border-b pb-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Vinted Control Center
          </h1>
          <p className="text-sm text-muted-foreground">
            Monitor scrape performance, manage configurations, and track cron
            schedules.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button
            variant="outline"
            size="sm"
            onClick={refreshAll}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <Loader2 className="animate-spin" />
            ) : (
              <RefreshCcw className="size-4" />
            )}
            Refresh data
          </Button>
          <Button size="sm" onClick={openCreateDialog}>
            <Plus className="size-4" />
            New config
          </Button>
        </div>
      </header>

      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as TabValue)}>
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="listings">Listings</TabsTrigger>
          <TabsTrigger value="configs">Scrape configs</TabsTrigger>
          <TabsTrigger value="cron">Cron jobs</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="flex flex-col gap-6 pt-4">
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard
              title="Active listings"
              value={stats?.active_listings}
              loading={statsLoading}
            />
            <StatCard
              title="Total listings"
              value={stats?.total_listings}
              loading={statsLoading}
            />
            <StatCard
              title="Average price"
              value={
                stats?.avg_price_cents
                  ? formatCurrency(stats.avg_price_cents)
                  : null
              }
              loading={statsLoading}
            />
            <StatCard
              title="Configs"
              value={configs.length}
              loading={statsLoading}
              caption={
                cronError
                  ? "Cron jobs unavailable"
                  : !cronLoading
                    ? `${cronJobs.length} cron job${cronJobs.length === 1 ? "" : "s"}`
                    : undefined
              }
            />
          </section>

          <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
            <Card>
              <CardHeader>
                <CardTitle>Recent price movement</CardTitle>
                <CardDescription>
                  Overview for page {listingPage.page} showing {listingPage.items.length} {listingActiveOnly ? "active" : "recent"} listings (total {listingPage.total}).
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <TrendPill label="Price increase" value={priceChangeSummary.up} tone="up" />
                  <TrendPill label="Price decrease" value={priceChangeSummary.down} tone="down" />
                  <TrendPill label="Unchanged" value={priceChangeSummary.same} tone="neutral" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Active scrape configs</CardTitle>
                <CardDescription>
                  Quick glance at scheduled and manual configurations.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {configs.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No configurations found. Add one in the Scrape configs tab.
                  </p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {configs.slice(0, 4).map((config) => (
                      <li
                        key={config.id}
                        className="flex flex-col rounded-lg border p-3"
                      >
                        <span className="font-medium">{config.name}</span>
                        <span className="text-muted-foreground">
                          {config.search_text} ·{" "}
                          {config.cron_schedule ?? "manual"}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </section>
        </TabsContent>

        <TabsContent value="listings" className="flex flex-col gap-4 pt-4">
          <ListingsSection
            page={listingPage}
            loading={listingsLoading}
            error={listingsError}
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            onReload={() => {
              void loadListings();
            }}
            onPageChange={handleListingsPageChange}
            onPageSizeChange={handleListingsPageSizeChange}
            pageSizeOptions={PAGE_SIZE_OPTIONS}
            activeOnly={listingActiveOnly}
            onToggleActiveOnly={handleListingActiveToggle}
            sortField={listingSortField}
            sortOrder={listingSortOrder}
            onSortChange={handleListingsSortChange}
            currency={listingCurrency}
            onCurrencyChange={handleListingsCurrencyChange}
            availableCurrencies={listingPage.available_currencies}
          />
        </TabsContent>

        <TabsContent value="configs" className="flex flex-col gap-4 pt-4">
          <ConfigsSection
            configs={configs}
            statuses={configStatuses}
            onEdit={openEditDialog}
            onRun={handleRun}
            onDelete={handleDelete}
          />
        </TabsContent>
        <TabsContent value="cron" className="flex flex-col gap-4 pt-4">
          <CronSection
            jobs={cronJobs}
            configs={configs}
            loading={cronLoading}
            syncing={cronSyncing}
            error={cronError}
            onReload={() => {
              void loadCronJobs(true);
            }}
            onSync={() => {
              void handleSyncCron();
            }}
          />
        </TabsContent>
      </Tabs>

      <ConfigDialog
        open={isConfigDialogOpen}
        onOpenChange={handleConfigDialogOpenChange}
        form={configForm}
        onFormChange={handleFormUpdate}
        onSubmit={handleSaveConfig}
        onPreviewCron={handlePreviewCron}
        preview={cronPreview}
        previewLoading={cronPreviewLoading}
        previewError={cronPreviewError}
        isSaving={isSavingConfig}
        categories={categories}
        platforms={platforms}
      />
    </main>
  );
}

interface CronSectionProps {
  jobs: CronJobEntry[];
  configs: ScrapeConfigResponse[];
  loading: boolean;
  syncing: boolean;
  error: string | null;
  onReload: () => void | Promise<void>;
  onSync: () => void | Promise<void>;
}

function CronSection({
  jobs,
  configs,
  loading,
  syncing,
  error,
  onReload,
  onSync,
}: CronSectionProps) {
  const configLookup = useMemo(() => {
    const map = new Map<number, ScrapeConfigResponse>();
    configs.forEach((cfg) => {
      map.set(cfg.id, cfg);
    });
    return map;
  }, [configs]);

  async function handleCopy(command: string) {
    if (!command) return;
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      toast.error("Clipboard API not available in this environment.");
      return;
    }
    try {
      await navigator.clipboard.writeText(command);
      toast.success("Cron command copied to clipboard");
    } catch (copyError) {
      const message =
        copyError instanceof Error
          ? copyError.message
          : "Unable to access clipboard";
      toast.error("Failed to copy cron command", { description: message });
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <CardTitle>Cron scheduler</CardTitle>
          <CardDescription>
            View scheduled scrape jobs and keep the system crontab in sync.
          </CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            onClick={() => {
              void onSync();
            }}
            disabled={syncing}
          >
            {syncing ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Repeat className="size-4" />
            )}
            Sync cron
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              void onReload();
            }}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCcw className="size-4" />
            )}
            Refresh list
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center gap-2 py-10 text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading cron jobs…
          </div>
        ) : error ? (
          <p className="text-sm text-destructive">{error}</p>
        ) : jobs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No cron jobs configured yet. Use sync to pull active schedules.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[120px]">Schedule</TableHead>
                <TableHead>Configuration</TableHead>
                <TableHead>Command</TableHead>
                <TableHead className="w-[120px]">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job, index) => {
                const config =
                  job.config_id != null
                    ? configLookup.get(job.config_id)
                    : undefined;
                const configLabel = config
                  ? config.name
                  : job.config_id != null
                    ? `Config #${job.config_id}`
                    : "Manual entry";

                return (
                  <TableRow key={`${job.comment ?? job.command}-${index}`}>
                    <TableCell className="align-top font-mono text-xs">
                      {job.schedule}
                    </TableCell>
                    <TableCell className="align-top">
                      <div className="flex flex-col">
                        <span className="font-medium">{configLabel}</span>
                        {job.comment ? (
                          <span className="text-xs text-muted-foreground">
                            {job.comment}
                          </span>
                        ) : null}
                      </div>
                    </TableCell>
                    <TableCell className="align-top">
                      <div className="flex items-start gap-2">
                        <pre className="max-h-32 flex-1 overflow-auto rounded-md border bg-muted px-2 py-1 text-xs font-mono whitespace-pre-wrap">
                          {job.command}
                        </pre>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Copy cron command"
                          onClick={() => {
                            void handleCopy(job.command);
                          }}
                        >
                          <Copy className="size-4" />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell className="align-top">
                      <Badge
                        className={
                          job.enabled
                            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
                            : "bg-muted text-muted-foreground"
                        }
                      >
                        {job.enabled ? "Enabled" : "Disabled"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

interface ListingsSectionProps {
  page: ListingsPage;
  loading: boolean;
  error: string | null;
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onReload: () => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  pageSizeOptions: readonly number[];
  activeOnly: boolean;
  onToggleActiveOnly: (value: boolean) => void;
  sortField: "last_seen_at" | "first_seen_at" | "price" | "title";
  sortOrder: "asc" | "desc";
  onSortChange: (field: "last_seen_at" | "first_seen_at" | "price" | "title") => void;
  currency: string;
  onCurrencyChange: (currency: string) => void;
  availableCurrencies: string[];
}

function ListingsSection({
  page,
  loading,
  error,
  searchTerm,
  onSearchChange,
  onReload,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions,
  activeOnly,
  onToggleActiveOnly,
  sortField,
  sortOrder,
  onSortChange,
  currency,
  onCurrencyChange,
  availableCurrencies,
}: ListingsSectionProps) {
  const totalPages = Math.max(1, Math.ceil(page.total / Math.max(page.page_size, 1)));
  const startIndex = page.total === 0 ? 0 : (page.page - 1) * page.page_size + 1;
  const endIndex = startIndex === 0 ? 0 : startIndex + page.items.length - 1;

  const currencyOptions = availableCurrencies.length
    ? ["ALL", ...availableCurrencies]
    : ["ALL"];

  const renderSortIcon = (field: "last_seen_at" | "first_seen_at" | "price" | "title") => {
    if (sortField !== field) {
      return <ChevronsUpDown className="size-3 opacity-0 transition-opacity group-hover:opacity-70" />;
    }
    if (sortOrder === "asc") {
      return <ChevronUp className="size-3" />;
    }
    return <ChevronDown className="size-3" />;
  };

  const SortButton = ({
    field,
    label,
    className,
  }: {
    field: "last_seen_at" | "first_seen_at" | "price" | "title";
    label: string;
    className?: string;
  }) => (
    <button
      type="button"
      onClick={() => onSortChange(field)}
      className={cn(
        "group flex w-full items-center gap-1 text-left text-xs font-medium uppercase tracking-wide",
        sortField === field ? "text-foreground" : "text-muted-foreground",
        className,
      )}
    >
      <span>{label}</span>
      {renderSortIcon(field)}
    </button>
  );

  return (
    <>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex w-full max-w-xl items-center gap-3">
          <div className="relative w-full">
            <Search className="text-muted-foreground absolute left-3 top-1/2 size-4 -translate-y-1/2" />
            <Input
              value={searchTerm}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder="Search listings by title…"
              className="pl-9"
            />
          </div>
          <Button
            variant="outline"
            onClick={onReload}
            disabled={loading}
            className="whitespace-nowrap"
          >
            {loading ? (
              <Loader2 className="animate-spin" />
            ) : (
              <RefreshCcw className="size-4" />
            )}
            Refresh
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Switch
              id="active-only"
              checked={activeOnly}
              onCheckedChange={(checked) => onToggleActiveOnly(Boolean(checked))}
            />
            <Label htmlFor="active-only" className="text-sm">Active only</Label>
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="currency-filter" className="text-sm text-muted-foreground">
              Currency
            </Label>
            <Select
              value={currency || "ALL"}
              onValueChange={onCurrencyChange}
            >
              <SelectTrigger id="currency-filter" className="h-9 w-[110px]">
                <SelectValue placeholder="Currency" />
              </SelectTrigger>
              <SelectContent>
                {currencyOptions.map((value) => (
                  <SelectItem key={value} value={value}>
                    {value === "ALL" ? "All" : value.toUpperCase()}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="page-size" className="text-sm text-muted-foreground">
              Page size
            </Label>
            <Select
              value={String(page.page_size)}
              onValueChange={(value) => onPageSizeChange(Number(value))}
            >
              <SelectTrigger id="page-size" className="h-9 w-[90px]">
                <SelectValue placeholder="Page size" />
              </SelectTrigger>
              <SelectContent>
                {pageSizeOptions.map((size) => (
                  <SelectItem key={size} value={String(size)}>
                    {size}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => onPageChange(page.page - 1)}
              disabled={loading || page.page <= 1}
              aria-label="Previous page"
            >
              <ChevronLeft className="size-4" />
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page.page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => onPageChange(page.page + 1)}
              disabled={loading || !page.has_next}
              aria-label="Next page"
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      </div>

      <span className="text-sm text-muted-foreground">
        {page.total === 0
          ? "No listings to display."
          : `Showing ${startIndex}-${endIndex} of ${page.total} listings.`}
      </span>

      <Card>
        <CardHeader>
          <CardTitle>Latest listings</CardTitle>
          <CardDescription>
            Filter by title to track price movements across scrape runs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 py-12 text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Loading listings…
            </div>
          ) : error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : page.items.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No listings found for the current filters.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>
                    <SortButton field="title" label="Title" />
                  </TableHead>
                  <TableHead>
                    <SortButton field="price" label="Price" />
                  </TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>
                    <SortButton field="last_seen_at" label="Last seen" className="justify-end" />
                  </TableHead>
                  <TableHead>Source</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {page.items.map((listing) => (
                  <TableRow key={listing.id}>
                    <TableCell>
                      <ListingAvatar listing={listing} />
                    </TableCell>
                    <TableCell className="max-w-[320px]">
                      <a
                        href={listing.url}
                        target="_blank"
                        rel="noreferrer"
                        className="line-clamp-2 font-medium hover:underline"
                      >
                        {listing.title ?? "Untitled listing"}
                      </a>
                      <p className="text-muted-foreground text-xs">
                        {listing.location ?? "Unknown location"}
                      </p>
                    </TableCell>
                    <TableCell>
                      {formatCurrency(
                        listing.price_cents,
                        listing.currency ?? undefined,
                      )}
                    </TableCell>
                    <TableCell>
                      <PriceChangeBadge
                        change={listing.price_change}
                        current={listing.price_cents}
                        previous={listing.previous_price_cents}
                        currency={listing.currency ?? undefined}
                      />
                    </TableCell>
                    <TableCell className="text-right">{formatDate(listing.last_seen_at)}</TableCell>
                    <TableCell className="capitalize">
                      {listing.source ?? "vinted"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}

interface ConfigsSectionProps {
  configs: ScrapeConfigResponse[];
  statuses: Record<number, RuntimeStatusResponse | null>;
  onEdit: (config: ScrapeConfigResponse) => void;
  onRun: (config: ScrapeConfigResponse) => void;
  onDelete: (config: ScrapeConfigResponse) => void;
}

function ConfigsSection({
  configs,
  statuses,
  onEdit,
  onRun,
  onDelete,
}: ConfigsSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Scrape configurations</CardTitle>
        <CardDescription>
          Manage search parameters, scheduler settings, and trigger manual runs.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {configs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No configurations yet — create your first via “New config”.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Search text</TableHead>
                <TableHead>Schedule</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-48">Last run</TableHead>
                <TableHead className="w-[160px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {configs.map((config) => (
                <TableRow key={config.id}>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium">{config.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {config.is_active ? "Active" : "Inactive"} · {config.max_pages} pages · delay {formatDelaySeconds(config.delay)}s
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Proxy {formatProxyFlag(config.use_proxy)} · Details {describeDetailsMode(config)} · Strategy {config.details_strategy ?? "browser"}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="max-w-[220px]">
                    <span className="line-clamp-2 text-sm">
                      {config.search_text}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Categories: {formatList(config.categories)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Platforms: {formatList(config.platform_ids)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Locales: {formatList(config.locales ?? null)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Order: {config.order ?? "default"}
                    </span>
                    {getExtraFilters(config).length ? (
                      <span className="text-xs text-muted-foreground">
                        Extra filters: {formatList(getExtraFilters(config))}
                      </span>
                    ) : null}
                    {config.base_url ? (
                      <span className="text-xs text-muted-foreground">
                        Base URL: {config.base_url}
                      </span>
                    ) : null}
                  </TableCell>
                  <TableCell className="text-sm">
                    {config.cron_schedule ?? "Manual"}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={statuses[config.id]} />
                  </TableCell>
                  <TableCell className="text-sm">
                    {config.last_run_at ? (
                      <div className="flex flex-col">
                        <span>{formatDate(config.last_run_at)}</span>
                        {typeof config.last_run_items === "number" ? (
                          <span className="text-xs text-muted-foreground">
                            {config.last_run_items} items scraped
                          </span>
                        ) : null}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-sm">
                        Never run
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onRun(config)}
                      >
                        <Play className="size-4" />
                        Run
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => onEdit(config)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-destructive hover:bg-destructive/10"
                        onClick={() => onDelete(config)}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

interface ConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  form: ConfigFormState;
  onFormChange: (updater: ConfigFormState) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
  onPreviewCron: () => Promise<void>;
  preview: CronCommandResponse | null;
  previewLoading: boolean;
  previewError: string | null;
  isSaving: boolean;
  categories: CategoryResponse[];
  platforms: CategoryResponse[];
}

function ConfigDialog({
  open,
  onOpenChange,
  form,
  onFormChange,
  onSubmit,
  onPreviewCron,
  preview,
  previewLoading,
  previewError,
  isSaving,
  categories,
  platforms,
}: ConfigDialogProps) {
  const title = form.id ? "Edit configuration" : "Create configuration";
  const previewDisabled = !form.name.trim() || !form.search_text.trim();
  const extraFiltersHelp =
    "One key=value per line; maps to repeated -e flags in the scraper CLI.";
  const extraArgsHelp =
    "Optional CLI arguments appended verbatim (one per line, e.g. --order=created_at).";
  const orderSelectValue =
    form.order && form.order.trim().length > 0 ? form.order : "default";
  const cronPresetValue =
    form.cron_schedule && form.cron_schedule.trim().length > 0
      ? CRON_PRESETS.find(
          (preset) => preset.value === form.cron_schedule.trim(),
        )?.value ?? "custom"
      : "custom";

  const handleCopyPreview = async () => {
    if (!preview?.command) return;
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      toast.error("Clipboard API not available in this environment.");
      return;
    }
    try {
      await navigator.clipboard.writeText(preview.command);
      toast.success("Cron command copied to clipboard");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to access clipboard";
      toast.error("Failed to copy cron command", { description: message });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="relative max-h-[85vh] max-w-5xl overflow-y-auto"
        onEscapeKeyDown={(event) => event.preventDefault()}
      >
        <DialogClose asChild>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="absolute right-3 top-3"
            aria-label="Close configuration dialog"
          >
            <X className="size-4" />
          </Button>
        </DialogClose>
        <form onSubmit={onSubmit} className="grid gap-6">
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>
              Configure search filters, scraping behavior, and scheduling for this job.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="config-name">Name</Label>
                <Input
                  id="config-name"
                  value={form.name}
                  onChange={(event) =>
                    onFormChange({ ...form, name: event.target.value })
                  }
                  placeholder="PS5 Games Monitor"
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="config-search">Search text</Label>
                <Input
                  id="config-search"
                  value={form.search_text}
                  onChange={(event) =>
                    onFormChange({ ...form, search_text: event.target.value })
                  }
                  placeholder="ps5"
                  required
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Provide at least one of search text, categories, or platform IDs.
            </p>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="config-categories">
                  Categories (comma-separated IDs)
                </Label>
                <Input
                  id="config-categories"
                  value={form.categories}
                  onChange={(event) =>
                    onFormChange({ ...form, categories: event.target.value })
                  }
                  placeholder="3026,1953"
                />
                <HelperList items={categories} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="config-platforms">
                  Platform IDs (comma-separated)
                </Label>
                <Input
                  id="config-platforms"
                  value={form.platform_ids}
                  onChange={(event) =>
                    onFormChange({ ...form, platform_ids: event.target.value })
                  }
                  placeholder="1281,1280"
                />
                <HelperList items={platforms} />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="config-locales">Locales (comma-separated)</Label>
                <Input
                  id="config-locales"
                  value={form.locales}
                  onChange={(event) =>
                    onFormChange({ ...form, locales: event.target.value })
                  }
                  placeholder="sk,cz"
                />
                <p className="text-xs text-muted-foreground">
                  Leave blank to use the backend default locale list.
                </p>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="config-order">Sort order</Label>
                <Select
                  value={orderSelectValue}
                  onValueChange={(value) =>
                    onFormChange({
                      ...form,
                      order: value === "default" ? "" : value,
                    })
                  }
                >
                  <SelectTrigger id="config-order">
                    <SelectValue placeholder="Default (relevance)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default (relevance)</SelectItem>
                    {ORDER_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="config-extra">Extra filters (-e)</Label>
                <Textarea
                  id="config-extra"
                  value={form.extra_filters}
                  onChange={(event) =>
                    onFormChange({ ...form, extra_filters: event.target.value })
                  }
                  placeholder={"price_to=100\ncatalog[]=3026"}
                  className="min-h-[96px]"
                />
                <p className="text-xs text-muted-foreground">{extraFiltersHelp}</p>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="config-extra-args">Extra CLI arguments</Label>
                <Textarea
                  id="config-extra-args"
                  value={form.extra_args}
                  onChange={(event) =>
                    onFormChange({ ...form, extra_args: event.target.value })
                  }
                  placeholder={"--details-timeout=30"}
                  className="min-h-[96px]"
                />
                <p className="text-xs text-muted-foreground">{extraArgsHelp}</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="config-base-url">Base URL override</Label>
                <Input
                  id="config-base-url"
                  value={form.base_url}
                  onChange={(event) =>
                    onFormChange({ ...form, base_url: event.target.value })
                  }
                  placeholder="https://www.vinted.sk/catalog"
                />
                <p className="text-xs text-muted-foreground">
                  Blank uses the default URL configured on the backend.
                </p>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="config-detail-strategy">Detail strategy</Label>
                <Select
                  value={form.details_strategy}
                  onValueChange={(value) =>
                    onFormChange({
                      ...form,
                      details_strategy: value as "browser" | "http",
                    })
                  }
                >
                  <SelectTrigger id="config-detail-strategy">
                    <SelectValue placeholder="browser" />
                  </SelectTrigger>
                  <SelectContent>
                    {DETAIL_STRATEGY_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <NumberField
                label="Max pages"
                value={form.max_pages}
                min={1}
                max={1000}
                onChange={(value) => onFormChange({ ...form, max_pages: value })}
              />
              <NumberField
                label="Per page"
                value={form.per_page}
                min={1}
                max={100}
                onChange={(value) => onFormChange({ ...form, per_page: value })}
              />
              <NumberField
                label="Delay (seconds)"
                step={0.1}
                value={form.delay}
                min={0.1}
                max={10}
                onChange={(value) => onFormChange({ ...form, delay: value })}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <NumberField
                label="Error wait (minutes)"
                value={form.error_wait_minutes}
                min={0}
                max={240}
                onChange={(value) =>
                  onFormChange({ ...form, error_wait_minutes: value })
                }
              />
              <NumberField
                label="Max retries"
                value={form.max_retries}
                min={0}
                max={10}
                onChange={(value) =>
                  onFormChange({ ...form, max_retries: value })
                }
              />
              <NumberField
                label="Details concurrency"
                value={form.details_concurrency}
                min={1}
                max={16}
                onChange={(value) =>
                  onFormChange({ ...form, details_concurrency: value })
                }
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <SwitchField
                label="Fetch details"
                description="Fetch each listing detail page (slower but richer data)."
                checked={form.fetch_details}
                onCheckedChange={(checked) =>
                  onFormChange({ ...form, fetch_details: checked })
                }
              />
              <SwitchField
                label="Details for new only"
                description="Only fetch details for listings that are new to the database."
                checked={form.details_for_new_only}
                onCheckedChange={(checked) =>
                  onFormChange({ ...form, details_for_new_only: checked })
                }
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <SwitchField
                label="Use proxy"
                description="Disable to connect directly (recommended in most cases)."
                checked={form.use_proxy}
                onCheckedChange={(checked) =>
                  onFormChange({ ...form, use_proxy: checked })
                }
              />
              <SwitchField
                label="Active"
                description="Active configs are eligible for cron scheduling."
                checked={form.is_active}
                onCheckedChange={(checked) =>
                  onFormChange({ ...form, is_active: checked })
                }
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="config-cron">
                Cron schedule (leave empty for manual runs)
              </Label>
              <Select
                value={cronPresetValue}
                onValueChange={(value) => {
                  if (value === "custom") {
                    onFormChange({ ...form, cron_schedule: "" });
                    return;
                  }
                  onFormChange({ ...form, cron_schedule: value });
                }}
              >
                <SelectTrigger id="config-cron-preset">
                  <SelectValue placeholder="Select a preset" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custom">Custom schedule</SelectItem>
                  {CRON_PRESETS.map((preset) => (
                    <SelectItem key={preset.value} value={preset.value}>
                      {preset.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Textarea
                id="config-cron"
                value={form.cron_schedule}
                onChange={(event) =>
                  onFormChange({ ...form, cron_schedule: event.target.value })
                }
                placeholder="0 */6 * * *"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="config-healthcheck">
                Healthcheck ping URL (optional)
              </Label>
              <Input
                id="config-healthcheck"
                value={form.healthcheck_ping_url}
                onChange={(event) =>
                  onFormChange({
                    ...form,
                    healthcheck_ping_url: event.target.value,
                  })
                }
                placeholder="https://hc-ping.com/your-check"
              />
              <p className="text-xs text-muted-foreground">
                We will call <code>/start</code> before each cron run and <code>/fail</code> on errors.
              </p>
            </div>

            <div className="grid gap-3">
              <Label>Cron command preview</Label>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void onPreviewCron()}
                  disabled={previewLoading || previewDisabled}
                >
                  {previewLoading ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="size-4 animate-spin" /> Building...
                    </span>
                  ) : (
                    "Preview command"
                  )}
                </Button>
                {previewError ? (
                  <span className="text-sm text-destructive">{previewError}</span>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    Generates the exact CLI command cron will run with these values.
                  </span>
                )}
              </div>
              {preview ? (
                <div className="relative">
                  <pre className="max-h-48 overflow-auto rounded-md border bg-muted p-3 text-xs font-mono whitespace-pre-wrap">
                    {preview.command}
                    {preview.schedule ? `\n# schedule: ${preview.schedule}` : ""}
                  </pre>
                  <Button
                    type="button"
                    size="icon-sm"
                    variant="secondary"
                    className="absolute right-2 top-2"
                    onClick={handleCopyPreview}
                  >
                    <Copy className="size-4" />
                  </Button>
                </div>
              ) : null}
            </div>
          </div>

          <DialogFooter className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Saving…
                </>
              ) : (
                "Save configuration"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface NumberFieldProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
}

function buildConfigPayload(form: ConfigFormState): ScrapeConfigWritePayload {
  const categories = parseIdList(form.categories);
  const platformIds = parseIdList(form.platform_ids);
  const extraFilters = parseStringListInput(form.extra_filters);
  const locales = parseLocalesInput(form.locales);
  const extraArgs = parseExtraArgs(form.extra_args);

  const maxPages = sanitizeInteger(form.max_pages, 1, 1000, 5);
  const perPage = sanitizeInteger(form.per_page, 1, 100, 24);
  const delay = sanitizeFloat(form.delay, 0.1, 10, 1);
  const errorWait = sanitizeInteger(form.error_wait_minutes, 0, 240, 30);
  const maxRetries = sanitizeInteger(form.max_retries, 0, 10, 3);
  const detailsConcurrency = sanitizeInteger(form.details_concurrency, 1, 16, 2);

  const order = form.order.trim() || null;
  const baseUrl = form.base_url.trim() || null;
  const cronSchedule = form.cron_schedule.trim() || null;
  const detailsStrategy = form.details_strategy === "http" ? "http" : "browser";
  const healthcheckUrl = form.healthcheck_ping_url.trim() || null;

  return {
    name: form.name.trim(),
    search_text: form.search_text.trim(),
    categories,
    platform_ids: platformIds,
    order,
    extra_filters: extraFilters,
    locales,
    extra_args: extraArgs,
    max_pages: maxPages,
    per_page: perPage,
    delay,
    fetch_details: form.fetch_details,
    details_for_new_only: form.details_for_new_only,
    use_proxy: form.use_proxy,
    error_wait_minutes: errorWait,
    max_retries: maxRetries,
    base_url: baseUrl,
    details_strategy: detailsStrategy,
    details_concurrency: detailsConcurrency,
    cron_schedule: cronSchedule,
    is_active: form.is_active,
    healthcheck_ping_url: healthcheckUrl,
  };
}

function formatIdList(values?: number[] | null): string {
  if (!values || values.length === 0) return "";
  return values.join(",");
}

function formatStringList(
  values: (string | number)[] | null | undefined,
  delimiter = ",",
): string {
  if (!values || values.length === 0) return "";
  return values.map(String).join(delimiter);
}

function formatList(values?: (string | number)[] | null): string {
  if (!values || values.length === 0) return "—";
  const limited = values.slice(0, 3).map(String).join(", ");
  return values.length > 3 ? `${limited}, ...` : limited;
}

function getExtraFilters(config: ScrapeConfigResponse): string[] {
  return config.extra_filters ?? config.extra ?? [];
}

function describeDetailsMode(config: ScrapeConfigResponse): string {
  if (!config.fetch_details) {
    return "none";
  }
  return config.details_for_new_only ? "new only" : "all";
}

function formatDelaySeconds(value: unknown): string {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) {
    return "—";
  }
  return numeric.toFixed(1);
}

function formatProxyFlag(value: boolean | null | undefined): string {
  return value === false ? "off" : "on";
}

function NumberField({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: NumberFieldProps) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      <Input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(event) => {
          const next = Number(event.target.value);
          onChange(Number.isNaN(next) ? value : next);
        }}
      />
    </div>
  );
}

interface SwitchFieldProps {
  label: string;
  description?: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}

function SwitchField({
  label,
  description,
  checked,
  onCheckedChange,
}: SwitchFieldProps) {
  return (
    <label className="flex flex-1 items-start gap-3 rounded-lg border p-3">
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
      <span>
        <span className="block font-medium">{label}</span>
        {description ? (
          <span className="text-sm text-muted-foreground">{description}</span>
        ) : null}
      </span>
    </label>
  );
}

interface HelperListProps {
  items: CategoryResponse[];
}

function HelperList({ items }: HelperListProps) {
  if (!items.length) return null;

  return (
    <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
      {items.slice(0, 6).map((item) => (
        <Badge key={item.id} variant="secondary">
          {item.id}: {item.name}
        </Badge>
      ))}
      {items.length > 6 ? <span>…</span> : null}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number | string | null | undefined;
  caption?: string;
  loading?: boolean;
}

function StatCard({ title, value, caption, loading }: StatCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        <span className="text-3xl font-semibold tracking-tight">
          {loading ? (
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          ) : value !== null && value !== undefined ? (
            value
          ) : (
            "—"
          )}
        </span>
        {caption ? (
          <span className="text-xs text-muted-foreground">{caption}</span>
        ) : null}
      </CardContent>
    </Card>
  );
}

interface TrendPillProps {
  label: string;
  value: number;
  tone: "up" | "down" | "neutral";
}

function TrendPill({ label, value, tone }: TrendPillProps) {
  const toneClasses = {
    up: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
    down: "bg-red-500/10 text-red-500 border-red-500/30",
    neutral: "bg-muted text-muted-foreground border-transparent",
  } as const;

  return (
    <div
      className={cn(
        "flex flex-col gap-0.5 rounded-lg border px-4 py-3",
        toneClasses[tone],
      )}
    >
      <span className="text-xs uppercase tracking-wide">{label}</span>
      <span className="text-xl font-semibold">{value}</span>
    </div>
  );
}

interface ListingAvatarProps {
  listing: ListingResponse;
}

function ListingAvatar({ listing }: ListingAvatarProps) {
  if (listing.photo) {
    return (
      <div className="size-12 overflow-hidden rounded-md border">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={listing.photo}
          alt={listing.title ?? "Listing photo"}
          className="size-full object-cover"
          loading="lazy"
        />
      </div>
    );
  }

  return (
    <div className="bg-muted text-muted-foreground flex size-12 items-center justify-center rounded-md border">
      {listing.title?.charAt(0) ?? "?"}
    </div>
  );
}

interface PriceChangeBadgeProps {
  change: ListingResponse["price_change"];
  current: number | null;
  previous: number | null;
  currency?: string;
}

function PriceChangeBadge({
  change,
  current,
  previous,
  currency,
}: PriceChangeBadgeProps) {
  if (!change || current === null || previous === null) {
    return <span className="text-muted-foreground text-xs">—</span>;
  }

  const toneClasses =
    change === "up"
      ? "bg-emerald-500/10 text-emerald-500"
      : change === "down"
        ? "bg-red-500/10 text-red-500"
        : "bg-muted text-muted-foreground";

  if (!previous) {
    return (
      <span className={cn("rounded-md px-2 py-1 text-xs font-medium", toneClasses)}>
        {formatCurrency(current, currency)}
      </span>
    );
  }

  const delta = ((current - previous) / previous) * 100;
  const formattedDelta = `${delta > 0 ? "+" : ""}${delta.toFixed(1)}%`;

  return (
    <span className={cn("rounded-md px-2 py-1 text-xs font-medium", toneClasses)}>
      {formatCurrency(current, currency)} ({formattedDelta})
    </span>
  );
}

interface StatusBadgeProps {
  status: RuntimeStatusResponse | null | undefined;
}

function StatusBadge({ status }: StatusBadgeProps) {
  if (!status) {
    return (
      <Badge variant="outline" className="text-muted-foreground">
        Idle
      </Badge>
    );
  }

  const tone =
    status.status === "success"
      ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
      : status.status === "failed"
        ? "bg-red-500/10 text-red-500 border-red-500/30"
        : "bg-blue-500/10 text-blue-500 border-blue-500/30";

  return (
    <div className="flex flex-col gap-1">
      <Badge className={tone}>
        {status.status} · {status.items ?? 0} items
      </Badge>
      {status.message ? (
        <span className="text-xs text-muted-foreground">
          {status.message}
        </span>
      ) : null}
      <span className="text-xs text-muted-foreground">
        Updated {formatDate(status.updated_at)}
      </span>
    </div>
  );
}

function splitInput(value: string, pattern: RegExp): string[] {
  return value
    .split(pattern)
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

function parseIdList(value: string): number[] | null {
  const parts = splitInput(value, /[\s,]+/);
  if (parts.length === 0) {
    return null;
  }

  const result = parts
    .map((part) => Number(part))
    .filter((num) => Number.isFinite(num) && num > 0);

  return result.length ? result : null;
}

function parseStringListInput(value: string, pattern: RegExp = /[\n,]+/): string[] | null {
  const parts = splitInput(value, pattern);
  return parts.length ? parts : null;
}

function parseExtraArgs(value: string): string[] | null {
  const parts = splitInput(value, /\n+/);
  return parts.length ? parts : null;
}

function parseLocalesInput(value: string): string[] | null {
  const parts = splitInput(value, /[\s,]+/);
  return parts.length ? parts : null;
}

function sanitizeInteger(
  value: unknown,
  min: number,
  max?: number,
  fallback?: number,
): number {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback ?? min;
  }
  const rounded = Math.floor(numeric);
  const clampedLower = Math.max(min, rounded);
  if (typeof max === "number") {
    return Math.min(max, clampedLower);
  }
  return clampedLower;
}

function sanitizeFloat(
  value: unknown,
  min: number,
  max?: number,
  fallback?: number,
): number {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback ?? min;
  }
  const clampedLower = Math.max(min, numeric);
  if (typeof max === "number") {
    return Math.min(max, clampedLower);
  }
  return clampedLower;
}
