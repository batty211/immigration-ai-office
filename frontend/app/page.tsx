"use client";

import Link from "next/link";
import { startTransition, useEffect, useState } from "react";

import { buildApiUrl } from "../lib/api";

type DashboardMessage = {
  id: number;
  gmail_message_id: string;
  subject: string | null;
  sender: string | null;
  recipients: string | null;
  snippet: string | null;
  body: string;
  received_at: string | null;
  processing_status: string;
  attachments: Array<{ filename?: string; mime_type?: string; size?: number }>;
  is_unread: boolean;
  analysis: {
    summary: string;
    category: string;
    priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    requires_action: boolean;
    requires_reply: boolean;
    deadline: string | null;
    recommended_action: string;
    recommended_assignee: string;
    tags: string[];
    confidence: number;
  } | null;
};

type DashboardData = {
  connected: boolean;
  email: string | null;
  last_sync: string | null;
  metrics: {
    stored: number;
    processed: number;
    unread: number;
  };
  messages: DashboardMessage[];
};

const EMPTY_DASHBOARD: DashboardData = {
  connected: false,
  email: null,
  last_sync: null,
  metrics: {
    stored: 0,
    processed: 0,
    unread: 0,
  },
  messages: [],
};

export default function Home() {
  const [dashboard, setDashboard] = useState<DashboardData>(EMPTY_DASHBOARD);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        const response = await fetch(buildApiUrl("/gmail/dashboard"), { cache: "no-store" });
        if (!response.ok) {
          throw new Error("Unable to load dashboard");
        }

        const data: DashboardData = await response.json();
        if (!cancelled) {
          setDashboard(data);
          setMessage("");
        }
      } catch (error) {
        if (!cancelled) {
          setMessage(error instanceof Error ? error.message : "Unable to load dashboard");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    startTransition(() => {
      loadDashboard();
    });

    return () => {
      cancelled = true;
    };
  }, []);

  async function syncInbox() {
    setSyncing(true);
    setMessage("");

    try {
      const response = await fetch(buildApiUrl("/gmail/sync"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "Unable to sync inbox");
      }

      const refreshed = await fetch(buildApiUrl("/gmail/dashboard"), { cache: "no-store" });
      if (!refreshed.ok) {
        throw new Error("Inbox synced, but the dashboard could not be refreshed");
      }

      const nextDashboard: DashboardData = await refreshed.json();
      setDashboard(nextDashboard);
      setMessage(`Inbox synced. ${data.stored} new message${data.stored === 1 ? "" : "s"} stored.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to sync inbox");
    } finally {
      setSyncing(false);
    }
  }

  const connected = dashboard.connected;
  const lastSync = dashboard.last_sync ? new Date(dashboard.last_sync).toLocaleString() : "Never";

  return (
    <main className="shell dashboardShell">
      <section className="hero">
        <p className="eyebrow">Operations</p>
        <h1>Email Dashboard</h1>
        <p className="subtitle">Every Gmail message stored, processed, and surfaced here as a real system record.</p>
      </section>

      <section className="statusCard dashboardHeader" aria-label="Dashboard Status">
        <div>
          <p className="cardLabel">Connected Inbox</p>
          <h2>{loading ? "Loading..." : connected ? dashboard.email : "No Gmail account connected"}</h2>
          <p className="supportingText">Last Sync: {lastSync}</p>
        </div>
        <div className="buttonRow">
          <button
            className="primaryButton"
            disabled={!connected || syncing}
            onClick={syncInbox}
            type="button"
          >
            {syncing ? "Syncing..." : "Sync Inbox"}
          </button>
          <Link className="secondaryButton" href="/gmail-settings">
            Gmail Settings
          </Link>
        </div>
      </section>

      <section className="metricGrid" aria-label="Workflow Metrics">
        <article className="statusCard stackCard metricCard">
          <p className="cardLabel">Stored</p>
          <h2>{dashboard.metrics.stored}</h2>
          <p className="supportingText">Real Gmail messages committed to the database.</p>
        </article>

        <article className="statusCard stackCard metricCard">
          <p className="cardLabel">Analyzed</p>
          <h2>{dashboard.messages.filter((message) => message.analysis !== null).length}</h2>
          <p className="supportingText">Messages already converted into executive work items.</p>
        </article>

        <article className="statusCard stackCard metricCard">
          <p className="cardLabel">Unread</p>
          <h2>{dashboard.metrics.unread}</h2>
          <p className="supportingText">Messages still carrying Gmail&apos;s unread label.</p>
        </article>
      </section>

      <section className="statusCard stackCard" aria-label="Inbox Records">
        <div className="listHeader">
          <div>
            <p className="cardLabel">Inbox Records</p>
            <h2>Recent Messages</h2>
          </div>
          <span className={`pill ${connected ? "ok" : "error"}`}>{connected ? "live" : "offline"}</span>
        </div>

        {message ? <p className="inlineMessage">{message}</p> : null}

        {!connected && !loading ? (
          <p className="supportingText">
            Connect Gmail in settings, enable watch, and new inbox messages will start landing here as stored records.
          </p>
        ) : null}

        {connected && dashboard.messages.length === 0 && !loading ? (
          <p className="supportingText">No stored messages yet. Run a sync or wait for the next Gmail notification.</p>
        ) : null}

        <div className="messageList">
          {dashboard.messages.map((email) => (
            <article className="messageCard" key={email.gmail_message_id}>
              <div className="messageTopRow">
                <div>
                  <h3>{email.subject || "(No subject)"}</h3>
                  <p className="supportingText">{email.sender || "Unknown sender"}</p>
                </div>
                <div className="messageMeta">
                  <span className={`pill ${email.is_unread ? "loading" : "ok"}`}>
                    {email.is_unread ? "unread" : "read"}
                  </span>
                  <span className="metaText">
                    {email.received_at ? new Date(email.received_at).toLocaleString() : "Unknown time"}
                  </span>
                </div>
              </div>

              <p className="messageSnippet">{email.snippet || email.body || "No preview available."}</p>

              {email.analysis ? (
                <div className="messageFooter">
                  <span className={`pill ${email.analysis.priority === "CRITICAL" || email.analysis.priority === "HIGH" ? "error" : email.analysis.priority === "MEDIUM" ? "loading" : "ok"}`}>
                    {email.analysis.priority}
                  </span>
                  <span className="metaText">
                    Deadline: {email.analysis.deadline ?? "None"}
                  </span>
                </div>
              ) : (
                <div className="messageFooter">
                  <span className="metaText">Analysis pending</span>
                  <span className="metaText">Attachments: {email.attachments.length}</span>
                </div>
              )}

              <div className="messageFooter">
                <span className="metaText">
                  Summary: {email.analysis?.summary ?? "Executive summary not available yet."}
                </span>
              </div>
              <div className="messageFooter">
                <span className="metaText">
                  Recommended Action: {email.analysis?.recommended_action ?? "Pending analysis"}
                </span>
              </div>
              <div className="messageFooter">
                <span className="metaText">
                  Category: {email.analysis?.category ?? "Pending"}
                </span>
                <span className="metaText">
                  Reply: {email.analysis ? (email.analysis.requires_reply ? "Yes" : "No") : "Pending"}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
