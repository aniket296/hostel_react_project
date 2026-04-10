import Header from './Header'
import Sidebar from './Sidebar'
import { useAuth } from '../context/AuthContext'

export default function Shell({ children }) {
  const { user } = useAuth()
  if (!user) return children

  if (user.role === 'student') {
    return (
      <>
        <Header />
        <div className='student-page-shell'>
          <main className='student-main-content student-top-offset'>
            {children}
          </main>
        </div>
        <footer className='footer'>© Government Polytechnic Nagpur 2026<br /><br />Developed by IT Department Batch 2023-26</footer>
      </>
    )
  }

  return (
    <>
      <Header />
      <div className='page-shell'>
        <Sidebar />
        <section className='main-content'>
          {children}
        </section>
      </div>
      <footer className='footer'>© Government Polytechnic Nagpur 2026<br /><br />Developed by IT Department Batch 2023-26</footer>
    </>
  )
}
