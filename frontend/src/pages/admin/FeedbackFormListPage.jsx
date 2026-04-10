import { Link } from 'react-router-dom'
import { useState } from 'react'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate, hostelLabel, statusLabel } from '../../utils'

export default function FeedbackFormListPage() {
  const { data, loading, error } = useApi(() => client.get('/feedback/forms/'), [])
  const forms = Array.isArray(data) ? data : []
  const [note, setNote] = useState('')

  return (
    <>
      <h1 className='page-title'>Edit Feedback Form</h1>
      <div className='top-actions'><button type='button' className='action-btn' onClick={() => setNote('Feedback form creation, stop, and delete need backend API endpoints. Analysis and student submission are connected.')}>Create Form</button></div>
      {note && <div className='readonly-box' style={{ marginBottom: 12 }}>{note}</div>}
      {loading && <div className='loading-box'>Loading feedback forms...</div>}
      {error && <div className='error-box'>{error}</div>}
      {!loading && !error && (
        <div className='panel'>
          <div className='panel-header'>All Feedback Forms</div>
          <div className='panel-body table-wrap'>
            <table className='data-table'>
              <thead>
                <tr>
                  <th>Form Name</th>
                  <th>Hostel</th>
                  <th>Date of Upload</th>
                  <th>Status</th>
                  <th>Expiry</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {forms.length ? forms.map((feedbackForm) => (
                  <tr key={feedbackForm.id}>
                    <td>{feedbackForm.name}</td>
                    <td>{hostelLabel(feedbackForm.hostel)}</td>
                    <td>{formatDate(feedbackForm.created_at)}</td>
                    <td>{statusLabel(feedbackForm.status)}</td>
                    <td>{formatDate(feedbackForm.ends_at)}</td>
                    <td><Link className='action-btn' to={`/admin/feedback/analysis/${feedbackForm.id}`}>View</Link></td>
                  </tr>
                )) : <tr><td colSpan='6'>No feedback forms available.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
