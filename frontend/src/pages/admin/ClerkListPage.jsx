import { Link } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { hostelLabel } from '../../utils'

export default function ClerkListPage() {
  const { data, setData, loading, error } = useApi(() => client.get('/clerks/'), [])
  const clerks = Array.isArray(data) ? data : []

  async function deleteClerk(id) {
    if (!window.confirm('Delete this clerk?')) return
    await client.delete(`/clerks/${id}/`)
    setData((old) => (old || []).filter((item) => item.id !== id))
  }

  return (
    <>
      <h1 className='page-title'>Clerk Management</h1>
      <div className='top-actions'>
        <Link to='/admin/clerks/add'>Add Clerk</Link>
      </div>

      {loading && <div className='loading-box'>Loading clerks...</div>}
      {error && <div className='error-box'>{error}</div>}

      {!loading && !error && (
        <div className='panel'>
          <div className='panel-header'>Clerk Records</div>
          <div className='panel-body table-wrap'>
            <table className='data-table'>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Full Name</th>
                  <th>Username</th>
                  <th>Phone Number</th>
                  <th>Assigned Hostel</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {clerks.length ? clerks.map((clerk) => (
                  <tr key={clerk.id}>
                    <td>{clerk.id}</td>
                    <td>{clerk.full_name}</td>
                    <td>{clerk.username}</td>
                    <td>{clerk.phone_number}</td>
                    <td>{hostelLabel(clerk.assigned_hostel)}</td>
                    <td>
                      <Link to={`/admin/clerks/${clerk.id}/edit`}>Edit</Link>
                      <button className='inline-btn action-btn-danger' type='button' onClick={() => deleteClerk(clerk.id)} style={{ marginLeft: 8 }}>Delete</button>
                    </td>
                  </tr>
                )) : <tr><td colSpan='6'>No clerks found.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
