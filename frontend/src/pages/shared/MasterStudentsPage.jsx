
import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function MasterStudentsPage({ role, canAdd = true }) {
  const [students, setStudents] = useState([])
  const [departments, setDepartments] = useState([])
  const [q, setQ] = useState('')
  const [error, setError] = useState('')
  const [form, setForm] = useState({ full_name: '', phone_number: '', department: '', year: 'year_1', gender: 'male', room_number: '', password: '' })

  const load = async () => {
    const res = await client.get('/students/', { params: { q } })
    setStudents(res.data)
  }

  useEffect(() => {
    client.get('/departments/').then(r => setDepartments(r.data))
    load()
  }, [])

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      await client.post('/students/', form)
      setForm({ full_name: '', phone_number: '', department: '', year: 'year_1', gender: 'male', room_number: '', password: '' })
      load()
    } catch (err) {
      setError(err.response?.data ? JSON.stringify(err.response.data) : 'Unable to save student')
    }
  }

  async function remove(id){
    await client.delete(`/students/${id}/`)
    load()
  }

  return (
    <div>
      <h1 className="page-title">{role === 'admin' ? 'Students' : 'Hostel Students'}</h1>
      <div className="grid two-col">
        {canAdd && <form className="card" onSubmit={submit}>
          <h3>Add Student</h3>
          <input placeholder="Full name" value={form.full_name} onChange={e=>setForm({...form, full_name:e.target.value})} required />
          <input placeholder="Phone number" value={form.phone_number} onChange={e=>setForm({...form, phone_number:e.target.value})} required />
          <select value={form.department} onChange={e=>setForm({...form, department:e.target.value})}>
            <option value="">Select department</option>
            {departments.map(dep => <option key={dep.id} value={dep.id}>{dep.name}</option>)}
          </select>
          <select value={form.year} onChange={e=>setForm({...form, year:e.target.value})}><option value="year_1">Year 1</option><option value="year_2">Year 2</option><option value="year_3">Year 3</option></select>
          <select value={form.gender} onChange={e=>setForm({...form, gender:e.target.value})}><option value="male">Male</option><option value="female">Female</option></select>
          <input placeholder="Room number" value={form.room_number} onChange={e=>setForm({...form, room_number:e.target.value})} required />
          <input type="password" placeholder="Password (optional)" value={form.password} onChange={e=>setForm({...form, password:e.target.value})} />
          {error && <div className="error-box">{error}</div>}
          <button className="btn">Save Student</button>
        </form>}
        <div className="card">
          <div className="toolbar"><h3>Student List</h3><input placeholder="Search name / phone / room / department" value={q} onChange={e=>setQ(e.target.value)} /></div>
          <button className="btn btn-light" onClick={load}>Search</button>
          <table className="table">
            <thead><tr><th>Name</th><th>Phone</th><th>Department</th><th>Year</th><th>Room</th><th>Hostel</th><th></th></tr></thead>
            <tbody>{students.map(item => <tr key={item.id}><td>{item.full_name}</td><td>{item.phone_number}</td><td>{item.department_name || '-'}</td><td>{item.year}</td><td>{item.room_number}</td><td>{item.hostel}</td><td><button className="btn btn-danger" onClick={()=>remove(item.id)}>Delete</button></td></tr>)}</tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
