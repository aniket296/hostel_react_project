import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { downloadCsv, hostelLabel, yearLabel } from '../../utils'

export default function StudentListPage({ role }) {
  const location = useLocation()
  const navigate = useNavigate()
  const params = new URLSearchParams(location.search)
  const initialSearch = params.get('search') || ''
  const hostel = params.get('hostel') || ''
  const [search, setSearch] = useState(initialSearch)
  const query = useMemo(() => initialSearch ? `?q=${encodeURIComponent(initialSearch)}` : '', [initialSearch])
  const { data, setData, loading, error } = useApi(() => client.get(`/students/${query}`), [query])
  const students = Array.isArray(data) ? data.filter((s) => !hostel || s.hostel === hostel) : []
  const [selectedIds, setSelectedIds] = useState([])
  const [statusMessage, setStatusMessage] = useState('')

  const base = role === 'admin' ? '/admin/students' : '/clerk/students'

  const applySearch = (e) => {
    e.preventDefault()
    const next = new URLSearchParams()
    if (search) next.set('search', search)
    if (hostel) next.set('hostel', hostel)
    navigate(`${base}${next.toString() ? `?${next}` : ''}`)
  }

  async function deleteOne(id) {
    if (!window.confirm('Delete this student?')) return
    try {
      await client.delete(`/students/${id}/`)
      setData((old) => (old || []).filter((item) => item.id !== id))
      setSelectedIds((old) => old.filter((x) => x !== id))
      setStatusMessage('')
    } catch {
      setStatusMessage('Failed to delete the student. Please try again.')
    }
  }

  async function bulkDelete() {
    if (!selectedIds.length || !window.confirm('Delete selected students?')) return
    const failedIds = []
    for (const id of selectedIds) {
      try {
        await client.delete(`/students/${id}/`)
      } catch {
        failedIds.push(id)
      }
    }
    setData((old) => (old || []).filter((item) => !selectedIds.includes(item.id)))
    setSelectedIds([])
    if (failedIds.length) {
      setStatusMessage(`Failed to delete ${failedIds.length} selected student${failedIds.length > 1 ? 's' : ''}.`)
    } else {
      setStatusMessage('')
    }
  }

  function exportStudents() {
    downloadCsv('students.csv', [
      ['Name', 'Phone', 'Department', 'Year', 'Gender', 'Hostel', 'Room'],
      ...students.map((s) => [s.full_name, s.phone_number, s.department_name || '', yearLabel(s.year), s.gender, hostelLabel(s.hostel), s.room_number]),
    ])
  }

  function toggleAll(checked) {
    setSelectedIds(checked ? students.map((s) => s.id) : [])
  }

  function toggleOne(id, checked) {
    setSelectedIds((old) => checked ? [...new Set([...old, id])] : old.filter((x) => x !== id))
  }

  return (
    <>
      <h1 className='page-title'>Student Management</h1>
      <div className='top-actions'>
        <Link to={`${base}/add`}>Add Student</Link>
        <Link to={`${base}/import`}>Import Students</Link>
        <button type='button' className='inline-btn' onClick={exportStudents}>Export Students</button>
      </div>

      <div className='filter-bar'>
        <form onSubmit={applySearch} className='filter-grid'>
          <div><label>Search Student</label><input className='form-control' value={search} onChange={(e) => setSearch(e.target.value)} placeholder='Name, phone, room, department' /></div>
          {role === 'admin' && <div><label>Hostel</label><div className='readonly-box'>{hostel ? hostelLabel(hostel) : 'All'}</div></div>}
          <div><button className='action-btn' type='submit'>Apply Filters</button></div>
        </form>
      </div>

      {loading && <div className='loading-box'>Loading students...</div>}
      {error && <div className='error-box'>{error}</div>}
      {statusMessage && <div className='error-box'>{statusMessage}</div>}

      {!loading && !error && (
        <>
          <div className='page-card table-wrap'>
            <table className='data-table'>
              <thead>
                <tr>
                  <th><input type='checkbox' checked={students.length > 0 && selectedIds.length === students.length} onChange={(e) => toggleAll(e.target.checked)} /></th>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Department</th>
                  <th>Year</th>
                  <th>Gender</th>
                  <th>Hostel</th>
                  <th>Room</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.length ? students.map((student) => (
                  <tr key={student.id}>
                    <td><input type='checkbox' checked={selectedIds.includes(student.id)} onChange={(e) => toggleOne(student.id, e.target.checked)} /></td>
                    <td>{student.full_name}</td>
                    <td>{student.phone_number}</td>
                    <td>{student.department_name || '-'}</td>
                    <td>{yearLabel(student.year)}</td>
                    <td>{student.gender}</td>
                    <td>{hostelLabel(student.hostel)}</td>
                    <td>{student.room_number}</td>
                    <td><Link to={`${base}/${student.id}/edit`}>Edit</Link><button className='inline-btn action-btn-danger' type='button' onClick={() => deleteOne(student.id)} style={{ marginLeft: 8 }}>Delete</button></td>
                  </tr>
                )) : <tr><td colSpan='9'>No students found.</td></tr>}
              </tbody>
            </table>
          </div>
          <div className='top-actions'>
            <button className='action-btn action-btn-danger' type='button' onClick={bulkDelete}>Bulk Delete Selected</button>
          </div>
        </>
      )}
    </>
  )
}
