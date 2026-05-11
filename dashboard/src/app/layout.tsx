import type { Metadata } from "next";

import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Loang Agent",
  description: "Dashboard placeholder shipped with the Loang IA template-agent.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
