import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Upload from './routes/Upload'
import Reconcile from './routes/Reconcile'
import Exceptions from './routes/Exceptions'
import Span from './routes/Span'
import Audit from './routes/Audit'
import OTC from './routes/OTC'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Upload />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/reconcile" element={<Reconcile />} />
          <Route path="/reconcile/:runId" element={<Reconcile />} />
          <Route path="/exceptions" element={<Exceptions />} />
          <Route path="/span" element={<Span />} />
          <Route path="/otc" element={<OTC />} />
          <Route path="/audit" element={<Audit />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
