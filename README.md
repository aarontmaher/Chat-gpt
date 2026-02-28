/*
Grappling 3-Tab Web App — Full Project (Canvas)

This single canvas contains the entire repo as concatenated files.
Each file starts with:  // FILE: <path>

To run locally:
  npm install
  npm run dev

Data:
- Uses /public/data/grappling.opml if present
- Falls back to /public/data/sample.json
*/


// FILE: .eslintrc.json
{
  "extends": [
    "next/core-web-vitals"
  ]
}


// FILE: README.md
# Grappling 3-Tab App (Reference / 2D / 3D)

This Next.js + TypeScript app renders the same grappling dataset in 3 synced formats:
1) Reference outline
2) 2D mind map (tree)
3) 3D weighted force graph

## Local run

```bash
npm install
npm run dev
```

Open http://localhost:3000

## OPML

By default, the app loads `/public/data/grappling.opml` if present.
If not present (or parsing fails), it falls back to `/public/data/sample.json`.

To use your Mindomo export:
1. Copy your OPML file into `public/data/grappling.opml` (overwrite).
2. Refresh.

## Stripe (future)

There is a `PaywallPlaceholder` component and architecture notes in `docs/stripe-notes.md`.


// FILE: app/docs/stripe-notes/page.tsx
import fs from "node:fs";
import path from "node:path";

export default function StripeNotesPage() {
  const p = path.join(process.cwd(), "docs", "stripe-notes.md");
  const content = fs.readFileSync(p, "utf-8");
  return (
    <div className="container" style={{ padding: "18px 0 90px" }}>
      <div className="card" style={{ padding: 16 }}>
        <pre style={{ whiteSpace: "pre-wrap", margin: 0, color: "var(--text-dim)", lineHeight: 1.5 }}>{content}</pre>
      </div>
    </div>
  );
}


// FILE: app/globals.css
:root{
  --bg:#0a0c10;
  --surface:#0f1218;
  --surface2:#13161e;
  --border:#1e2535;
  --text:#dde1ed;
  --text-dim:#8890a8;
  --text-muted:#505870;
  --accent:#e8ff47;
  --blue:#47c8ff;
  --green:#34d399;
  --orange:#ff6b35;
  --purple:#a78bfa;
}

