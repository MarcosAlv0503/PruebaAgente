import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Nav from "@/components/nav";

import "@/styles/globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Loang · Soporte Operativo",
  description: "Dashboard de incidencias ecommerce — Loang IA",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning className={inter.variable}>
      <body className="min-h-screen antialiased">
        <Nav />
        {children}
      </body>
    </html>
  );
}
