'use client'
import React from 'react'
import Image from 'next/image'
import { FaBars, FaChartLine } from 'react-icons/fa'
import Link from 'next/link'

const Header = ({ isPanelOpen, onTogglePanel }) => {
  return (
    <header className="main-header">
      <div className="header-content">
        <div className="header-left">
          <button 
            className={`menu-button ${!isPanelOpen ? 'menu-button-closed' : ''}`}
            onClick={onTogglePanel}
            aria-label="Alternar panel"
            title={isPanelOpen ? "Ocultar panel" : "Mostrar panel"}
          >
            <div className="button-content">
              <FaBars size={24} className="menu-icon" />
              <span className="button-ripple"></span>
            </div>
          </button>
          
          <div className="logos-container">
            <div className="logo-wrapper">
              <div className="logo-glow"></div>
              <Image
                src="/geoportal/epm-logo.png"
                alt="Logo EPM"
                width={52}
                height={52}
                className="header-logo"
                quality={100}
                priority
              />
            </div>
            <div className="logo-wrapper">
              <div className="logo-glow"></div>
              <Image
                src="/geoportal/cruz-roja-logo.png"
                alt="Logo Cruz Roja"
                width={52}
                height={52}
                className="header-logo"
                quality={100}
                priority
              />
            </div>
          </div>

          <div className="header-title-container">
            <h1 className="header-title">
              Geoportal - Plan de Gestión del Riesgo Proyecto Hidroituango
            </h1>
          </div>
        </div>
        
        <div className="header-right">
          <a href="https://aplicativosgrd.crantioquia.org.co/dashboard/" className="dashboard-button" target="_blank" rel="noopener noreferrer">
            <FaChartLine size={18} className="dashboard-icon" />
            <span>Dashboard</span>
          </a>
        </div>
      </div>
    </header>
  )
}

export default Header 
