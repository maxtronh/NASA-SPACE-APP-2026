"use client";

import { useEffect } from "react";

/**
 * Last-resort boundary. It only renders when the root layout itself throws,
 * which means the global stylesheet and every component dependency may be
 * unavailable — so everything here is inline and self-contained.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#030712",
          color: "#e2e8f0",
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        }}
      >
        <main style={{ maxWidth: "32rem", padding: "2rem", textAlign: "center" }}>
          <p
            style={{
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
              fontSize: "0.75rem",
              letterSpacing: "0.15em",
              color: "#fbbf24",
              textTransform: "uppercase",
            }}
          >
            Application Error
          </p>
          <h1 style={{ fontSize: "1.5rem", margin: "0.5rem 0 0.75rem" }}>
            Flame in Freefall could not start
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.875rem", lineHeight: 1.6 }}>
            A critical error interrupted the interface before the page could be
            rendered
            {error.digest ? ` (digest: ${error.digest})` : ""}.
          </p>
          <button
            type="button"
            onClick={reset}
            style={{
              marginTop: "1.5rem",
              padding: "0.625rem 1.25rem",
              borderRadius: "0.5rem",
              border: "none",
              backgroundColor: "#00e5ff",
              color: "#030712",
              fontSize: "0.875rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Reload the application
          </button>
        </main>
      </body>
    </html>
  );
}
