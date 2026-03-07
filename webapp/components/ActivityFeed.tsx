'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  Camera,
  Bell,
  Shield,
  AlertTriangle,
  Eye,
  Volume2,
  Clock,
  RefreshCw
} from 'lucide-react'
import { RingDevice, RingEvent } from '@/types/ring'
import { ringApi } from '@/lib/api'
import { formatRelativeTime } from '@/lib/utils'

interface ActivityFeedProps {
  devices: RingDevice[]
}

export function ActivityFeed({ devices }: ActivityFeedProps) {
  const [events, setEvents] = useState<RingEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadRecentEvents()
  }, [devices])

  const loadRecentEvents = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const allEvents: RingEvent[] = []

      // Get events from devices that support them
      for (const device of devices) {
        if (device.type === 'camera' || device.type === 'doorbell') {
          try {
            const deviceEvents = await ringApi.getDeviceEvents(device.id, 3)
            allEvents.push(...deviceEvents.map(event => ({
              ...event,
              deviceName: device.name,
              deviceType: device.type
            })))
          } catch (err) {
            console.warn(`Failed to get events for ${device.name}:`, err)
          }
        }
      }

      // Sort by timestamp (newest first)
      allEvents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

      setEvents(allEvents.slice(0, 10)) // Keep only the 10 most recent
    } catch (err: any) {
      console.error('Failed to load events:', err)
      setError(err.message || 'Failed to load activity')
    } finally {
      setIsLoading(false)
    }
  }

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'motion':
        return <Eye className="w-5 h-5 text-blue-500" />
      case 'doorbell':
        return <Bell className="w-5 h-5 text-green-500" />
      case 'alarm':
        return <Shield className="w-5 h-5 text-red-500" />
      default:
        return <Activity className="w-5 h-5 text-gray-500" />
    }
  }

  const getEventDescription = (event: any) => {
    const deviceName = event.deviceName || 'Unknown device'
    const eventType = event.kind || 'unknown'

    switch (eventType) {
      case 'motion':
        return `Motion detected at ${deviceName}`
      case 'doorbell':
        return `Doorbell pressed at ${deviceName}`
      case 'alarm':
        return `Security alert from ${deviceName}`
      default:
        return `Activity at ${deviceName}`
    }
  }

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'motion':
        return 'border-l-blue-500 bg-blue-50'
      case 'doorbell':
        return 'border-l-green-500 bg-green-50'
      case 'alarm':
        return 'border-l-red-500 bg-red-50'
      default:
        return 'border-l-gray-500 bg-gray-50'
    }
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Activity</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadRecentEvents}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Activity className="w-6 h-6 text-ring-500" />
          <h2 className="text-xl font-semibold text-gray-900">Recent Activity</h2>
        </div>
        <button
          onClick={loadRecentEvents}
          disabled={isLoading}
          className="flex items-center space-x-2 text-sm text-ring-600 hover:text-ring-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
                <div className="w-16 h-3 bg-gray-200 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Recent Activity</h3>
          <p className="text-gray-600">
            Your Ring devices haven't detected any activity recently.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {events.map((event, index) => (
            <motion.div
              key={`${event.id}-${index}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
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
                    <span>{formatRelativeTime(event.created_at)}</span>
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
      )}

      {events.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600 text-center">
            Showing {events.length} most recent events
          </p>
        </div>
      )}
    </div>
  )
}