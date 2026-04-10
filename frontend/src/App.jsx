import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Shell from './components/Shell'
import { useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import DashboardRouterPage from './pages/DashboardRouterPage'
import AdminHostelDashboardPage from './pages/admin/AdminHostelDashboardPage'
import ComplaintStatusPage from './pages/shared/ComplaintStatusPage'
import ComplaintDetailPage from './pages/shared/ComplaintDetailPage'
import ComplaintHistoryPage from './pages/shared/ComplaintHistoryPage'
import StudentListPage from './pages/shared/StudentListPage'
import StudentFormPage from './pages/shared/StudentFormPage'
import StudentImportPage from './pages/shared/StudentImportPage'
import ClerkListPage from './pages/admin/ClerkListPage'
import ClerkFormPage from './pages/admin/ClerkFormPage'
import DepartmentListPage from './pages/admin/DepartmentListPage'
import DepartmentFormPage from './pages/admin/DepartmentFormPage'
import AcademicListPage from './pages/shared/AcademicListPage'
import AcademicUploadPage from './pages/shared/AcademicUploadPage'
import FeedbackFormListPage from './pages/admin/FeedbackFormListPage'
import FeedbackAnalysisListPage from './pages/admin/FeedbackAnalysisListPage'
import FeedbackAnalysisViewPage from './pages/admin/FeedbackAnalysisViewPage'
import LockedAccountsPage from './pages/admin/LockedAccountsPage'
import SystemSettingsPage from './pages/admin/SystemSettingsPage'
import BackupListPage from './pages/admin/BackupListPage'
import StudentComplaintHomePage from './pages/student/StudentComplaintHomePage'
import StudentComplaintListPage from './pages/student/StudentComplaintListPage'
import StudentComplaintFormPage from './pages/student/StudentComplaintFormPage'
import StudentComplaintDetailPage from './pages/student/StudentComplaintDetailPage'
import StudentAcademicsHomePage from './pages/student/StudentAcademicsHomePage'
import StudentAcademicsListPage from './pages/student/StudentAcademicsListPage'
import StudentAcademicsUploadPage from './pages/student/StudentAcademicsUploadPage'
import StudentFeedbackPage from './pages/student/StudentFeedbackPage'

function HomePage() {
  const { user } = useAuth()
  if (!user) return <Navigate to='/login' replace />
  return <Shell><DashboardRouterPage /></Shell>
}

function withShell(element) {
  return <Shell>{element}</Shell>
}

export default function App() {
  return (
    <Routes>
      <Route path='/login' element={<LoginPage />} />
      <Route path='/' element={<ProtectedRoute><HomePage /></ProtectedRoute>} />

      <Route path='/student/complaints' element={<ProtectedRoute roles={['student']}>{withShell(<StudentComplaintHomePage />)}</ProtectedRoute>} />
      <Route path='/student/complaints/history' element={<ProtectedRoute roles={['student']}>{withShell(<StudentComplaintListPage />)}</ProtectedRoute>} />
      <Route path='/student/complaints/new' element={<ProtectedRoute roles={['student']}>{withShell(<StudentComplaintFormPage />)}</ProtectedRoute>} />
      <Route path='/student/complaints/:id' element={<ProtectedRoute roles={['student']}>{withShell(<StudentComplaintDetailPage />)}</ProtectedRoute>} />
      <Route path='/student/academics' element={<ProtectedRoute roles={['student']}>{withShell(<StudentAcademicsHomePage />)}</ProtectedRoute>} />
      <Route path='/student/academics/download' element={<ProtectedRoute roles={['student']}>{withShell(<StudentAcademicsListPage />)}</ProtectedRoute>} />
      <Route path='/student/academics/upload' element={<ProtectedRoute roles={['student']}>{withShell(<StudentAcademicsUploadPage />)}</ProtectedRoute>} />
      <Route path='/student/feedback' element={<ProtectedRoute roles={['student']}>{withShell(<StudentFeedbackPage />)}</ProtectedRoute>} />

      <Route path='/clerk/students' element={<ProtectedRoute roles={['clerk']}>{withShell(<StudentListPage role='clerk' />)}</ProtectedRoute>} />
      <Route path='/clerk/students/add' element={<ProtectedRoute roles={['clerk']}>{withShell(<StudentFormPage role='clerk' />)}</ProtectedRoute>} />
      <Route path='/clerk/students/import' element={<ProtectedRoute roles={['clerk']}>{withShell(<StudentImportPage role='clerk' />)}</ProtectedRoute>} />
      <Route path='/clerk/students/:id/edit' element={<ProtectedRoute roles={['clerk']}>{withShell(<StudentFormPage role='clerk' />)}</ProtectedRoute>} />
      <Route path='/clerk/academics' element={<ProtectedRoute roles={['clerk']}>{withShell(<AcademicListPage role='clerk' />)}</ProtectedRoute>} />
      <Route path='/clerk/academics/upload' element={<ProtectedRoute roles={['clerk']}>{withShell(<AcademicUploadPage role='clerk' />)}</ProtectedRoute>} />
      <Route path='/clerk/complaints/:status' element={<ProtectedRoute roles={['clerk']}>{withShell(<ComplaintStatusPage role='clerk' />)}</ProtectedRoute>} />
      <Route path='/clerk/complaints/:id' element={<ProtectedRoute roles={['clerk']}>{withShell(<ComplaintDetailPage />)}</ProtectedRoute>} />
      <Route path='/clerk/history' element={<ProtectedRoute roles={['clerk']}>{withShell(<ComplaintHistoryPage role='clerk' />)}</ProtectedRoute>} />

      <Route path='/admin/hostels/:hostelType' element={<ProtectedRoute roles={['admin']}>{withShell(<AdminHostelDashboardPage />)}</ProtectedRoute>} />
      <Route path='/admin/students' element={<ProtectedRoute roles={['admin']}>{withShell(<StudentListPage role='admin' />)}</ProtectedRoute>} />
      <Route path='/admin/students/add' element={<ProtectedRoute roles={['admin']}>{withShell(<StudentFormPage role='admin' />)}</ProtectedRoute>} />
      <Route path='/admin/students/import' element={<ProtectedRoute roles={['admin']}>{withShell(<StudentImportPage role='admin' />)}</ProtectedRoute>} />
      <Route path='/admin/students/:id/edit' element={<ProtectedRoute roles={['admin']}>{withShell(<StudentFormPage role='admin' />)}</ProtectedRoute>} />
      <Route path='/admin/clerks' element={<ProtectedRoute roles={['admin']}>{withShell(<ClerkListPage />)}</ProtectedRoute>} />
      <Route path='/admin/clerks/add' element={<ProtectedRoute roles={['admin']}>{withShell(<ClerkFormPage />)}</ProtectedRoute>} />
      <Route path='/admin/clerks/:id/edit' element={<ProtectedRoute roles={['admin']}>{withShell(<ClerkFormPage />)}</ProtectedRoute>} />
      <Route path='/admin/departments' element={<ProtectedRoute roles={['admin']}>{withShell(<DepartmentListPage />)}</ProtectedRoute>} />
      <Route path='/admin/departments/add' element={<ProtectedRoute roles={['admin']}>{withShell(<DepartmentFormPage />)}</ProtectedRoute>} />
      <Route path='/admin/departments/:id/edit' element={<ProtectedRoute roles={['admin']}>{withShell(<DepartmentFormPage />)}</ProtectedRoute>} />
      <Route path='/admin/academics' element={<ProtectedRoute roles={['admin']}>{withShell(<AcademicListPage role='admin' />)}</ProtectedRoute>} />
      <Route path='/admin/academics/upload' element={<ProtectedRoute roles={['admin']}>{withShell(<AcademicUploadPage role='admin' />)}</ProtectedRoute>} />
      <Route path='/admin/complaints/:status' element={<ProtectedRoute roles={['admin']}>{withShell(<ComplaintStatusPage role='admin' />)}</ProtectedRoute>} />
      <Route path='/admin/complaints/:id' element={<ProtectedRoute roles={['admin']}>{withShell(<ComplaintDetailPage />)}</ProtectedRoute>} />
      <Route path='/admin/history' element={<ProtectedRoute roles={['admin']}>{withShell(<ComplaintHistoryPage role='admin' />)}</ProtectedRoute>} />
      <Route path='/admin/feedback/forms' element={<ProtectedRoute roles={['admin']}>{withShell(<FeedbackFormListPage />)}</ProtectedRoute>} />
      <Route path='/admin/feedback/analysis' element={<ProtectedRoute roles={['admin']}>{withShell(<FeedbackAnalysisListPage />)}</ProtectedRoute>} />
      <Route path='/admin/feedback/analysis/:id' element={<ProtectedRoute roles={['admin']}>{withShell(<FeedbackAnalysisViewPage />)}</ProtectedRoute>} />
      <Route path='/admin/locked-accounts' element={<ProtectedRoute roles={['admin']}>{withShell(<LockedAccountsPage />)}</ProtectedRoute>} />
      <Route path='/admin/settings' element={<ProtectedRoute roles={['admin']}>{withShell(<SystemSettingsPage />)}</ProtectedRoute>} />
      <Route path='/admin/backups' element={<ProtectedRoute roles={['admin']}>{withShell(<BackupListPage />)}</ProtectedRoute>} />

      <Route path='*' element={<Navigate to='/' replace />} />
    </Routes>
  )
}
