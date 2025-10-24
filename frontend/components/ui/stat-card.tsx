'use client'

import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import { Card } from './card'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  icon: LucideIcon
  gradient: string
  delay?: number
}

export function StatCard({ title, value, change, icon: Icon, gradient, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className="overflow-hidden border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]">
        <div className={cn("h-full p-6", gradient)}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-white/80 mb-1">{title}</p>
              <p className="text-3xl font-bold text-white mb-2">{value}</p>
              {change !== undefined && (
                <div className="flex items-center space-x-1">
                  <span className={cn(
                    "text-sm font-medium",
                    change >= 0 ? "text-green-200" : "text-red-200"
                  )}>
                    {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
                  </span>
                  <span className="text-xs text-white/60">vs last month</span>
                </div>
              )}
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
              <Icon className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

