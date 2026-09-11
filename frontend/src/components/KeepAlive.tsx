"use client";
import { useEffect } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const FRONTEND_URL = typeof window !== "undefined" ? window.location.origin : "";
const INTERVAL_MS = 14 * 60 * 1000; // 14 minutes

export default function KeepAlive() {
  useEffect(() => {
    const ping = async () => {
      try {
        await fetch(`${BACKEND_URL}/ping`);
        await fetch(`${FRONTEND_URL}/api/ping`);
      } catch {
        // silent fail — just a keep-alive ping
      }
    };

    // Ping immediately on mount
    ping();

    // Then every 14 minutes
    const interval = setInterval(ping, INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  return null; // invisible component
}
