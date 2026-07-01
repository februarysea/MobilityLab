import { useMemo, useState } from "react";

import DeckMapPanel from "../components/DeckMapPanel";
import EventPanel from "../components/EventPanel";
import MetricsPanel from "../components/MetricsPanel";
import TimelinePlayer from "../components/TimelinePlayer";
import type { LoadedVisualization, ReplayFrame } from "../types";

export default function ReplayDashboard({ data }: { data: LoadedVisualization }) {
  const times = useMemo(
    () => data.replayFrames.map((frame) => frame.time).sort((a, b) => a - b),
    [data.replayFrames],
  );
  const [currentTime, setCurrentTime] = useState(times[0] ?? 0);
  const currentFrame = useMemo(
    () => frameAt(data.replayFrames, currentTime),
    [data.replayFrames, currentTime],
  );
  const dashboard = data.manifest.dashboards[0];

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>MobilityLab Replay</h1>
          <p>
            {data.manifest.scenario_id} · {data.manifest.variant_id} · run{" "}
            {data.manifest.run_id}
          </p>
        </div>
        <div className="run-stats" aria-label="Run summary">
          <span>{data.network.features.length} map features</span>
          <span>{data.replayFrames.length} frames</span>
          <span>{data.metrics.rows.length} metrics</span>
        </div>
      </header>

      <section className="workspace" aria-label={dashboard?.title ?? "Replay dashboard"}>
        <div className="map-region">
          <DeckMapPanel
            network={data.network}
            facilities={data.facilities}
            currentFrame={currentFrame}
          />
        </div>

        <aside className="side-region">
          <MetricsPanel metrics={data.metrics} />
          <EventPanel
            currentFrame={currentFrame}
            traceEvents={data.traceEvents}
            currentTime={currentTime}
          />
        </aside>
      </section>

      <TimelinePlayer
        times={times}
        currentTime={currentTime}
        onChange={setCurrentTime}
      />
    </main>
  );
}

function frameAt(frames: ReplayFrame[], time: number): ReplayFrame | null {
  return frames.find((frame) => frame.time === time) ?? null;
}
