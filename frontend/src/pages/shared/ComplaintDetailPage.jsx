import { useParams } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate, hostelLabel, statusLabel, yearLabel } from '../../utils'

export default function ComplaintDetailPage() {
  const { id } = useParams()
  const { data, loading, error } = useApi(() => client.get('/complaints/'), [id])
  const complaint = Array.isArray(data) ? data.find((item) => String(item.id) === String(id)) : null

  if (loading) return <div className='loading-box'>Loading complaint...</div>
  if (error) return <div className='error-box'>{error}</div>
  if (!complaint) return <div className='empty-box'>Complaint not found.</div>

  return (
    <>
      <h1 className='page-title'>Complaint Detail</h1>

      <div className='panel'>
        <div className='panel-header'>Complaint Information</div>
        <div className='panel-body'>
          <p><strong>Description:</strong> {complaint.description}</p>
          <p><strong>Student:</strong> {complaint.student_name_snapshot}</p>
          <p><strong>Phone:</strong> {complaint.student_phone_snapshot || '-'}</p>
          <p><strong>Department:</strong> {complaint.department_name_snapshot || '-'}</p>
          <p><strong>Year:</strong> {yearLabel(complaint.year_snapshot)}</p>
          <p><strong>Hostel:</strong> {hostelLabel(complaint.hostel_snapshot)}</p>
          <p><strong>Room Number:</strong> {complaint.room_number_snapshot}</p>
          <p><strong>Worker:</strong> {complaint.worker_name || 'Not assigned'}</p>
          <p><strong>Current Status:</strong> {statusLabel(complaint.status)}</p>
        </div>
      </div>

      <div className='panel'>
        <div className='panel-header'>Complaint History / Timeline</div>
        <div className='panel-body'>
          {complaint.status_history?.length ? complaint.status_history.map((item) => (
            <div key={item.id} className='timeline-entry'>
              <p><strong>Status:</strong> {statusLabel(item.status)}</p>
              <p><strong>Changed By:</strong> {item.changed_by_role_snapshot || '-'}</p>
              <p><strong>Time:</strong> {formatDate(item.timestamp)}</p>
            </div>
          )) : <div className='empty-box'>No complaint history available.</div>}
        </div>
      </div>
    </>
  )
}
