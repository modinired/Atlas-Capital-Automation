import React, { useState } from 'react'
import axios from 'axios'

interface RunResult {
  dossier?: any
  [key: string]: any
}

const CardRunner: React.FC = () => {
  const [card, setCard] = useState<string>('QBR')
  const [description, setDescription] = useState<string>('')
  const [inputText, setInputText] = useState<string>(JSON.stringify({
    accounts: ["ACME"],
    time_window: "90d",
    kpi_definitions: {},
    file_locations: {},
  }, null, 2))
  const [result, setResult] = useState<RunResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const API_BASE = import.meta.env.VITE_MCP_URL || 'http://localhost:9000/mcp'

  const handleRun = async () => {
    setError(null)
    setResult(null)
    let inputs
    try {
      inputs = JSON.parse(inputText)
    } catch (e: any) {
      setError('Invalid JSON: ' + e.message)
      return
    }
    setLoading(true)
    try {
      const { data } = await axios.post(`${API_BASE}/cards/${card}`, inputs, {
        headers: { 'Content-Type': 'application/json' },
      })
      setResult(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadTemplate = (selected: string) => {
    if (selected === 'QBR') {
      setInputText(JSON.stringify({
        accounts: ["ACME"],
        time_window: "90d",
        kpi_definitions: {},
        file_locations: {},
      }, null, 2))
    } else if (selected === 'IncidentPostmortem') {
      setInputText(JSON.stringify({
        incident_id: "INC12345",
        log_paths: ["/var/log/app.log"],
        time_range: "48h",
      }, null, 2))
    }
  }

  const handleSuggest = () => {
    const desc = description.toLowerCase()
    let suggested = card
    if (desc.includes('incident') || desc.includes('postmortem')) {
      suggested = 'IncidentPostmortem'
    } else if (desc.includes('quarter') || desc.includes('business') || desc.includes('review') || desc.includes('qbr')) {
      suggested = 'QBR'
    }
    setCard(suggested)
    loadTemplate(suggested)
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Run a Workflow</h2>
      <div className="mb-4">
        <label htmlFor="description" className="block text-sm font-medium mb-1">Task Description (optional)</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="Describe your task and click Suggest to auto‑select a workflow"
          className="w-full border border-gray-300 rounded-md p-2 text-sm"
        ></textarea>
        <button
          onClick={handleSuggest}
          className="mt-2 bg-accent text-black px-3 py-1 rounded-md hover:bg-yellow-400"
        >
          Suggest Workflow
        </button>
      </div>
      <div className="mb-4">
        <label htmlFor="card" className="block text-sm font-medium mb-1">Select Card</label>
        <select
          id="card"
          value={card}
          onChange={(e) => {
            const selected = e.target.value
            setCard(selected)
            loadTemplate(selected)
          }}
          className="w-full border border-gray-300 rounded-md p-2"
        >
          <option value="QBR">Quarterly Business Review</option>
          <option value="IncidentPostmortem">Incident Postmortem</option>
        </select>
      </div>
      <div className="mb-4">
        <label htmlFor="inputs" className="block text-sm font-medium mb-1">Inputs (JSON)</label>
        <textarea
          id="inputs"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          rows={8}
          className="w-full border border-gray-300 rounded-md p-2 font-mono text-sm"
        ></textarea>
      </div>
      <button
        onClick={handleRun}
        className="bg-secondary text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
        disabled={loading}
      >
        {loading ? 'Running...' : 'Run'}
      </button>
      {error && <p className="text-red-600 mt-4">Error: {error}</p>}
      {result && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-2">Result</h3>
          <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default CardRunner