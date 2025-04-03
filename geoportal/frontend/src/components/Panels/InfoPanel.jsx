'use client'
import React from 'react'
import { FaGithub, FaEnvelope } from 'react-icons/fa'

const InfoPanel = () => {
  return (
    <div className="info-panel">
      <div className="info-content">
        <h1 className="info-title">
          Geoportal - Plan de Gestión del Riesgo
        </h1>
        
        <div className="info-section">
          <p className="info-text">
            Plataforma geográfica desarrollada para la visualización y análisis de información 
            territorial del Plan de Gestión del Riesgo del Proyecto Hidroeléctrico Ituango.
          </p>
        </div>

        <div className="info-section">
          <h2 className="info-subtitle">Propiedad</h2>
          <p className="info-text">
            Este geoportal es propiedad del equipo de Gestión del Riesgo del Proyecto 
            Hidroeléctrico Ituango (Empresas Públicas de Medellín y Cruz Roja Colombiana 
            Seccional Antioquia), una herramienta diseñada para facilitar la toma de 
            decisiones y el análisis espacial de las actividades del proyecto.
          </p>
        </div>

        <div className="info-section">
          <h2 className="info-subtitle">Funcionalidades</h2>
          <ul className="info-list">
            <li>Visualización de capas geográficas del proyecto</li>
            <li>Análisis estadístico de actividades territoriales</li>
            <li>Gestión de información espacial del Plan de Gestión del Riesgo</li>
            <li>Monitoreo de infraestructura crítica</li>
            <li>Seguimiento a actividades comunitarias</li>
          </ul>
        </div>

        <div className="info-section">
          <h2 className="info-subtitle">Desarrollo</h2>
          <p className="info-text">
            Desarrollado por <span className="highlight">Héctor Camilo Pérez Contreras</span>, 
            Analista SIG del proyecto, implementando tecnologías modernas como:
          </p>
          <ul className="info-list tech-list">
            <li>Next.js y React para el frontend</li>
            <li>FastAPI y Python para el backend</li>
            <li>PostgreSQL/PostGIS como base de datos espacial</li>
            <li>Leaflet para visualización de mapas</li>
            <li>Recharts y Tremor para visualización de datos</li>
            <li>TailwindCSS para estilos</li>
          </ul>
        </div>

        <div className="info-section">
          <h2 className="info-subtitle">Contacto</h2>
          <div className="contact-links">
            <a href="mailto:analistasig2.ant@crantioquia.org.co" className="contact-link">
              <FaEnvelope className="contact-icon" />
              <span>analistasig2.ant@crantioquia.org.co</span>
            </a>
            <a href="https://github.com/hcamilop" className="contact-link" target="_blank" rel="noopener noreferrer">
              <FaGithub className="contact-icon" />
              <span>GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InfoPanel 