import { useState } from 'react'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate } from '../../utils'

export default function BackupListPage() {
  const { data, loading, error } = useApi(() => client.get('/backups/'), [])
  const backups = Array.isArray(data) ? data : []
  const [note, setNote] = useState('')

  return (
    <>
      <h1 className='page-title'>Database Backups</h1>
      <div className='top-actions'><button className='action-btn' type='button' onClick={() => setNote('Create Backup needs backend API support. List view is connected, but create/download/restore are not exposed in the current API build yet.')}>Create Backup</button></div>
      {note && <div className='readonly-box' style={{ marginBottom: 12 }}>{note}</div>}
      {loading && <div className='loading-box'>Loading backups...</div>}
      {error && <div className='error-box'>{error}</div>}
      {!loading && !error && (
        <div className='panel'>
          <div className='panel-header'>Backup Records</div>
          <div className='panel-body table-wrap'>
            <table className='data-table'>
              <thead><tr><th>ID</th><th>Created By</th><th>Created At</th><th>File</th></tr></thead>
              <tbody>
                {backups.length ? backups.map((backup) => <tr key={backup.id}><td>{backup.id}</td><td>{backup.created_by || '-'}</td><td>{formatDate(backup.created_at)}</td><td>{backup.backup_file || '-'}</td></tr>) : <tr><td colSpan='4'>No backups found.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
