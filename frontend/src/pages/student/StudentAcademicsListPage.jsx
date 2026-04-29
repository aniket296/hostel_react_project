import { useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import client from '../../api/client'
import { useApi } from '../../hooks'
import { formatDate, yearLabel } from '../../utils'

function fileTypeDisplay(value) {
  const map = {
    pyq_pt: 'PYQ PT',
    pyq_semester: 'PYQ Semester',
    notes: 'Notes',
    question_bank: 'Question Bank',
    curriculum: 'Curriculum',
  }
  return map[value] || value || '-'
}

export default function StudentAcademicsListPage() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const initialSearch = params.get('search') || ''
  const [search, setSearch] = useState(initialSearch)
  const query = useMemo(
    () => (initialSearch ? `?q=${encodeURIComponent(initialSearch)}` : ''),
    [initialSearch]
  )
  const { data, loading, error } = useApi(() => client.get(`/academics/${query}`), [query])
  const files = Array.isArray(data) ? data : []

  const applySearch = (e) => {
    e.preventDefault()
    const next = new URLSearchParams()
    if (search) next.set('search', search)
    window.location.search = next.toString()
  }

  return (
    <>
      <div className='back-row'>
        <button type='button' className='action-btn' onClick={() => window.history.back()}>
          ← Back
        </button>
      </div>

      <h1 className='page-title'>Academics</h1>

      <div className='panel'>
        <div className='panel-header'>Academic File Filters</div>
        <div className='panel-body'>
          <form onSubmit={applySearch} className='filter-grid'>
            <div>
              <label>Search Subject / Course Code / Description</label>
              <input
                className='form-control'
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div>
              <button className='action-btn' type='submit'>
                Apply Filter
              </button>
            </div>
          </form>
        </div>
      </div>

      {loading && <div className='loading-box'>Loading academic files...</div>}
      {error && <div className='error-box'>{error}</div>}

      {!loading && !error && (
        <div className='student-record-list'>
          {files.length ? (
            files.map((file) => (
              <div className='student-record-box' key={file.id}>
                <div className='student-record-head'>
                  <div className='student-record-title'>
                    {file.course_code || file.subject_name || 'Academic File'}
                  </div>
                  <div className='student-record-badge'>{fileTypeDisplay(file.file_type)}</div>
                </div>

                <div className='student-record-body'>
                  <div><strong>Subject:</strong> {file.subject_name || '-'}</div>
                  <div><strong>Course Code:</strong> {file.course_code || '-'}</div>
                  <div><strong>Description:</strong> {file.description || '-'}</div>
                  <div><strong>Department:</strong> {file.department_name || '-'}</div>
                  <div><strong>Year:</strong> {yearLabel(file.year)}</div>
                  <div><strong>Uploaded By:</strong> {file.uploaded_by_name || file.uploaded_by_name_snapshot || '-'}</div>
                  <div><strong>Uploaded At:</strong> {formatDate(file.created_at)}</div>
                </div>

                <div className='student-record-actions'>
                  <a className='action-btn' href={file.download_url} target='_blank' rel='noreferrer'>
                    Download
                  </a>
                </div>
              </div>
            ))
          ) : (
            <div className='empty-box'>No academic files found.</div>
          )}
        </div>
      )}
    </>
  )
}