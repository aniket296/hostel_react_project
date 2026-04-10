import { Link } from 'react-router-dom'
import client from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useApi } from '../hooks'

function StudentDashboard() {
  return (
    <>
      <h1 className='page-title'>Student Dashboard</h1>
      <div className='dashboard-section'>
        <div className='section-strip'>Student Services</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to='/student/complaints'>Complaint Section</Link>
          <Link className='action-btn' to='/student/academics'>Academics Section</Link>
          <Link className='action-btn' to='/student/feedback'>Hostel Feedback</Link>
        </div>
      </div>
    </>
  )
}

function ClerkDashboard({ data }) {
  return (
    <>
      <h1 className='page-title'>Clerk Dashboard</h1>
      <div className='dashboard-section'>
        <div className='section-strip'>Actions</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to='/clerk/complaints/new'>Complaints List</Link>
          <Link className='action-btn' to='/clerk/history'>Report</Link>
        </div>
      </div>

      <div className='dashboard-section'>
        <div className='section-strip'>Complaint Section</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to='/clerk/complaints/new'>New Complaints ({data.new_count ?? 0})</Link>
          <Link className='action-btn' to='/clerk/complaints/in_progress'>In Progress ({data.in_progress_count ?? 0})</Link>
          <Link className='action-btn' to='/clerk/complaints/completed'>Completed ({data.completed_count ?? 0})</Link>
          <Link className='action-btn' to='/clerk/complaints/solved'>Solved ({data.solved_count ?? 0})</Link>
          <Link className='action-btn' to='/clerk/complaints/unsolved'>Unsolved ({data.unsolved_count ?? 0})</Link>
        </div>
      </div>

      <div className='dashboard-section'>
        <div className='section-strip'>Student and Academics Section</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to='/clerk/students'>Student Management</Link>
          <Link className='action-btn' to='/clerk/academics'>Academics Management</Link>
        </div>
      </div>
    </>
  )
}

function AdminDashboard({ data }) {
  return (
    <>
      <h1 className='page-title'>Global Admin Dashboard</h1>

      <div className='dashboard-section'>
        <div className='section-strip'>Complaint Section</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to='/admin/complaints/new'>New Complaints ({data.new_count ?? 0})</Link>
          <Link className='action-btn' to='/admin/complaints/in_progress'>In Progress ({data.in_progress_count ?? 0})</Link>
          <Link className='action-btn' to='/admin/complaints/completed'>Completed ({data.completed_count ?? 0})</Link>
          <Link className='action-btn' to='/admin/complaints/solved'>Solved ({data.solved_count ?? 0})</Link>
          <Link className='action-btn' to='/admin/complaints/unsolved'>Unsolved ({data.unsolved_count ?? 0})</Link>
        </div>
      </div>

      <div className='dashboard-section'>
        <div className='section-strip'>Student and Hostel Administration</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to='/admin/students'>Student Management</Link>
          <Link className='action-btn' to='/admin/clerks'>Clerk Management</Link>
          <Link className='action-btn' to='/admin/locked-accounts'>Locked Accounts</Link>
          <Link className='action-btn' to='/admin/departments'>Departments</Link>
        </div>
      </div>

      <div className='dashboard-section'>
        <div className='section-strip'>Academic and System Tools</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to='/admin/academics'>Academics</Link>
          <Link className='action-btn' to='/admin/settings'>System Settings</Link>
          <Link className='action-btn' to='/admin/backups'>Backups</Link>
        </div>
      </div>

      <div className='dashboard-section'>
        <div className='section-strip'>Feedback section </div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to='/admin/feedback/forms'>Edit Feedback Form</Link>
          <Link className='action-btn' to='/admin/feedback/analysis'>Analyse Feedback</Link>
        </div>
      </div>
    </>
  )
}

export default function DashboardRouterPage() {
  const { user } = useAuth()
  const { data, loading, error } = useApi(() => client.get('/dashboard/summary/'), [])

  if (loading) return <div className='loading-box'>Loading dashboard...</div>
  if (error) return <div className='error-box'>{error}</div>

  if (user.role === 'student') return <StudentDashboard />
  if (user.role === 'clerk') return <ClerkDashboard data={data || {}} />
  return <AdminDashboard data={data || {}} />
}
