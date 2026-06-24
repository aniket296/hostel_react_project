import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../../api/client'
import { parseCsvText } from '../../utils'

export default function StudentImportPage({ role }) {
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('Upload a CSV with columns: full_name, phone_number, department(optional id), year, gender, room_number, password(optional).')
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    if (!file) return
    setBusy(true)
    setMessage('Reading file...')
    try {
      const text = await file.text()
      const rows = parseCsvText(text)
      let success = 0
      let fail = 0
      const rowErrors = []

      for (let rowIndex = 0; rowIndex < rows.length; rowIndex += 1) {
        const row = rows[rowIndex]
        try {
          await client.post('/students/', {
            full_name: row.full_name || row.name || '',
            phone_number: row.phone_number || row.phone || '',
            department: row.department || null,
            year: row.year || 'year_1',
            gender: row.gender || 'male',
            room_number: row.room_number || row.room || '',
            password: row.password || '',
          })
          success += 1
        } catch (err) {
          fail += 1
          const detail = err.response?.data?.detail || err.response?.data || err.message || 'Unknown error'
          if (rowErrors.length < 3) {
            rowErrors.push(`Row ${rowIndex + 1}: ${detail}`)
          }
        }
      }

      let summary = `Import finished. Success: ${success}, Failed: ${fail}`
      if (rowErrors.length) {
        summary += ` - ${rowErrors.join('; ')}`
      }
      setMessage(summary)

      if (fail === 0) {
        setTimeout(() => navigate(role === 'admin' ? '/admin/students' : '/clerk/students'), 1200)
      }
    } catch {
      setMessage('Import failed. Please check CSV format.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h1 className='page-title'>Import Students</h1>
      <div className='top-actions'><Link to={role === 'admin' ? '/admin/students' : '/clerk/students'}>Back to Student List</Link></div>
      <div className='panel'>
        <div className='panel-header'>Student CSV Import</div>
        <div className='panel-body'>
          <div className='readonly-box' style={{ marginBottom: 16 }}>{message}</div>
          <form onSubmit={submit} className='form-grid'>
            <div>
              <label>CSV File</label>
              <input className='form-control' type='file' accept='.csv' onChange={(e) => setFile(e.target.files?.[0] || null)} required />
            </div>
            <div>
              <button className='action-btn' type='submit' disabled={busy}>{busy ? 'Importing...' : 'Start Import'}</button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
