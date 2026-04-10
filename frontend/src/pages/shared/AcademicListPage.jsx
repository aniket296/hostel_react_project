import { useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { fileTypeLabel, formatDate, yearLabel } from '../../utils'

export default function AcademicListPage({ role }) {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const initialSearch = params.get('search') || ''
  const [search, setSearch] = useState(initialSearch)
  const query = useMemo(() => initialSearch ? `?q=${encodeURIComponent(initialSearch)}` : '', [initialSearch])
  const { data, setData, loading, error } = useApi(() => client.get(`/academics/${query}`), [query])
  const files = Array.isArray(data) ? data : []

  const applySearch = (e) => {
    e.preventDefault()
    const next = new URLSearchParams()
    if (search) next.set('search', search)
    window.location.search = next.toString()
  }

  async function removeFile(id) {
    await client.delete(`/academics/${id}/`)
    setData((old) => (old || []).filter((item) => item.id !== id))
  }

  return (
    <>
      <h1 className='page-title'>Academics</h1>
      <div className='top-actions'>
        <a href={role === 'admin' ? '/admin/academics/upload' : role === 'clerk' ? '/clerk/academics/upload' : '/student/academics/upload'}>{role === 'clerk' ? 'Upload File' : role === 'admin' ? 'Upload Academic File' : 'Upload File'}</a>
      </div>
      <div className='filter-bar'>
        <form onSubmit={applySearch} className='filter-grid'>
          <div><label>Search Subject / Course Code</label><input className='form-control' value={search} onChange={(e) => setSearch(e.target.value)} /></div>
          <div><button className='action-btn' type='submit'>Apply Filters</button></div>
        </form>
      </div>
      {loading && <div className='loading-box'>Loading academics...</div>}
      {error && <div className='error-box'>{error}</div>}
      {!loading && !error && (
        <div className='page-card table-wrap'>
          <table className='data-table'>
            <thead>
              <tr>
                <th>ID</th>
                <th>Subject</th>
                <th>Course Code</th>
                <th>Department</th>
                <th>Year</th>
                <th>File Type</th>
                <th>Uploaded By</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {files.length ? files.map((file) => (
                <tr key={file.id}>
                  <td>{file.id}</td>
                  <td>{file.subject_name || '-'}</td>
                  <td>{file.course_code || '-'}</td>
                  <td>{file.department_name || '-'}</td>
                  <td>{yearLabel(file.year)}</td>
                  <td>{fileTypeLabel(file.file_type)}</td>
                  <td>{file.uploaded_by_name_snapshot || '-'}</td>
                  <td>{formatDate(file.created_at)}</td>
                  <td>
                    <a href={file.download_url} target='_blank' rel='noreferrer'>Download</a>
                    {(role === 'admin' || role === 'clerk') && <button className='inline-btn action-btn-danger' type='button' onClick={() => removeFile(file.id)} style={{ marginLeft: 8 }}>Delete</button>}
                  </td>
                </tr>
              )) : <tr><td colSpan='9'>No academic files found.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
