import Markdown from 'react-markdown'
import Avatar from './Avatar.jsx'

const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })

// Open links from the agent in a new tab so the chat stays put.
const markdownComponents = {
  a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer" />,
}

export default function Message({ kind, name, text, time }) {
  if (kind === 'user') {
    return (
      <div className="message message--user">
        <div className="bubble bubble--user">{text}</div>
        {time && <span className="time">{formatTime(time)}</span>}
      </div>
    )
  }

  return (
    <div className="message message--agent">
      <Avatar name={name} />
      <div className="message__body">
        <span className="sender">{name}</span>
        <div className="bubble bubble--agent">
          <Markdown components={markdownComponents}>{text}</Markdown>
        </div>
        {time && <span className="time">{formatTime(time)}</span>}
      </div>
    </div>
  )
}
