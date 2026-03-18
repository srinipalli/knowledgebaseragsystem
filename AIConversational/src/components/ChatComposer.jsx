import { useState } from "react";

export default function ChatComposer({ onSubmit, disabled, compact }) {
  const [value, setValue] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) {
      return;
    }
    onSubmit(trimmed);
    setValue("");
  }

  return (
    <form className={`composer ${compact ? "compact" : ""}`} onSubmit={handleSubmit}>
      <div className="composer-shell">
        <button className="composer-icon" type="button" aria-label="Add prompt">
          +
        </button>
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Ask anything"
          rows={1}
          disabled={disabled}
        />
        <button className="composer-submit" type="submit" disabled={disabled || !value.trim()}>
          Send
        </button>
      </div>
    </form>
  );
}
