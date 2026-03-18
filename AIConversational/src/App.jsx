import { useEffect, useMemo, useState } from "react";
import ChatComposer from "./components/ChatComposer";
import MessageThread from "./components/MessageThread";
import SessionSidebar from "./components/SessionSidebar";
import SourceDrawer from "./components/SourceDrawer";
import { askQuestion } from "./services/api";

const STORAGE_KEY = "centene-knowledgebase-sessions";

function createSession(title = "New chat") {
  return {
    id: crypto.randomUUID(),
    title,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: [],
    sources: []
  };
}

function buildSessionTitle(question) {
  return question.length > 40 ? `${question.slice(0, 40)}...` : question;
}

export default function App() {
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) {
      return [createSession()];
    }

    try {
      const parsed = JSON.parse(saved);
      return parsed.length ? parsed : [createSession()];
    } catch {
      return [createSession()];
    }
  });
  const [activeSessionId, setActiveSessionId] = useState(() => sessions[0]?.id);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  }, [sessions]);

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? sessions[0],
    [activeSessionId, sessions]
  );

  function createNewSession() {
    const nextSession = createSession();
    setSessions((current) => [nextSession, ...current]);
    setActiveSessionId(nextSession.id);
  }

  function updateActiveSession(updater) {
    setSessions((current) =>
      current.map((session) => {
        if (session.id !== activeSessionId) {
          return session;
        }
        return updater(session);
      })
    );
  }

  async function handleSubmit(question) {
    if (!activeSession) {
      return;
    }

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question
    };

    updateActiveSession((session) => ({
      ...session,
      title: session.messages.length === 0 ? buildSessionTitle(question) : session.title,
      updatedAt: new Date().toISOString(),
      messages: [...session.messages, userMessage]
    }));

    setLoading(true);
    try {
      const response = await askQuestion(question);
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer
      };

      updateActiveSession((session) => ({
        ...session,
        updatedAt: new Date().toISOString(),
        messages: [...session.messages, assistantMessage],
        sources: response.sources
      }));
    } catch (error) {
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: error.message || "Something went wrong while contacting the API."
      };

      updateActiveSession((session) => ({
        ...session,
        updatedAt: new Date().toISOString(),
        messages: [...session.messages, assistantMessage]
      }));
    } finally {
      setLoading(false);
    }
  }

  const isEmpty = !activeSession || activeSession.messages.length === 0;

  return (
    <div className="layout-shell">
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onNewChat={createNewSession}
        onSelectSession={setActiveSessionId}
      />

      <main className="main-shell">
        <header className="main-header">
          <h1>Centene KnowledgeBase</h1>
        </header>

        <section className={`conversation-shell ${isEmpty ? "empty" : ""}`}>
          {isEmpty ? (
            <div className="empty-state">
              <h2>What can I help you find today?</h2>
              <p>Ask questions across indexed enterprise documents and get grounded answers with source context.</p>
            </div>
          ) : (
            <MessageThread messages={activeSession.messages} loading={loading} />
          )}

          <ChatComposer onSubmit={handleSubmit} disabled={loading} compact={!isEmpty} />
        </section>
      </main>

      <SourceDrawer sources={activeSession?.sources ?? []} />
    </div>
  );
}
