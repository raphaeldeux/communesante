import { createContext, useContext, useState, type ReactNode } from 'react'

const DEFAULT_INSEE = import.meta.env.VITE_COMMUNE_INSEE || '44194'
const STORAGE_KEY = 'communesante_insee'

interface CommuneContextType {
  insee: string
  setInsee: (insee: string) => void
}

const CommuneContext = createContext<CommuneContextType>({
  insee: DEFAULT_INSEE,
  setInsee: () => {},
})

export function CommuneProvider({ children }: { children: ReactNode }) {
  const [insee, setInseeState] = useState<string>(
    () => localStorage.getItem(STORAGE_KEY) || DEFAULT_INSEE
  )

  const setInsee = (code: string) => {
    localStorage.setItem(STORAGE_KEY, code)
    setInseeState(code)
  }

  return (
    <CommuneContext.Provider value={{ insee, setInsee }}>
      {children}
    </CommuneContext.Provider>
  )
}

export function useSelectedCommune() {
  return useContext(CommuneContext)
}
