export default function Avatar({ name }) {
  return (
    <div className="avatar" aria-hidden="true">
      {name.trim().charAt(0).toUpperCase()}
    </div>
  )
}
