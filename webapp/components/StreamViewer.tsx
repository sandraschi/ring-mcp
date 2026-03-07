'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  AlertTriangle,
  Loader
} from 'lucide-react'
import { RingDevice } from '@/types/ring'

interface StreamViewerProps {
  device: RingDevice
  streamUrl?: string
  onClose?: () => void
}

export function StreamViewer({ device, streamUrl, onClose }: StreamViewerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Simulate stream loading
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 2000)

    return () => clearTimeout(timer)
  }, [])

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  const handleMute = () => {
    setIsMuted(!isMuted)
  }

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  const handleClose = () => {
    setIsPlaying(false)
    setIsMuted(false)
    setIsFullscreen(false)
    setIsLoading(true)
    setError(null)
    onClose?.()
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
        onClick={handleClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className={`bg-white rounded-xl shadow-2xl overflow-hidden ${
            isFullscreen ? 'w-full h-full' : 'max-w-4xl w-full max-h-[80vh]'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Play className="w-4 h-4 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{device.name}</h3>
                <p className="text-sm text-gray-600">{device.model}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleFullscreen}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
              </button>

              <button
                onClick={handleClose}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Stream Container */}
          <div className={`relative bg-black ${isFullscreen ? 'h-full' : 'aspect-video'}`}>
            {isLoading ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Loader className="w-12 h-12 text-white animate-spin mx-auto mb-4" />
                  <p className="text-white text-lg">Loading stream...</p>
                  <p className="text-gray-400 text-sm mt-2">Connecting to {device.name}</p>
                </div>
              </div>
            ) : error ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                  <p className="text-white text-lg">Stream Error</p>
                  <p className="text-gray-400 text-sm mt-2">{error}</p>
                  <button
                    onClick={() => setError(null)}
                    className="mt-4 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Retry
                  </button>
                </div>
              </div>
            ) : streamUrl ? (
              <div className="absolute inset-0">
                {/* Video Element Placeholder */}
                <div className="w-full h-full bg-gray-900 flex items-center justify-center">
                  <div className="text-center text-white">
                    <Play className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p className="text-xl mb-2">Live Stream</p>
                    <p className="text-gray-400">{device.name}</p>
                    <p className="text-gray-500 text-sm mt-2">Stream URL: {streamUrl.substring(0, 50)}...</p>
                  </div>
                </div>

                {/* Stream Controls Overlay */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
                  <div className="flex items-center justify-center space-x-4">
                    <button
                      onClick={handlePlayPause}
                      className="p-3 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full transition-colors"
                    >
                      {isPlaying ? (
                        <Pause className="w-6 h-6 text-white" />
                      ) : (
                        <Play className="w-6 h-6 text-white" />
                      )}
                    </button>

                    <button
                      onClick={handleMute}
                      className="p-3 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full transition-colors"
                    >
                      {isMuted ? (
                        <VolumeX className="w-6 h-6 text-white" />
                      ) : (
                        <Volume2 className="w-6 h-6 text-white" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center text-white">
                  <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                  <p className="text-xl mb-2">Stream Not Available</p>
                  <p className="text-gray-400">Unable to load stream for {device.name}</p>
                  <p className="text-gray-500 text-sm mt-2">Device may be offline or subscription inactive</p>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 bg-gray-50 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <div className="flex items-center space-x-4">
                <span>Status: {device.online ? 'Online' : 'Offline'}</span>
                <span>Battery: {device.battery_life ? `${device.battery_life}%` : 'Wired'}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span>Live</span>
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}