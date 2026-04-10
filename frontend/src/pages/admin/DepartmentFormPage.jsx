import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import client from '../../api/client'

export default function DepartmentFormPage() {
  const { id } = useParams()
  const editing = Boolean(id)
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(editing)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/departments/').then((res) => {
      const list = Array.isArray(res.data) ? res.data : []
      setDepartments(list)
      if (editing) {
        const dept = list.find((item) => String(item.id) === String(id))
        if (dept) setName(dept.name)
        else setError('Department not found in current API list.')
      }
    }).catch((err) => setError(err.response?.data?.detail || 'Failed to load departments.')).finally(() => setLoading(false))
  }, [editing, id])

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (editing) {
        setError('Department edit is not available in the current backend API yet.')
        return
      }
      await client.post('/departments/', { name })
      navigate('/admin/departments')
    } catch (err) {
      const data = err.response?.data
      setError(typeof data === 'object' ? JSON.stringify(data) : (data?.detail || 'Save failed.'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className='loading-box'>Loading department...</div>

  return (
    <>
      <h1 className='page-title'>{editing ? 'Edit Department' : 'Add Department'}</h1>
      <div className='top-actions'><Link to='/admin/departments'>Back to Department List</Link></div>
      <div className='panel'>
        <div className='panel-header'>{editing ? 'Update Department' : 'Create Department'}</div>
        <div className='panel-body'>
          {error && <div className='error-box'>{error}</div>}
          <form onSubmit={submit} className='form-grid'>
            <div>
              <label>Department Name</label>
              <input className='form-control' value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <button className='action-btn' type='submit' disabled={saving}>{saving ? 'Saving...' : (editing ? 'Update Department' : 'Add Department')}</button>
            </div>
          </form>
        </div>
      </div>
      {editing && departments.length > 0 && <div className='readonly-box'>This page is visible for route completeness, but department edit/delete needs backend API support.</div>}
    </>
  )
}
