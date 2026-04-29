import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'

const FILE_TYPES = [
  { value: 'pyq_pt', label: 'PYQ PT' },
  { value: 'pyq_semester', label: 'PYQ Semester' },
  { value: 'notes', label: 'Notes' },
  { value: 'question_bank', label: 'Question Bank' },
  { value: 'curriculum', label: 'Curriculum' },
]

export default function StudentAcademicsUploadPage() {
  const navigate = useNavigate()
  const { data: departments } = useApi(() => client.get('/departments/'), [])
  const [form, setForm] = useState({
    subject_name: '',
    department: '',
    year: 'year_1',
    file_type: 'notes',
    course_code: '',
    description: '',
    file: null,
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const setField = (key, value) => setForm((prev) => ({ ...prev, [key]: value }))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')

    const fd = new FormData()
    fd.append('subject_name', form.subject_name.trim())
    fd.append('course_code', form.course_code.trim())
    fd.append('description', form.description.trim())
    fd.append('department', form.department)
    fd.append('year', form.year)
    fd.append('file_type', form.file_type)
    if (form.file) fd.append('file', form.file)

    try {
      await client.post('/academics/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      navigate('/student/academics/download')
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') setError(data)
      else if (data?.detail) setError(data.detail)
      else if (data && typeof data === 'object') {
        const first = Object.values(data)[0]
        setError(Array.isArray(first) ? first[0] : String(first))
      } else {
        setError('Upload failed.')
      }
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
          <div className='top-note'>
            Upload notes, curriculum, previous year question papers, or question banks. Add a short
            description like unit, lesson, or topic before submitting.
          </div>

          <form onSubmit={submit}>
            {error && <div className='form-errors'>{error}</div>}

            <div className='form-row'>
              <label>Subject Name</label>
              <input
                className='form-control'
                value={form.subject_name}
                onChange={(e) => setField('subject_name', e.target.value)}
                required
              />
            </div>

            <div className='form-row'>
              <label>Course Code</label>
              <input
                className='form-control'
                value={form.course_code}
                onChange={(e) => setField('course_code', e.target.value)}
              />
            </div>

            <div className='form-row'>
              <label>Description</label>
              <textarea
                className='form-control'
                rows='3'
                value={form.description}
                onChange={(e) => setField('description', e.target.value)}
                placeholder='Example: Unit 2 notes, Lesson 4 PYQ, Chapter 3 important questions'
              />
            </div>

            <div className='form-row'>
              <label>Department</label>
              <select
                className='form-control'
                value={form.department}
                onChange={(e) => setField('department', e.target.value)}
                required
              >
                <option value=''>Select Department</option>
                {Array.isArray(departments) &&
                  departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
              </select>
            </div>

            <div className='form-row'>
              <label>Year</label>
              <select
                className='form-control'
                value={form.year}
                onChange={(e) => setField('year', e.target.value)}
              >
                <option value='year_1'>Year 1</option>
                <option value='year_2'>Year 2</option>
                <option value='year_3'>Year 3</option>
              </select>
            </div>

            <div className='form-row'>
              <label>File Type</label>
              <select
                className='form-control'
                value={form.file_type}
                onChange={(e) => setField('file_type', e.target.value)}
              >
                {FILE_TYPES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>

            <div className='form-row'>
              <label>Choose File</label>
              <input
                className='form-control'
                type='file'
                onChange={(e) => setField('file', e.target.files?.[0] || null)}
                required
              />
            </div>

            <div className='top-actions' style={{ marginTop: 8 }}>
              <button className='action-btn' type='submit' disabled={busy}>
                {busy ? 'Uploading...' : 'Upload File'}
              </button>
              <button
                className='action-btn'
                type='button'
                onClick={() => navigate('/student/academics/download')}
              >
                Back to Academics
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}