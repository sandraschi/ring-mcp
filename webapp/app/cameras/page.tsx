'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Camera,
  Play,
  Pause,
  Settings,
  AlertTriangle,
  CheckCircle,
  Clock,
  Wifi,
  WifiOff,
  Battery,
  Eye
} from 'lucide-react'
import { DeviceCard } from '@/components/DeviceCard'
import { StreamViewer } from '@/components/StreamViewer'
import { ringApi } from '@/lib/api'
import { RingDevice } from '@/types/ring'
import toast from 'react-hot-toast'

export default function CamerasPage() {
  const [devices, setDevices] = useState<RingDevice[]>([])
  const [selectedDevice, setSelectedDevice] = useState<RingDevice | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [streamUrls, setStreamUrls] = useState<Record<string, string>>({})

  useEffect(() => {
    loadCameras()
  }, [])

  const loadCameras = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const allDevices = await ringApi.getDevices()
      const cameras = allDevices.filter(device => device.type === 'camera')

      setDevices(cameras)

      // Pre-load stream URLs for available cameras
      const urls: Record<string, string> = {}
      for (const camera of cameras) {
        if (camera.online) {
          try {
            const url = await ringApi.getLiveStreamUrl(camera.id)
            urls[camera.id] = url
          } catch (err) {
            console.warn(`Failed to get stream URL for ${camera.name}:`, err)
          }
        }
      }
      setStreamUrls(urls)

    } catch (err: any) {
      console.error('Failed to load cameras:', err)
      setError(err.message || 'Failed to load cameras')
      toast.error('Failed to load cameras')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeviceAction = async (deviceId: string, action: string) => {
    if (action === 'stream') {
      const device = devices.find(d => d.id === deviceId)
      if (device) {
        setSelectedDevice(device)
      }
    }
  }

  const handleStreamClose = () => {
    setSelectedDevice(null)
  }

  const cameraStats = {
    total: devices.length,
    online: devices.filter(d => d.online).length,
    offline: devices.filter(d => !d.online).length,
    streaming: Object.keys(streamUrls).length
  }

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Cameras</h1>
            <p className="text-gray-600 mt-1">Live camera feeds and recordings</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="w-12 h-12 bg-gray-200 rounded-xl mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded"></div>
                  <div className="h-3 bg-gray-200 rounded w-4/5"></div>
                </div>
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
            <h1 className="text-3xl font-bold text-gray-900">Cameras</h1>
            <p className="text-gray-600 mt-1">Live camera feeds and recordings</p>
          </div>
          <button
            onClick={loadCameras}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>

        <div className="text-center py-12">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Cameras</h3>
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
          <h1 className="text-3xl font-bold text-gray-900">Cameras</h1>
          <p className="text-gray-600 mt-1">Live camera feeds and recordings</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
          <button
            onClick={loadCameras}
            className="bg-ring-500 text-white px-4 py-2 rounded-lg hover:bg-ring-600 transition-colors flex items-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </motion.div>

      {/* Camera Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Camera className="w-5 h-5 text-blue-500" />
            <span className="text-sm text-gray-600">Total Cameras</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-2">{cameraStats.total}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-sm text-gray-600">Online</span>
          </div>
          <div className="text-2xl font-bold text-green-600 mt-2">{cameraStats.online}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <WifiOff className="w-5 h-5 text-red-500" />
            <span className="text-sm text-gray-600">Offline</span>
          </div>
          <div className="text-2xl font-bold text-red-600 mt-2">{cameraStats.offline}</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2">
            <Eye className="w-5 h-5 text-purple-500" />
            <span className="text-sm text-gray-600">Streams Ready</span>
          </div>
          <div className="text-2xl font-bold text-purple-600 mt-2">{cameraStats.streaming}</div>
        </div>
      </motion.div>

      {/* Camera Grid */}
      {devices.length === 0 ? (
        <div className="text-center py-12">
          <Camera className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Cameras Found</h3>
          <p className="text-gray-600">
            No Ring cameras are currently configured in your system.
          </p>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {devices.map((device, index) => (
            <motion.div
              key={device.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 * index }}
            >
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                {/* Camera Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      device.online ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                    }`}>
                      <Camera className="w-6 h-6" />
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

                {/* Camera Status */}
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

                  {streamUrls[device.id] && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Play className="w-4 h-4 text-blue-500" />
                        <span className="text-sm text-gray-600">Stream</span>
                      </div>
                      <span className="text-sm font-medium text-blue-600">Ready</span>
                    </div>
                  )}
                </div>

                {/* Action Button */}
                <button
                  onClick={() => handleDeviceAction(device.id, 'stream')}
                  disabled={!device.online}
                  className="w-full flex items-center justify-center space-x-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Play className="w-4 h-4" />
                  <span>View Live Stream</span>
                </button>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Stream Viewer Modal */}
      {selectedDevice && (
        <StreamViewer
          device={selectedDevice}
          streamUrl={streamUrls[selectedDevice.id]}
          onClose={handleStreamClose}
        />
      )}
    </div>
  )
}