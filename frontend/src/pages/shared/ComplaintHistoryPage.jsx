import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { downloadCsv, formatDate, hostelLabel, statusLabel } from '../../utils'

export default function ComplaintHistoryPage({ role }) {
  const location = useLocation()
  const navigate = useNavigate()
  const params = new URLSearchParams(location.search)
  const initialSearch = params.get('search') || ''
  const initialStatus = params.get('status') || ''
  const hostel = params.get('hostel') || ''
  const [search, setSearch] = useState(initialSearch)
  const [status, setStatus] = useState(initialStatus)
  const query = useMemo(() => {
    const qp = new URLSearchParams()
    if (initialSearch) qp.set('q', initialSearch)
    if (initialStatus) qp.set('status', initialStatus)
    return qp.toString()
  }, [initialSearch, initialStatus])
  const { data, loading, error } = useApi(() => client.get(`/complaints/${query ? `?${query}` : ''}`), [query])
  const complaints = Array.isArray(data) ? data.filter((item) => !hostel || item.hostel_snapshot === hostel) : []

  const applyFilters = (e) => {
    e.preventDefault()
    const next = new URLSearchParams()
    if (search) next.set('search', search)
    if (status) next.set('status', status)
    if (hostel) next.set('hostel', hostel)
    navigate(`/${role}/history${next.toString() ? `?${next}` : ''}`)
  }

  function exportComplaints() {
    downloadCsv('complaint_history.csv', [
      ['ID', 'Description', 'Student', 'Hostel', 'Phone', 'Room', 'Worker', 'Status', 'Created'],
      ...complaints.map((c) => [c.id, c.description, c.student_name_snapshot, hostelLabel(c.hostel_snapshot), c.student_phone_snapshot || '', c.room_number_snapshot, c.worker_name || '', statusLabel(c.status), formatDate(c.created_at)]),
    ])
  }

  return (
    <>
      <h1 className='page-title'>{role === 'admin' ? (hostel === 'boys_hostel' ? 'Boys Hostel Complaint History' : hostel === 'girls_hostel' ? 'Girls Hostel Complaint History' : 'All Complaint History') : 'Complaint History'}</h1>
      <div className='top-actions'><button type='button' className='inline-btn' onClick={exportComplaints}>Export Complaints</button></div>
      <div className='filter-bar'>
        <form onSubmit={applyFilters} className='filter-grid'>
          <div><label>Search</label><input className='form-control' value={search} onChange={(e) => setSearch(e.target.value)} placeholder='Student, worker, room, description' /></div>
          <div><label>Status</label><select className='form-control' value={status} onChange={(e) => setStatus(e.target.value)}><option value=''>All</option><option value='new'>New</option><option value='in_progress'>In Progress</option><option value='completed'>Completed</option><option value='solved'>Solved</option><option value='unsolved'>Unsolved</option></select></div>
          {role === 'admin' && <div><label>Hostel</label><div className='readonly-box'>{hostel ? hostelLabel(hostel) : 'All'}</div></div>}
          <div><button className='action-btn' type='submit'>Apply Filters</button></div>
        </form>
      </div>
      {loading && <div className='loading-box'>Loading complaint history...</div>}
      {error && <div className='error-box'>{error}</div>}
      {!loading && !error && (
        <div className='page-card table-wrap'>
          <table className='data-table'>
            <thead>
              <tr>
                <th>ID</th><th>Description</th><th>Student</th>{role === 'admin' && <th>Hostel</th>}<th>Phone</th><th>Room</th><th>Worker</th><th>Status</th><th>Created</th><th>Timeline</th>
              </tr>
            </thead>
            <tbody>
              {complaints.length ? complaints.map((complaint) => (
                <tr key={complaint.id}>
                  <td>{complaint.id}</td><td>{complaint.description}</td><td>{complaint.student_name_snapshot}</td>{role === 'admin' && <td>{hostelLabel(complaint.hostel_snapshot)}</td>}<td>{complaint.student_phone_snapshot || '-'}</td><td>{complaint.room_number_snapshot}</td><td>{complaint.worker_name || '-'}</td><td>{statusLabel(complaint.status)}</td><td>{formatDate(complaint.created_at)}</td><td><Link to={`/${role}/complaints/${complaint.id}`}>Open Timeline</Link></td>
                </tr>
              )) : <tr><td colSpan={role === 'admin' ? 10 : 9}>No complaint history found.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
