import type { Metadata } from "next";

const SITE_NAME = "Flame in Freefall";

/** Shared shape for route-level metadata so titles stay consistent. */
export function pageMetadata(title: string, description: string): Metadata {
  return {
    title: `${title} | ${SITE_NAME}`,
    description,
    openGraph: {
      title: `${title} | ${SITE_NAME}`,
      description,
      siteName: SITE_NAME,
      type: "website",
    },
  };
}
