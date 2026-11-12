import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Flame in Freefall — NASA Microgravity Combustion Intelligence",
  description:
    "Scientific Intelligence platform leveraging authentic NASA microgravity combustion research data from the International Space Station (CIR, MSG) and Glenn Research Center.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-space-950 text-slate-100 min-h-screen flex flex-col selection:bg-cyan-500/30 selection:text-nasa-cyan antialiased">
        <Navbar />
        <main className="flex-1 flex flex-col">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
