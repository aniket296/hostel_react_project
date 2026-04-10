import { useParams } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate, statusLabel } from '../../utils'

export default function StudentComplaintDetailPage() {
  const { id } = useParams()
  const { data, loading, error } = useApi(() => client.get('/complaints/'), [id])
  const complaint = Array.isArray(data) ? data.find((item) => String(item.id) === String(id)) : null

  if (loading) return <div className='loading-box'>Loading complaint...</div>
  if (error) return <div className='error-box'>{error}</div>
  if (!complaint) return <div className='empty-box'>No timeline available.</div>

  return (
    <>
      <h1 className='page-title'>Complaint Timeline</h1>
      <div className='panel'>
        <div className='panel-header'>Complaint Details</div>
        <div className='panel-body'>
          <p><strong>Description:</strong> {complaint.description}</p>
          <p><strong>Current Status:</strong> {statusLabel(complaint.status)}</p>
        </div>
      </div>
      <div className='panel'>
        <div className='panel-header'>Status History</div>
        <div className='panel-body'>
          {complaint.status_history?.length ? complaint.status_history.map((item) => (
            <div key={item.id} className='timeline-entry'>
              <p><strong>Status:</strong> {statusLabel(item.status)}</p>
              <p><strong>Timestamp:</strong> {formatDate(item.timestamp)}</p>
            </div>
          )) : <div className='empty-box'>No timeline available.</div>}
        </div>
      </div>
    </>
  )
}
