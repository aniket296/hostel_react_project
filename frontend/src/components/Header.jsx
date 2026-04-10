import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import logo from '../assets/gpn_logo.jpg'
import { roleLabel } from '../utils'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className='site-header'>
      <div className='site-header-inner'>
        <div className='site-brand'>
          <div className='site-brand-logo'>
            <img src={logo} alt='Government Polytechnic Nagpur Logo' />
          </div>
          <div className='site-brand-text'>
            <h1>Government Polytechnic, Nagpur</h1>
            <p>Hostel Management System</p>
          </div>
        </div>

        {user && (
          <div className='site-user-area'>
            <div className='site-user'>
              <div><strong>{user.display_name || user.username || user.phone_number || 'User'}</strong></div>
              <div>{roleLabel(user.role)}</div>
            </div>

            <div className='site-header-actions'>
              <button type='button' className='header-btn' onClick={() => window.history.back()}>← Back</button>
              <Link className='header-btn' to='/'>Dashboard</Link>
              <button
                type='button'
                className='header-btn header-btn-danger'
                onClick={async () => {
                  await logout()
                  navigate('/login')
                }}
              >
                Logout
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
