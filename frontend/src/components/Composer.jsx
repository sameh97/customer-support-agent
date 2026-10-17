import { useRef, useState } from 'react'

// disabled: can't send right now (agent is replying or waiting on a confirmation).
// locked: can't even type, because a confirmation card needs an answer first.
export default function Composer({ onSend, disabled, locked, businessName, onTalkToPerson }) {
  const [text, setText] = useState('')
  const inputRef = useRef(null)

  const submit = (e) => {
    e.preventDefault()
    const message = text.trim()
    if (!message || disabled) return
    onSend(message)
    setText('')
    inputRef.current.style.height = ''
  }

  // Enter sends, Shift+Enter adds a new line
  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) submit(e)
  }

  // Grow the box with its content, up to the CSS max-height
  const onChange = (e) => {
    setText(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${e.target.scrollHeight}px`
  }

  return (
    <form className="composer" onSubmit={submit}>
      <div className="composer__box">
        <label htmlFor="message" className="visually-hidden">Message</label>
        <textarea
          id="message"
          ref={inputRef}
          rows={1}
          value={text}
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder={locked ? 'Choose an option above to continue' : 'Type your message…'}
          disabled={locked}
        />
        <button type="submit" className="send" aria-label="Send" disabled={disabled || !text.trim()}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M12 19V5M5 12l7-7 7 7" />
          </svg>
        </button>
      </div>
      <p className="composer__note">
        You're chatting with {businessName}'s virtual assistant. We'll always ask before changing anything.{' '}
        <button type="button" className="link" onClick={onTalkToPerson} disabled={disabled}>
          Talk to a person
        </button>
      </p>
    </form>
  )
}
