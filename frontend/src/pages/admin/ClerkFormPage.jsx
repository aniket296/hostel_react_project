import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'

const initialForm = {
  username: '',
  password: '',
  full_name: '',
  phone_number: '',
  assigned_hostel: 'boys_hostel',
}

export default function ClerkFormPage() {
  const { id } = useParams()
  const editing = Boolean(id)
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(editing)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!editing) return
    client.get(`/clerks/${id}/`).then((res) => {
      setForm({
        username: res.data.username || '',
        password: '',
        full_name: res.data.full_name || '',
        phone_number: res.data.phone_number || '',
        assigned_hostel: res.data.assigned_hostel || 'boys_hostel',
      })
    }).catch((err) => setError(err.response?.data?.detail || 'Failed to load clerk.')).finally(() => setLoading(false))
  }, [editing, id])

  function updateField(key, value) {
    setForm((old) => ({ ...old, [key]: value }))
  }

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = { ...form }
      if (!payload.password) delete payload.password
      if (editing) {
        await client.put(`/clerks/${id}/`, payload)
      } else {
        await client.post('/clerks/', payload)
      }
      navigate('/admin/clerks')
    } catch (err) {
      const data = err.response?.data
      const message = typeof data === 'object' ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ') : (data?.detail || 'Save failed.')
      setError(message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className='loading-box'>Loading clerk...</div>

  return (
    <>
      <h1 className='page-title'>{editing ? 'Edit Clerk' : 'Add Clerk'}</h1>
      <div className='top-actions'><Link to='/admin/clerks'>Back to Clerk List</Link></div>
      <div className='panel'>
        <div className='panel-header'>{editing ? 'Update Clerk Details' : 'Create Clerk Account'}</div>
        <div className='panel-body'>
          {error && <div className='error-box'>{error}</div>}
          <form onSubmit={submit} className='form-grid'>
            <div>
              <label>Full Name</label>
              <input className='form-control' value={form.full_name} onChange={(e) => updateField('full_name', e.target.value)} required />
            </div>
            <div>
              <label>Username</label>
              <input className='form-control' value={form.username} onChange={(e) => updateField('username', e.target.value)} required />
            </div>
            <div>
              <label>Phone Number</label>
              <input className='form-control' value={form.phone_number} onChange={(e) => updateField('phone_number', e.target.value)} required />
            </div>
            <div>
              <label>{editing ? 'New Password (optional)' : 'Password'}</label>
              <input className='form-control' type='password' value={form.password} onChange={(e) => updateField('password', e.target.value)} required={!editing} />
            </div>
            <div>
              <label>Assigned Hostel</label>
              <select className='form-control' value={form.assigned_hostel} onChange={(e) => updateField('assigned_hostel', e.target.value)}>
                <option value='boys_hostel'>Boys Hostel</option>
                <option value='girls_hostel'>Girls Hostel</option>
              </select>
            </div>
            <div>
              <button className='action-btn' type='submit' disabled={saving}>{saving ? 'Saving...' : (editing ? 'Update Clerk' : 'Create Clerk')}</button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
