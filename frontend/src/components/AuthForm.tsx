import { useState } from 'react'
import { login } from '../api/auth'

export function AuthForm({ onLogin }: { onLogin: () => void }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  return (
    <section className="auth-card">
      <h1>Log in</h1>
      <p className="muted">Enter the shared password to view events.</p>
      <form onSubmit={async (event) => {
        event.preventDefault()
        setError(null)
        setIsSubmitting(true)
        try {
          await login(password)
          onLogin()
          setPassword('')
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Unable to authenticate')
        } finally {
          setIsSubmitting(false)
        }
      }}>
        <label htmlFor="password">Password</label>
        <input id="password" name="password" type="password" required
          autoComplete="current-password"
          minLength={1} maxLength={128} value={password}
          onChange={(event) => setPassword(event.target.value)} />
        {error && <p className="error-message" role="alert">{error}</p>}
        <button className="refresh-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Please wait…' : 'Log in'}
        </button>
      </form>
    </section>
  )
}
