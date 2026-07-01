import { useEffect, useState } from "react";

import { loadVisualization } from "./data/loaders";
import type { LoadedVisualization } from "./types";
import ReplayDashboard from "./views/ReplayDashboard";

type LoadState =
  | { status: "loading" }
  | { status: "loaded"; data: LoadedVisualization }
  | { status: "error"; message: string };

export default function App() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    loadVisualization()
      .then((data) => {
        if (!cancelled) {
          setState({ status: "loaded", data });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : String(error),
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") {
    return <StatusScreen title="Loading replay" detail="Reading manifest and datasets." />;
  }

  if (state.status === "error") {
    return (
      <StatusScreen
        title="Replay unavailable"
        detail={state.message}
        secondary="Set CAMPUSSOCIETY_RUN_DIR to a run directory with visualization_manifest.json, or pass ?manifest= to an HTTP-served manifest URL."
      />
    );
  }

  return <ReplayDashboard data={state.data} />;
}

function StatusScreen({
  title,
  detail,
  secondary,
}: {
  title: string;
  detail: string;
  secondary?: string;
}) {
  return (
    <main className="status-screen">
      <section className="status-panel">
        <h1>{title}</h1>
        <p>{detail}</p>
        {secondary ? <p className="status-secondary">{secondary}</p> : null}
      </section>
    </main>
  );
}
