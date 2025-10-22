import React, { useState } from 'react'
import axios from 'axios'

interface ExecResult {
  stdout: string
  stderr: string
  returncode: number
  timed_out: boolean
}

const CodeExec: React.FC = () => {
  const [language, setLanguage] = useState<string>('python')
  const [code, setCode] = useState<string>('print("Hello, world!")')
  const [args, setArgs] = useState<string>('')
  const [timeout, setTimeoutVal] = useState<number>(5)
  const [result, setResult] = useState<ExecResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const API_BASE = import.meta.env.VITE_MCP_URL || 'http://localhost:9000/mcp'

  const handleRun = async () => {
    setError(null)
    setResult(null)
    setLoading(true)
    const body: any = { language, code, timeout }
    const argList = args.trim().split(/\s+/).filter(Boolean)
    if (argList.length > 0) body.args = argList
    try {
      const { data } = await axios.post(`${API_BASE}/codeexec/execute`, body, {
        headers: { 'Content-Type': 'application/json' },
      })
      setResult(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Execute Code</h2>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1" htmlFor="language">Language</label>
        <select
          id="language"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full border border-gray-300 rounded-md p-2"
        >
          <option value="python">Python</option>
        </select>
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1" htmlFor="code">Code</label>
        <textarea
          id="code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={6}
          className="w-full border border-gray-300 rounded-md p-2 font-mono text-sm"
        ></textarea>
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1" htmlFor="args">Arguments (space separated)</label>
        <input
          id="args"
          type="text"
          value={args}
          onChange={(e) => setArgs(e.target.value)}
          className="w-full border border-gray-300 rounded-md p-2"
        />
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1" htmlFor="timeout">Timeout (seconds)</label>
        <input
          id="timeout"
          type="number"
          min={1}
          value={timeout}
          onChange={(e) => setTimeoutVal(Number(e.target.value))}
          className="w-full border border-gray-300 rounded-md p-2"
        />
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
          <h3 className="text-xl font-semibold mb-2">Output</h3>
          <div className="bg-gray-100 p-4 rounded-md text-sm">
            <p><span className="font-medium">stdout:</span></p>
            <pre className="whitespace-pre-wrap break-words mb-2">{result.stdout || '<empty>'}</pre>
            <p><span className="font-medium">stderr:</span></p>
            <pre className="whitespace-pre-wrap break-words mb-2 text-red-600">{result.stderr || '<empty>'}</pre>
            <p><span className="font-medium">return code:</span> {result.returncode}</p>
            <p><span className="font-medium">timed out:</span> {result.timed_out ? 'true' : 'false'}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default CodeExec