import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'

export default function AcademicUploadPage({ role }) {
  const navigate = useNavigate()
  const { data: departments } = useApi(() => client.get('/departments/'), [])
  const { data: subjects } = useApi(() => client.get('/subjects/'), [])
  const [form, setForm] = useState({ subject: '', department: '', year: 'year_1', file_type: 'notes', course_code: '', file: null })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const backPath = role === 'admin' ? '/admin/academics' : role === 'clerk' ? '/clerk/academics' : '/student/academics/download'

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    const fd = new FormData()
    Object.entries(form).forEach(([key, value]) => {
      if (value !== null && value !== '') fd.append(key, value)
    })
    try {
      await client.post('/academics/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      navigate(backPath)
    } catch (err) {
      const data = err.response?.data
      setError(typeof data === 'object' ? JSON.stringify(data) : (data?.detail || 'Upload failed.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h1 className='page-title'>Upload Academic File</h1>
      <div className='panel'>
        <div className='panel-header'>Academic File Upload</div>
        <div className='panel-body'>
          <div className='top-note'>Upload notes, curriculum, or previous year question papers. Make sure the department, year, file type, and subject are correct before submitting.</div>
          <form onSubmit={submit}>
            {error && <div className='form-errors'>{error}</div>}
            <div className='form-row'><label>Subject Name</label><select value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} required><option value=''>Select Subject</option>{Array.isArray(subjects) && subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></div>
            <div className='form-row'><label>Course Code</label><input value={form.course_code} onChange={(e) => setForm({ ...form, course_code: e.target.value })} /></div>
            <div className='form-row'><label>Department</label><select value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} required><option value=''>Select Department</option>{Array.isArray(departments) && departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
            <div className='form-row'><label>Year</label><select value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })}><option value='year_1'>Year 1</option><option value='year_2'>Year 2</option><option value='year_3'>Year 3</option></select></div>
            <div className='form-row'><label>File Type</label><select value={form.file_type} onChange={(e) => setForm({ ...form, file_type: e.target.value })}><option value='notes'>Notes</option><option value='pyq'>Previous Year Question Papers</option><option value='syllabus'>Syllabus</option></select></div>
            <div className='form-row'><label>Choose File</label><input type='file' onChange={(e) => setForm({ ...form, file: e.target.files?.[0] || null })} required /></div>
            <div className='top-actions' style={{ marginTop: 8 }}>
              <button className='action-btn' type='submit' disabled={busy}>{busy ? 'Uploading...' : 'Upload File'}</button>
              <button className='action-btn' type='button' onClick={() => navigate(backPath)}>Back to Academics</button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
