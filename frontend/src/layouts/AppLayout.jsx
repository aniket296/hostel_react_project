import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
export default function AppLayout({ children }) { return <div className='app-shell'><Navbar /><div className='app-body'><Sidebar /><main className='content'>{children}</main></div></div> }
