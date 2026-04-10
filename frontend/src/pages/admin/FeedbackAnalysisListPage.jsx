import { Link } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate, hostelLabel, statusLabel } from '../../utils'

export default function FeedbackAnalysisListPage() {
  const { data, loading, error } = useApi(() => client.get('/feedback/forms/'), [])
  const forms = Array.isArray(data) ? data : []

  return (
    <>
      <h1 className='page-title'>Analyse Feedback</h1>
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
                  <th>Created Date</th>
                  <th>Status</th>
                  <th>Total Responses</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {forms.length ? forms.map((feedbackForm) => (
                  <tr key={feedbackForm.id}>
                    <td>{feedbackForm.name}</td>
                    <td>{hostelLabel(feedbackForm.hostel)}</td>
                    <td>{formatDate(feedbackForm.created_at)}</td>
                    <td>{statusLabel(feedbackForm.status)}</td>
                    <td>-</td>
                    <td><Link className='action-btn' to={`/admin/feedback/analysis/${feedbackForm.id}`}>View Analysis</Link></td>
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
