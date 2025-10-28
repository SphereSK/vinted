"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Play, Pencil, Trash2, Copy, Power, PowerOff } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";

import type { ScrapeConfigResponse, RuntimeStatusResponse } from "@/lib/types";
import { StatusBadge } from "../common/StatusBadge";
import { formatDate, formatDelaySeconds, formatProxyFlag } from "@/lib/format";

interface ConfigsSectionProps {
  configs: ScrapeConfigResponse[];
  statuses: Record<number, RuntimeStatusResponse | null>;
  onEdit: (config: ScrapeConfigResponse) => void;
  onCopy?: (config: ScrapeConfigResponse) => void;
  onRun?: (config: ScrapeConfigResponse) => Promise<void> | void;
  onDelete?: (config: ScrapeConfigResponse) => Promise<void> | void;
  onToggleActive?: (config: ScrapeConfigResponse, newActiveState: boolean) => Promise<void> | void;
}

export function ConfigsSection({
  configs,
  statuses,
  onEdit,
  onCopy,
  onRun,
  onDelete,
  onToggleActive,
}: ConfigsSectionProps) {
  console.log("ConfigsSection received configs:", configs);
  if (!configs.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Scrape configurations</CardTitle>
          <CardDescription>
            Manage search parameters, scheduler settings, and trigger manual runs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No configurations yet — create your first via “New config”.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scrape configurations</CardTitle>
        <CardDescription>
          Manage search parameters, scheduler settings, and trigger manual runs.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Search text</TableHead>
              <TableHead>Schedule</TableHead>
              <TableHead>Active</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-48">Last run</TableHead>
              <TableHead className="w-[160px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {configs.map((config) => (
              <TableRow key={config.id} className={!config.is_active ? "opacity-60" : ""}>
                <TableCell>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{config.name}</span>
                      <Badge
                        variant={config.is_active ? "default" : "secondary"}
                        className={config.is_active ? "bg-green-500 hover:bg-green-600" : ""}
                      >
                        {config.is_active ? (
                          <><Power className="size-3 mr-1" /> Active</>
                        ) : (
                          <><PowerOff className="size-3 mr-1" /> Inactive</>
                        )}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {config.max_pages} pages · delay {formatDelaySeconds(config.delay)}s
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Proxy {formatProxyFlag(config.use_proxy)} · Strategy {config.details_strategy ?? "browser"}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="max-w-[220px]">
                  <span className="line-clamp-2 text-sm">
                    {config.search_text}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Order: {config.order ?? "default"}
                  </span>
                  {config.base_url && (
                    <span className="text-xs text-muted-foreground">
                      Base URL: {config.base_url}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-sm">
                  {config.cron_schedule ?? "Manual"}
                </TableCell>
                <TableCell>
                  {onToggleActive ? (
                    <Switch
                      checked={config.is_active}
                      onCheckedChange={(checked) => void onToggleActive(config, checked)}
                      title={config.is_active ? "Disable configuration" : "Enable configuration"}
                    />
                  ) : (
                    <span className="text-sm text-muted-foreground">
                      {config.is_active ? "Enabled" : "Disabled"}
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  <StatusBadge status={statuses[config.id]} />
                </TableCell>
                <TableCell className="text-sm">
                  {config.last_run_at ? (
                    <div className="flex flex-col">
                      <span>{formatDate(config.last_run_at)}</span>
                      {typeof config.last_run_items === "number" && (
                        <span className="text-xs text-muted-foreground">
                          {config.last_run_items} items scraped
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-muted-foreground text-sm">Never run</span>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {onRun && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => void onRun(config)}
                      >
                        <Play className="size-4" /> Run
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => onEdit(config)}
                      title="Edit configuration"
                    >
                      <Pencil className="size-4" />
                    </Button>
                    {onCopy && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => onCopy(config)}
                        title="Copy configuration"
                      >
                        <Copy className="size-4" />
                      </Button>
                    )}
                    {onDelete && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-destructive hover:bg-destructive/10"
                        onClick={() => void onDelete(config)}
                        title="Delete configuration"
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

