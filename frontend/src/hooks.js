import { useEffect, useState } from 'react'

export function useApi(getter, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError('')
    getter()
      .then((res) => {
        if (alive) setData(res.data)
      })
      .catch((err) => {
        if (alive) setError(err.response?.data?.detail || 'Failed to load data.')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, deps)

  return { data, setData, loading, error }
}
