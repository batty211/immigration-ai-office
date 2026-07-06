"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { buildApiUrl } from "../lib/api";

type HealthState = "loading" | "ok" | "error";

export default function Home() {
  const [status, setStatus] = useState<HealthState>("loading");

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const response = await fetch(buildApiUrl("/health"), { cache: "no-store" });
        if (!response.ok) {
          throw new Error("Health check failed");
        }

        const data: { status?: string } = await response.json();
        if (!cancelled && data.status === "ok") {
          setStatus("ok");
          return;
        }

        throw new Error("Unexpected response");
      } catch {
        if (!cancelled) {
          setStatus("error");
        }
      }
    }

    loadHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Immigration AI Office</p>
        <h1>Immigration AI Office</h1>
        <p className="subtitle">Executive AI Secretary</p>
      </section>

      <section className="statusCard" aria-label="Backend Status">
        <div>
          <p className="cardLabel">Backend Status</p>
          <h2>{status === "loading" ? "Checking..." : status === "ok" ? "Healthy" : "Unavailable"}</h2>
        </div>
        <span className={`pill ${status}`}>{status === "ok" ? "healthy" : status}</span>
      </section>

      <section className="settingsCard" aria-label="Integrations">
        <div>
          <p className="cardLabel">Integrations</p>
          <h2>Gmail Settings</h2>
          <p className="supportingText">Connect a personal Gmail account and enable inbox watch from one place.</p>
        </div>
        <Link className="primaryButton" href="/gmail-settings">
          Open Settings
        </Link>
      </section>
    </main>
  );
}
