import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import dynamic from 'next/dynamic'

const Navbar = dynamic(() => import('@/components/navbar').then(mod => ({ default: mod.Navbar })), {
  ssr: false,
})

const FloatingChatWidget = dynamic(() => import('@/components/floating-chat-widget').then(mod => ({ default: mod.FloatingChatWidget })), {
  ssr: false,
})

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Zyana - Personal AI Assistant',
  description: 'Multi-agent AI assistant for finance, calendar, and more',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          {children}
          <FloatingChatWidget />
        </div>
      </body>
    </html>
  )
}

