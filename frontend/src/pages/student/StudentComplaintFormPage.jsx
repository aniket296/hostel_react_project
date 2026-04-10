import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import client from '../../api/client'
import { hostelLabel } from '../../utils'

export default function StudentComplaintFormPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [description, setDescription] = useState('')
  const [roomNumber, setRoomNumber] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await client.post('/student/complaints/', { description, room_number: roomNumber })
      navigate('/student/complaints/history')
    } catch (err) {
      setError(err.response?.data?.description?.[0] || err.response?.data?.detail || 'Failed to submit complaint.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <h1 className='page-title'>New Complaint</h1>

      <div className='panel'>
        <div className='panel-header'>Student Information</div>
        <div className='panel-body'>
          <div className='form-row'><label>Full Name</label><div className='readonly-box'>{user?.display_name || '-'}</div></div>
          <div className='form-row'><label>Phone Number</label><div className='readonly-box'>{user?.phone_number || '-'}</div></div>
          <div className='form-row'><label>Hostel</label><div className='readonly-box'>{hostelLabel(user?.hostel)}</div></div>
        </div>
      </div>

      <div className='panel'>
        <div className='panel-header'>Complaint Form</div>
        <div className='panel-body'>
          <form onSubmit={submit}>
            {error && <div className='form-errors'>{error}</div>}
            <div className='form-row'>
              <label>Room Number</label>
              <input value={roomNumber} onChange={(e) => setRoomNumber(e.target.value)} required />
            </div>
            <div className='form-row'>
              <label>Complaint Description</label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} required />
            </div>
            <div className='top-actions'>
              <button className='action-btn' type='submit' disabled={busy}>{busy ? 'Submitting...' : 'Submit Complaint'}</button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
