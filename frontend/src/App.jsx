import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import AppLayout from './layouts/AppLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import AdminStudentsPage from './pages/admin/AdminStudentsPage'
import ClerkStudentsPage from './pages/clerk/ClerkStudentsPage'
import AdminClerksPage from './pages/admin/AdminClerksPage'
import AdminDepartmentsPage from './pages/admin/AdminDepartmentsPage'
import AdminComplaintsPage from './pages/admin/AdminComplaintsPage'
import ClerkComplaintsPage from './pages/clerk/ClerkComplaintsPage'
import StudentComplaintsPage from './pages/student/StudentComplaintsPage'
import AdminAcademicsPage from './pages/admin/AdminAcademicsPage'
import ClerkAcademicsPage from './pages/clerk/ClerkAcademicsPage'
import StudentAcademicsPage from './pages/student/StudentAcademicsPage'
import StudentFeedbackPage from './pages/student/StudentFeedbackPage'
import AdminFeedbackPage from './pages/admin/AdminFeedbackPage'
import AdminSettingsPage from './pages/admin/AdminSettingsPage'
import AdminLockedAccountsPage from './pages/admin/AdminLockedAccountsPage'

function Home(){ const { user } = useAuth(); if(!user) return <Navigate to='/login' replace />; return <AppLayout><DashboardPage /></AppLayout> }

function withLayout(node){ return <AppLayout>{node}</AppLayout> }

export default function App(){
  return <Routes>
    <Route path='/login' element={<LoginPage />} />
    <Route path='/' element={<ProtectedRoute>{<Home />}</ProtectedRoute>} />
    <Route path='/admin/students' element={<ProtectedRoute roles={['admin']}>{withLayout(<AdminStudentsPage />)}</ProtectedRoute>} />
    <Route path='/clerk/students' element={<ProtectedRoute roles={['clerk']}>{withLayout(<ClerkStudentsPage />)}</ProtectedRoute>} />
    <Route path='/admin/clerks' element={<ProtectedRoute roles={['admin']}>{withLayout(<AdminClerksPage />)}</ProtectedRoute>} />
    <Route path='/admin/departments' element={<ProtectedRoute roles={['admin']}>{withLayout(<AdminDepartmentsPage />)}</ProtectedRoute>} />
    <Route path='/admin/complaints' element={<ProtectedRoute roles={['admin']}>{withLayout(<AdminComplaintsPage />)}</ProtectedRoute>} />
    <Route path='/clerk/complaints' element={<ProtectedRoute roles={['clerk']}>{withLayout(<ClerkComplaintsPage />)}</ProtectedRoute>} />
    <Route path='/student/complaints' element={<ProtectedRoute roles={['student']}>{withLayout(<StudentComplaintsPage />)}</ProtectedRoute>} />
    <Route path='/admin/academics' element={<ProtectedRoute roles={['admin']}>{withLayout(<AdminAcademicsPage />)}</ProtectedRoute>} />
    <Route path='/clerk/academics' element={<ProtectedRoute roles={['clerk']}>{withLayout(<ClerkAcademicsPage />)}</ProtectedRoute>} />
    <Route path='/student/academics' element={<ProtectedRoute roles={['student']}>{withLayout(<StudentAcademicsPage />)}</ProtectedRoute>} />
    <Route path='/student/feedback' element={<ProtectedRoute roles={['student']}>{withLayout(<StudentFeedbackPage />)}</ProtectedRoute>} />
    <Route path='/admin/feedback' element={<ProtectedRoute roles={['admin']}>{withLayout(<AdminFeedbackPage />)}</ProtectedRoute>} />
    <Route path='/admin/settings' element={<ProtectedRoute roles={['admin']}>{withLayout(<AdminSettingsPage />)}</ProtectedRoute>} />
    <Route path='/admin/locked' element={<ProtectedRoute roles={['admin']}>{withLayout(<AdminLockedAccountsPage />)}</ProtectedRoute>} />
  </Routes>
}
