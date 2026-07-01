import type { ReplayFrame, SimulationEvent } from "../types";

interface EventPanelProps {
  currentFrame: ReplayFrame | null;
  traceEvents: SimulationEvent[];
  currentTime: number;
}

export default function EventPanel({
  currentFrame,
  traceEvents,
  currentTime,
}: EventPanelProps) {
  const currentEvents = currentFrame?.events ?? [];
  const nearbyEvents = traceEvents
    .filter((event) => typeof event.time === "number" && event.time <= currentTime)
    .slice(-6)
    .reverse();

  return (
    <section className="panel event-panel">
      <header className="panel-header">
        <h2>Events</h2>
        <span>{currentEvents.length}</span>
      </header>
      <div className="event-section">
        <h3>Current frame</h3>
        <EventList events={currentEvents} emptyText="No events at this time." />
      </div>
      <div className="event-section">
        <h3>Recent trace</h3>
        <EventList events={nearbyEvents} emptyText="No trace events yet." />
      </div>
    </section>
  );
}

function EventList({
  events,
  emptyText,
}: {
  events: SimulationEvent[];
  emptyText: string;
}) {
  if (events.length === 0) {
    return <p className="empty-text">{emptyText}</p>;
  }
  return (
    <ul className="event-list">
      {events.map((event, index) => (
        <li key={`${event.time ?? "na"}-${event.sequence ?? index}`}>
          <span className="event-topic">{event.topic ?? "event"}</span>
          <span className="event-time">t={event.time ?? "?"}</span>
          <p>{eventSummary(event)}</p>
        </li>
      ))}
    </ul>
  );
}

function eventSummary(event: SimulationEvent): string {
  const payload = event.payload ?? {};
  const movementId = stringValue(payload.movement_id);
  const agentId = stringValue(payload.agent_id);
  const destination = payload.destination;
  if (movementId && agentId) {
    return `${agentId} · ${movementId}`;
  }
  if (agentId) {
    return agentId;
  }
  if (typeof destination === "object" && destination !== null) {
    return JSON.stringify(destination);
  }
  return JSON.stringify(payload);
}

function stringValue(value: unknown): string {
  if (typeof value === "string" && value.length > 0) {
    return value;
  }
  return "";
}
