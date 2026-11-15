/**
 * Canonical public origin used for metadata, robots, and the sitemap.
 * Set NEXT_PUBLIC_SITE_URL in deployment so absolute URLs are correct.
 */
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
