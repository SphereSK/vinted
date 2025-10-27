"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { StatsResponse, ScrapeConfigResponse, CronJobEntry } from "@/lib/types";
import { formatCurrency } from "@/lib/format";
import { StatCard, TrendPill } from "../common/StatCard";

const calculateTrend = (current: number, previous: number) => {
  if (previous === 0) return 0; // Avoid division by zero
  return ((current - previous) / previous) * 100;
};

const getTrendIcon = (trend: number) => {
  if (trend > 0) return <ArrowUpRight className="h-4 w-4 text-green-500" />;
  if (trend < 0) return <ArrowDownRight className="h-4 w-4 text-red-500" />;
  return null;
};

const getTrendColor = (trend: number) => {
  if (trend > 0) return "text-green-500";
  if (trend < 0) return "text-red-500";
  return "text-gray-500";
};

interface DashboardSectionProps {
  stats: StatsResponse | null;
  statsLoading: boolean;
  configs: ScrapeConfigResponse[];
  cronJobs: CronJobEntry[];
  cronError: Error | null;
  cronLoading: boolean;
}

export function DashboardSection({
  stats,
  statsLoading,
  configs,
  cronJobs,
  cronError,
  cronLoading,
}: DashboardSectionProps) {
  const totalConfigs = configs.length;
  const totalCrons = cronJobs.length;
  const configsCaption = cronError
    ? "Cron jobs unavailable"
    : !cronLoading
      ? `${totalCrons} cron job${totalCrons === 1 ? "" : "s"}`
      : undefined;

  const priceChangeSummary = {
    up: stats?.price_increase_count ?? 0,
    down: stats?.price_decrease_count ?? 0,
    same: stats?.price_unchanged_count ?? 0,
  };

  const totalListingsTrendToday = calculateTrend(
    stats?.total_listings ?? 0,
    stats?.total_listings_previous_day ?? 0
  );
  const totalListingsTrend7Days = calculateTrend(
    stats?.total_listings ?? 0,
    stats?.total_listings_previous_7_days ?? 0
  );
  const totalListingsTrend30Days = calculateTrend(
    stats?.total_listings ?? 0,
    stats?.total_listings_previous_30_days ?? 0
  );

  return (
    <div className="flex flex-col gap-6 pt-4">
      {/* Stats overview cards */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Active listings" value={stats?.active_listings} loading={statsLoading} />
        <StatCard title="Total listings" value={stats?.total_listings} loading={statsLoading} />
        <StatCard
          title="Average price"
          value={stats?.avg_price_cents ? formatCurrency(stats.avg_price_cents) : null}
          loading={statsLoading}
        />
        <StatCard
          title="Min price"
          value={stats?.min_price_cents ? formatCurrency(stats.min_price_cents) : null}
          loading={statsLoading}
        />
        <StatCard
          title="Max price"
          value={stats?.max_price_cents ? formatCurrency(stats.max_price_cents) : null}
          loading={statsLoading}
        />
        <StatCard title="Configs" value={totalConfigs} loading={statsLoading} caption={configsCaption} />
      </section>

      {/* Listings created trends */}
      <section className="grid gap-4 md:grid-cols-1 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Listings Created</CardTitle>
            <CardDescription>New listings added over time</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            <div className="flex items-center justify-between">
              <span>Today:</span>
              <span className="flex items-center gap-1">
                {stats?.total_scraped_today ?? 0}
                {getTrendIcon(totalListingsTrendToday)}
                <span className={getTrendColor(totalListingsTrendToday)}>
                  {totalListingsTrendToday.toFixed(2)}%
                </span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Last 7 Days:</span>
              <span className="flex items-center gap-1">
                {stats?.total_scraped_last_7_days ?? 0}
                {getTrendIcon(totalListingsTrend7Days)}
                <span className={getTrendColor(totalListingsTrend7Days)}>
                  {totalListingsTrend7Days.toFixed(2)}%
                </span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Last 30 Days:</span>
              <span className="flex items-center gap-1">
                {stats?.total_scraped_last_30_days ?? 0}
                {getTrendIcon(totalListingsTrend30Days)}
                <span className={getTrendColor(totalListingsTrend30Days)}>
                  {totalListingsTrend30Days.toFixed(2)}%
                </span>
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Active/Inactive Listings */}
        <Card>
          <CardHeader>
            <CardTitle>Active/Inactive Listings</CardTitle>
            <CardDescription>Current status of listings</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            <div className="flex items-center justify-between">
              <span>Active (Last 7 Days):</span>
              <span>{stats?.active_listings_last_7_days ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Inactive (Today):</span>
              <span>{stats?.inactive_listings_today ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Inactive (Last 7 Days):</span>
              <span>{stats?.inactive_listings_last_7_days ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Inactive (Last 30 Days):</span>
              <span>{stats?.inactive_listings_last_30_days ?? 0}</span>
            </div>
          </CardContent>
        </Card>

        {/* Recent price movement and configs overview */}
        <Card>
          <CardHeader>
            <CardTitle>Recent price movement</CardTitle>
            <CardDescription>Overview of tracked listings price changes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <TrendPill label="Price increase" value={priceChangeSummary.up} tone="up" />
              <TrendPill label="Price decrease" value={priceChangeSummary.down} tone="down" />
              <TrendPill label="Unchanged" value={priceChangeSummary.same} tone="neutral" />
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Source-wise Statistics */}
      <section>
        <Card>
          <CardHeader>
            <CardTitle>Listings by Source</CardTitle>
            <CardDescription>Breakdown of listings by their source marketplace</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
              {Object.entries(stats?.source_stats ?? {}).map(([source, data]) => (
                <Card key={source} className="p-4">
                  <CardTitle className="text-md mb-2">{source}</CardTitle>
                  <p className="text-sm">Total: {data.total_items}</p>
                  <p className="text-sm text-green-600">Active: {data.active_items}</p>
                  <p className="text-sm text-red-600">Inactive: {data.inactive_items}</p>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
