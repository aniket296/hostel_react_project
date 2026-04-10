import { useParams } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'

export default function FeedbackAnalysisViewPage() {
  const { id } = useParams()
  const { data, loading, error } = useApi(() => client.get(`/feedback/analysis/${id}/`), [id])

  if (loading) return <div className='loading-box'>Loading feedback analysis...</div>
  if (error) return <div className='error-box'>{error}</div>

  const overallRows = data?.overall_analysis || []
  const detailRows = data?.student_feedback_details || []

  return (
    <>
      <h1 className='page-title'>Feedback Analysis</h1>
      <div className='panel'>
        <div className='panel-header'>Overall Analysis</div>
        <div className='panel-body table-wrap'>
          <table className='data-table'>
            <thead><tr><th>Question</th><th>Average Rating</th><th>Total Responses</th></tr></thead>
            <tbody>
              {overallRows.length ? overallRows.map((row, index) => <tr key={index}><td>{row.question_text || row.question}</td><td>{row.average_rating ?? '-'}</td><td>{row.total_responses ?? '-'}</td></tr>) : <tr><td colSpan='3'>No overall analysis available.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <div className='panel'>
        <div className='panel-header'>Student Feedback Details</div>
        <div className='panel-body table-wrap'>
          <table className='data-table'>
            <thead>
              <tr>
                {detailRows.length ? Object.keys(detailRows[0]).map((key) => <th key={key}>{key}</th>) : <th>Details</th>}
              </tr>
            </thead>
            <tbody>
              {detailRows.length ? detailRows.map((row, index) => <tr key={index}>{Object.values(row).map((value, idx) => <td key={idx}>{String(value ?? '-')}</td>)}</tr>) : <tr><td>No student feedback details available.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
