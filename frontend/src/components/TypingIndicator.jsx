import Avatar from './Avatar.jsx'

export default function TypingIndicator({ name }) {
  return (
    <div className="message message--agent">
      <Avatar name={name} />
      <div className="message__body">
        <div className="bubble bubble--agent typing" role="status" aria-label={`${name} is typing`}>
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  )
}
