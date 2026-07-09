import { useMemo, useState } from 'react'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { hostelLabel } from '../../utils'

export default function StudentFeedbackPage() {
  const { data, loading, error } = useApi(() => client.get('/feedback/forms/'), [])
  const feedbackForm = useMemo(() => Array.isArray(data) ? data[0] : null, [data])
  const [answers, setAnswers] = useState({})
  const [submitMsg, setSubmitMsg] = useState('')
  const [submitErr, setSubmitErr] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setSubmitMsg('')
    setSubmitErr('')
    try {
      await client.post(`/feedback/forms/${feedbackForm.id}/submit/`, { answers })
      setSubmitMsg('Feedback submitted successfully.')
    } catch (err) {
      setSubmitErr(err.response?.data?.detail || 'Failed to submit feedback.')
    }
  }

  if (loading) return <div className='loading-box'>Loading feedback form...</div>
  if (error) return <div className='error-box'>{error}</div>
  if (!feedbackForm) return <div className='panel'><div className='panel-header'>Hostel Feedback</div><div className='panel-body'><p>No active feedback form available right now.</p></div></div>
  if (feedbackForm.already_submitted) return <div className='panel'><div className='panel-header'>{feedbackForm.name}</div><div className='panel-body'><p>You have already submitted your hostel feedback for the active form.</p></div></div>

  return (
    <div className='student-page-wrap'>
      <div className='page-header'>
        <h1 className='page-title'>Hostel Feedback</h1>
      </div>
      <div className='panel feedback-student-panel'>
        <div className='panel-header'>{feedbackForm.name}</div>
        <div className='panel-body'>
          <p><strong>Hostel:</strong> {hostelLabel(feedbackForm.hostel)}</p>
          <p><strong>Available Until:</strong> {feedbackForm.ends_at || '-'}</p>
          {submitMsg && <div className='gov-alert gov-alert-success'>{submitMsg}</div>}
          {submitErr && <div className='gov-alert gov-alert-error'>{submitErr}</div>}
          <form onSubmit={submit}>
            <div className='feedback-question-list'>
              {feedbackForm.questions?.map((question, index) => (
                <div className='feedback-question-item' style={{ marginBottom: 16 }} key={question.id}>
                  <label>{index + 1}. {question.text}</label>
                  {question.question_type === 'rating' ? (
                    <select className='form-control' required value={answers[question.id] || ''} onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })}>
                      <option value=''>Select Rating</option>
                      <option value='1'>1</option><option value='2'>2</option><option value='3'>3</option><option value='4'>4</option><option value='5'>5</option>
                    </select>
                  ) : question.question_type === 'radio' ? (
                    <div style={{ marginTop: 8 }}>
                      {(question.radio_options || '').split(/\r?\n|,/).map((option) => option.trim()).filter(Boolean).map((option) => (
                        <div style={{ marginBottom: 6 }} key={option}>
                          <label style={{ fontWeight: 'normal' }}><input type='radio' name={`q_${question.id}`} value={option} checked={answers[question.id] === option} onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })} required /> {option}</label>
                        </div>
                      ))}
                    </div>
                  ) : question.question_type === 'textarea' ? (
                    <textarea className='form-control' rows='4' required value={answers[question.id] || ''} onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })} />
                  ) : (
                    <input className='form-control' type='text' required value={answers[question.id] || ''} onChange={(e) => setAnswers({ ...answers, [question.id]: e.target.value })} />
                  )}
                </div>
              ))}
            </div>
            <div className='top-actions' style={{ marginTop: 20 }}>
              <button type='submit' className='action-btn'>Submit Feedback</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
