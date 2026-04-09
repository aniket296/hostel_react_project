
export default function StatusBadge({ value }) {
  return <span className={`badge badge-${value}`}>{String(value).replaceAll('_', ' ')}</span>
}
