"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import type { StatsResponse, ScrapeConfigResponse, CronJobEntry } from "@/lib/types";
import { formatCurrency } from "@/lib/format";
import { StatCard, TrendPill } from "../common/StatCard";

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

  const priceChangeSummary = stats?.price_change_summary ?? { up: 0, down: 0, same: 0 };

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
        <StatCard title="Configs" value={totalConfigs} loading={statsLoading} caption={configsCaption} />
      </section>

      {/* Recent price movement and configs overview */}
      <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
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

        <Card>
          <CardHeader>
            <CardTitle>Active scrape configs</CardTitle>
            <CardDescription>Quick glance at scheduled and manual configurations.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {configs.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No configurations found. Add one in the Scrape configs tab.
              </p>
            ) : (
              <ul className="space-y-2 text-sm">
                {configs.slice(0, 4).map((config) => (
                  <li key={config.id} className="flex flex-col rounded-lg border p-3">
                    <span className="font-medium">{config.name}</span>
                    <span className="text-muted-foreground">
                      {config.search_text} · {config.cron_schedule ?? "manual"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
