'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  ShieldCheck,
  ShieldX,
  Lock,
  Unlock,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react'
import { RingDevice } from '@/types/ring'
import { ringApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface SecurityPanelProps {
  devices: RingDevice[]
}

type SecurityStatus = 'armed' | 'disarmed' | 'arming' | 'disarming'

export function SecurityPanel({ devices }: SecurityPanelProps) {
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus>('disarmed')
  const [isLoading, setIsLoading] = useState(false)
  const [lastAction, setLastAction] = useState<Date | null>(null)

  const securityDevices = devices.filter(d => d.type === 'alarm')

  const handleSecurityAction = async (action: 'arm' | 'disarm') => {
    if (securityDevices.length === 0) {
      toast.error('No security devices found')
      return
    }

    setIsLoading(true)
    const targetStatus = action === 'arm' ? 'arming' : 'disarming'
    setSecurityStatus(targetStatus)

    try {
      // Use the first security device for now
      // In a real implementation, you might want to arm/disarm all security devices
      const deviceId = securityDevices[0].id
      const result = await ringApi.setArmStatus(deviceId, action === 'arm')

      if (result.success) {
        const newStatus = action === 'arm' ? 'armed' : 'disarmed'
        setSecurityStatus(newStatus)
        setLastAction(new Date())

        toast.success(
          `Security system ${action === 'arm' ? 'armed' : 'disarmed'} successfully`,
          {
            icon: action === 'arm' ? '🔒' : '🔓',
          }
        )
      } else {
        throw new Error(result.message || 'Operation failed')
      }
    } catch (error: any) {
      console.error('Security action failed:', error)
      setSecurityStatus('disarmed') // Reset to safe state
      toast.error(`Security operation failed: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = () => {
    switch (securityStatus) {
      case 'armed':
        return 'bg-red-50 border-red-200'
      case 'arming':
      case 'disarming':
        return 'bg-yellow-50 border-yellow-200'
      default:
        return 'bg-green-50 border-green-200'
    }
  }

  const getStatusIcon = () => {
    switch (securityStatus) {
      case 'armed':
        return <ShieldX className="w-8 h-8 text-red-600" />
      case 'arming':
        return <Shield className="w-8 h-8 text-yellow-600 animate-pulse" />
      case 'disarming':
        return <ShieldCheck className="w-8 h-8 text-yellow-600 animate-pulse" />
      default:
        return <ShieldCheck className="w-8 h-8 text-green-600" />
    }
  }

  const getStatusText = () => {
    switch (securityStatus) {
      case 'armed':
        return 'System Armed'
      case 'arming':
        return 'Arming System...'
      case 'disarming':
        return 'Disarming System...'
      default:
        return 'System Disarmed'
    }
  }

  const getActionButton = () => {
    if (securityDevices.length === 0) {
      return null
    }

    const isArmed = securityStatus === 'armed'
    const canAct = securityStatus === 'armed' || securityStatus === 'disarmed'

    return (
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => handleSecurityAction(isArmed ? 'disarm' : 'arm')}
        disabled={!canAct || isLoading}
        className={`
          flex items-center space-x-3 px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200
          ${isArmed
            ? 'bg-green-500 hover:bg-green-600 text-white shadow-lg hover:shadow-xl'
            : 'bg-red-500 hover:bg-red-600 text-white shadow-lg hover:shadow-xl'
          }
          disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
        `}
      >
        {isArmed ? <Unlock className="w-6 h-6" /> : <Lock className="w-6 h-6" />}
        <span>{isArmed ? 'Disarm System' : 'Arm System'}</span>
      </motion.button>
    )
  }

  if (securityDevices.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Security Devices</h3>
          <p className="text-gray-600">
            No Ring Alarm or security devices are configured in your system.
          </p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl shadow-sm border p-8 transition-colors duration-300 ${getStatusColor()}`}
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          {getStatusIcon()}
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Security System</h2>
            <p className="text-gray-600">Control your Ring Alarm and security devices</p>
          </div>
        </div>

        {lastAction && (
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Clock className="w-4 h-4" />
            <span>Last action: {lastAction.toLocaleTimeString()}</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-4">
            <div className={`w-3 h-3 rounded-full ${
              securityStatus === 'armed' ? 'bg-red-500' :
              securityStatus === 'disarmed' ? 'bg-green-500' : 'bg-yellow-500'
            }`} />
            <span className="text-xl font-semibold text-gray-900">
              {getStatusText()}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{securityDevices.length}</div>
              <div className="text-sm text-gray-600">Security Devices</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {securityDevices.filter(d => d.online).length}
              </div>
              <div className="text-sm text-gray-600">Online</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {devices.filter(d => d.has_subscription).length}
              </div>
              <div className="text-sm text-gray-600">Active Subscriptions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {devices.filter(d => d.battery_life && d.battery_life < 20).length}
              </div>
              <div className="text-sm text-gray-600">Low Battery</div>
            </div>
          </div>
        </div>

        <div className="ml-8">
          {getActionButton()}
        </div>
      </div>

      {/* Security Device List */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Devices</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {securityDevices.map((device) => (
            <div key={device.id} className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200">
              <div className={`w-3 h-3 rounded-full ${
                device.online ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <div className="flex-1">
                <div className="font-medium text-gray-900">{device.name}</div>
                <div className="text-sm text-gray-600">{device.model}</div>
              </div>
              {device.online ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-red-500" />
              )}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}