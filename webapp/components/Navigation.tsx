'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Home,
  Camera,
  Bell,
  Shield,
  Activity,
  Settings,
  Wifi,
  WifiOff,
  Battery,
  AlertTriangle,
  CheckCircle,
  Zap
} from 'lucide-react'
import { ringApi } from '@/lib/api'
import { DashboardStats } from '@/types/ring'
import { cn } from '@/lib/utils'

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  description: string
}

const navigation: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/',
    icon: Home,
    description: 'Overview and device status'
  },
  {
    name: 'Cameras',
    href: '/cameras',
    icon: Camera,
    description: 'Live camera feeds and recordings'
  },
  {
    name: 'Doorbells',
    href: '/doorbells',
    icon: Bell,
    description: 'Doorbell management and history'
  },
  {
    name: 'Security',
    href: '/security',
    icon: Shield,
    description: 'Alarm system and security controls'
  },
  {
    name: 'Activity',
    href: '/activity',
    icon: Activity,
    description: 'Recent events and motion history'
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    description: 'Configuration and preferences'
  }
]

export function Navigation() {
  const pathname = usePathname()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadStats = async () => {
      try {
        const connectionTest = await ringApi.testConnection()
        setIsConnected(connectionTest)

        if (connectionTest) {
          const systemStats = await ringApi.getSystemStats()
          setStats({
            ...systemStats,
            recentEvents: 0, // TODO: Implement event counting
            securityStatus: 'disarmed' // TODO: Implement security status
          })
        }
      } catch (error) {
        console.error('Failed to load navigation stats:', error)
        setIsConnected(false)
      } finally {
        setIsLoading(false)
      }
    }

    loadStats()

    // Refresh stats every 30 seconds
    const interval = setInterval(loadStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = () => {
    if (isLoading) return <Zap className="w-4 h-4 animate-pulse text-yellow-500" />
    if (isConnected) return <Wifi className="w-4 h-4 text-green-500" />
    return <WifiOff className="w-4 h-4 text-red-500" />
  }

  const getStatusText = () => {
    if (isLoading) return 'Connecting...'
    return isConnected ? 'Connected' : 'Disconnected'
  }

  return (
    <nav className="fixed left-0 top-0 h-full w-64 bg-white shadow-xl border-r border-gray-200 z-40">
      <div className="flex flex-col h-full">
        {/* Logo and Status */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-ring-500 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">Ring MCP</h1>
              <p className="text-xs text-gray-500">Security Dashboard</p>
            </div>
          </div>

          {/* Connection Status */}
          <div className="mt-4 flex items-center space-x-2">
            {getStatusIcon()}
            <span className={cn(
              "text-sm font-medium",
              isLoading && "text-yellow-600",
              isConnected && "text-green-600",
              !isConnected && !isLoading && "text-red-600"
            )}>
              {getStatusText()}
            </span>
          </div>
        </div>

        {/* Navigation Menu */}
        <div className="flex-1 px-4 py-6">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href

              return (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className={cn(
                      "group flex items-center px-3 py-3 rounded-lg transition-all duration-200",
                      isActive
                        ? "bg-ring-50 text-ring-700 border-r-2 border-ring-500"
                        : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
                    )}
                  >
                    <Icon className={cn(
                      "w-5 h-5 mr-3 transition-colors",
                      isActive ? "text-ring-500" : "text-gray-400 group-hover:text-gray-500"
                    )} />
                    <div>
                      <div className="font-medium">{item.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{item.description}</div>
                    </div>
                  </Link>
                </li>
              )
            })}
          </ul>
        </div>

        {/* Stats Panel */}
        {stats && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">System Overview</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Devices</span>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="font-medium">{stats.onlineDevices}/{stats.totalDevices}</span>
                </div>
              </div>

              {stats.batteryWarnings > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Battery</span>
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    <span className="font-medium text-yellow-600">{stats.batteryWarnings} low</span>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Security</span>
                <div className="flex items-center space-x-2">
                  <Shield className="w-4 h-4 text-gray-400" />
                  <span className="font-medium capitalize">{stats.securityStatus}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 text-center">
            Ring MCP v1.0.3
          </div>
        </div>
      </div>
    </nav>
  )
}