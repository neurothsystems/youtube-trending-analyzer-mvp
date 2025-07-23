import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Toaster } from 'react-hot-toast';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'YouTube Trending Analyzer MVP',
  description: 'LLM-powered platform for genuine regional YouTube trend analysis',
  keywords: ['youtube', 'trending', 'analysis', 'AI', 'LLM', 'regional', 'video'],
  authors: [{ name: 'YouTube Trending Analyzer Team' }],
  robots: 'index, follow',
  openGraph: {
    title: 'YouTube Trending Analyzer MVP',
    description: 'LLM-powered platform for genuine regional YouTube trend analysis',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'YouTube Trending Analyzer MVP',
    description: 'LLM-powered platform for genuine regional YouTube trend analysis',
  },
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
          {children}
        </div>
        
        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
              fontSize: '14px',
            },
            success: {
              style: {
                background: '#059669',
              },
            },
            error: {
              style: {
                background: '#dc2626',
              },
            },
          }}
        />
      </body>
    </html>
  );
}