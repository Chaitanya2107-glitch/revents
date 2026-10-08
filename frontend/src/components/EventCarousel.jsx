import { useId, useRef, useState } from "react";
import EventCard from "./EventCard.jsx";

export default function EventCarousel({ events }) {
  const trackRef = useRef(null);
  const trackId = useId();
  const [active, setActive] = useState(0);

  if (events.length === 0) return null;

  const show = (index) => {
    const track = trackRef.current;
    const next = Math.max(0, Math.min(events.length - 1, index));
    track.scrollTo({
      left: track.children[next].offsetLeft - track.children[0].offsetLeft,
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    });
  };

  const handleScroll = (event) => {
    const track = event.currentTarget;
    const step = events.length > 1
      ? track.children[1].offsetLeft - track.children[0].offsetLeft
      : track.clientWidth;
    setActive(Math.max(0, Math.min(events.length - 1, Math.round(track.scrollLeft / step))));
  };

  const handleKeyDown = (event) => {
    if (event.target !== event.currentTarget) return;
    const destinations = { ArrowLeft: active - 1, ArrowRight: active + 1, Home: 0, End: events.length - 1 };
    if (event.key in destinations) {
      event.preventDefault();
      show(destinations[event.key]);
    }
  };

  return (
    <section className="carousel" aria-label="Campus spotlight" aria-roledescription="carousel">
      <div className="carousel__header">
        <h2>Campus spotlight</h2>
        <span className="carousel__count" aria-hidden="true">
          {String(active + 1).padStart(2, "0")} <span className="muted">/ {String(events.length).padStart(2, "0")}</span>
        </span>
      </div>
      <div
        id={trackId}
        ref={trackRef}
        className="carousel__track"
        tabIndex={0}
        aria-label="Featured events. Use left and right arrow keys to browse."
        onScroll={handleScroll}
        onKeyDown={handleKeyDown}
      >
        {events.map((event, index) => (
          <div
            key={event.id}
            className="carousel__slide"
            role="group"
            aria-roledescription="slide"
            aria-label={`${index + 1} of ${events.length}`}
          >
            <EventCard event={event} />
          </div>
        ))}
      </div>
      <div className="carousel__footer">
        <span className="muted small">Swipe or use the arrows to explore</span>
        <div className="carousel__controls">
          <button
            type="button"
            className="carousel__arrow"
            aria-label="Previous featured event"
            aria-controls={trackId}
            disabled={active === 0}
            onClick={() => show(active - 1)}
          >
            <span aria-hidden="true">←</span>
          </button>
          <button
            type="button"
            className="carousel__arrow"
            aria-label="Next featured event"
            aria-controls={trackId}
            disabled={active === events.length - 1}
            onClick={() => show(active + 1)}
          >
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
      <p className="sr-only" role="status" aria-atomic="true">
        Featured event {active + 1} of {events.length}: {events[active].title}
      </p>
    </section>
  );
}
