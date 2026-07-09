import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate, hostelLabel, statusLabel } from '../../utils'

export default function FeedbackFormListPage() {
  const { data, loading, error } = useApi(() => client.get('/feedback/forms/'), [])
  const forms = Array.isArray(data) ? data : []
  const [note, setNote] = useState('')
  const [busyId, setBusyId] = useState(null)
  const [showComposer, setShowComposer] = useState(false)
  const [form, setForm] = useState({
    name: '',
    hostel: 'boys_hostel',
    duration_hours: 24,
    questions: [
      { text: 'How would you rate the hostel food?', type: 'rating', options: '' },
      { text: 'Would you recommend this hostel to others?', type: 'radio', options: 'Yes\nNo' },
    ],
  })

  useEffect(() => {
    if (!showComposer) {
      setNote('')
    }
  }, [showComposer])

  async function createForm() {
    const payload = {
      ...form,
      duration_hours: Number(form.duration_hours || 24),
      questions: form.questions
        .map((question) => ({
          text: question.text.trim(),
          type: question.type,
          options: question.options,
        }))
        .filter((question) => question.text),
    }

    if (!payload.name.trim() || !payload.hostel || !payload.duration_hours || !payload.questions.length) {
      setNote('Please fill in the form name and at least one question.')
      return
    }

    try {
      setBusyId('create')
      const res = await client.post('/feedback/forms/', payload)
      setNote(`Created feedback form #${res.data.id}.`)
      setShowComposer(false)
      window.location.reload()
    } catch (err) {
      setNote(err.response?.data?.detail || 'Failed to create feedback form.')
    } finally {
      setBusyId(null)
    }
  }

  function updateQuestion(index, key, value) {
    setForm((prev) => {
      const questions = [...prev.questions]
      questions[index] = { ...questions[index], [key]: value }
      return { ...prev, questions }
    })
  }

  function addQuestion() {
    setForm((prev) => ({
      ...prev,
      questions: [...prev.questions, { text: '', type: 'rating', options: '' }],
    }))
  }

  function removeQuestion(index) {
    setForm((prev) => ({
      ...prev,
      questions: prev.questions.filter((_, i) => i !== index),
    }))
  }

  async function action(id, actionName) {
    try {
      setBusyId(`${actionName}:${id}`)
      await client.post(`/feedback/forms/${id}/${actionName}/`)
      window.location.reload()
    } catch (err) {
      setNote(err.response?.data?.detail || `Failed to ${actionName} feedback form.`)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <h1 className='page-title'>Edit Feedback Form</h1>
      <div className='top-actions'>
        <button type='button' className='action-btn' onClick={() => setShowComposer((prev) => !prev)}>
          {showComposer ? 'Hide Composer' : 'Create Form'}
        </button>
      </div>
      {note && <div className='readonly-box' style={{ marginBottom: 12 }}>{note}</div>}
      {showComposer && (
        <div className='panel' style={{ marginBottom: 16 }}>
          <div className='panel-header'>Create Feedback Form</div>
          <div className='panel-body'>
            <div className='form-grid'>
              <div>
                <label>Form Name</label>
                <input className='form-control' value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div>
                <label>Hostel</label>
                <select className='form-control' value={form.hostel} onChange={(e) => setForm({ ...form, hostel: e.target.value })}>
                  <option value='boys_hostel'>Boys Hostel</option>
                  <option value='girls_hostel'>Girls Hostel</option>
                </select>
              </div>
              <div>
                <label>Duration Hours</label>
                <select className='form-control' value={form.duration_hours} onChange={(e) => setForm({ ...form, duration_hours: Number(e.target.value) })}>
                  <option value='12'>12 Hours</option>
                  <option value='24'>24 Hours</option>
                  <option value='48'>48 Hours</option>
                  <option value='72'>72 Hours</option>
                  <option value='168'>7 Days</option>
                </select>
              </div>
            </div>

            <div style={{ marginTop: 16 }}>
              <h3 className='section-strip' style={{ marginBottom: 12 }}>Questions</h3>
              {form.questions.map((question, index) => (
                <div key={index} className='panel' style={{ marginBottom: 12 }}>
                  <div className='panel-body'>
                    <div className='form-grid'>
                      <div>
                        <label>Question Text</label>
                        <input className='form-control' value={question.text} onChange={(e) => updateQuestion(index, 'text', e.target.value)} />
                      </div>
                      <div>
                        <label>Type</label>
                        <select className='form-control' value={question.type} onChange={(e) => updateQuestion(index, 'type', e.target.value)}>
                          <option value='rating'>Rating Dropdown</option>
                          <option value='radio'>Radio Choice</option>
                          <option value='text'>Text Input</option>
                          <option value='textarea'>Textarea</option>
                        </select>
                      </div>
                    </div>
                    {question.type === 'radio' && (
                      <div style={{ marginTop: 12 }}>
                        <label>Radio Options, one per line</label>
                        <textarea className='form-control' rows='3' value={question.options} onChange={(e) => updateQuestion(index, 'options', e.target.value)} />
                      </div>
                    )}
                    <div style={{ marginTop: 12 }}>
                      <button type='button' className='inline-btn action-btn-danger' onClick={() => removeQuestion(index)} disabled={form.questions.length <= 1}>Remove</button>
                    </div>
                  </div>
                </div>
              ))}
              <div className='top-actions'>
                <button type='button' className='inline-btn' onClick={addQuestion}>Add Question</button>
                <button type='button' className='action-btn' onClick={createForm} disabled={busyId === 'create'}>{busyId === 'create' ? 'Creating...' : 'Save Form'}</button>
              </div>
            </div>
          </div>
        </div>
      )}
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
                    <td style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <Link className='action-btn' to={`/admin/feedback/analysis/${feedbackForm.id}`}>View</Link>
                      <button type='button' className='action-btn' onClick={() => action(feedbackForm.id, 'stop')} disabled={busyId === `stop:${feedbackForm.id}` || feedbackForm.status !== 'active'}>Stop</button>
                      <button type='button' className='action-btn action-btn-danger' onClick={() => action(feedbackForm.id, 'delete')} disabled={busyId === `delete:${feedbackForm.id}`}>Delete</button>
                    </td>
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
