import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate, statusLabel } from '../../utils'

export default function StudentComplaintListPage() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const selectedStatus = params.get('status') || ''
  const [status, setStatus] = useState(selectedStatus)
  const query = useMemo(() => selectedStatus ? `?status=${selectedStatus}` : '', [selectedStatus])
  const { data, setData, loading, error } = useApi(() => client.get(`/complaints/${query}`), [query])
  const complaints = Array.isArray(data) ? data : []

  const applyFilter = (e) => {
    e.preventDefault()
    const next = new URLSearchParams()
    if (status) next.set('status', status)
    window.location.search = next.toString()
  }

  async function markSolved(id) {
    const res = await client.post(`/complaints/${id}/mark-solved/`)
    setData((old) => (old || []).map((item) => item.id === id ? res.data : item))
  }

  async function markUnsolved(id) {
    const res = await client.post(`/complaints/${id}/mark-unsolved/`)
    setData((old) => (old || []).map((item) => item.id === id ? res.data : item))
  }

  return (
    <>
      <h1 className='page-title'>My Complaints</h1>

      <div className='panel'>
        <div className='panel-header'>Complaint Filters</div>
        <div className='panel-body'>
          <form onSubmit={applyFilter} className='filter-grid'>
            <div>
              <label>Status</label>
              <select className='form-control' value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value=''>All</option>
                <option value='new'>New</option>
                <option value='in_progress'>In Progress</option>
                <option value='completed'>Completed</option>
                <option value='solved'>Solved</option>
                <option value='unsolved'>Unsolved</option>
              </select>
            </div>
            <div>
              <label>Total Complaints</label>
              <div className='readonly-box'>{complaints.length}</div>
            </div>
            <div>
              <button className='action-btn' type='submit'>Apply Filter</button>
            </div>
          </form>
        </div>
      </div>

      {loading && <div className='loading-box'>Loading complaints...</div>}
      {error && <div className='error-box'>{error}</div>}

      {!loading && !error && (
        <div className='student-record-list'>
          {complaints.length ? complaints.map((complaint) => (
            <div className='student-record-box' key={complaint.id}>
              <div className='student-record-head'>
                <div className='student-record-title'>Complaint #{complaint.id}</div>
                <div className='student-record-badge'>{statusLabel(complaint.status)}</div>
              </div>
              <div className='student-record-body'>
                <div><strong>Description:</strong> {complaint.description}</div>
                <div><strong>Room Number:</strong> {complaint.room_number_snapshot}</div>
                <div><strong>Worker:</strong> {complaint.worker_name || 'Not assigned'}</div>
                <div><strong>Date:</strong> {formatDate(complaint.created_at)}</div>
              </div>
              <div className='student-record-actions'>
                <Link className='action-btn' to={`/student/complaints/${complaint.id}`}>View Timeline</Link>
                {complaint.status === 'completed' && (
                  <>
                    <button className='action-btn' type='button' onClick={() => markSolved(complaint.id)}>Mark Solved</button>
                    <button className='action-btn action-btn-danger' type='button' onClick={() => markUnsolved(complaint.id)}>Mark Unsolved</button>
                  </>
                )}
              </div>
            </div>
          )) : <div className='empty-box'>No complaints found.</div>}
        </div>
      )}
    </>
  )
}
