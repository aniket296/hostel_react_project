import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import logo from '../assets/gpn_logo.jpg'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(identifier, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className='gov-login-body'>
      <div className='gov-login-wrapper'>
        <div className='gov-login-card'>
          <div className='gov-login-topbar'>
            <div className='gov-login-brand'>
              <div className='gov-login-logo'>
                <img src={logo} alt='Government Polytechnic Nagpur Logo' />
              </div>
              <div className='gov-login-brand-text'>
                <h1>Government Polytechnic, Nagpur</h1>
                <p>Hostel Management System</p>
              </div>
            </div>
          </div>

          <div className='gov-login-header'>
            <h2> LOGIN</h2>
            <p>Access your hostel portal account</p>
          </div>

          <div className='gov-login-body-inner'>
            <form onSubmit={submit} noValidate>
              {error && <div className='gov-alert gov-alert-error'>{error}</div>}

              <div className='gov-form-group'>
                <label>USERNAME / PHONE NUMBER *</label>
                <input value={identifier} onChange={(e) => setIdentifier(e.target.value)} />
              </div>

              <div className='gov-form-group'>
                <label>PASSWORD *</label>
                <input type='password' value={password} onChange={(e) => setPassword(e.target.value)} />
              </div>

              <button type='submit' className='gov-login-btn' disabled={busy}>
                {busy ? 'LOGGING IN...' : 'LOGIN'}
              </button>
            </form>
          </div>

          <div className='gov-login-footer'>
            <p>Authorized access only. Contact hostel administration for login support.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
