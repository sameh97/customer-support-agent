// Shown when the agent pauses to ask the customer before acting
// (the LangGraph interrupt in src/graph.py).
export default function ConfirmCard({ action, status, onAnswer, disabled }) {
  const answered = status !== 'pending'

  return (
    <section className={`confirm ${answered ? 'confirm--answered' : ''}`} aria-label={action.title}>
      <h2 className="confirm__title">{action.title}</h2>
      {action.description && <p className="confirm__text">{action.description}</p>}

      {answered ? (
        <p className="confirm__status">
          {status === 'approved' ? action.confirm_label : action.cancel_label}
        </p>
      ) : (
        <div className="confirm__actions">
          <button type="button" className="btn btn--primary" onClick={() => onAnswer(true)} disabled={disabled}>
            {action.confirm_label}
          </button>
          <button type="button" className="btn btn--secondary" onClick={() => onAnswer(false)} disabled={disabled}>
            {action.cancel_label}
          </button>
        </div>
      )}
    </section>
  )
}
