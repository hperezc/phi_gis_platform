'use client'
import { Geist, Geist_Mono } from "next/font/google";
import './globals.css';
import '../styles/Sidebar.css';
import '../styles/components.css';
import '../styles/StatsPanel.css';
import '../styles/Statistics.css';
import Header from '../components/Header/Header'
import { useState } from 'react'
import ToasterProvider from '../components/ToasterProvider'

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Asegurarse de que los estilos se carguen en el orden correcto
const stylesheets = [
  '/styles/globals.css',
  '/styles/components.css'
];

export default function RootLayout({ children }) {
  const [isPanelOpen, setIsPanelOpen] = useState(true)

  return (
    <html lang="es">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Header 
          isPanelOpen={isPanelOpen} 
          onTogglePanel={() => setIsPanelOpen(!isPanelOpen)} 
        />
        <div className={`app-container ${!isPanelOpen ? 'panel-closed' : ''}`}>
          {children}
        </div>
        <ToasterProvider />
      </body>
    </html>
  );
}
