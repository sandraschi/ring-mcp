'use client'

import React, { useState } from 'react'
import {
  Camera,
  Bell,
  Shield,
  Battery,
  Wifi,
  WifiOff,
  Play,
  Volume2,
  MoreVertical,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'
import { RingDevice } from '@/types/ring'
import { formatBatteryLevel, getBatteryStatus, getConnectivityStatus } from '@/lib/api'
import { getDeviceTypeIcon, formatRelativeTime, cn } from '@/lib/utils'

interface DeviceCardProps {
  device: RingDevice
  onAction?: (deviceId: string, action: string) => void
}

export function DeviceCard({ device, onAction }: DeviceCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const batteryStatus = getBatteryStatus(device.battery_life)
  const connectivityStatus = getConnectivityStatus(device.online)

  const handleAction = async (action: string) => {
    if (onAction && !isLoading) {
      setIsLoading(true)
      try {
        await onAction(device.id, action)
      } finally {
        setIsLoading(false)
      }
    }
  }

  const getDeviceIcon = () => {
    switch (device.type) {
      case 'camera':
        return <Camera className="w-6 h-6" />
      case 'doorbell':
        return <Bell className="w-6 h-6" />
      case 'alarm':
        return <Shield className="w-6 h-6" />
      default:
        return <Shield className="w-6 h-6" />
    }
  }

  const getStatusIndicator = () => {
    if (!device.online) {
      return <WifiOff className="w-4 h-4 text-red-500" />
    }

    if (batteryStatus === 'critical') {
      return <AlertTriangle className="w-4 h-4 text-red-500" />
    }

    return <CheckCircle className="w-4 h-4 text-green-500" />
  }

  const getActionButtons = () => {
    const buttons = []

    if (device.type === 'camera') {
      buttons.push(
        <button
          key="stream"
          onClick={() => handleAction('stream')}
          disabled={isLoading || !device.online}
          className="flex items-center space-x-1 px-3 py-1 bg-blue-500 text-white text-xs rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Play className="w-3 h-3" />
          <span>Stream</span>
        </button>
      )
    }

    if (device.type === 'doorbell') {
      buttons.push(
        <button
          key="chime"
          onClick={() => handleAction('chime')}
          disabled={isLoading || !device.online}
          className="flex items-center space-x-1 px-3 py-1 bg-green-500 text-white text-xs rounded-md hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Volume2 className="w-3 h-3" />
          <span>Chime</span>
        </button>
      )
    }

    return buttons
  }

  return (
    <div
      className={cn(
        "device-card bg-white rounded-xl shadow-sm border border-gray-200 p-6 transition-all duration-200",
        isHovered && "shadow-lg scale-105",
        !device.online && "opacity-75"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={cn(
            "w-12 h-12 rounded-xl flex items-center justify-center",
            device.online ? "bg-green-100 text-green-600" : "bg-gray-100 text-gray-400"
          )}>
            {getDeviceIcon()}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 truncate max-w-32">{device.name}</h3>
            <p className="text-sm text-gray-500 capitalize">{device.type}</p>
          </div>
        </div>
        {getStatusIndicator()}
      </div>

      {/* Status Indicators */}
      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {device.online ? (
              <Wifi className="w-4 h-4 text-green-500" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500" />
            )}
            <span className="text-sm text-gray-600">Connectivity</span>
          </div>
          <span className={cn(
            "text-sm font-medium",
            device.online ? "text-green-600" : "text-red-600"
          )}>
            {device.online ? 'Online' : 'Offline'}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Battery className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">Battery</span>
          </div>
          <span className={cn(
            "text-sm font-medium",
            batteryStatus === 'good' && "text-green-600",
            batteryStatus === 'warning' && "text-yellow-600",
            batteryStatus === 'critical' && "text-red-600",
            batteryStatus === 'unknown' && "text-gray-500"
          )}>
            {formatBatteryLevel(device.battery_life)}
          </span>
        </div>
      </div>

      {/* Device Info */}
      <div className="text-xs text-gray-500 space-y-1 mb-4">
        <div>Model: {device.model}</div>
        {device.firmware && <div>Firmware: {device.firmware}</div>}
        {device.address && <div className="truncate">Location: {device.address}</div>}
        <div>Last seen: {formatRelativeTime(device.last_update)}</div>
      </div>

      {/* Action Buttons */}
      {getActionButtons().length > 0 && (
        <div className="flex flex-wrap gap-2">
          {getActionButtons()}
        </div>
      )}

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 rounded-xl flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-ring-500"></div>
        </div>
      )}
    </div>
  )
}