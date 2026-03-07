'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatsCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
  description?: string
  trend?: {
    value: number
    direction: 'up' | 'down' | 'neutral'
  }
}

const colorClasses = {
  blue: {
    bg: 'bg-blue-50',
    icon: 'text-blue-600',
    border: 'border-blue-200',
    text: 'text-blue-600'
  },
  green: {
    bg: 'bg-green-50',
    icon: 'text-green-600',
    border: 'border-green-200',
    text: 'text-green-600'
  },
  yellow: {
    bg: 'bg-yellow-50',
    icon: 'text-yellow-600',
    border: 'border-yellow-200',
    text: 'text-yellow-600'
  },
  red: {
    bg: 'bg-red-50',
    icon: 'text-red-600',
    border: 'border-red-200',
    text: 'text-red-600'
  },
  purple: {
    bg: 'bg-purple-50',
    icon: 'text-purple-600',
    border: 'border-purple-200',
    text: 'text-purple-600'
  }
}

export function StatsCard({ title, value, icon: Icon, color, description, trend }: StatsCardProps) {
  const colors = colorClasses[color]

  const getTrendIcon = () => {
    if (!trend) return null

    if (trend.direction === 'up') {
      return <span className="text-green-500 text-sm">↗ +{trend.value}%</span>
    } else if (trend.direction === 'down') {
      return <span className="text-red-500 text-sm">↘ -{Math.abs(trend.value)}%</span>
    } else {
      return <span className="text-gray-500 text-sm">→ {trend.value}%</span>
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className={cn(
        "bg-white rounded-xl shadow-sm border p-6 transition-all duration-200 hover:shadow-md",
        colors.border
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={cn(
            "w-12 h-12 rounded-xl flex items-center justify-center",
            colors.bg
          )}>
            <Icon className={cn("w-6 h-6", colors.icon)} />
          </div>

          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <div className="flex items-center space-x-2">
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              {getTrendIcon()}
            </div>
          </div>
        </div>
      </div>

      {description && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      )}
    </motion.div>
  )
}