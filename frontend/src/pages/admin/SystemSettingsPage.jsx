import { useEffect, useState } from 'react'
import client from '../../api/client'
import { useApi } from '../../hooks'

export default function SystemSettingsPage() {
  const { data, loading, error } = useApi(() => client.get('/system-settings/'), [])
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!data) return
    setForm({
      college_name: data.college_name || '',
      system_title: data.system_title || '',
      maintenance_mode: Boolean(data.maintenance_mode),
      college_logo: null,
      header_photo: null,
    })
  }, [data])

  async function save(e) {
    e.preventDefault()
    if (!form) return
    try {
      setSaving(true)
      setMessage('')
      const fd = new FormData()
      fd.append('college_name', form.college_name)
      fd.append('system_title', form.system_title)
      fd.append('maintenance_mode', form.maintenance_mode ? 'true' : 'false')
      if (form.college_logo) fd.append('college_logo', form.college_logo)
      if (form.header_photo) fd.append('header_photo', form.header_photo)
      const res = await client.patch('/system-settings/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setForm((prev) => prev ? {
        ...prev,
        college_name: res.data.college_name || '',
        system_title: res.data.system_title || '',
        maintenance_mode: Boolean(res.data.maintenance_mode),
        college_logo: null,
        header_photo: null,
      } : prev)
      setMessage('System settings saved.')
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Failed to save system settings.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className='loading-box'>Loading system settings...</div>
  if (error) return <div className='error-box'>{error}</div>
  if (!form) return null

  return (
    <>
      <h1 className='page-title'>System Settings</h1>
      <div className='panel'>
        <div className='panel-header'>Portal Configuration</div>
        <div className='panel-body'>
          {message && <div className='readonly-box' style={{ marginBottom: 12 }}>{message}</div>}
          <form onSubmit={save} className='form-grid'>
            <div>
              <label>College Name</label>
              <input className='form-control' value={form.college_name} onChange={(e) => setForm({ ...form, college_name: e.target.value })} />
            </div>
            <div>
              <label>System Title</label>
              <input className='form-control' value={form.system_title} onChange={(e) => setForm({ ...form, system_title: e.target.value })} />
            </div>
            <div>
              <label>College Logo</label>
              <input className='form-control' type='file' onChange={(e) => setForm({ ...form, college_logo: e.target.files?.[0] || null })} />
            </div>
            <div>
              <label>Header Photo</label>
              <input className='form-control' type='file' onChange={(e) => setForm({ ...form, header_photo: e.target.files?.[0] || null })} />
            </div>
            <div>
              <label>
                <input type='checkbox' checked={form.maintenance_mode} onChange={(e) => setForm({ ...form, maintenance_mode: e.target.checked })} />
                {' '}Maintenance Mode
              </label>
            </div>
            <div>
              <button className='action-btn' type='submit' disabled={saving}>{saving ? 'Saving...' : 'Save Settings'}</button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
