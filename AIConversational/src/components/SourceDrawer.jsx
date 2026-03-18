export default function SourceDrawer({ sources }) {
  return (
    <aside className="source-drawer">
      <div className="source-drawer-header">
        <p className="panel-label">Retrieved context</p>
        <h2>Sources</h2>
      </div>

      <div className="source-drawer-body">
        {sources.length === 0 ? (
          <div className="source-empty">Ask a question to load the supporting chunks used for the answer.</div>
        ) : (
          sources.map((source) => (
            <article className="source-item" key={`${source.file_name}-${source.chunk_index}`}>
              <div className="source-item-meta">
                <span>{source.file_name}</span>
                <span>Chunk {source.chunk_index}</span>
                <span>Score {source.score.toFixed(4)}</span>
              </div>
              <p>{source.content}</p>
            </article>
          ))
        )}
      </div>
    </aside>
  );
}
