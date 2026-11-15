import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

const ROUTES = [
  "",
  "/investigations",
  "/intelligence",
  "/compare",
  "/analytics",
  "/mission-control",
  "/handbook",
  "/fire-safety",
  "/diagnostics",
  "/optimizer",
  "/antigravity",
  "/milky-way",
  "/nasa-eyes",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  return ROUTES.map((route) => ({
    url: `${SITE_URL}${route}`,
    lastModified,
    changeFrequency: route === "" ? "daily" : "weekly",
    priority: route === "" ? 1 : 0.7,
  }));
}
