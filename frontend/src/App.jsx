import { useEffect, useRef, useState } from 'react'
import { answerConfirmation, getInfo, sendMessage } from './api.js'
import { useTheme } from './useTheme.js'
import Header from './components/Header.jsx'
import Message from './components/Message.jsx'
import ConfirmCard from './components/ConfirmCard.jsx'
import TypingIndicator from './components/TypingIndicator.jsx'
import Composer from './components/Composer.jsx'

const STORAGE_KEY = 'support-chat'
const SUGGESTIONS = ['What plans do you offer?', 'How do I cancel?', 'Where are my invoices?']
const HANDOFF_MESSAGE = "I'd like to talk to a person, please."
// Keep the typing dots up briefly even for fast replies, so it reads like a person typing.
const MIN_TYPING_MS = 700

const newId = () => Math.random().toString(36).slice(2)
const now = () => new Date().toISOString()
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

function loadChat() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || { sessionId: null, items: [] }
  } catch {
    return { sessionId: null, items: [] }
  }
}

export default function App() {
  const [theme, toggleTheme] = useTheme()
  const [info, setInfo] = useState({ business_name: 'Support', support_email: '' })
  const [chat, setChat] = useState(loadChat)
  const [typing, setTyping] = useState(false)
  const bottomRef = useRef(null)

  const { sessionId, items } = chat
  const pending = items.find((i) => i.kind === 'action' && i.status === 'pending')
  const busy = typing || Boolean(pending)

  useEffect(() => {
    getInfo().then(setInfo).catch(() => {})
  }, [])

  useEffect(() => {
    document.title = `${info.business_name} Support`
  }, [info.business_name])

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chat))
    } catch {
      // storage unavailable — the chat still works, it just won't survive a refresh
    }
  }, [chat])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [items.length, typing])

  const addItems = (...newItems) =>
    setChat((c) => ({ ...c, items: [...c.items, ...newItems] }))

  // Turn an API response into chat items (a reply, a confirmation card, or both).
  const handleResponse = (data) => {
    const added = []
    if (data.response) added.push({ id: newId(), kind: 'agent', text: data.response, time: now() })
    if (data.pending_action) added.push({ id: newId(), kind: 'action', action: data.pending_action, status: 'pending', time: now() })
    setChat((c) => ({ sessionId: data.session_id, items: [...c.items, ...added] }))
  }

  const run = async (call) => {
    setTyping(true)
    try {
      const [data] = await Promise.all([call(), wait(MIN_TYPING_MS)])
      handleResponse(data)
    } catch {
      addItems({ id: newId(), kind: 'error', time: now() })
    } finally {
      setTyping(false)
    }
  }

  const send = (text) => {
    if (busy) return
    addItems({ id: newId(), kind: 'user', text, time: now() })
    run(() => sendMessage(text, sessionId))
  }

  const answer = (approved) => {
    setChat((c) => ({
      ...c,
      items: c.items.map((i) => (i.id === pending.id ? { ...i, status: approved ? 'approved' : 'declined' } : i)),
    }))
    run(() => answerConfirmation(sessionId, approved))
  }

  const newChat = () => setChat({ sessionId: null, items: [] })

  return (
    <div className="app">
      <Header
        name={info.business_name}
        theme={theme}
        onToggleTheme={toggleTheme}
        onNewChat={newChat}
        onTalkToPerson={() => send(HANDOFF_MESSAGE)}
        busy={busy}
      />

      <main className="conversation" aria-live="polite">
        <Message kind="agent" name={info.business_name} text="Hi there! How can I help you today?" />

        {items.length === 0 && (
          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} type="button" className="chip" onClick={() => send(s)}>
                {s}
              </button>
            ))}
          </div>
        )}

        {items.map((item) => {
          if (item.kind === 'action') {
            return <ConfirmCard key={item.id} action={item.action} status={item.status} onAnswer={answer} disabled={typing} />
          }
          if (item.kind === 'error') {
            return (
              <p key={item.id} className="notice">
                Sorry, I couldn't get that through. Please try again in a moment.
              </p>
            )
          }
          return <Message key={item.id} kind={item.kind} name={info.business_name} text={item.text} time={item.time} />
        })}

        {typing && <TypingIndicator name={info.business_name} />}
        <div ref={bottomRef} />
      </main>

      <Composer
        onSend={send}
        disabled={busy}
        locked={Boolean(pending)}
        businessName={info.business_name}
        onTalkToPerson={() => send(HANDOFF_MESSAGE)}
      />
    </div>
  )
}
