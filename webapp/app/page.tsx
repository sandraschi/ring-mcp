'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  Camera,
  Bell,
  Activity,
  Battery,
  Wifi,
  WifiOff,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap
} from 'lucide-react'
import { DeviceCard } from '@/components/DeviceCard'
import { SecurityPanel } from '@/components/SecurityPanel'
import { ActivityFeed } from '@/components/ActivityFeed'
import { StatsCard } from '@/components/StatsCard'
import { ringApi } from '@/lib/api'
import { RingDevice, DashboardStats } from '@/types/ring'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const [devices, setDevices] = useState<RingDevice[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Load devices
      const deviceList = await ringApi.getDevices()
      setDevices(deviceList)

      // Load system stats
      const systemStats = await ringApi.getSystemStats()
      setStats({
        ...systemStats,
        recentEvents: 0, // TODO: Implement event counting
        securityStatus: 'disarmed' // TODO: Implement security status
      })

    } catch (err: any) {
      console.error('Failed to load dashboard data:', err)
      setError(err.message || 'Failed to load dashboard data')
      toast.error('Failed to load dashboard data')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeviceAction = async (deviceId: string, action: string) => {
    try {
      switch (action) {
        case 'chime':
          await ringApi.triggerDoorbellChime(deviceId)
          toast.success('Doorbell chime triggered!')
          break
        case 'stream':
          // This will be handled by opening the stream viewer
          break
        default:
          console.log(`Unknown action: ${action} for device ${deviceId}`)
      }
    } catch (err: any) {
      console.error('Device action failed:', err)
      toast.error(`Action failed: ${err.message}`)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ring-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Ring MCP Dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadDashboardData}
            className="bg-ring-500 text-white px-6 py-2 rounded-lg hover:bg-ring-600 transition-colors"
          >
            Retry Connection
          </button>
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
          <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor and control your Ring security ecosystem</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2 bg-green-100 px-3 py-1 rounded-full">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <span className="text-sm text-green-700">System Online</span>
          </div>
          <button
            onClick={loadDashboardData}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <Zap className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </motion.div>

      {/* Stats Overview */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          <StatsCard
            title="Total Devices"
            value={stats.totalDevices}
            icon={Shield}
            color="blue"
            description={`${stats.onlineDevices} online, ${stats.offlineDevices} offline`}
          />
          <StatsCard
            title="Online Devices"
            value={stats.onlineDevices}
            icon={Wifi}
            color="green"
            description={`${Math.round((stats.onlineDevices / stats.totalDevices) * 100)}% uptime`}
          />
          <StatsCard
            title="Battery Warnings"
            value={stats.batteryWarnings}
            icon={Battery}
            color={stats.batteryWarnings > 0 ? "yellow" : "green"}
            description={stats.batteryWarnings > 0 ? "Devices need attention" : "All batteries good"}
          />
          <StatsCard
            title="Security Status"
            value={stats.securityStatus}
            icon={Shield}
            color={stats.securityStatus === 'armed' ? 'red' : 'green'}
            description={stats.securityStatus === 'armed' ? 'System is armed' : 'System is disarmed'}
          />
        </motion.div>
      )}

      {/* Security Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <SecurityPanel devices={devices} />
      </motion.div>

      {/* Device Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="space-y-6"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-gray-900">Your Devices</h2>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
        </div>

        {devices.length === 0 ? (
          <div className="text-center py-12">
            <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Devices Found</h3>
            <p className="text-gray-600">
              No Ring devices are currently configured. Please check your Ring MCP server configuration.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {devices.map((device, index) => (
              <motion.div
                key={device.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 * index }}
              >
                <DeviceCard
                  device={device}
                  onAction={handleDeviceAction}
                />
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Activity Feed */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <ActivityFeed devices={devices} />
      </motion.div>
    </div>
  )
}