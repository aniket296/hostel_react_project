import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'

const emptyForm = {
  full_name: '',
  phone_number: '',
  department: '',
  year: 'year_1',
  gender: 'male',
  room_number: '',
  password: '',
}

export default function StudentFormPage({ role }) {
  const { id } = useParams()
  const editing = Boolean(id)
  const navigate = useNavigate()
  const [form, setForm] = useState(emptyForm)
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      client.get('/departments/'),
      editing ? client.get(`/students/${id}/`) : Promise.resolve({ data: null }),
    ]).then(([deptRes, studentRes]) => {
      setDepartments(Array.isArray(deptRes.data) ? deptRes.data : [])
      if (studentRes.data) {
        setForm({
          full_name: studentRes.data.full_name || '',
          phone_number: studentRes.data.phone_number || '',
          department: studentRes.data.department || '',
          year: studentRes.data.year || 'year_1',
          gender: studentRes.data.gender || 'male',
          room_number: studentRes.data.room_number || '',
          password: '',
        })
      }
    }).catch((err) => setError(err.response?.data?.detail || 'Failed to load form data.')).finally(() => setLoading(false))
  }, [editing, id])

  function updateField(key, value) {
    setForm((old) => ({ ...old, [key]: value }))
  }

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = { ...form, department: form.department || null }
      if (!payload.password) delete payload.password
      if (editing) await client.put(`/students/${id}/`, payload)
      else await client.post('/students/', payload)
      navigate(role === 'admin' ? '/admin/students' : '/clerk/students')
    } catch (err) {
      const data = err.response?.data
      const message = typeof data === 'object' ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ') : (data?.detail || 'Save failed.')
      setError(message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className='loading-box'>Loading student form...</div>

  return (
    <>
      <h1 className='page-title'>{editing ? 'Edit Student' : 'Add Student'}</h1>
      <div className='top-actions'><Link to={role === 'admin' ? '/admin/students' : '/clerk/students'}>Back to Student List</Link></div>
      <div className='panel'>
        <div className='panel-header'>{editing ? 'Update Student Details' : 'Create Student Account'}</div>
        <div className='panel-body'>
          {error && <div className='error-box'>{error}</div>}
          <form onSubmit={submit} className='form-grid'>
            <div><label>Full Name</label><input className='form-control' value={form.full_name} onChange={(e) => updateField('full_name', e.target.value)} required /></div>
            <div><label>Phone Number</label><input className='form-control' value={form.phone_number} onChange={(e) => updateField('phone_number', e.target.value)} required /></div>
            <div><label>Department</label><select className='form-control' value={form.department} onChange={(e) => updateField('department', e.target.value)}><option value=''>Select Department</option>{departments.map((dept) => <option key={dept.id} value={dept.id}>{dept.name}</option>)}</select></div>
            <div><label>Year</label><select className='form-control' value={form.year} onChange={(e) => updateField('year', e.target.value)}><option value='year_1'>Year 1</option><option value='year_2'>Year 2</option><option value='year_3'>Year 3</option></select></div>
            <div><label>Gender</label><select className='form-control' value={form.gender} onChange={(e) => updateField('gender', e.target.value)}><option value='male'>Male</option><option value='female'>Female</option></select></div>
            <div><label>Room Number</label><input className='form-control' value={form.room_number} onChange={(e) => updateField('room_number', e.target.value)} required /></div>
            <div><label>{editing ? 'New Password (optional)' : 'Password'}</label><input className='form-control' type='password' value={form.password} onChange={(e) => updateField('password', e.target.value)} required={!editing} /></div>
            <div><button className='action-btn' type='submit' disabled={saving}>{saving ? 'Saving...' : (editing ? 'Update Student' : 'Create Student')}</button></div>
          </form>
        </div>
      </div>
    </>
  )
}
