import { Link } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'

export default function DepartmentListPage() {
  const { data, loading, error } = useApi(() => client.get('/departments/'), [])
  const departments = Array.isArray(data) ? data : []

  return (
    <>
      <h1 className='page-title'>Department Management</h1>
      <div className='top-actions'><Link to='/admin/departments/add'>Add Department</Link></div>
      {loading && <div className='loading-box'>Loading departments...</div>}
      {error && <div className='error-box'>{error}</div>}
      {!loading && !error && (
        <div className='panel'>
          <div className='panel-header'>Department Records</div>
          <div className='panel-body table-wrap'>
            <table className='data-table'>
              <thead><tr><th>ID</th><th>Department Name</th><th>Actions</th></tr></thead>
              <tbody>
                {departments.length ? departments.map((dept) => <tr key={dept.id}><td>{dept.id}</td><td>{dept.name}</td><td><Link to={`/admin/departments/${dept.id}/edit`}>Edit</Link></td></tr>) : <tr><td colSpan='3'>No departments found.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
