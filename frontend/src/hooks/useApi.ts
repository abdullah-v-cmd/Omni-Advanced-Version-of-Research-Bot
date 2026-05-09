/**
 * OmniSynth - Custom API hooks
 */
import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'

export function useAsync<T>(
  fn: (...args: any[]) => Promise<T>,
  options?: { successMsg?: string; errorMsg?: string }
) {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(
    async (...args: any[]) => {
      setLoading(true)
      setError(null)
      try {
        const result = await fn(...args)
        setData(result)
        if (options?.successMsg) toast.success(options.successMsg)
        return result
      } catch (err: any) {
        const msg = err?.response?.data?.detail || options?.errorMsg || 'An error occurred'
        setError(msg)
        toast.error(msg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [fn, options?.successMsg, options?.errorMsg]
  )

  return { execute, loading, data, error }
}

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  const { useEffect } = require('react')
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])
  return debouncedValue
}
