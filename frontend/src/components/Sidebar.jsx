import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import logo from '../assets/gpn_logo.jpg'

function SidebarItem({ to, children }) {
  const location = useLocation()
  const active = location.pathname === to
  return (
    <li>
      <Link className={active ? 'active' : ''} to={to}>{children}</Link>
    </li>
  )
}

export default function Sidebar() {
  const { user } = useAuth()
  if (!user || user.role === 'student') return null

  return (
    <aside className='sidebar'>
      <div className='sidebar-brand'>
        <div className='sidebar-brand-logo'>
          <img src={logo} alt='Government Polytechnic Nagpur Logo' />
        </div>
        <h2>{user.role === 'admin' ? 'Admin Panel' : 'Clerk Panel'}</h2>
      </div>

      <ul className='sidebar-nav'>
        {user.role === 'admin' ? (
          <>
            <SidebarItem to='/'>Global</SidebarItem>
            <SidebarItem to='/admin/hostels/boys'>♂ Boys Hostel</SidebarItem>
            <SidebarItem to='/admin/hostels/girls'>♀ Girls Hostel</SidebarItem>
          </>
        ) : (
          <>
            <SidebarItem to='/'>Dashboard</SidebarItem>
            <SidebarItem to='/clerk/students'>Students</SidebarItem>
            <SidebarItem to='/clerk/academics'>Academics</SidebarItem>
            <SidebarItem to='/clerk/complaints/new'>New Complaints</SidebarItem>
            <SidebarItem to='/clerk/complaints/in_progress'>In Progress</SidebarItem>
            <SidebarItem to='/clerk/complaints/completed'>Completed</SidebarItem>
            <SidebarItem to='/clerk/complaints/unsolved'>Unsolved</SidebarItem>
            <SidebarItem to='/clerk/history'>Complaint History</SidebarItem>
          </>
        )}
      </ul>
    </aside>
  )
}
