import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { Dashboard } from './pages/Dashboard'
import { Recettes } from './pages/Recettes'
import { Depenses } from './pages/Depenses'
import { Investissements } from './pages/Investissements'
import { Dette } from './pages/Dette'
import { CommuneProvider, useSelectedCommune } from './contexts/CommuneContext'
import { useSync } from './hooks/useCommune'

function AppLayout() {
  const { insee } = useSelectedCommune()
  const sync = useSync(insee)

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar
        onSync={() => sync.mutate()}
        isSyncing={sync.isPending}
      />
      <main className="flex-1 p-8 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/recettes" element={<Recettes />} />
          <Route path="/depenses" element={<Depenses />} />
          <Route path="/investissements" element={<Investissements />} />
          <Route path="/dette" element={<Dette />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <CommuneProvider>
        <AppLayout />
      </CommuneProvider>
    </BrowserRouter>
  )
}

export default App
