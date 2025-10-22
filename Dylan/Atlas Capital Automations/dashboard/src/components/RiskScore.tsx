import React, { useState } from 'react'
import axios from 'axios'

/**
 * RiskScore component
 *
 * This form collects the five inputs required by the risk‑scoring API and
 * submits them to the backend for a prediction.  It uses a controlled
 * component pattern to keep form state in React and renders the result
 * in a friendly format.  If the request fails (e.g. due to authentication
 * errors or validation issues), the error message is displayed to the user.
 *
 * The API base URL defaults to `http://localhost:8000` but can be overridden
 * via a Vite environment variable `VITE_API_URL`.  When integrating into a
 * production environment, set this variable at build time to point at the
 * hosted API.  The API key, if enabled, should be provided via the
 * `X‑API‑Key` header — we read it from `VITE_API_KEY` for convenience.
 */
const RiskScore: React.FC = () => {
  const [inputs, setInputs] = useState({
    debt_to_income: 0.4,
    credit_utilization: 0.3,
    age_years: 42,
    savings_ratio: 0.2,
    has_delinquency: 0,
  })
  const [result, setResult] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const API_KEY = import.meta.env.VITE_API_KEY

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setInputs({
      ...inputs,
      [name]: name === 'has_delinquency' ? Number(value) : parseFloat(value),
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const { data } = await axios.post(
        `${API_BASE}/v1/risk/score`,
        inputs,
        {
          headers: {
            'Content-Type': 'application/json',
            ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
          },
        },
      )
      setResult(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Single Risk Score</h2>
      <p className="text-sm text-gray-700 mb-4">
        Enter the applicant&rsquo;s financial attributes to predict the risk score.  All
        fields are required.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="dti">
            Debt to Income (0–5)
          </label>
          <input
            id="dti"
            name="debt_to_income"
            type="number"
            min={0}
            max={5}
            step={0.01}
            value={inputs.debt_to_income}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md p-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="cu">
            Credit Utilization (0–1)
          </label>
          <input
            id="cu"
            name="credit_utilization"
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={inputs.credit_utilization}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md p-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="age">
            Age (18–100)
          </label>
          <input
            id="age"
            name="age_years"
            type="number"
            min={18}
            max={100}
            value={inputs.age_years}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md p-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="sr">
            Savings Ratio (0–5)
          </label>
          <input
            id="sr"
            name="savings_ratio"
            type="number"
            min={0}
            max={5}
            step={0.01}
            value={inputs.savings_ratio}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md p-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="delinq">
            Has Delinquency (0 or 1)
          </label>
          <select
            id="delinq"
            name="has_delinquency"
            value={inputs.has_delinquency}
            onChange={handleChange}
            className="w-full border border-gray-300 rounded-md p-2"
          >
            <option value={0}>No</option>
            <option value={1}>Yes</option>
          </select>
        </div>
        <button
          type="submit"
          className="bg-secondary text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Calculating...' : 'Calculate'}
        </button>
      </form>
      {error && <p className="text-red-600 mt-4">Error: {error}</p>}
      {result && (
        <div className="mt-6 bg-white shadow rounded-md p-4">
          <h3 className="text-xl font-semibold mb-2">Result</h3>
          <p className="text-sm mb-1">
            <span className="font-medium">Probability:</span> {result.probability}
          </p>
          <p className="text-sm mb-1">
            <span className="font-medium">Label:</span> {result.label}
          </p>
          <p className="text-sm mb-1">
            <span className="font-medium">Model Version:</span> {result.model_version}
          </p>
          <p className="text-sm font-medium mt-2 mb-1">Audit:</p>
          <pre className="bg-gray-50 p-2 rounded-md text-xs overflow-x-auto">
            {JSON.stringify(result.audit, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default RiskScore