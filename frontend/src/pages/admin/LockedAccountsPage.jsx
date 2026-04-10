import client from '../../api/client'
import { useApi } from '../../hooks'
import { roleLabel } from '../../utils'

export default function LockedAccountsPage() {
  const { data, setData, loading, error } = useApi(() => client.get('/locked-accounts/'), [])
  const users = Array.isArray(data) ? data : []

  async function unlock(userId) {
    await client.post('/locked-accounts/', { user_id: userId })
    setData((old) => (old || []).filter((user) => user.id !== userId))
  }

  return (
    <>
      <h1 className='page-title'>Locked Accounts</h1>
      {loading && <div className='loading-box'>Loading locked accounts...</div>}
      {error && <div className='error-box'>{error}</div>}
      {!loading && !error && (
        <div className='panel'>
          <div className='panel-header'>Locked User Records</div>
          <div className='panel-body table-wrap'>
            <table className='data-table'>
              <thead><tr><th>ID</th><th>Username</th><th>Phone Number</th><th>Role</th><th>Action</th></tr></thead>
              <tbody>
                {users.length ? users.map((user) => <tr key={user.id}><td>{user.id}</td><td>{user.username || '-'}</td><td>{user.phone_number || '-'}</td><td>{roleLabel(user.role)}</td><td><button className='inline-btn' type='button' onClick={() => unlock(user.id)}>Unlock</button></td></tr>) : <tr><td colSpan='5'>No locked accounts found.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
