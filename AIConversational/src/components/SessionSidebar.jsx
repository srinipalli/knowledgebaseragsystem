export default function SessionSidebar({ sessions, activeSessionId, onNewChat, onSelectSession }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <div className="sidebar-brand">
          <div className="sidebar-logo">CK</div>
          <span>Centene KnowledgeBase</span>
        </div>
        <button className="new-chat-button" onClick={onNewChat}>
          + New chat
        </button>
      </div>

      <div className="sidebar-section">
        <p className="sidebar-label">Sessions</p>
        <div className="session-list">
          {sessions.map((session) => (
            <button
              key={session.id}
              className={`session-item ${session.id === activeSessionId ? "active" : ""}`}
              onClick={() => onSelectSession(session.id)}
            >
              <span className="session-title">{session.title}</span>
              <span className="session-meta">
                {session.messages.length ? `${session.messages.length} messages` : "Empty conversation"}
              </span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
