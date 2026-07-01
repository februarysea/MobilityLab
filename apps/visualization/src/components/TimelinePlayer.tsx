import { useEffect, useMemo, useState } from "react";

interface TimelinePlayerProps {
  times: number[];
  currentTime: number;
  onChange: (time: number) => void;
}

export default function TimelinePlayer({
  times,
  currentTime,
  onChange,
}: TimelinePlayerProps) {
  const [playing, setPlaying] = useState(false);
  const currentIndex = Math.max(0, times.indexOf(currentTime));
  const maxIndex = Math.max(0, times.length - 1);
  const timeLabel = useMemo(() => formatSeconds(currentTime), [currentTime]);

  useEffect(() => {
    if (!playing || times.length <= 1) {
      return undefined;
    }
    const interval = window.setInterval(() => {
      const index = Math.max(0, times.indexOf(currentTime));
      const nextIndex = index >= maxIndex ? 0 : index + 1;
      onChange(times[nextIndex]);
    }, 900);
    return () => window.clearInterval(interval);
  }, [playing, times, currentTime, maxIndex, onChange]);

  return (
    <footer className="timeline">
      <button
        className="primary-button"
        type="button"
        onClick={() => setPlaying((value) => !value)}
      >
        {playing ? "Pause" : "Play"}
      </button>
      <div className="timeline-main">
        <div className="timeline-meta">
          <span>{timeLabel}</span>
          <span>
            frame {times.length === 0 ? 0 : currentIndex + 1} / {times.length}
          </span>
        </div>
        <input
          aria-label="Replay frame"
          type="range"
          min={0}
          max={maxIndex}
          value={currentIndex}
          disabled={times.length === 0}
          onChange={(event) => onChange(times[Number(event.target.value)] ?? 0)}
        />
      </div>
    </footer>
  );
}

function formatSeconds(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}
