import React, { useState } from 'react'
import {
  Menu,
  X,
  Calculator,
  List,
  Info,
  Workflow,
  Code2,
  Activity,
} from 'lucide-react'
import RiskScore from './components/RiskScore'
import RiskBatch from './components/RiskBatch'
import RiskExplain from './components/RiskExplain'
import CardRunner from './components/CardRunner'
import CodeExec from './components/CodeExec'
import Metrics from './components/Metrics'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [currentTab, setCurrentTab] = useState<
    'score' | 'batch' | 'explain' | 'cards' | 'code' | 'metrics'
  >('score')

  // Define navigation entries with icons
  const navItems: Array<{
    key: typeof currentTab
    label: string
    icon: React.ReactNode
  }> = [
    {
      key: 'score',
      label: 'Single Score',
      icon: <Calculator size={16} className="mr-3 shrink-0" />,
    },
    {
      key: 'batch',
      label: 'Batch Score',
      icon: <List size={16} className="mr-3 shrink-0" />,
    },
    {
      key: 'explain',
      label: 'Explain',
      icon: <Info size={16} className="mr-3 shrink-0" />,
    },
    {
      key: 'cards',
      label: 'Workflows',
      icon: <Workflow size={16} className="mr-3 shrink-0" />,
    },
    {
      key: 'code',
      label: 'Code Runner',
      icon: <Code2 size={16} className="mr-3 shrink-0" />,
    },
    {
      key: 'metrics',
      label: 'Metrics',
      icon: <Activity size={16} className="mr-3 shrink-0" />,
    },
  ]

  const renderContent = () => {
    switch (currentTab) {
      case 'score':
        return <RiskScore />
      case 'batch':
        return <RiskBatch />
      case 'explain':
        return <RiskExplain />
      case 'cards':
        return <CardRunner />
      case 'code':
        return <CodeExec />
      case 'metrics':
        return <Metrics />
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside
        className={
          `fixed inset-y-0 left-0 z-30 w-64 transform bg-primary text-white ` +
          `shadow-lg transition-transform duration-300 md:translate-x-0 ` +
          `${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`
        }
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-primary-700">
          <span className="text-lg font-semibold">Menu</span>
          <button
            className="md:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>
        <nav className="mt-2 flex flex-col space-y-1">
          {navItems.map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => {
                setCurrentTab(key)
                setSidebarOpen(false)
              }}
              className={`flex items-center px-4 py-2 text-sm font-medium transition-colors ` +
                `${currentTab === key ? 'bg-secondary text-white' : 'text-white hover:bg-secondary'}`}
            >
              {icon}
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>
      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black opacity-50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}
      {/* Main content area */}
      <div className="flex-1 flex flex-col md:ml-64 min-h-screen">
        <header className="bg-primary text-white flex items-center justify-between px-4 py-3 shadow-md">
          <button
            className="md:hidden"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={24} />
          </button>
          <h1 className="text-lg font-semibold">Terry Delmonaco AI Dashboard</h1>
        </header>
        <main className="flex-1 p-4 overflow-y-auto">
          {renderContent()}
        </main>
        <footer className="bg-gray-100 text-center text-sm text-gray-500 p-2">
          © {new Date().getFullYear()} Terry Delmonaco AI Platform
        </footer>
      </div>
    </div>
  )
}