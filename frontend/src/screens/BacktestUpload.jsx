import { useState, useRef } from 'react'
import axios from 'axios'
import { UploadCloud, AlertCircle, CheckCircle, FileText } from 'lucide-react'
import { API_URL } from '../config'

const MAX_FILE_BYTES = 5 * 1024 * 1024

function FormatBadge({ format }) {
  const isDetailed = format === 'detailed'
  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
        isDetailed ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
      }`}
    >
      {isDetailed ? 'Detailed trade log' : 'Summary report'}
    </span>
  )
}

function DetailedResults({ trades, warnings, notices, pnl }) {
  const safeWarnings = warnings ?? []
  const safeNotices = notices ?? []
  return (
    <div className="space-y-4">
      {safeWarnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
          <p className="font-medium text-yellow-800 mb-1">Warnings</p>
          <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
            {safeWarnings.map((w, i) => (
              <li key={i}>{w.message}</li>
            ))}
          </ul>
        </div>
      )}

      {safeNotices.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3">
          <p className="font-medium text-blue-800 mb-1">Open Positions</p>
          <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
            {safeNotices.map((n, i) => (
              <li key={i}>{n.message}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded p-3">
          <p className="text-xs text-gray-500">Total P&amp;L</p>
          <p className={`text-xl font-bold ${pnl.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {pnl.total_pnl >= 0 ? '+' : ''}{pnl.total_pnl.toFixed(2)}
          </p>
        </div>
        <div className="bg-gray-50 rounded p-3">
          <p className="text-xs text-gray-500">Total Return</p>
          <p className={`text-xl font-bold ${pnl.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {pnl.total_return_pct >= 0 ? '+' : ''}{pnl.total_return_pct.toFixed(2)}%
          </p>
        </div>
      </div>

      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">
          Trades ({trades.length})
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100 text-left text-xs text-gray-600">
                <th className="p-2">Date</th>
                <th className="p-2">Symbol</th>
                <th className="p-2">Action</th>
                <th className="p-2">Price</th>
                <th className="p-2">Shares</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="p-2">{t.date}</td>
                  <td className="p-2 font-medium">{t.symbol}</td>
                  <td className={`p-2 font-medium ${t.action === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                    {t.action}
                  </td>
                  <td className="p-2">{t.price}</td>
                  <td className="p-2">{t.shares}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function SummaryResults({ summary }) {
  const returnPct = (((summary.final_balance - summary.initial_capital) / summary.initial_capital) * 100).toFixed(2)
  const isPositive = summary.final_balance >= summary.initial_capital

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-gray-50 rounded p-3">
        <p className="text-xs text-gray-500">Initial Capital</p>
        <p className="text-lg font-bold">${summary.initial_capital.toLocaleString()}</p>
      </div>
      <div className="bg-gray-50 rounded p-3">
        <p className="text-xs text-gray-500">Final Balance</p>
        <p className={`text-lg font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          ${summary.final_balance.toLocaleString()}
        </p>
      </div>
      <div className="bg-gray-50 rounded p-3">
        <p className="text-xs text-gray-500">Return</p>
        <p className={`text-lg font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? '+' : ''}{returnPct}%
        </p>
      </div>
      <div className="bg-gray-50 rounded p-3">
        <p className="text-xs text-gray-500">Win Rate</p>
        <p className="text-lg font-bold">{(summary.win_rate * 100).toFixed(1)}%</p>
      </div>
      <div className="bg-gray-50 rounded p-3">
        <p className="text-xs text-gray-500">Trades</p>
        <p className="text-lg font-bold">{summary.num_trades}</p>
      </div>
      <div className="bg-gray-50 rounded p-3">
        <p className="text-xs text-gray-500">Period</p>
        <p className="text-sm font-medium">{summary.start_date} → {summary.end_date}</p>
      </div>
    </div>
  )
}

export default function BacktestUpload() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const inputRef = useRef(null)

  function handleFileChange(e) {
    const selected = e.target.files[0]
    setResult(null)
    setError('')

    if (!selected) {
      setFile(null)
      return
    }

    const isCSV = selected.name.endsWith('.csv') || selected.type === 'text/csv'
    if (!isCSV) {
      setError('Only .csv files are supported.')
      setFile(null)
      return
    }

    if (selected.size > MAX_FILE_BYTES) {
      setError('File exceeds the 5 MB limit.')
      setFile(null)
      return
    }

    setFile(selected)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const { data } = await axios.post(`${API_URL}/analyze-backtest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(data)
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to process CSV.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setFile(null)
    setResult(null)
    setError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-1">Backtest CSV Upload</h2>
      <p className="text-sm text-gray-500 mb-6">
        Upload a detailed trade log or a summary report — the format is detected automatically.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="flex flex-col items-center justify-center w-full h-36 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors">
          <UploadCloud className="w-8 h-8 text-gray-400 mb-2" />
          <span className="text-sm text-gray-600">
            {file ? file.name : 'Click to select a CSV file'}
          </span>
          <span className="text-xs text-gray-400 mt-1">Max 5 MB</span>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={!file || loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded transition-colors"
          >
            {loading ? 'Analysing...' : 'Analyse'}
          </button>
          {(file || result || error) && (
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 border border-gray-300 rounded text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Reset
            </button>
          )}
        </div>
      </form>

      {error && (
        <div className="mt-4 flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-sm font-medium text-gray-700">Format detected:</span>
            <FormatBadge format={result.format} />
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-4 text-gray-600">
              <FileText className="w-4 h-4" />
              <span className="text-sm font-medium">
                {result.format === 'detailed' ? 'Trade Log Results' : 'Summary Metrics'}
              </span>
            </div>

            {result.format === 'detailed' ? (
              <DetailedResults
                trades={result.trades}
                warnings={result.warnings}
                notices={result.notices}
                pnl={result.pnl}
              />
            ) : (
              <SummaryResults summary={result.summary} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}
