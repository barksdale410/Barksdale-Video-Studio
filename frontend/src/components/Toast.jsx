import React, { useState, useEffect } from 'react'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle
}

const colors = {
  success: 'bg-green-500/20 border-green-500 text-green-400',
  error: 'bg-red-500/20 border-red-500 text-red-400',
  info: 'bg-blue-500/20 border-blue-500 text-blue-400',
  warning: 'bg-yellow-500/20 border-yellow-500 text-yellow-400'
}

export default function Toast({ message, type = 'info', onClose, duration = 5000 }) {
  const [visible, setVisible] = useState(true)
  const Icon = icons[type]

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setVisible(false)
        setTimeout(onClose, 300)
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [duration, onClose])

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 flex items-center space-x-3 px-4 py-3 rounded-xl border ${colors[type]} transition-all duration-300 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
      }`}
    >
      <Icon className="w-5 h-5 flex-shrink-0" />
      <p className="text-sm font-medium">{message}</p>
      <button onClick={() => { setVisible(false); setTimeout(onClose, 300) }} className="ml-2 hover:opacity-70">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

// Toast container for managing multiple toasts
export function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  )
}
