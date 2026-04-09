import { useEffect, useState } from 'react'
import client from '../../api/client'

export default function AdminFeedbackPage(){
  const [forms,setForms]=useState([])
  const [analysis,setAnalysis]=useState(null)
  const load=async()=>{ const res=await client.get('/feedback/forms/'); setForms(res.data) }
  useEffect(()=>{load()},[])
  const openAnalysis=async(id)=>{ const res=await client.get(`/feedback/analysis/${id}/`); setAnalysis(res.data) }

  return <div>
    <h1 className='page-title'>Feedback</h1>
    <div className='card table-card'>
      <table><thead><tr><th>Name</th><th>Hostel</th><th>Status</th><th>Action</th></tr></thead><tbody>{forms.map((f)=><tr key={f.id}><td>{f.name}</td><td>{f.hostel}</td><td>{f.status}</td><td><button className='btn small' onClick={()=>openAnalysis(f.id)}>Analysis</button></td></tr>)}</tbody></table>
    </div>
    {analysis && <div className='card'>
      <h2>Overall Analysis</h2>
      <pre className='json-box'>{JSON.stringify(analysis.overall_analysis ?? analysis, null, 2)}</pre>
      {analysis.student_feedback_details && <>
        <h2>Student Feedback Details</h2>
        <pre className='json-box'>{JSON.stringify(analysis.student_feedback_details, null, 2)}</pre>
      </>}
    </div>}
  </div>
}