*{ box-sizing:border-box; }
html,body{ height:100%; }
body{
  margin:0;
  background:var(--bg);
  color:var(--text);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

a{ color:inherit; text-decoration:none; }
button,input{ font:inherit; }

.container{
  max-width:1200px;
  margin:0 auto;
  padding:0 14px;
}

.card{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:10px;
}

.hr{ height:1px; background:var(--border); }

.kbd{
  font-size:11px;
  color:var(--text-muted);
  border:1px solid var(--border);
  padding:2px 6px;
  border-radius:6px;
}

.pill{
  font-size:11px;
  letter-spacing:0.6px;
  text-transform:uppercase;
  padding:6px 10px;
  border:1px solid var(--border);
  border-radius:999px;
  background:transparent;
  color:var(--text-muted);
  cursor:pointer;
}
.pill.active{ background:var(--accent); color:#000; border-color:var(--accent); }
.pill.blue{ border-color:var(--blue); color:var(--blue); }
.pill.green{ border-color:var(--green); color:var(--green); }
.pill.orange{ border-color:var(--orange); color:var(--orange); }
.pill.purple{ border-color:var(--purple); color:var(--purple); }

.iconBtn{
  height:34px;
  width:34px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  border-radius:8px;
  border:1px solid var(--border);
  background:transparent;
  color:var(--text-muted);
  cursor:pointer;
}
.iconBtn:hover{ border-color:var(--accent); color:var(--accent); }

.textBtn{
  height:34px;
  padding:0 12px;
  border-radius:10px;
  border:1px solid var(--border);
  background:transparent;
  color:var(--text-muted);
  cursor:pointer;
  font-size:12px;
  letter-spacing:0.8px;
  text-transform:uppercase;
}
.textBtn:hover{ border-color:var(--accent); color:var(--accent); }

.input{
  height:36px;
  border-radius:10px;
  border:1px solid var(--border);
  background:var(--bg);
  color:var(--text);
  padding:0 12px;
  outline:none;
}
.input::placeholder{ color:var(--text-muted); }

.stickyTop{
  position:sticky;
  top:0;
  z-index:40;
  background:rgba(15,18,24,0.92);
  backdrop-filter: blur(16px);
  border-bottom:1px solid var(--border);
}

@media (max-width: 720px){
  .hideMobile{ display:none !important; }
}


// FILE: app/layout.tsx
import "./globals.css";

export const metadata = {
  title: "Grappling Instructional Map",
  description: "Reference + 2D mind map + 3D weighted network, synced via Zustand.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}


// FILE: app/page.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import type { GraphModel } from "../lib/model";
import { loadGraph } from "../lib/data";
import { computeVisibleSet } from "../lib/graph";
import { useGrapplingStore } from "../store/useGrapplingStore";
import { TabsNav, type TabKey } from "../components/TabsNav";
import { TopBar } from "../components/TopBar";
import { PaywallPlaceholder } from "../components/PaywallPlaceholder";
import { NodeDetails } from "../components/NodeDetails";
import { ReferenceTab } from "../components/tabs/ReferenceTab";
import { Map2DTab } from "../components/tabs/Map2DTab";
import { Map3DTab } from "../components/tabs/Map3DTab";

export default function HomePage() {
  const store = useGrapplingStore();
  const [tab, setTab] = useState<TabKey>("reference");
  const [graph, setGraph] = useState<GraphModel | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  useEffect(() => {
    loadGraph().then(setGraph).catch((e) => {
      console.error(e);
    });
  }, []);

  const visCounts = useMemo(() => {
    if (!graph) return { visible: 0, total: 0 };
    const vis = computeVisibleSet(graph, {
      expanded: store.expandedNodeIds,
      drillingIds: store.drillingIds,
      learnedIds: store.learnedIds,
      drillingOnly: store.drillingOnly,
      learnedOnly: store.learnedOnly,
    });
    return { visible: vis.visible.size, total: Object.keys(graph.nodesById).length };
  }, [graph, store.drillingIds, store.drillingOnly, store.expandedNodeIds, store.learnedIds, store.learnedOnly]);

  if (!graph) {
    return (
      <div className="container" style={{ padding: "18px 0" }}>
        <div className="card" style={{ padding: 16, color: "var(--text-dim)" }}>
          Loading dataset…
        </div>
      </div>
    );
  }

  const isMobile = typeof window !== "undefined" ? window.innerWidth <= 720 : false;

  return (
    <>
      <TopBar graph={graph} visibleCount={visCounts.visible} totalCount={visCounts.total} />
      <TabsNav value={tab} onChange={setTab} />

      <div className="container" style={{ paddingTop: 12, paddingBottom: 12 }}>
        <PaywallPlaceholder />
      </div>

      <div style={{ display: "flex", minHeight: "calc(100vh - 120px)" }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {tab === "reference" ? (
            <ReferenceTab graph={graph} onOpenDetails={() => setDetailsOpen(true)} />
          ) : null}

          {tab === "map2d" ? <Map2DTab graph={graph} onOpenDetails={() => setDetailsOpen(true)} /> : null}

          {tab === "map3d" ? (
            <Map3DTab
              graph={graph}
              onOpenDetails={() => setDetailsOpen(true)}
              onDeepLinkToReference={(id) => {
                setTab("reference");
                // set query params for reference tab to expand and select
                const url = new URL(window.location.href);
                url.searchParams.set("selectedId", id);
                window.history.replaceState({}, "", url.toString());
              }}
            />
          ) : null}
        </div>

        {/* Desktop details sidebar */}
        <div className="hideMobile">
          <NodeDetails graph={graph} open={detailsOpen} onClose={() => setDetailsOpen(false)} mode="sidebar" />
        </div>

        {/* Mobile details bottom sheet */}
        <div style={{ display: isMobile ? "block" : "none" }}>
          <NodeDetails graph={graph} open={detailsOpen} onClose={() => setDetailsOpen(false)} mode="bottomsheet" />
        </div>
      </div>
    </>
  );
}


// FILE: components/BottomSheet.tsx
"use client";

import { useEffect } from "react";

export function BottomSheet(props: {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") props.onClose();
    };
    if (props.open) window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [props.open, props]);

  if (!props.open) return null;

  return (
    <>
      <div
        onClick={props.onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.55)",
          zIndex: 70,
        }}
      />
      <div
        role="dialog"
        aria-modal="true"
        style={{
          position: "fixed",
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 80,
          background: "rgba(15,18,24,0.98)",
          borderTop: "1px solid var(--border)",
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ padding: "12px 14px", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 34, height: 4, borderRadius: 999, background: "rgba(255,255,255,0.12)", margin: "0 auto" }} />
        </div>
        <div style={{ padding: "0 14px 12px", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ flex: 1, fontSize: 14, letterSpacing: 0.8 }}>{props.title ?? "Details"}</div>
          <button className="iconBtn" onClick={props.onClose} aria-label="Close details">
            ×
          </button>
        </div>
        <div style={{ overflow: "auto", padding: "0 14px 18px" }}>{props.children}</div>
      </div>
    </>
  );
}


// FILE: components/NodeDetails.tsx
"use client";

import { useMemo, useState } from "react";
import type { GraphModel, GrapplingNode } from "../lib/model";
import { useGrapplingStore } from "../store/useGrapplingStore";
import { BottomSheet } from "./BottomSheet";
import { VideoModal } from "./VideoModal";

function findNode(graph: GraphModel, id: string | null): GrapplingNode | null {
  if (!id) return null;
  return graph.nodesById[id] ?? null;
}

export function NodeDetails(props: {
  graph: GraphModel;
  open: boolean;
  onClose: () => void;
  mode: "sidebar" | "bottomsheet";
  onJumpToNode?: (id: string) => void; // used in 3D to deep link to Reference
}) {
  const store = useGrapplingStore();
  const node = findNode(props.graph, store.selectedNodeId);
  const [videoOpen, setVideoOpen] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [videoTitle, setVideoTitle] = useState("");

  const content = useMemo(() => {
    if (!node) {
      return <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Select a node to see details.</div>;
    }

    return (
      <div style={{ display: "grid", gap: 10 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="pill blue" onClick={() => store.toggleDrilling(node.id)}>
            {store.drillingIds.has(node.id) ? "Drilling ✓" : "Drilling"}
          </button>
          <button className="pill" onClick={() => store.toggleLearned(node.id)}>
            {store.learnedIds.has(node.id) ? "Learned ✓" : "Learned"}
          </button>
          <button className="pill" onClick={() => store.toggleExpanded(node.id)}>
            Toggle expand
          </button>
        </div>

        {node.note ? (
          <div className="card" style={{ padding: 12 }}>
            <div style={{ fontSize: 12, letterSpacing: 1, textTransform: "uppercase", color: "var(--text-muted)" }}>Notes</div>
            <div style={{ marginTop: 8, color: "var(--text-dim)", fontSize: 13, lineHeight: 1.5 }}>{node.note}</div>
          </div>
        ) : null}

        {(node.videos ?? []).length ? (
          <div className="card" style={{ padding: 12 }}>
            <div style={{ fontSize: 12, letterSpacing: 1, textTransform: "uppercase", color: "var(--text-muted)" }}>Video</div>
            <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
              {(node.videos ?? []).map((v, idx) => (
                <button
                  key={idx}
                  className={"pill " + (v.kind === "live" ? "green" : "orange")}
                  onClick={() => {
                    setVideoTitle(`${node.title} — ${v.kind === "live" ? "Live Footage" : "Instructional"}`);
                    setVideoUrl(v.url);
                    setVideoOpen(true);
                  }}
                >
                  {v.kind === "live" ? "🎥 Live" : "📖 Instructional"}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {node.offence_ids?.length || node.defence_ids?.length ? (
          <div className="card" style={{ padding: 12 }}>
            <div style={{ fontSize: 12, letterSpacing: 1, textTransform: "uppercase", color: "var(--text-muted)" }}>Offence / Defence</div>

            {node.offence_ids?.length ? (
              <div style={{ marginTop: 10 }}>
                <div style={{ color: "var(--orange)", fontSize: 12, letterSpacing: 1, textTransform: "uppercase" }}>Offence</div>
                <div style={{ marginTop: 6, display: "grid", gap: 6 }}>
                  {node.offence_ids.map((id) => (
                    <button
                      key={id}
                      className="textBtn"
                      style={{ justifyContent: "flex-start", textTransform: "none", letterSpacing: 0, height: "auto", padding: "10px 12px" }}
                      onClick={() => props.onJumpToNode?.(id)}
                    >
                      {id}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {node.defence_ids?.length ? (
              <div style={{ marginTop: 12 }}>
                <div style={{ color: "var(--blue)", fontSize: 12, letterSpacing: 1, textTransform: "uppercase" }}>Defence</div>
                <div style={{ marginTop: 6, display: "grid", gap: 6 }}>
                  {node.defence_ids.map((id) => (
                    <button
                      key={id}
                      className="textBtn"
                      style={{ justifyContent: "flex-start", textTransform: "none", letterSpacing: 0, height: "auto", padding: "10px 12px" }}
                      onClick={() => props.onJumpToNode?.(id)}
                    >
                      {id}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    );
  }, [node, props, store]);

  if (props.mode === "bottomsheet") {
    return (
      <>
        <BottomSheet open={props.open} onClose={props.onClose} title={node?.title ?? "Details"}>
          {content}
        </BottomSheet>
        <VideoModal open={videoOpen} onClose={() => setVideoOpen(false)} title={videoTitle} url={videoUrl} />
      </>
    );
  }

  return (
    <>
      <div
        style={{
          width: 340,
          borderLeft: "1px solid var(--border)",
          background: "rgba(15,18,24,0.92)",
          backdropFilter: "blur(16px)",
          padding: 14,
          overflow: "auto",
          display: props.open ? "block" : "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ fontSize: 14, flex: 1, color: "var(--text-dim)" }}>{node?.title ?? "Details"}</div>
          <button className="iconBtn" onClick={props.onClose} aria-label="Close details">
            ×
          </button>
        </div>
        <div style={{ marginTop: 12 }}>{content}</div>
      </div>
      <VideoModal open={videoOpen} onClose={() => setVideoOpen(false)} title={videoTitle} url={videoUrl} />
    </>
  );
}


// FILE: components/PaywallPlaceholder.tsx
export function PaywallPlaceholder() {
  return (
    <div className="card" style={{ padding: 14 }}>
      <div style={{ fontSize: 12, letterSpacing: 1, textTransform: "uppercase", color: "var(--text-muted)" }}>
        Paywall placeholder
      </div>
      <div style={{ marginTop: 8, color: "var(--text-dim)", lineHeight: 1.5, fontSize: 13 }}>
        Stripe subscription (A$5/week) is not implemented yet. This component is here to reserve the layout and
        show where entitlement checks will go.
      </div>
      <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button className="textBtn" disabled style={{ opacity: 0.55, cursor: "not-allowed" }}>
          Subscribe (soon)
        </button>
        <a className="textBtn" href="/docs/stripe-notes" style={{ display: "inline-flex", alignItems: "center" }}>
          Architecture notes
        </a>
      </div>
    </div>
  );
}


// FILE: components/TabsNav.tsx
"use client";

import clsx from "clsx";

export type TabKey = "reference" | "map2d" | "map3d";

const tabs: { key: TabKey; label: string; emoji: string }[] = [
  { key: "reference", label: "Reference", emoji: "📋" },
  { key: "map2d", label: "2D Map", emoji: "✦" },
  { key: "map3d", label: "3D Graph", emoji: "⬡" },
];

export function TabsNav(props: { value: TabKey; onChange: (v: TabKey) => void }) {
  return (
    <>
      {/* Desktop / tablet top tabs */}
      <div className="hideMobile stickyTop" style={{ padding: "0 14px" }}>
        <div style={{ display: "flex", gap: 6, overflowX: "auto", padding: "10px 0" }}>
          {tabs.map((t) => (
            <button
              key={t.key}
              className={clsx("pill", props.value === t.key && "active")}
              onClick={() => props.onChange(t.key)}
            >
              {t.emoji} {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Mobile bottom nav */}
      <div
        className="card"
        style={{
          position: "fixed",
          left: 10,
          right: 10,
          bottom: 10,
          zIndex: 60,
          padding: 6,
          display: "none",
        }}
      >
        {/* show only on small screens via inline media query */}
      </div>

      <style jsx>{`
        @media (max-width: 720px) {
          div.card {
            display: flex !important;
            justify-content: space-around;
          }
        }
      `}</style>

      <div
        className="card"
        style={{
          position: "fixed",
          left: 10,
          right: 10,
          bottom: 10,
          zIndex: 60,
          padding: 6,
          display: "flex",
          justifyContent: "space-around",
        }}
      >
        {tabs.map((t) => (
          <button
            key={t.key}
            className={clsx("pill", props.value === t.key && "active")}
            style={{ flex: 1, margin: "0 4px", padding: "10px 10px" }}
            onClick={() => props.onChange(t.key)}
          >
            <div style={{ fontSize: 14 }}>{t.emoji}</div>
            <div style={{ fontSize: 10, marginTop: 2 }}>{t.label}</div>
          </button>
        ))}
      </div>
    </>
  );
}


// FILE: components/TopBar.tsx
"use client";

import { useMemo, useState } from "react";
import type { GraphModel } from "../lib/model";
import { useGrapplingStore } from "../store/useGrapplingStore";
import { FiltersDrawer } from "./filters/FiltersDrawer";

export function TopBar(props: { graph: GraphModel; visibleCount: number; totalCount: number }) {
  const store = useGrapplingStore();
  const [filtersOpen, setFiltersOpen] = useState(false);

  const allIds = useMemo(() => Object.keys(props.graph.nodesById), [props.graph.nodesById]);

  return (
    <div className="stickyTop">
      <div className="container" style={{ paddingTop: 10, paddingBottom: 10, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <div style={{ fontSize: 18, letterSpacing: 2, color: "var(--accent)", fontWeight: 700 }}>GRAPPLING</div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
            Visible {props.visibleCount} / {props.totalCount}
          </div>
        </div>

        <div style={{ flex: 1 }} />

        <button className="textBtn" onClick={() => store.collapseAllToRoot(props.graph.rootId)}>
          Collapse all
        </button>

        <button className="textBtn" onClick={() => store.expandAll(allIds, props.graph.rootId)}>
          Expand all
        </button>

        <button className="textBtn" onClick={() => setFiltersOpen(true)}>
          Filters
        </button>
      </div>

      <FiltersDrawer open={filtersOpen} onClose={() => setFiltersOpen(false)} />
    </div>
  );
}


// FILE: lib/slug.ts
export function slugify(input: string): string {
  return input
    .trim()
    .toLowerCase()
    .replace(/^[-•]\s*/, "")
    .replace(/\[[^\]]+\]/g, (m) => m.replace(/\s+/g, "-"))
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}


// FILE: next.config.mjs
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};
export default nextConfig;


// FILE: tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "es2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "types": ["node"]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
