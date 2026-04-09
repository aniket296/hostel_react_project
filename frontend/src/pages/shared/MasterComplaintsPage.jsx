
import { useEffect, useState } from 'react'
import client from '../../api/client'
import StatusBadge from '../../components/StatusBadge'

export default function MasterComplaintsPage({ role }) {
  const [items, setItems] = useState([])
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const [description, setDescription] = useState('')
  const [roomNumber, setRoomNumber] = useState('')
  const [error, setError] = useState('')

  const load = () => client.get('/complaints/', { params: { status, q } }).then(r => setItems(r.data))
  useEffect(() => { load() }, [])

  async function createComplaint(e) {
    e.preventDefault()
    setError('')
    try {
      await client.post('/student/complaints/', { description, room_number: roomNumber })
      setDescription('')
      setRoomNumber('')
      load()
    } catch (err) {
      setError(err.response?.data ? JSON.stringify(err.response.data) : 'Unable to create complaint')
    }
  }

  async function assignWorker(id) {
    const worker_name = window.prompt('Enter worker name')
    if (!worker_name) return
    await client.post(`/complaints/${id}/assign-worker/`, { worker_name })
    load()
  }

  async function markCompleted(id) { await client.post(`/complaints/${id}/mark-completed/`); load() }
  async function markSolved(id) { await client.post(`/complaints/${id}/mark-solved/`); load() }
  async function markUnsolved(id) { await client.post(`/complaints/${id}/mark-unsolved/`); load() }
  async function reopen(id) { await client.post(`/complaints/${id}/reopen/`); load() }

  return (
    <div>
      <h1 className="page-title">Complaints</h1>
      {role === 'student' && <form className="card" onSubmit={createComplaint}>
        <h3>Create Complaint</h3>
        <input maxLength="100" value={description} onChange={(e)=>setDescription(e.target.value)} placeholder="Complaint description (max 6 words)" required />
        <input maxLength="20" value={roomNumber} onChange={(e)=>setRoomNumber(e.target.value)} placeholder="Room number" required />
        {error && <div className="error-box">{error}</div>}
        <button className="btn">Submit Complaint</button>
      </form>}
      <div className="card">
        <div className="toolbar">
          <input placeholder="Search" value={q} onChange={(e)=>setQ(e.target.value)} />
          <select value={status} onChange={(e)=>setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="new">New</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="solved">Solved</option>
            <option value="unsolved">Unsolved</option>
          </select>
          <button className="btn btn-light" onClick={load}>Apply</button>
        </div>
        <table className="table"><thead><tr><th>ID</th><th>Student</th><th>Description</th><th>Room</th><th>Status</th><th>Worker</th><th>Actions</th></tr></thead><tbody>{items.map(item => <tr key={item.id}><td>{item.id}</td><td>{item.student_name_snapshot}</td><td>{item.description}</td><td>{item.room_number_snapshot}</td><td><StatusBadge value={item.status} /></td><td>{item.worker_name || '-'}</td><td className="actions-cell">{role !== 'student' && item.status === 'new' && <button className="btn" onClick={()=>assignWorker(item.id)}>Assign</button>}{role !== 'student' && item.status === 'in_progress' && <button className="btn" onClick={()=>markCompleted(item.id)}>Complete</button>}{role === 'student' && item.status === 'completed' && <><button className="btn" onClick={()=>markSolved(item.id)}>Solved</button><button className="btn btn-light" onClick={()=>markUnsolved(item.id)}>Unsolved</button></>}{role !== 'student' && item.status === 'unsolved' && <button className="btn btn-light" onClick={()=>reopen(item.id)}>Reopen</button>}</td></tr>)}</tbody></table>
      </div>
    </div>
  )
}
