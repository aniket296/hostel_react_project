import { Link } from 'react-router-dom'

export default function StudentAcademicsHomePage() {
  return (
    <div className='student-page-wrap'>
      <div className='page-header'>
        <h1 className='page-title'>Academics</h1>
      </div>

      <div className='panel academics-home-panel'>
        <div className='panel-header'>Academics Section</div>
        <div className='panel-body'>
          <p className='academics-home-text'>Select an option below:</p>
          <div className='top-actions academics-home-actions'>
            <Link to='/student/academics/download'>Download Academics</Link>
            <Link to='/student/academics/upload'>Upload Academics</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
