"use client";

import { TableRow, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ListingAvatar } from "../common/ListingAvatar";
import { PriceChangeBadge } from "../common/PriceChangeBadge";
import { formatCurrency, formatDate, formatActiveDuration } from "@/lib/format";
import type { ListingResponse, ConditionResponse, PlatformResponse, SourceResponse, CategoryResponse } from "@/lib/types";

interface ListingRowProps {
  listing: ListingResponse;
  conditions: ConditionResponse[];
  platforms: PlatformResponse[];
  sources: SourceResponse[];
  categories: CategoryResponse[];
}

export function ListingRow({ listing, conditions, platforms, sources, categories }: ListingRowProps) {
  const condition = conditions.find(c => c.label === listing.condition_label);
  const source = sources.find(s => s.label === listing.source_label);
  const category = categories.find(cat => cat.id === listing.category_id);

  return (
    <TableRow>
      <TableCell className="flex items-center gap-3">
        <ListingAvatar listing={listing} />
        <div className="flex flex-col">
          <a href={listing.url} target="_blank" rel="noopener noreferrer" className="font-medium hover:underline">
            {listing.title}
          </a>
          <span className="text-xs text-muted-foreground">#{listing.id}</span>
        </div>
      </TableCell>

      <TableCell className="text-sm">
        {listing.price_cents
          ? formatCurrency(listing.price_cents, listing.currency)
          : "—"}
      </TableCell>

      <TableCell>
        <PriceChangeBadge
          change={listing.price_change}
          current={listing.price_cents}
          previous={listing.previous_price_cents}
          currency={listing.currency}
        />
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {listing.condition_label && condition && (
            <Badge style={condition.color ? { backgroundColor: condition.color } : {}}>
              {listing.condition_label}
            </Badge>
          )}
        </div>
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {listing.category_name && category && (
            <Badge style={category.color ? { backgroundColor: category.color } : {}}>
              {listing.category_name}
            </Badge>
          )}
        </div>
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {listing.platform_names?.map((platformName) => {
            const platform = platforms.find(p => p.name === platformName);
            return (
              <Badge key={platformName} style={platform?.color ? { backgroundColor: platform.color } : {}}>
                {platformName}
              </Badge>
            );
          })}
        </div>
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {listing.source_label && source && (
            <Badge style={source.color ? { backgroundColor: source.color } : {}}>
              {listing.source_label}
            </Badge>
          )}
        </div>
      </TableCell>

      <TableCell className="text-xs text-muted-foreground">
        {formatDate(listing.last_seen_at)}
      </TableCell>

      <TableCell className="text-xs text-muted-foreground">
        {formatDate(listing.first_seen_at)}
      </TableCell>

      <TableCell className="text-xs text-muted-foreground">
        {formatActiveDuration(listing.first_seen_at)}
      </TableCell>
    </TableRow>
  );
}
