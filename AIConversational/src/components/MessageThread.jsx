export default function MessageThread({ messages, loading }) {
  return (
    <div className="message-thread">
      {messages.map((message) => (
        <article key={message.id} className={`message-row ${message.role}`}>
          <div className="message-bubble">
            <div className="message-avatar">{message.role === "user" ? "You" : "AI"}</div>
            <div className="message-content">
              <p>{message.content}</p>
            </div>
          </div>
        </article>
      ))}
      {loading ? <div className="loading-message">Thinking through the knowledge base...</div> : null}
    </div>
  );
}
