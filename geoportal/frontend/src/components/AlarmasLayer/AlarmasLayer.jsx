'use client'
import { useEffect, useState, useRef } from 'react'
import { Marker, Popup } from 'react-leaflet'
import { alarmasService } from '../../services/alarmasService'
import L from 'leaflet'

// Crear ícono personalizado de estrella para las alarmas
const createStarIcon = (color = '#fbbf24', estado = '') => {
    return L.divIcon({
        html: `
            <div style="
                width: 24px; 
                height: 24px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            " data-estado="${estado.toLowerCase()}">
                <svg viewBox="0 0 24 24" fill="${color}" style="width: 100%; height: 100%;">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
            </div>
        `,
        className: 'alarma-star-icon',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12]
    })
}

// Colores para las estrellas según el estado
const getStarColor = (estado) => {
    switch (estado?.toLowerCase()) {
        case 'operativo':
            return '#fbbf24' // Amarillo
        case 'no operativo':
            return '#f59e0b' // Amarillo más oscuro
        default:
            return '#ec4899' // Rosado
    }
}

const AlarmasLayer = ({ visible, filters = {} }) => {
    const [alarmas, setAlarmas] = useState([])
    const [loading, setLoading] = useState(false)
    const [hasLoaded, setHasLoaded] = useState(false)
    const abortControllerRef = useRef(null)

    useEffect(() => {
        if (visible && !hasLoaded && !loading) {
            loadAlarmas()
        }
        
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort()
            }
        }
    }, [visible, hasLoaded, loading])

    const loadAlarmas = async () => {
        if (loading) return
        
        // Cancelar petición anterior si existe
        if (abortControllerRef.current) {
            abortControllerRef.current.abort()
        }
        
        abortControllerRef.current = new AbortController()
        setLoading(true)
        
        try {
            console.log('🔍 Cargando alarmas...')
            const data = await alarmasService.getAlarmas(filters)
            console.log('✅ Alarmas cargadas:', data)
            setAlarmas(data)
            setHasLoaded(true)
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('❌ Error loading alarmas:', err)
            }
        } finally {
            setLoading(false)
        }
    }

    if (!visible || loading) return null

    return (
        <>
            {alarmas.map((alarma, index) => {
                // Usar las coordenadas lat/lng que vienen del backend
                const lat = alarma.lat
                const lng = alarma.lng

                if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
                    console.warn('⚠️ Coordenadas inválidas para alarma:', alarma)
                    return null
                }

                // Crear ícono de estrella con color según el estado
                const starColor = getStarColor(alarma.ESTADO)
                const starIcon = createStarIcon(starColor, alarma.ESTADO)

                return (
                    <Marker
                        key={`alarma-${index}`}
                        position={[lat, lng]}
                        icon={starIcon}
                        eventHandlers={{
                            mouseover: (e) => {
                                const marker = e.target
                                marker.setZIndexOffset(1000)
                            },
                            mouseout: (e) => {
                                const marker = e.target
                                marker.setZIndexOffset(0)
                            }
                        }}
                    >
                        <Popup>
                            <div className="alarma-popup">
                                <h3 className="font-bold text-lg mb-2">⭐ Sistema de Alarmas</h3>
                                <div className="space-y-1 text-sm">
                                    <p><strong>Nombre SAT:</strong> {alarma.NOMBRE_SAT}</p>
                                    <p><strong>Departamento:</strong> {alarma.DEPARTAMEN}</p>
                                    <p><strong>Municipio:</strong> {alarma.MUNICIPIO}</p>
                                    <p><strong>Estado:</strong> 
                                        <span className={`ml-1 px-2 py-1 rounded text-xs ${
                                            alarma.ESTADO?.toLowerCase() === 'operativo' 
                                                ? 'bg-green-100 text-green-800' 
                                                : 'bg-red-100 text-red-800'
                                        }`}>
                                            {alarma.ESTADO}
                                        </span>
                                    </p>
                                    <p><strong>Alcance:</strong> {alarma.ALCANCE} m</p>
                                    <p><strong>Tipo Activación:</strong> {alarma.TIPO_ACTIV}</p>
                                    <p><strong>Responsable:</strong> {alarma.RESPONSABL}</p>
                                    <p><strong>Coordenadas:</strong> {alarma.LATITUD}, {alarma.LONGITUD}</p>
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                )
            })}
        </>
    )
}

export default AlarmasLayer
