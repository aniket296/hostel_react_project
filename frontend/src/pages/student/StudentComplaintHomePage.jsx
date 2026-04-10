import { Link } from 'react-router-dom'

export default function StudentComplaintHomePage() {
  return (
    <div className='student-page-wrap'>
      <div className='page-header'>
        <h1 className='page-title'>Complaints</h1>
      </div>

      <div className='panel complaint-home-panel'>
        <div className='panel-header'>Complaint Section</div>
        <div className='panel-body'>
          <p className='complaint-home-text'>Select an option below:</p>
          <div className='top-actions complaint-home-actions'>
            <Link to='/student/complaints/history'>Complaint History</Link>
            <Link to='/student/complaints/new'>New Complaint</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
