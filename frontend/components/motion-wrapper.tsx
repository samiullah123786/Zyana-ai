'use client'

import dynamic from 'next/dynamic'
import { ComponentProps } from 'react'

// Create a wrapper that loads motion components only on client side
const MotionDiv = dynamic(
  () => import('framer-motion').then((mod) => mod.motion.div),
  { ssr: false }
)

export function AnimatedDiv(props: ComponentProps<typeof MotionDiv>) {
  return <MotionDiv {...props} />
}

export { AnimatedDiv as motion }

