import React, { useEffect, useState } from 'react'
import axios from 'axios'

/**
 * Metrics component
 *
 * Displays basic server health and Prometheus metrics from the risk scoring API.  When the
 * component mounts it fetches the `/health` endpoint to verify the server is
 * responding, then retrieves the raw Prometheus metrics from `/metrics` and
 * attempts to parse a few key statistics.  The parsed metrics are shown in
 * a table, while the raw metrics text is available in an expandable
 * accordion for transparency.  Errors during fetch operations are
 * surfaced to the user.
 */
const Metrics: React.FC = () => {
  const [health, setHealth] = useState<string>('unknown')
  const [parsed, setParsed] = useState<Array<{ metric: string; value: number }>>([])
  const [rawMetrics, setRawMetrics] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // Fetch health status
        const hres = await axios.get(`${API_BASE}/health`)
        setHealth(hres.data || hres.statusText)
        // Fetch metrics as plain text
        const mres = await axios.get(`${API_BASE}/metrics`, { responseType: 'text' })
        const text: string = mres.data
        setRawMetrics(text)
        // Parse a few key counters and histograms
        const metrics: Array<{ metric: string; value: number }> = []
        const lines = text.split('\n')
        lines.forEach((line) => {
          // skip comments
          if (line.startsWith('#') || line.trim() === '') return
          const [metricWithLabels, valueStr] = line.split(/\s+/)
          const value = parseFloat(valueStr)
          if (isNaN(value)) return
          if (metricWithLabels.startsWith('http_requests_total') || metricWithLabels.startsWith('http_request_duration_seconds_sum')) {
            metrics.push({ metric: metricWithLabels, value })
          }
        })
        setParsed(metrics)
      } catch (err: any) {
        setError(err.message)
      }
    }
    fetchMetrics()
  }, [API_BASE])

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Server Metrics & Health</h2>
      {error && <p className="text-red-600 mb-4">Error: {error}</p>}
      <div className="mb-4">
        <p className="text-sm text-gray-700">
          <span className="font-medium">Health:</span> {health}
        </p>
      </div>
      {parsed.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Key Metrics</h3>
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Metric</th>
                <th className="px-4 py-2 text-left font-medium">Value</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {parsed.map((m, idx) => (
                <tr key={idx}>
                  <td className="px-4 py-2 whitespace-nowrap font-mono text-xs">{m.metric}</td>
                  <td className="px-4 py-2 whitespace-nowrap">{m.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <details className="mb-4">
        <summary className="cursor-pointer font-medium text-blue-600">Raw Metrics</summary>
        <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto text-xs whitespace-pre-wrap">
{rawMetrics}
        </pre>
      </details>
    </div>
  )
}

export default Metrics