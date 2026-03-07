'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  Bell,
  Camera,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter,
  RefreshCw,
  Eye,
  Volume2,
  MessageSquare
} from 'lucide-react'
import { ActivityFeed } from '@/components/ActivityFeed'
import { ringApi } from '@/lib/api'
import { RingDevice, RingEvent } from '@/types/ring'
import toast from 'react-hot-toast'

type EventFilter = 'all' | 'doorbell' | 'camera' | 'alarm' | 'motion'

export default function ActivityPage() {
  const [devices, setDevices] = useState<RingDevice[]>([])
  const [allEvents, setAllEvents] = useState<RingEvent[]>([])
  const [filteredEvents, setFilteredEvents] = useState<RingEvent[]>([])
  const [currentFilter, setCurrentFilter] = useState<EventFilter>('all')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadActivityData()
  }, [])

  useEffect(() => {
    applyFilter()
  }, [allEvents, currentFilter])

  const loadActivityData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const allDevices = await ringApi.getDevices()
      setDevices(allDevices)

      // Load events from all devices
      const events: RingEvent[] = []
      for (const device of allDevices) {
        try {
          const deviceEvents = await ringApi.getDeviceEvents(device.id, 20)
          events.push(...deviceEvents.map(event => ({
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
      setAllEvents(events)

    } catch (err: any) {
      console.error('Failed to load activity data:', err)
      setError(err.message || 'Failed to load activity data')
      toast.error('Failed to load activity data')
    } finally {
      setIsLoading(false)
    }
  }

  const applyFilter = () => {
    let filtered = [...allEvents]

    if (currentFilter !== 'all') {
      switch (currentFilter) {
        case 'doorbell':
          filtered = allEvents.filter(event => event.kind === 'doorbell')
          break
        case 'camera':
          // Motion events can come from cameras, filter by motion kind for now
          filtered = allEvents.filter(event => event.kind === 'motion')
          break
        case 'alarm':
          filtered = allEvents.filter(event => event.kind === 'alarm')
          break
        case 'motion':
          filtered = allEvents.filter(event => event.kind === 'motion')
          break
      }
    }

    setFilteredEvents(filtered)
  }

  const getEventIcon = (event: any) => {
    switch (event.kind) {
      case 'doorbell':
        return <Bell className="w-5 h-5 text-green-500" />
      case 'motion':
        return event.deviceType === 'camera' ?
          <Camera className="w-5 h-5 text-blue-500" /> :
          <MessageSquare className="w-5 h-5 text-blue-500" />
      case 'alarm':
        return <Shield className="w-5 h-5 text-red-500" />
      default:
        return <Activity className="w-5 h-5 text-gray-500" />
    }
  }

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'doorbell':
        return 'border-l-green-500 bg-green-50'
      case 'motion':
        return 'border-l-blue-500 bg-blue-50'
      case 'alarm':
        return 'border-l-red-500 bg-red-50'
      default:
        return 'border-l-gray-500 bg-gray-50'
    }
  }

  const getEventDescription = (event: any) => {
    const deviceName = event.deviceName || 'Unknown device'

    switch (event.kind) {
      case 'doorbell':
        return `Doorbell pressed at ${deviceName}`
      case 'motion':
        return `Motion detected at ${deviceName}`
      case 'alarm':
        return `Security alarm triggered at ${deviceName}`
      default:
        return `Activity at ${deviceName}`
    }
  }

  const filterOptions: { value: EventFilter; label: string; icon: React.ReactNode; color: string }[] = [
    { value: 'all', label: 'All Events', icon: <Activity className="w-4 h-4" />, color: 'bg-gray-100 text-gray-700' },
    { value: 'doorbell', label: 'Doorbell', icon: <Bell className="w-4 h-4" />, color: 'bg-green-100 text-green-700' },
    { value: 'camera', label: 'Cameras', icon: <Camera className="w-4 h-4" />, color: 'bg-blue-100 text-blue-700' },
    { value: 'alarm', label: 'Security', icon: <Shield className="w-4 h-4" />, color: 'bg-red-100 text-red-700' },
    { value: 'motion', label: 'Motion', icon: <MessageSquare className="w-4 h-4" />, color: 'bg-purple-100 text-purple-700' }
  ]

  const activityStats = {
    totalEvents: allEvents.length,
    doorbellEvents: allEvents.filter(e => e.kind === 'doorbell').length,
    motionEvents: allEvents.filter(e => e.kind === 'motion').length,
    alarmEvents: allEvents.filter(e => e.kind === 'alarm').length,
    answeredEvents: allEvents.filter(e => e.answered).length
  }

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Activity</h1>
            <p className="text-gray-600 mt-1">Recent events and motion history</p>
          </div>
        </div>

        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg p-4 border border-gray-200">
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
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Activity</h1>
            <p className="text-gray-600 mt-1">Recent events and motion history</p>
          </div>
          <button
            onClick={loadActivityData}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>

        <div className="text-center py-12">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Activity</h3>
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
          <h1 className="text-3xl font-bold text-gray-900">Activity</h1>
          <p className="text-gray-600 mt-1">Recent events and motion history</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
          <button
            onClick={loadActivityData}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </motion.div>

      {/* Activity Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-5 gap-4"
      >
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-gray-500" />
            <span className="text-sm text-gray-600">Total Events</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-2">{activityStats.totalEvents}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Bell className="w-5 h-5 text-green-500" />
            <span className="text-sm text-gray-600">Doorbell</span>
          </div>
          <div className="text-2xl font-bold text-green-600 mt-2">{activityStats.doorbellEvents}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Camera className="w-5 h-5 text-blue-500" />
            <span className="text-sm text-gray-600">Camera Motion</span>
          </div>
          <div className="text-2xl font-bold text-blue-600 mt-2">{activityStats.motionEvents}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-red-500" />
            <span className="text-sm text-gray-600">Security</span>
          </div>
          <div className="text-2xl font-bold text-red-600 mt-2">{activityStats.alarmEvents}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-sm text-gray-600">Answered</span>
          </div>
          <div className="text-2xl font-bold text-green-600 mt-2">{activityStats.answeredEvents}</div>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-lg p-4 border border-gray-200"
      >
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-900">Filter Events:</span>
          <div className="flex space-x-2">
            {filterOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setCurrentFilter(option.value)}
                className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  currentFilter === option.value
                    ? option.color.replace('100', '500').replace('text-', 'bg-').replace('700', '50') + ' text-current'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {option.icon}
                <span>{option.label}</span>
                {currentFilter === option.value && (
                  <span className="text-xs bg-white bg-opacity-50 px-1 rounded">
                    {filteredEvents.length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Activity Feed */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        {filteredEvents.length === 0 ? (
          <div className="text-center py-12">
            <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {currentFilter === 'all' ? 'No Activity Found' : `No ${currentFilter} Events`}
            </h3>
            <p className="text-gray-600">
              {currentFilter === 'all'
                ? 'Your Ring devices haven\'t detected any activity recently.'
                : `No ${currentFilter} events found. Try changing the filter.`
              }
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="space-y-4">
              {filteredEvents.map((event, index) => (
                <motion.div
                  key={`${event.id}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.05 * index }}
                  className={`flex items-center space-x-4 p-4 rounded-lg border-l-4 ${getEventColor(event.kind)}`}
                >
                  <div className="flex-shrink-0">
                    {getEventIcon(event)}
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
                Showing {filteredEvents.length} of {allEvents.length} total events
                {currentFilter !== 'all' && ` (filtered by ${currentFilter})`}
              </p>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  )
}