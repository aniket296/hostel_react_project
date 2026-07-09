import { useState } from 'react'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate } from '../../utils'

export default function BackupListPage() {
  const { data, loading, error } = useApi(() => client.get('/backups/'), [])
  const backups = Array.isArray(data) ? data : []
  const [note, setNote] = useState('')
  const [busyId, setBusyId] = useState(null)

  async function createBackup() {
    try {
      setBusyId('create')
      const res = await client.post('/backups/')
      setNote(`Created backup #${res.data.id}.`)
      window.location.reload()
    } catch (err) {
      setNote(err.response?.data?.detail || 'Failed to create backup.')
    } finally {
      setBusyId(null)
    }
  }

  async function action(id, actionName) {
    try {
      setBusyId(`${actionName}:${id}`)
      await client.post(`/backups/${id}/${actionName}/`)
      window.location.reload()
    } catch (err) {
      setNote(err.response?.data?.detail || `Failed to ${actionName} backup.`)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <h1 className='page-title'>Database Backups</h1>
      <div className='top-actions'><button className='action-btn' type='button' onClick={createBackup} disabled={busyId === 'create'}>{busyId === 'create' ? 'Creating...' : 'Create Backup'}</button></div>
      {note && <div className='readonly-box' style={{ marginBottom: 12 }}>{note}</div>}
      {loading && <div className='loading-box'>Loading backups...</div>}
      {error && <div className='error-box'>{error}</div>}
      {!loading && !error && (
        <div className='panel'>
          <div className='panel-header'>Backup Records</div>
          <div className='panel-body table-wrap'>
            <table className='data-table'>
              <thead><tr><th>ID</th><th>Created By</th><th>Created At</th><th>File</th><th>Actions</th></tr></thead>
              <tbody>
                {backups.length ? backups.map((backup) => <tr key={backup.id}><td>{backup.id}</td><td>{backup.created_by || '-'}</td><td>{formatDate(backup.created_at)}</td><td><a href={backup.download_url} target='_blank' rel='noreferrer'>{backup.backup_file || 'Download'}</a></td><td style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}><button className='inline-btn' type='button' onClick={() => action(backup.id, 'restore')} disabled={busyId === `restore:${backup.id}`}>Restore</button><button className='inline-btn action-btn-danger' type='button' onClick={() => action(backup.id, 'delete')} disabled={busyId === `delete:${backup.id}`}>Delete</button></td></tr>) : <tr><td colSpan='5'>No backups found.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
