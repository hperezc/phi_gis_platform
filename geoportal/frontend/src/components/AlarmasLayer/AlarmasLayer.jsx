'use client'
import { useEffect, useState, useRef } from 'react'
import { CircleMarker, Popup } from 'react-leaflet'
import { alarmasService } from '../../services/alarmasService'

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
                const lat = parseFloat(alarma.LATITUD)
                const lng = parseFloat(alarma.LONGITUD)

                if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
                    console.warn('⚠️ Coordenadas inválidas para alarma:', alarma)
                    return null
                }

                return (
                    <CircleMarker
                        key={`alarma-${index}`}
                        center={[lat, lng]}
                        radius={8}
                        fillColor="#ff4444"
                        color="#cc0000"
                        weight={2}
                        opacity={0.8}
                        fillOpacity={0.6}
                    >
                        <Popup>
                            <div className="alarma-popup">
                                <h3 className="font-bold text-lg mb-2">Sistema de Alarmas</h3>
                                <div className="space-y-1 text-sm">
                                    <p><strong>Nombre SAT:</strong> {alarma.NOMBRE_SAT}</p>
                                    <p><strong>Departamento:</strong> {alarma.DEPARTAMEN}</p>
                                    <p><strong>Municipio:</strong> {alarma.MUNICIPIO}</p>
                                    <p><strong>Estado:</strong> {alarma.ESTADO}</p>
                                    <p><strong>Alcance:</strong> {alarma.ALCANCE} m</p>
                                    <p><strong>Tipo Activación:</strong> {alarma.TIPO_ACTIV}</p>
                                    <p><strong>Responsable:</strong> {alarma.RESPONSABL}</p>
                                </div>
                            </div>
                        </Popup>
                    </CircleMarker>
                )
            })}
        </>
    )
}

export default AlarmasLayer
