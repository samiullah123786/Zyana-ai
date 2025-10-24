import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navbar } from '@/components/navbar'
import { FloatingChatWidget } from '@/components/floating-chat-widget'

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

