import { useState } from "react";
import { Star } from "lucide-react";

export default function FeedbackForm({ eventTitle, onSubmit }) {
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState("");
  const [sent, setSent] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!rating) return;
    onSubmit?.({ rating, comment });
    setSent(true);
  };

  if (sent) {
    return (
      <div className="card animate-fade-up" style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ 
          width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(34, 197, 94, 0.1)', 
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem auto' 
        }}>
          <Star size={32} color="rgb(34, 197, 94)" fill="rgb(34, 197, 94)" />
        </div>
        <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Thanks for your feedback!</h3>
        <p style={{ color: 'var(--text-secondary)' }}>You rated this event {rating}/5.</p>
      </div>
    );
  }

  return (
    <form className="card" onSubmit={handleSubmit} style={{ padding: '1.5rem' }}>
      <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
        Rate {eventTitle ? `“${eventTitle}”` : "this event"}
      </h3>

      <div 
        role="radiogroup" 
        aria-label="Rating"
        style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}
      >
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={rating === n}
            aria-label={`${n} star${n > 1 ? "s" : ""}`}
            onMouseEnter={() => setHover(n)}
            onMouseLeave={() => setHover(0)}
            onClick={() => setRating(n)}
            style={{
              background: 'none',
              border: 'none',
              padding: '0.5rem',
              cursor: 'pointer',
              color: n <= (hover || rating) ? 'var(--primary-color)' : 'var(--border-color)',
              transition: 'all 0.2s ease',
              transform: n <= hover ? 'scale(1.1)' : 'scale(1)'
            }}
          >
            <Star 
              size={32} 
              fill={n <= (hover || rating) ? 'currentColor' : 'none'} 
              strokeWidth={1.5}
            />
          </button>
        ))}
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label htmlFor="comment" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
          Comments (optional)
        </label>
        <textarea
          id="comment"
          rows="3"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="What did you like? What could be better?"
          style={{ 
            width: '100%', 
            padding: '0.75rem 1rem', 
            borderRadius: '8px', 
            border: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            fontSize: '1rem',
            resize: 'vertical',
            fontFamily: 'inherit'
          }}
        />
      </div>

      <button className="btn btn-primary" type="submit" disabled={!rating} style={{ width: '100%' }}>
        Submit feedback
      </button>
    </form>
  );
}
