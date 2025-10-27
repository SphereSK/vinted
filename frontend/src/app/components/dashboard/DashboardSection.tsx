"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { StatsResponse, ScrapeConfigResponse, CronJobEntry, ListingsByPeriod } from "@/lib/types";
import { formatCurrency } from "@/lib/format";
import { StatCard, TrendPill } from "../common/StatCard";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

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
  listingsByPeriod: ListingsByPeriod[];
  listingsByPeriodLoading: boolean;
  selectedPeriod: "daily" | "weekly" | "monthly";
  setSelectedPeriod: (period: "daily" | "weekly" | "monthly") => void;
}

export function DashboardSection({
  stats,
  statsLoading,
  configs,
  cronJobs,
  cronError,
  cronLoading,
  listingsByPeriod,
  listingsByPeriodLoading,
  selectedPeriod,
  setSelectedPeriod,
}: DashboardSectionProps) {
  const totalConfigs = configs.length;
  const totalCrons = cronJobs.length;
  const configsCaption = cronError
    ? "Cron jobs unavailable"
    : !cronLoading
      ? `${totalCrons} cron job${totalCrons === 1 ? "" : "s"}`
      : undefined;

  const inactiveListings = (stats?.total_listings ?? 0) - (stats?.active_listings ?? 0);

  const priceChangeSummary = {
    up: stats?.price_increase_count ?? 0,
    down: stats?.price_decrease_count ?? 0,
    same: stats?.price_unchanged_count ?? 0,
  };

  const totalListingsTrendToday = calculateTrend(
    stats?.total_scraped_today ?? 0,
    stats?.total_scraped_previous_day ?? 0
  );
  const totalListingsTrendYesterday = calculateTrend(
    stats?.total_scraped_previous_day ?? 0,
    stats?.total_scraped_day_before_previous ?? 0
  );
  const totalListingsTrend7Days = calculateTrend(
    stats?.total_scraped_last_7_days ?? 0,
    stats?.total_scraped_previous_7_days ?? 0
  );
  const totalListingsTrend30Days = calculateTrend(
    stats?.total_scraped_last_30_days ?? 0,
    stats?.total_scraped_previous_30_days ?? 0
  );

  return (
    <div className="flex flex-col gap-6 pt-4">
      {/* Stats overview cards */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Listings Overview</CardTitle>
            <CardDescription>Current and total listings</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            <div className="flex items-center justify-between">
              <span>Active Listings:</span>
              <span>{stats?.active_listings ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Inactive Listings:</span>
              <span>{inactiveListings}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Total Listings:</span>
              <span>{stats?.total_listings ?? 0}</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Price Overview</CardTitle>
            <CardDescription>Min, max, and average prices</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            <div className="flex items-center justify-between">
              <span>Min Price:</span>
              <span>{stats?.min_price_cents ? formatCurrency(stats.min_price_cents) : "N/A"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Max Price:</span>
              <span>{stats?.max_price_cents ? formatCurrency(stats.max_price_cents) : "N/A"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Average Price:</span>
              <span>{stats?.avg_price_cents ? formatCurrency(stats.avg_price_cents) : "N/A"}</span>
            </div>
          </CardContent>
        </Card>
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
              <span>Yesterday:</span>
              <span className="flex items-center gap-1">
                {stats?.total_scraped_previous_day ?? 0}
                {getTrendIcon(totalListingsTrendYesterday)}
                <span className={getTrendColor(totalListingsTrendYesterday)}>
                  {totalListingsTrendYesterday.toFixed(2)}%
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

      {/* Listings by Period Chart */}
      <section className="grid gap-4 md:grid-cols-1 lg:grid-cols-1">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Listings by Period</CardTitle>
            <div className="flex space-x-2">
              <Button
                variant={selectedPeriod === "daily" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedPeriod("daily")}
              >
                Daily
              </Button>
              <Button
                variant={selectedPeriod === "weekly" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedPeriod("weekly")}
              >
                Weekly
              </Button>
              <Button
                variant={selectedPeriod === "monthly" ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedPeriod("monthly")}
              >
                Monthly
              </Button>
            </div>
          </CardHeader>
          <CardContent style={{ height: '300px' }}>
            {listingsByPeriodLoading ? (
              <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={listingsByPeriod ?? []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="new_listings" stackId="a" fill="#8884d8" name="New Listings" />
                  <Bar dataKey="total_listings" stackId="a" fill="#82ca9d" name="Total Listings" />
                </BarChart>
              </ResponsiveContainer>
            )}
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
