
import { useEffect, useState } from 'react'
import client from '../../api/client'

const initialForm = { department:'', year:'year_1', subject:'', course_code:'', file_type:'notes', file:null }

export default function MasterAcademicsPage({ role, canUpload = true }) {
  const [items, setItems] = useState([])
  const [departments, setDepartments] = useState([])
  const [subjects, setSubjects] = useState([])
  const [form, setForm] = useState(initialForm)
  const [q, setQ] = useState('')
  const [error, setError] = useState('')

  const load = () => client.get('/academics/', { params: { q } }).then(r => setItems(r.data))

  useEffect(() => {
    client.get('/departments/').then(r => setDepartments(r.data))
    client.get('/subjects/').then(r => setSubjects(r.data))
    load()
  }, [])

  async function upload(e){
    e.preventDefault()
    setError('')
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k,v]) => { if (v !== null && v !== '') fd.append(k, v) })
      await client.post('/academics/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setForm(initialForm)
      const fileInput = document.getElementById('academic-file-input')
      if (fileInput) fileInput.value = ''
      load()
    } catch (err) {
      setError(err.response?.data ? JSON.stringify(err.response.data) : 'Unable to upload file')
    }
  }

  async function remove(id){
    await client.delete(`/academics/${id}/`)
    load()
  }

  return (
    <div>
      <h1 className="page-title">Academics</h1>
      {canUpload && <form className="card" onSubmit={upload}>
        <h3>Upload Academic File</h3>
        <div className="grid two-col">
          <select value={form.department} onChange={e=>setForm({...form, department:e.target.value})} required><option value="">Select department</option>{departments.map(dep => <option key={dep.id} value={dep.id}>{dep.name}</option>)}</select>
          <select value={form.year} onChange={e=>setForm({...form, year:e.target.value})} required><option value="year_1">Year 1</option><option value="year_2">Year 2</option><option value="year_3">Year 3</option></select>
          <select value={form.subject} onChange={e=>setForm({...form, subject:e.target.value})} required><option value="">Select subject</option>{subjects.map(sub => <option key={sub.id} value={sub.id}>{sub.name}</option>)}</select>
          <input placeholder="Course code" value={form.course_code} onChange={e=>setForm({...form, course_code:e.target.value})} />
          <select value={form.file_type} onChange={e=>setForm({...form, file_type:e.target.value})} required>
            <option value="curriculum">Curriculum</option>
            <option value="notes">Notes</option>
            <option value="pyq_pt">PYQ (PT Exam)</option>
            <option value="pyq_semester">PYQ (Semester Exam)</option>
          </select>
          <input id="academic-file-input" type="file" onChange={e=>setForm({...form,file:e.target.files?.[0] || null})} required />
        </div>
        {error && <div className="error-box">{error}</div>}
        <button className="btn">Upload</button>
      </form>}
      <div className="card">
        <div className="toolbar"><input placeholder="Search by course code / subject / department" value={q} onChange={e=>setQ(e.target.value)} /><button className="btn btn-light" onClick={load}>Apply</button></div>
        <table className="table"><thead><tr><th>Department</th><th>Year</th><th>Subject</th><th>Course</th><th>Type</th><th>File</th><th></th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.department_name}</td><td>{item.year}</td><td>{item.subject_name}</td><td>{item.course_code || '-'}</td><td>{item.file_type}</td><td><a href={item.download_url} target="_blank" rel="noreferrer">Download</a></td><td>{role !== 'student' && <button className="btn btn-danger" onClick={()=>remove(item.id)}>Delete</button>}</td></tr>)}</tbody></table>
      </div>
    </div>
  )
}
