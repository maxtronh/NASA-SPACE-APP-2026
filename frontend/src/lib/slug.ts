const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/i;

/**
 * Cheap validation for route slugs before they reach the API. Rejects empty,
 * overlong, and malformed values so junk URLs become 404s instead of requests.
 */
export function isSafeSlug(value: string): boolean {
  return value.length > 0 && value.length <= 120 && SLUG_PATTERN.test(value);
}
