import client from '../../api/client'
import { useApi } from '../../hooks'

export default function SystemSettingsPage() {
  const { data, loading, error } = useApi(() => client.get('/system-settings/'), [])

  if (loading) return <div className='loading-box'>Loading system settings...</div>
  if (error) return <div className='error-box'>{error}</div>

  return (
    <>
      <h1 className='page-title'>System Settings</h1>
      <div className='panel'>
        <div className='panel-header'>Portal Configuration</div>
        <div className='panel-body'>
          <div className='form-row'><label>College Name</label><div className='readonly-box'>{data?.college_name || '-'}</div></div>
          <div className='form-row'><label>System Title</label><div className='readonly-box'>{data?.system_title || '-'}</div></div>
          <div className='form-row'><label>Maintenance Mode</label><div className='readonly-box'>{data?.maintenance_mode ? 'Enabled' : 'Disabled'}</div></div>
          <div className='top-note'>This page is connected in read-only mode in the current API build.</div>
        </div>
      </div>
    </>
  )
}
