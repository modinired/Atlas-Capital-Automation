import React, { useState } from 'react'
import axios from 'axios'

/**
 * RiskBatch component
 *
 * This view allows users to score multiple applicants in a single request.  Users
 * provide a JSON array of objects adhering to the RiskInput schema.  Upon
 * submission, the component sends the array to `/v1/risk/score/batch` and
 * renders the returned list of results.  Results are displayed in a table
 * pairing each input with its corresponding probability and label.  Invalid
 * JSON or server errors are surfaced to the user.
 *
 * The API base URL defaults to `http://localhost:8000` but can be overridden
 * via `VITE_API_URL`.  If API key authentication is enabled, set
 * `VITE_API_KEY` at build time.
 */
const RiskBatch: React.FC = () => {
  const [inputText, setInputText] = useState<string>(JSON.stringify([
    {
      debt_to_income: 0.4,
      credit_utilization: 0.3,
      age_years: 42,
      savings_ratio: 0.2,
      has_delinquency: 0,
    },
    {
      debt_to_income: 0.6,
      credit_utilization: 0.8,
      age_years: 35,
      savings_ratio: 0.1,
      has_delinquency: 1,
    },
  ], null, 2))
  const [results, setResults] = useState<any[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const API_KEY = import.meta.env.VITE_API_KEY

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setResults(null)
    let payloads: any[]
    try {
      payloads = JSON.parse(inputText)
      if (!Array.isArray(payloads)) {
        throw new Error('Input must be a JSON array')
      }
    } catch (e: any) {
      setError('Invalid JSON: ' + e.message)
      return
    }
    setLoading(true)
    try {
      const { data } = await axios.post(
        `${API_BASE}/v1/risk/score/batch`,
        payloads,
        {
          headers: {
            'Content-Type': 'application/json',
            ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
          },
        },
      )
      setResults(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Batch Risk Scoring</h2>
      <p className="text-sm text-gray-700 mb-4">
        Provide a JSON array of applicants to score them in a single API call.
        Each object must contain the keys: debt_to_income, credit_utilization,
        age_years, savings_ratio and has_delinquency.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="batchInputs">
            Inputs (JSON array)
          </label>
          <textarea
            id="batchInputs"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            rows={10}
            className="w-full border border-gray-300 rounded-md p-2 font-mono text-sm"
          ></textarea>
        </div>
        <button
          type="submit"
          className="bg-secondary text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Scoring...' : 'Score'}
        </button>
      </form>
      {error && <p className="text-red-600 mt-4">Error: {error}</p>}
      {results && (
        <div className="mt-6 overflow-x-auto">
          <h3 className="text-xl font-semibold mb-2">Results</h3>
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 font-medium text-left">Applicant</th>
                <th className="px-4 py-2 font-medium text-left">Probability</th>
                <th className="px-4 py-2 font-medium text-left">Label</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((res: any, idx: number) => (
                <tr key={idx}>
                  <td className="px-4 py-2 whitespace-nowrap">
                    <pre className="text-xs bg-gray-50 p-2 rounded-md">
                      {JSON.stringify(res.audit, null, 2)}
                    </pre>
                  </td>
                  <td className="px-4 py-2">{res.probability}</td>
                  <td className="px-4 py-2">{res.label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default RiskBatch