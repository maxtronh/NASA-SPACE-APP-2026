import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { SITE_URL } from "@/lib/site";

const DESCRIPTION =
  "Scientific Intelligence platform leveraging authentic NASA microgravity combustion research data from the International Space Station (CIR, MSG) and Glenn Research Center.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "Flame in Freefall — NASA Microgravity Combustion Intelligence",
  description: DESCRIPTION,
  applicationName: "Flame in Freefall",
  openGraph: {
    title: "Flame in Freefall — NASA Microgravity Combustion Intelligence",
    description: DESCRIPTION,
    siteName: "Flame in Freefall",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Flame in Freefall — NASA Microgravity Combustion Intelligence",
    description: DESCRIPTION,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-space-950 text-slate-100 min-h-dvh flex flex-col selection:bg-cyan-500/30 selection:text-nasa-cyan antialiased">
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <Navbar />
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 flex flex-col scroll-mt-16"
        >
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
