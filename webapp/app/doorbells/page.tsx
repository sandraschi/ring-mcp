'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Bell,
  Volume2,
  History,
  AlertTriangle,
  CheckCircle,
  Clock,
  Wifi,
  WifiOff,
  Battery,
  MessageSquare
} from 'lucide-react'
import { DeviceCard } from '@/components/DeviceCard'
import { ringApi } from '@/lib/api'
import { RingDevice, RingEvent } from '@/types/ring'
import toast from 'react-hot-toast'

export default function DoorbellsPage() {
  const [devices, setDevices] = useState<RingDevice[]>([])
  const [recentEvents, setRecentEvents] = useState<RingEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDoorbells()
  }, [])

  const loadDoorbells = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const allDevices = await ringApi.getDevices()
      const doorbells = allDevices.filter(device => device.type === 'doorbell')

      setDevices(doorbells)

      // Load recent doorbell events
      const events: RingEvent[] = []
      for (const doorbell of doorbells) {
        try {
          const deviceEvents = await ringApi.getDeviceEvents(doorbell.id, 5)
          events.push(...deviceEvents.map(event => ({
            ...event,
            deviceName: doorbell.name,
            deviceType: doorbell.type
          })))
        } catch (err) {
          console.warn(`Failed to get events for ${doorbell.name}:`, err)
        }
      }

      // Sort by timestamp (newest first) and take top 20
      events.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      setRecentEvents(events.slice(0, 20))

    } catch (err: any) {
      console.error('Failed to load doorbells:', err)
      setError(err.message || 'Failed to load doorbells')
      toast.error('Failed to load doorbells')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeviceAction = async (deviceId: string, action: string) => {
    if (action === 'chime') {
      try {
        await ringApi.triggerDoorbellChime(deviceId)
        toast.success('Doorbell chime triggered!')
      } catch (err: any) {
        toast.error(`Failed to trigger chime: ${err.message}`)
      }
    }
  }

  const doorbellStats = {
    total: devices.length,
    online: devices.filter(d => d.online).length,
    offline: devices.filter(d => !d.online).length,
    recentRings: recentEvents.filter(e => e.kind === 'doorbell').length
  }

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'doorbell':
        return <Bell className="w-5 h-5 text-green-500" />
      case 'motion':
        return <MessageSquare className="w-5 h-5 text-blue-500" />
      default:
        return <History className="w-5 h-5 text-gray-500" />
    }
  }

  const getEventDescription = (event: any) => {
    const deviceName = event.deviceName || 'Unknown doorbell'

    switch (event.kind) {
      case 'doorbell':
        return `Doorbell pressed at ${deviceName}`
      case 'motion':
        return `Motion detected at ${deviceName}`
      default:
        return `Activity at ${deviceName}`
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Doorbells</h1>
            <p className="text-gray-600 mt-1">Doorbell management and history</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="w-12 h-12 bg-gray-200 rounded-xl mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Doorbells</h1>
            <p className="text-gray-600 mt-1">Doorbell management and history</p>
          </div>
          <button
            onClick={loadDoorbells}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <History className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>

        <div className="text-center py-12">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Doorbells</h3>
          <p className="text-gray-600">{error}</p>
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
          <h1 className="text-3xl font-bold text-gray-900">Doorbells</h1>
          <p className="text-gray-600 mt-1">Doorbell management and history</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
          <button
            onClick={loadDoorbells}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <History className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </motion.div>

      {/* Doorbell Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Bell className="w-5 h-5 text-blue-500" />
            <span className="text-sm text-gray-600">Total Doorbells</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-2">{doorbellStats.total}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-sm text-gray-600">Online</span>
          </div>
          <div className="text-2xl font-bold text-green-600 mt-2">{doorbellStats.online}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <WifiOff className="w-5 h-5 text-red-500" />
            <span className="text-sm text-gray-600">Offline</span>
          </div>
          <div className="text-2xl font-bold text-red-600 mt-2">{doorbellStats.offline}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Volume2 className="w-5 h-5 text-purple-500" />
            <span className="text-sm text-gray-600">Recent Rings</span>
          </div>
          <div className="text-2xl font-bold text-purple-600 mt-2">{doorbellStats.recentRings}</div>
        </div>
      </motion.div>

      {/* Doorbell Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Doorbells</h2>

        {devices.length === 0 ? (
          <div className="text-center py-12">
            <Bell className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Doorbells Found</h3>
            <p className="text-gray-600">
              No Ring doorbells are currently configured in your system.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {devices.map((device, index) => (
              <motion.div
                key={device.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 * index }}
              >
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  {/* Doorbell Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        device.online ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                      }`}>
                        <Bell className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 truncate max-w-32">{device.name}</h3>
                        <p className="text-sm text-gray-500">{device.model}</p>
                      </div>
                    </div>
                    {device.online ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <WifiOff className="w-5 h-5 text-red-500" />
                    )}
                  </div>

                  {/* Doorbell Status */}
                  <div className="space-y-3 mb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {device.online ? (
                          <Wifi className="w-4 h-4 text-green-500" />
                        ) : (
                          <WifiOff className="w-4 h-4 text-red-500" />
                        )}
                        <span className="text-sm text-gray-600">Status</span>
                      </div>
                      <span className={`text-sm font-medium ${
                        device.online ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {device.online ? 'Online' : 'Offline'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Battery className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">Battery</span>
                      </div>
                      <span className="text-sm font-medium">
                        {device.battery_life ? `${device.battery_life}%` : 'Wired'}
                      </span>
                    </div>
                  </div>

                  {/* Action Button */}
                  <button
                    onClick={() => handleDeviceAction(device.id, 'chime')}
                    disabled={!device.online}
                    className="w-full flex items-center justify-center space-x-2 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Volume2 className="w-4 h-4" />
                    <span>Test Chime</span>
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Recent Activity */}
      {recentEvents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="space-y-4">
              {recentEvents.slice(0, 10).map((event, index) => (
                <motion.div
                  key={`${event.id}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * index }}
                  className="flex items-center space-x-4 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-shrink-0">
                    {getEventIcon(event.kind)}
                  </div>

                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {getEventDescription(event)}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs text-gray-500">
                        {new Date(event.created_at).toLocaleString()}
                      </span>
                      {event.answered && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                          Answered
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex-shrink-0">
                    <span className="text-xs text-gray-500">
                      {event.recording_status === 'ready' ? '✓ Recorded' : 'Processing'}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>

            {recentEvents.length > 10 && (
              <div className="mt-4 pt-4 border-t border-gray-200 text-center">
                <p className="text-sm text-gray-600">
                  Showing 10 most recent events out of {recentEvents.length} total
                </p>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  )
}