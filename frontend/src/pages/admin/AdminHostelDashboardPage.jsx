import { Link, useParams } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'

export default function AdminHostelDashboardPage() {
  const { hostelType } = useParams()
  const hostelValue = hostelType === 'girls' ? 'girls_hostel' : 'boys_hostel'
  const hostelLabel = hostelType === 'girls' ? 'Girls Hostel' : 'Boys Hostel'
  const { data, loading, error } = useApi(() => client.get('/dashboard/summary/'), [hostelType])

  if (loading) return <div className='loading-box'>Loading dashboard...</div>
  if (error) return <div className='error-box'>{error}</div>

  return (
    <>
      <h1 className='page-title'>{hostelLabel} Dashboard</h1>

      <div className='dashboard-section'>
        <div className='section-strip'>{hostelLabel} Complaint Section</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to={`/admin/complaints/new?hostel=${hostelValue}`}>New Complaints ({data?.new_count ?? 0})</Link>
          <Link className='action-btn' to={`/admin/complaints/in_progress?hostel=${hostelValue}`}>In Progress ({data?.in_progress_count ?? 0})</Link>
          <Link className='action-btn' to={`/admin/complaints/completed?hostel=${hostelValue}`}>Completed ({data?.completed_count ?? 0})</Link>
          <Link className='action-btn' to={`/admin/complaints/solved?hostel=${hostelValue}`}>Solved ({data?.solved_count ?? 0})</Link>
          <Link className='action-btn' to={`/admin/complaints/unsolved?hostel=${hostelValue}`}>Unsolved ({data?.unsolved_count ?? 0})</Link>
        </div>
      </div>

      <div className='dashboard-section'>
        <div className='section-strip'>{hostelLabel} Student Section</div>
        <div className='dashboard-plain-grid'>
          <Link className='action-btn' to={`/admin/students?hostel=${hostelValue}`}>Students</Link>
          <Link className='action-btn' to={`/admin/students?hostel=${hostelValue}`}>Export Students</Link>
          <Link className='action-btn' to={`/admin/history?hostel=${hostelValue}`}>Complaint History</Link>
        </div>
      </div>
    </>
  )
}
