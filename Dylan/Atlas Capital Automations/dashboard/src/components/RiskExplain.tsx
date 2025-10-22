import React, { useState } from 'react'
import axios from 'axios'

/**
 * RiskExplain component
 *
 * Allows users to compute the linear contributions of each feature to the risk
 * score.  The form collects the same inputs as the single risk score form and
 * submits them to the `/v1/risk/explain` endpoint.  The response includes
 * per‑feature contributions, the model intercept, the linear score, and the
 * resulting probability.  These are rendered in a table for easy reading.
 */
const RiskExplain: React.FC = () => {
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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
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
        `${API_BASE}/v1/risk/explain`,
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
      <h2 className="text-2xl font-semibold mb-4">Explain Risk Score</h2>
      <p className="text-sm text-gray-700 mb-4">
        Understand how each feature contributes to the risk score.  Provide the
        same inputs as for scoring to see the linear contributions, model
        intercept, linear score and resulting probability.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="dti_e">
            Debt to Income (0–5)
          </label>
          <input
            id="dti_e"
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
          <label className="block text-sm font-medium mb-1" htmlFor="cu_e">
            Credit Utilization (0–1)
          </label>
          <input
            id="cu_e"
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
          <label className="block text-sm font-medium mb-1" htmlFor="age_e">
            Age (18–100)
          </label>
          <input
            id="age_e"
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
          <label className="block text-sm font-medium mb-1" htmlFor="sr_e">
            Savings Ratio (0–5)
          </label>
          <input
            id="sr_e"
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
          <label className="block text-sm font-medium mb-1" htmlFor="delinq_e">
            Has Delinquency (0 or 1)
          </label>
          <select
            id="delinq_e"
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
          {loading ? 'Explaining...' : 'Explain'}
        </button>
      </form>
      {error && <p className="text-red-600 mt-4">Error: {error}</p>}
      {result && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-2">Contributions</h3>
          <table className="min-w-full divide-y divide-gray-200 text-sm mb-4">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Feature</th>
                <th className="px-4 py-2 text-left font-medium">Contribution</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(result.contributions).map(([feat, val]) => (
                <tr key={feat}>
                  <td className="px-4 py-2 font-medium whitespace-nowrap">{feat}</td>
                  <td className="px-4 py-2 whitespace-nowrap">{val.toFixed(6)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="text-sm space-y-1">
            <p><span className="font-medium">Intercept:</span> {result.intercept}</p>
            <p><span className="font-medium">Linear score:</span> {result.linear_score}</p>
            <p><span className="font-medium">Probability:</span> {result.probability}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default RiskExplain