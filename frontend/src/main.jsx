import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import './styles/auth.css'
import './styles/base.css'
import './styles/layout.css'
import './styles/dashboard.css'
import './styles/forms.css'
import './styles/tables.css'
import './styles/student_mobile.css'
import './styles/react-overrides.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
