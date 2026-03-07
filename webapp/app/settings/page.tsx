'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Settings,
  Server,
  Wifi,
  WifiOff,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Info,
  Database,
  Shield,
  Save,
  Key,
  Trash2,
  Eye,
  EyeOff
} from 'lucide-react'
import { ringApi } from '@/lib/api'
import { HealthStatus } from '@/types/ring'
import toast from 'react-hot-toast'

interface AuthCredentials {
  username: string
  password: string
}

export default function SettingsPage() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isTestingConnection, setIsTestingConnection] = useState(false)

  // Authentication form state
  const [credentials, setCredentials] = useState<AuthCredentials>({
    username: '',
    password: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [isSavingCredentials, setIsSavingCredentials] = useState(false)
  const [savedCredentials, setSavedCredentials] = useState<AuthCredentials | null>(null)

  useEffect(() => {
    loadHealthStatus()
    loadSavedCredentials()
  }, [])

  const loadSavedCredentials = () => {
    // In a real implementation, this would load from secure storage
    // For demo purposes, we'll check if there are any saved credentials
    const saved = localStorage.getItem('ring_credentials')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setSavedCredentials(parsed)
        setCredentials({ username: '', password: '' }) // Don't populate form with saved data for security
      } catch (error) {
        console.error('Failed to parse saved credentials:', error)
        localStorage.removeItem('ring_credentials')
      }
    }
  }

  const loadHealthStatus = async () => {
    try {
      setIsLoading(true)
      const health = await ringApi.getHealthStatus()
      setHealthStatus(health)
    } catch (error: any) {
      console.error('Failed to load health status:', error)
      setHealthStatus({
        success: false,
        message: error.message || 'Failed to check system health',
        health_status: {
          api_connected: false,
          devices_accessible: 0,
          authentication_valid: false,
          last_check: new Date().toISOString()
        }
      })
    } finally {
      setIsLoading(false)
    }
  }

  const testConnection = async () => {
    setIsTestingConnection(true)
    try {
      const isConnected = await ringApi.testConnection()
      if (isConnected) {
        toast.success('Connection to Ring MCP server successful!')
        await loadHealthStatus() // Refresh health status
      } else {
        toast.error('Failed to connect to Ring MCP server')
      }
    } catch (error: any) {
      toast.error(`Connection test failed: ${error.message}`)
    } finally {
      setIsTestingConnection(false)
    }
  }

  const handleSaveCredentials = async () => {
    if (!credentials.username || !credentials.password) {
      toast.error('Please enter both username and password')
      return
    }

    setIsSavingCredentials(true)
    try {
      // First, configure authentication on the server
      const authResponse = await ringApi.configureAuth(credentials)
      if (!authResponse.success) {
        throw new Error('Server authentication failed')
      }

      // Then save to localStorage for webapp state management
      localStorage.setItem('ring_credentials', JSON.stringify(credentials))

      setSavedCredentials(credentials)
      setCredentials({ username: '', password: '' })

      toast.success('Ring credentials configured and saved successfully!')

      // Refresh health status to show authenticated state
      await loadHealthStatus()

    } catch (error: any) {
      toast.error(`Failed to configure credentials: ${error.message}`)
    } finally {
      setIsSavingCredentials(false)
    }
  }

  const handleClearCredentials = () => {
    localStorage.removeItem('ring_credentials')
    setSavedCredentials(null)
    setCredentials({ username: '', password: '' })
    toast.success('Ring credentials cleared')
  }

  const handleInputChange = (field: keyof AuthCredentials, value: string) => {
    setCredentials(prev => ({ ...prev, [field]: value }))
  }

  const systemInfo = [
    {
      label: 'Webapp Version',
      value: '1.0.3',
      icon: <Info className="w-4 h-4 text-blue-500" />
    },
    {
      label: 'Server Port',
      value: '11110',
      icon: <Server className="w-4 h-4 text-green-500" />
    },
    {
      label: 'API Endpoint',
      value: '/api (proxied to localhost:8123)',
      icon: <Database className="w-4 h-4 text-purple-500" />
    },
    {
      label: 'Authentication',
      value: savedCredentials ? `Configured (${savedCredentials.username})` : 'Not configured',
      icon: savedCredentials ?
        <CheckCircle className="w-4 h-4 text-green-500" /> :
        <AlertTriangle className="w-4 h-4 text-yellow-500" />
    },
    {
      label: 'Technology',
      value: 'Next.js 14, TypeScript, Tailwind CSS',
      icon: <Settings className="w-4 h-4 text-gray-500" />
    }
  ]

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
            <p className="text-gray-600 mt-1">Configuration and preferences</p>
          </div>
        </div>

        <div className="animate-pulse space-y-6">
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex justify-between">
                  <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Configuration and system information</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={loadHealthStatus}
            className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh Status</span>
          </button>
        </div>
      </motion.div>

      {/* Authentication Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Key className="w-6 h-6 text-ring-500" />
            <h2 className="text-xl font-semibold text-gray-900">Ring Authentication</h2>
          </div>
          {savedCredentials && (
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm font-medium">Credentials Saved</span>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div className="text-sm text-yellow-800">
                <p className="font-medium">Security Notice</p>
                <p className="mt-1">
                  Credentials are stored locally in your browser for demo purposes only.
                  In production, credentials should be securely managed on the server-side.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ring Email/Username
              </label>
              <input
                type="email"
                value={credentials.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
                placeholder="your@email.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ring-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={credentials.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  placeholder="Enter your Ring password"
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ring-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="w-4 h-4 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={handleSaveCredentials}
              disabled={isSavingCredentials || !credentials.username || !credentials.password}
              className="flex items-center space-x-2 bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              <span>{isSavingCredentials ? 'Saving...' : 'Save Credentials'}</span>
            </button>

            {savedCredentials && (
              <button
                onClick={handleClearCredentials}
                className="flex items-center space-x-2 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                <span>Clear Credentials</span>
              </button>
            )}
          </div>

          {savedCredentials && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2 text-green-800">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">
                  Credentials saved for user: <strong>{savedCredentials.username}</strong>
                </span>
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* System Health */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Shield className="w-6 h-6 text-ring-500" />
            <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
          </div>
          <div className="flex items-center space-x-4">
            {healthStatus?.success ? (
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="w-5 h-5" />
                <span className="text-sm font-medium">System Healthy</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-red-600">
                <AlertTriangle className="w-5 h-5" />
                <span className="text-sm font-medium">System Issues</span>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center mb-2">
              {healthStatus?.health_status?.api_connected ? (
                <Wifi className="w-6 h-6 text-green-500" />
              ) : (
                <WifiOff className="w-6 h-6 text-red-500" />
              )}
            </div>
            <div className="text-sm text-gray-600">API Connection</div>
            <div className={`text-lg font-semibold ${
              healthStatus?.health_status?.api_connected ? 'text-green-600' : 'text-red-600'
            }`}>
              {healthStatus?.health_status?.api_connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600 mb-2">
              {healthStatus?.health_status?.devices_accessible || 0}
            </div>
            <div className="text-sm text-gray-600">Devices Accessible</div>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center mb-2">
              {healthStatus?.health_status?.authentication_valid ? (
                <CheckCircle className="w-6 h-6 text-green-500" />
              ) : (
                <AlertTriangle className="w-6 h-6 text-yellow-500" />
              )}
            </div>
            <div className="text-sm text-gray-600">Authentication</div>
            <div className={`text-sm font-semibold ${
              healthStatus?.health_status?.authentication_valid ? 'text-green-600' : 'text-yellow-600'
            }`}>
              {healthStatus?.health_status?.authentication_valid ? 'Valid' : 'Check Required'}
            </div>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <button
              onClick={testConnection}
              disabled={isTestingConnection}
              className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 disabled:opacity-50 transition-colors text-sm font-medium"
            >
              {isTestingConnection ? 'Testing...' : 'Test Connection'}
            </button>
          </div>
        </div>

        {healthStatus?.message && (
          <div className="text-center text-gray-600">
            <p>{healthStatus.message}</p>
          </div>
        )}
      </motion.div>

      {/* System Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <div className="flex items-center space-x-3 mb-6">
          <Settings className="w-6 h-6 text-gray-500" />
          <h2 className="text-xl font-semibold text-gray-900">System Information</h2>
        </div>

        <div className="space-y-4">
          {systemInfo.map((info, index) => (
            <motion.div
              key={info.label}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 * index }}
              className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-center space-x-3">
                {info.icon}
                <span className="text-sm font-medium text-gray-900">{info.label}</span>
              </div>
              <span className="text-sm text-gray-600">{info.value}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Configuration Tips */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200"
      >
        <div className="flex items-start space-x-4">
          <Info className="w-8 h-8 text-blue-600 mt-1" />
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Configuration Notes</h3>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• Configure your Ring credentials above to enable real device access</li>
            <li>• The webapp connects to the Ring MCP server running on port 8123</li>
            <li>• All API calls are proxied through Next.js for security</li>
            <li>• Real device testing requires valid Ring account credentials</li>
            <li>• Mock data is used when no real devices are available</li>
            <li>• The system automatically detects and adapts to your environment</li>
          </ul>
        </div>
        </div>
      </motion.div>
    </div>
  )
}