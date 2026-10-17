import Avatar from './Avatar.jsx'

const SunIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </svg>
)

const MoonIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
  </svg>
)

export default function Header({ name, theme, onToggleTheme, onNewChat, onTalkToPerson, busy }) {
  const dark = theme === 'dark'

  return (
    <header className="header">
      <div className="header__brand">
        <Avatar name={name} />
        <div>
          <div className="header__name">{name}</div>
          <div className="header__status">
            <span className="dot" aria-hidden="true" />
            Typically replies instantly
          </div>
        </div>
      </div>

      <div className="header__actions">
        <button
          type="button"
          className="icon-btn"
          onClick={onToggleTheme}
          aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          title={dark ? 'Light mode' : 'Dark mode'}
        >
          {dark ? <SunIcon /> : <MoonIcon />}
        </button>
        <button type="button" className="btn btn--secondary btn--small hide-on-phone" onClick={onTalkToPerson} disabled={busy}>
          Talk to a person
        </button>
        <button type="button" className="btn btn--strong btn--small" onClick={onNewChat}>
          New chat
        </button>
      </div>
    </header>
  )
}
