import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { downloadCsv, formatDate, hostelLabel, statusLabel } from '../../utils'

export default function ComplaintStatusPage({ role }) {
  const { status } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const params = new URLSearchParams(location.search)
  const initialSearch = params.get('search') || ''
  const hostel = params.get('hostel') || ''
  const [search, setSearch] = useState(initialSearch)
  const endpointParams = useMemo(() => {
    const qp = new URLSearchParams()
    if (status) qp.set('status', status)
    if (initialSearch) qp.set('q', initialSearch)
    return qp.toString()
  }, [status, initialSearch])
  const { data, setData, loading, error } = useApi(() => client.get(`/complaints/?${endpointParams}`), [endpointParams])

  const complaints = Array.isArray(data) ? data.filter((item) => !hostel || item.hostel_snapshot === hostel) : []
  const title = status === 'new' ? 'New Complaints' : status === 'in_progress' ? 'In Progress Complaints' : status === 'completed' ? 'Completed Complaints' : status === 'solved' ? 'Solved Complaints' : status === 'unsolved' ? 'Unsolved Complaints' : 'Complaint Records'

  const applySearch = (e) => {
    e.preventDefault()
    const next = new URLSearchParams()
    if (search) next.set('search', search)
    if (hostel) next.set('hostel', hostel)
    navigate(`/${role}/complaints/${status}${next.toString() ? `?${next}` : ''}`)
  }

  function exportComplaints() {
    downloadCsv(`complaints_${status || 'all'}.csv`, [
      ['ID', 'Description', 'Student', 'Hostel', 'Room', 'Worker', 'Status', 'Created'],
      ...complaints.map((c) => [c.id, c.description, c.student_name_snapshot, hostelLabel(c.hostel_snapshot), c.room_number_snapshot, c.worker_name || '', statusLabel(c.status), formatDate(c.created_at)]),
    ])
  }

  async function assignWorker(id, workerName, currentStatus) {
    if (!workerName.trim()) return
    const action = currentStatus === 'unsolved' ? 'reopen' : 'assign-worker'
    const body = currentStatus === 'unsolved' ? {} : { worker_name: workerName }
    const res = await client.post(`/complaints/${id}/${action}/`, body)
    if (currentStatus === 'unsolved') {
      const res2 = await client.post(`/complaints/${id}/assign-worker/`, { worker_name: workerName })
      setData((old) => (old || []).map((item) => item.id === id ? res2.data : item))
      return
    }
    setData((old) => (old || []).map((item) => item.id === id ? res.data : item))
  }

  async function markCompleted(id) {
    const res = await client.post(`/complaints/${id}/mark-completed/`)
    setData((old) => (old || []).map((item) => item.id === id ? res.data : item))
  }

  return (
    <>
      <h1 className='page-title'>{title}</h1>

      <div className='top-actions'>
        <button type='button' className='inline-btn' onClick={exportComplaints}>Export Complaints</button>
      </div>

      <div className='panel'>
        <div className='panel-header'>Complaint Search</div>
        <div className='panel-body'>
          <form onSubmit={applySearch} className='filter-grid'>
            <div>
              <label>{role === 'admin' ? 'Search by room / worker / student' : 'Search by Room / Worker'}</label>
              <input className='form-control' type='text' value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            {role === 'admin' && (
              <div>
                <label>Hostel</label>
                <div className='readonly-box'>{hostel ? hostelLabel(hostel) : 'All'}</div>
              </div>
            )}
            <div>
              <button className='action-btn' type='submit'>Search</button>
            </div>
          </form>
        </div>
      </div>

      {loading && <div className='loading-box'>Loading complaints...</div>}
      {error && <div className='error-box'>{error}</div>}

      {!loading && !error && (
        <div className='panel'>
          <div className='panel-header'>Complaint Records</div>
          <div className='panel-body table-wrap'>
            <table className='data-table'>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Description</th>
                  <th>Student</th>
                  {role === 'admin' && <th>Hostel</th>}
                  <th>Room</th>
                  <th>Worker</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>History</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {complaints.length ? complaints.map((complaint) => (
                  <ComplaintRow key={complaint.id} complaint={complaint} role={role} onAssign={assignWorker} onCompleted={markCompleted} />
                )) : (
                  <tr><td colSpan={role === 'admin' ? 10 : 9}>No complaints found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}

function ComplaintRow({ complaint, role, onAssign, onCompleted }) {
  const [workerName, setWorkerName] = useState('')
  return (
    <tr>
      <td>{complaint.id}</td>
      <td>{complaint.description}</td>
      <td>{complaint.student_name_snapshot}</td>
      {role === 'admin' && <td>{hostelLabel(complaint.hostel_snapshot)}</td>}
      <td>{complaint.room_number_snapshot}</td>
      <td>{complaint.worker_name || '-'}</td>
      <td>{statusLabel(complaint.status)}</td>
      <td>{formatDate(complaint.created_at)}</td>
      <td><Link to={`/${role}/complaints/${complaint.id}`}>Open Timeline</Link></td>
      <td className='table-actions'>
        {(complaint.status === 'new' || complaint.status === 'unsolved') && (
          <form className='inline-form' onSubmit={(e) => { e.preventDefault(); onAssign(complaint.id, workerName, complaint.status); setWorkerName('') }}>
            <input className='inline-input' type='text' value={workerName} onChange={(e) => setWorkerName(e.target.value)} placeholder='Worker name' required />
            <button className='inline-btn' type='submit'>{complaint.status === 'unsolved' ? 'Reopen + Assign' : 'Assign Worker'}</button>
          </form>
        )}
        {complaint.status === 'in_progress' && (
          <button className='action-btn' type='button' onClick={() => onCompleted(complaint.id)}>Mark Completed</button>
        )}
      </td>
    </tr>
  )
}
