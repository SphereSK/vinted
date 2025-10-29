export interface StatsResponse {
  total_listings: number;
  active_listings: number;
  total_scraped_today: number;
  total_scraped_last_7_days: number;
  total_scraped_previous_day: number;
  total_scraped_day_before_previous: number;
  active_listings_last_7_days: number;
  active_listings_last_30_days: number;
  inactive_listings_today: number;
  inactive_listings_last_7_days: number;
  inactive_listings_last_30_days: number;
  active_configs: number;
  avg_price_cents: number | null;
  min_price_cents: number | null;
  max_price_cents: number | null;
  price_increase_count: number;
  price_decrease_count: number;
  price_unchanged_count: number;
  total_listings_previous_day: number;
  total_listings_previous_7_days: number;
  total_listings_previous_30_days: number;
  source_stats: { [key: string]: { total_items: number; active_items: number; inactive_items: number } };
}

export interface ListingsPage {
  items: ListingResponse[];
  total_items: number;
  total_pages: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ScrapeConfigResponse {
  id: number;
  name: string;
  search_text: string;
  categories: number[] | null;
  platform_ids: number[] | null;
  order: string | null;
  extra_filters: string[] | null;
  locales: string[] | null;
  extra_args: string[] | null;
  max_pages: number;
  per_page: number;
  delay: number;
  fetch_details: boolean;
  details_for_new_only: boolean;
  use_proxy: boolean;
  error_wait_minutes: number | null;
  max_retries: number | null;
  base_url: string | null;
  details_strategy: string | null;
  details_concurrency: number | null;
  cron_schedule: string | null;
  is_active: boolean;
  healthcheck_ping_url: string | null;
  created_at?: string;
  last_run_at: string | null;
  last_run_status: string | null;
  last_run_items: number | null;
  last_health_status?: string | null;
  last_health_check_at?: string | null;
}

export interface ScrapeConfigWritePayload {
  name: string;
  search_text: string;
  categories?: string | number[];
  platform_ids?: string | number[];
  order?: string;
  extra_filters?: string | string[];
  locales?: string | string[];
  extra_args?: string | string[];
  max_pages: number;
  per_page: number;
  delay: number;
  fetch_details: boolean;
  details_for_new_only: boolean;
  use_proxy: boolean;
  error_wait_minutes?: number;
  max_retries?: number;
  base_url?: string;
  details_strategy: "browser" | "http";
  details_concurrency: number;
  cron_schedule?: string;
  is_active: boolean;
  healthcheck_ping_url?: string;
}

export interface RuntimeStatusResponse {
  is_running: boolean;
  last_run_at: string | null;
  last_run_status: string | null;
}

export interface CronJobEntry {
  command: string;
  schedule: string;
  comment: string;
  config_id: number | null;
  enabled: boolean;
}

export interface CronHealthStatus {
  config_id: number;
  status: string | null;
  checked_at: string | null;
}

export interface CronCommandResponse {
  status: string;
  message?: string;
}

export interface CategoryResponse {
  id: number;
  name: string;
  color: string | null;
}

export interface PlatformResponse {
  id: number;
  name: string;
  color: string | null;
}

export interface ConditionResponse {
  id: number;
  name: string;
  label: string;
  color: string | null;
}

export interface SourceResponse {
  id: number;
  name: string;
  label: string;
}

export type ListingSortField =
  | "last_seen_at"
  | "first_seen_at"
  | "price"
  | "title"
  | "seller_name"
  | "price_change"
  | "condition"
  | "category_id"
  | "platform_ids"
  | "source";

export interface ListingResponse {
  id: number;
  title: string;
  price_cents: number;
  currency: string;
  previous_price_cents: number | null;
  price_change: number | null;
  condition_label: string | null;
  platform_names: string[] | null;
  source_label: string | null;
  last_seen_at: string;
  first_seen_at: string;
  photo_url: string | null;
  url: string;
  seller_name: string | null;
  photo: string | null;
}

export interface ListingsQuery {
  page: number;
  page_size: number;
  sort_field: string;
  sort_order: "asc" | "desc";
  search?: string;
  brand?: string;
  size?: string;
  material?: string;
  color?: string;
  condition?: string;
  source?: string;
  platform?: string;
  category?: string;
  is_sold?: boolean;
  price_min?: number;
  price_max?: number;
  currency?: string;
}

export interface FilterRequest {
  title?: string;
  price_min?: number;
  price_max?: number;
  conditions?: string[];
  platforms?: string[];
  sources?: string[];
  categories?: string[];
}

export interface FilterResponse {
  results: ListingResponse[];
  total: number;
  availableFilters: {
    conditions: ConditionResponse[];
    platforms: PlatformResponse[];
    sources: SourceResponse[];
    categories: CategoryResponse[];
  };
}

export interface FilterState extends FilterRequest {
  isLoading: boolean;
  error: Error | null;
}

export interface ListingsByPeriod {
  period: string;
  new_listings: number;
  total_listings: number;
}

export interface ListingsByPeriodResponse {
  items: ListingsByPeriod[];
}

export interface FilterOptionsResponse {
  conditions: ConditionResponse[];
  sources: SourceResponse[];
  categories: CategoryResponse[];
  platforms: PlatformResponse[];
  currencies: string[];
  sold_statuses: Array<{ label: string; value: boolean }>;
  price_min: number | null;
  price_max: number | null;
}