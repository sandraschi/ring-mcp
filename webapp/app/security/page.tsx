'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  ShieldCheck,
  ShieldX,
  AlertTriangle,
  CheckCircle,
  Clock,
  Lock,
  Unlock,
  Activity,
  Settings
} from 'lucide-react'
import { SecurityPanel } from '@/components/SecurityPanel'
import { ringApi } from '@/lib/api'
import { RingDevice, RingEvent } from '@/types/ring'
import toast from 'react-hot-toast'

export default function SecurityPage() {
  const [devices, setDevices] = useState<RingDevice[]>([])
  const [securityEvents, setSecurityEvents] = useState<RingEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSecurityData()
  }, [])

  const loadSecurityData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const allDevices = await ringApi.getDevices()
      const securityDevices = allDevices.filter(device => device.type === 'alarm')

      setDevices(securityDevices)

      // Load security-related events from all devices
      const events: RingEvent[] = []
      for (const device of allDevices) {
        try {
          const deviceEvents = await ringApi.getDeviceEvents(device.id, 10)
          const securityRelatedEvents = deviceEvents.filter(event =>
            event.kind === 'alarm' || event.kind === 'motion'
          )
          events.push(...securityRelatedEvents.map(event => ({
            ...event,
            deviceName: device.name,
            deviceType: device.type
          })))
        } catch (err) {
          console.warn(`Failed to get events for ${device.name}:`, err)
        }
      }

      // Sort by timestamp (newest first)
      events.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      setSecurityEvents(events.slice(0, 50))

    } catch (err: any) {
      console.error('Failed to load security data:', err)
      setError(err.message || 'Failed to load security data')
      toast.error('Failed to load security data')
    } finally {
      setIsLoading(false)
    }
  }

  const securityStats = {
    totalDevices: devices.length,
    onlineDevices: devices.filter(d => d.online).length,
    offlineDevices: devices.filter(d => !d.online).length,
    recentAlarms: securityEvents.filter(e => e.kind === 'alarm').length,
    recentMotion: securityEvents.filter(e => e.kind === 'motion').length,
    totalEvents: securityEvents.length
  }

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'alarm':
        return <ShieldX className="w-5 h-5 text-red-500" />
      case 'motion':
        return <Activity className="w-5 h-5 text-blue-500" />
      default:
        return <Shield className="w-5 h-5 text-gray-500" />
    }
  }

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'alarm':
        return 'border-l-red-500 bg-red-50'
      case 'motion':
        return 'border-l-blue-500 bg-blue-50'
      default:
        return 'border-l-gray-500 bg-gray-50'
    }
  }

  const getEventDescription = (event: any) => {
    const deviceName = event.deviceName || 'Unknown device'

    switch (event.kind) {
      case 'alarm':
        return `Security alarm triggered at ${deviceName}`
      case 'motion':
        return `Motion detected at ${deviceName}`
      default:
        return `Security event at ${deviceName}`
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Security</h1>
            <p className="text-gray-600 mt-1">Alarm system and security controls</p>
          </div>
        </div>

        <div className="animate-pulse">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
            <div className="h-12 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Security</h1>
            <p className="text-gray-600 mt-1">Alarm system and security controls</p>
          </div>
          <button
            onClick={loadSecurityData}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>

        <div className="text-center py-12">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Security Data</h3>
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
          <h1 className="text-3xl font-bold text-gray-900">Security</h1>
          <p className="text-gray-600 mt-1">Alarm system and security controls</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
          <button
            onClick={loadSecurityData}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </motion.div>

      {/* Security Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <SecurityPanel devices={devices} />
      </motion.div>

      {/* Security Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 md:grid-cols-3 gap-4"
      >
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-blue-500" />
            <span className="text-sm text-gray-600">Security Devices</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-2">{securityStats.totalDevices}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <ShieldX className="w-5 h-5 text-red-500" />
            <span className="text-sm text-gray-600">Recent Alarms</span>
          </div>
          <div className="text-2xl font-bold text-red-600 mt-2">{securityStats.recentAlarms}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-blue-500" />
            <span className="text-sm text-gray-600">Motion Events</span>
          </div>
          <div className="text-2xl font-bold text-blue-600 mt-2">{securityStats.recentMotion}</div>
        </div>
      </motion.div>

      {/* Security Events */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Security Events</h2>

        {securityEvents.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <div className="text-center py-8">
              <ShieldCheck className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">All Clear</h3>
              <p className="text-gray-600">
                No security events detected recently. Your home is secure.
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="space-y-4">
              {securityEvents.map((event, index) => (
                <motion.div
                  key={`${event.id}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * index }}
                  className={`flex items-center space-x-4 p-4 rounded-lg border-l-4 ${getEventColor(event.kind)}`}
                >
                  <div className="flex-shrink-0">
                    {getEventIcon(event.kind)}
                  </div>

                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {getEventDescription(event)}
                    </p>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-xs text-gray-500 flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(event.created_at).toLocaleString()}</span>
                      </span>
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full capitalize">
                        {event.kind}
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

            <div className="mt-6 pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-600 text-center">
                Showing {securityEvents.length} security events
              </p>
            </div>
          </div>
        )}
      </motion.div>

      {/* Security Tips */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200"
      >
        <div className="flex items-start space-x-4">
          <Shield className="w-8 h-8 text-blue-600 mt-1" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Security Tips</h3>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Regularly test your alarm system to ensure it's working properly</li>
              <li>• Keep motion sensors clear of obstructions and pets</li>
              <li>• Change default alarm codes and keep them secure</li>
              <li>• Test doorbell functionality regularly</li>
              <li>• Ensure all security devices have adequate battery levels</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </div>
  )
}