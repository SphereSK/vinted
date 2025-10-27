import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import type { CronHealthStatus } from "@/lib/types";

interface HealthStatusBadgeProps {
  configId: number;
}

export function HealthStatusBadge({ configId }: HealthStatusBadgeProps) {
  const [health, setHealth] = useState<CronHealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await fetch(`/api/cron/health/${configId}`);
        if (!response.ok) {
          throw new Error("Failed to fetch health status");
        }
        const data = (await response.json()) as CronHealthStatus;
        setHealth(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }

    void fetchHealth();
  }, [configId]);

  const getBadgeClass = () => {
    if (loading) return "bg-muted text-muted-foreground";
    if (!health || !health.status) return "bg-muted text-muted-foreground";

    switch (health.status) {
      case "ok":
        return "border-emerald-500/30 bg-emerald-500/10 text-emerald-500";
      case "fail":
        return "border-red-500/30 bg-red-500/10 text-red-500";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getStatusText = () => {
    if (loading) return "Loading...";
    if (!health || !health.status) return "Unknown";
    return health.status;
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Badge className={getBadgeClass()}>{getStatusText()}</Badge>
        </TooltipTrigger>
        <TooltipContent>
          {loading
            ? "Loading health status..."
            : `Last check: ${health?.checked_at ? new Date(health.checked_at).toLocaleString() : "N/A"}`}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
