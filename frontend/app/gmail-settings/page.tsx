"use client";

import { startTransition, useEffect, useState } from "react";

type GmailStatus = {
  connected: boolean;
  email?: string | null;
  last_sync?: string | null;
};

export default function GmailSettingsPage() {
  const [status, setStatus] = useState<GmailStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [watchState, setWatchState] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    async function loadStatus() {
      try {
        const response = await fetch("/gmail/status", { cache: "no-store" });
        if (!response.ok) {
          throw new Error("Unable to load Gmail status");
        }

        const data: GmailStatus = await response.json();
        if (!cancelled) {
          setStatus(data);
          setMessage("");
        }
      } catch (error) {
        if (!cancelled) {
          setMessage(error instanceof Error ? error.message : "Unable to load Gmail status");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    startTransition(() => {
      loadStatus();
    });

    return () => {
      cancelled = true;
    };
  }, []);

  async function enableWatch() {
    setWatchState("loading");
    setMessage("");

    try {
      const response = await fetch("/gmail/watch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "Unable to start Gmail watch");
      }

      setWatchState("success");
      setStatus((current) =>
        current
          ? {
              ...current,
              last_sync: new Date().toISOString(),
            }
          : current,
      );
      setMessage("Gmail watch is active.");
    } catch (error) {
      setWatchState("error");
      setMessage(error instanceof Error ? error.message : "Unable to start Gmail watch");
    }
  }

  const connected = Boolean(status?.connected);
  const lastSync = status?.last_sync ? new Date(status.last_sync).toLocaleString() : "Never";

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Settings</p>
        <h1>Gmail Settings</h1>
        <p className="subtitle">Connect Gmail with OAuth2, store the refresh token securely, and enable new email watch.</p>
      </section>

      <section className="settingsGrid" aria-label="Gmail Status">
        <article className="statusCard stackCard">
          <p className="cardLabel">Connection</p>
          <h2>{loading ? "Checking..." : connected ? "Connected" : "Disconnected"}</h2>
          <p className="supportingText">{status?.email ?? "No Gmail account connected yet."}</p>
          <div className="metaRow">
            <span className={`pill ${connected ? "ok" : "error"}`}>{connected ? "connected" : "disconnected"}</span>
            <span className="metaText">Last Sync: {lastSync}</span>
          </div>
        </article>

        <article className="statusCard stackCard">
          <p className="cardLabel">Actions</p>
          <h2>Connect and Watch</h2>
          <p className="supportingText">Use Google login for a personal Gmail account, then register Gmail Watch API for new messages.</p>
          <div className="buttonRow">
            <a className="primaryButton" href="/gmail/connect">
              Connect Gmail
            </a>
            <button
              className="secondaryButton"
              onClick={enableWatch}
              disabled={!connected || watchState === "loading"}
              type="button"
            >
              {watchState === "loading" ? "Starting..." : "Enable Watch"}
            </button>
          </div>
          {message ? <p className="inlineMessage">{message}</p> : null}
        </article>
      </section>
    </main>
  );
}
