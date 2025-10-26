"use client";

import type { ListingResponse } from "@/lib/types";

export function ListingAvatar({ listing }: { listing: ListingResponse }) {
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
