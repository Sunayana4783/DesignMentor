import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DesignMentor AI",
  description: "Agentic AI system for learning Low-Level and High-Level Design",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-surface text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
