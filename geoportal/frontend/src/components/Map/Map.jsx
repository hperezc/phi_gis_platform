'use client'
import { useEffect, useState, useRef, useImperativeHandle, forwardRef } from 'react'
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Marker, Popup, useMap, ScaleControl } from 'react-leaflet'
import { getGeometries } from '../../services/api'
import 'leaflet/dist/leaflet.css'
import BaseMapControl from './BaseMapControl'
import LoadingSpinner from '../LoadingSpinner'
import L from 'leaflet'

// Necesitamos importar los íconos por defecto de Leaflet
import "leaflet/dist/images/marker-shadow.png"
import "leaflet/dist/images/marker-icon.png"
import "leaflet/dist/images/marker-icon-2x.png"

// Corregir el problema de los íconos por defecto de Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png').default,
  iconUrl: require('leaflet/dist/images/marker-icon.png').default,
  shadowUrl: require('leaflet/dist/images/marker-shadow.png').default,
});

// Definir íconos personalizados
const puntoEncuentroIcon = new L.DivIcon({
  html: `<div class="punto-encuentro-icon">
    <svg viewBox="0 0 24 24" fill="currentColor" class="icon">
      <path d="M12 0C7.6 0 4 3.6 4 8c0 3.8 6.1 11.8 7.4 13.5.2.3.6.5 1 .5.4 0 .7-.2 1-.5C14.7 19.8 20 11.8 20 8c0-4.4-3.6-8-8-8zm0 11c-1.7 0-3-1.3-3-3s1.3-3 3-3 3 1.3 3 3-1.3 3-3 3z"/>
    </svg>
  </div>`,
  className: 'punto-encuentro-marker',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
})

const senalEvacuacionIcon = new L.DivIcon({
  html: `<div class="senal-evacuacion-icon">
    <svg viewBox="0 0 24 24" fill="currentColor" class="icon">
      <path d="M4.47 21h15.06L12 5 4.47 21zm13.73-2H5.8L12 9l6.2 10zM13 18h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
      <path d="M12 3l-1 1.7v1.5l1-1.7 1 1.7V4.7L12 3z"/>
    </svg>
  </div>`,
  className: 'senal-evacuacion-marker',
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -28]
})

// Componente separado para manejar la creación de panes
const PaneInitializer = () => {
  const map = useMap(); // Usar el hook dentro del componente
  
  useEffect(() => {
    if (!map) return;
    
    // Crear panes con diferentes z-index
    map.createPane('vias').style.zIndex = 395;
    map.createPane('puntos').style.zIndex = 400;
    map.createPane('señales').style.zIndex = 405;
    
  }, [map]);
  
  return null;
};

// Componente para renderizar diferentes tipos de geometrías
const GeometryLayer = ({ feature, layerId, style, onEachFeature }) => {
  if (!feature.geometry) return null

  switch (feature.geometry.type) {
    case 'Point':
      switch (layerId) {
        case 'puntos_encuentro':
          return (
            <CircleMarker 
              center={[
                feature.geometry.coordinates[1],
                feature.geometry.coordinates[0]
              ]}
              radius={8}
              fillColor="#16a34a"
              color="#ffffff"
              weight={2}
              opacity={1}
              fillOpacity={0.9}
              className="punto-encuentro-marker"
              eventHandlers={{
                click: (e) => onEachFeature(feature, e.target, layerId)
              }}
            />
          )
        case 'senales_evacuacion':
          return (
            <CircleMarker 
              center={[
                feature.geometry.coordinates[1],
                feature.geometry.coordinates[0]
              ]}
              radius={6}
              fillColor="#dc2626"
              color="#ffffff"
              weight={2}
              opacity={1}
              fillOpacity={0.9}
              className="senal-evacuacion-marker"
              eventHandlers={{
                mouseover: (e) => {
                  const layer = e.target;
                  layer.setStyle({
                    radius: 8,
                    fillOpacity: 1
                  });
                },
                mouseout: (e) => {
                  const layer = e.target;
                  layer.setStyle({
                    radius: 6,
                    fillOpacity: 0.9
                  });
                },
                click: (e) => onEachFeature(feature, e.target, layerId)
              }}
            />
          )
        default:
          return (
            <CircleMarker 
              center={[
                feature.geometry.coordinates[1],
                feature.geometry.coordinates[0]
              ]}
              {...style}
              eventHandlers={{
                click: (e) => onEachFeature(feature, e.target, layerId)
              }}
            />
          )
      }
    default:
      return (
        <GeoJSON 
          data={feature} 
          style={style}
          onEachFeature={(feature, layer) => onEachFeature(feature, layer, layerId)}
        />
      )
  }
}

// Actualizar el componente MapUpdater
const MapUpdater = ({ layers, geometries, getLayerStyle, onEachFeature }) => {
  return (
    <>
      {Object.entries(layers).map(([layerId, layer]) => {
        if (layer.visible && geometries[layerId] && layerId !== 'baseMaps') {
          if (['puntos_encuentro', 'senales_evacuacion'].includes(layerId)) {
            return geometries[layerId].features.map((feature, index) => (
              <CircleMarker
                key={`${layerId}-${index}`}
                center={[
                  feature.geometry.coordinates[1],
                  feature.geometry.coordinates[0]
                ]}
                {...getLayerStyle(layerId, feature)}
                eventHandlers={{
                  mouseover: (e) => {
                    const layer = e.target;
                    layer.setStyle({
                      radius: layerId === 'puntos_encuentro' ? 10 : 8,
                      fillOpacity: 1
                    });
                  },
                  mouseout: (e) => {
                    const layer = e.target;
                    layer.setStyle(getLayerStyle(layerId, feature));
                  },
                  click: (e) => onEachFeature(feature, e.target, layerId)
                }}
              />
            ));
          }

          return (
            <GeoJSON
              key={`${layerId}-${layer.visible}-${JSON.stringify(layer.subTypes)}`}
              data={geometries[layerId]}
              style={(feature) => getLayerStyle(layerId, feature)}
              onEachFeature={(feature, layer) => onEachFeature(feature, layer, layerId)}
              pane="vias"
            />
          );
        }
        return null;
      })}
    </>
  );
}

const Map = forwardRef(({ layers, onFeatureSelect, currentLevel, isPanelOpen }, ref) => {
  const [geometries, setGeometries] = useState({})
  const [loading, setLoading] = useState({})
  const [activeFeature, setActiveFeature] = useState(null)
  const loadingRef = useRef({})
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  
  // Estado inicial del mapa base
  const [activeBaseMap, setActiveBaseMap] = useState('satellite')

  const mapRef = useRef(null);
  
  // Exponer la referencia del mapa al componente padre
  useImperativeHandle(ref, () => ({
    fitBounds: (bounds, options) => {
      if (mapRef.current) {
        const map = mapRef.current;
        map.fitBounds(bounds, options);
      }
    }
  }));

  // Efecto para manejar cambios en el mapa base
  useEffect(() => {
    if (layers.baseMaps) {
      const activeMap = Object.entries(layers.baseMaps).find(([_, map]) => map.visible)
      if (activeMap) {
        setActiveBaseMap(activeMap[0])
      }
    }
  }, [layers.baseMaps])

  useEffect(() => {
    // Simular un tiempo mínimo de carga para evitar parpadeos
    const timer = setTimeout(() => {
      setIsInitialLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    const loadGeometry = async (layerId) => {
      if (loadingRef.current[layerId] || geometries[layerId]) return

      try {
        loadingRef.current[layerId] = true
        setLoading(prev => ({ ...prev, [layerId]: true }))
        
        console.log(`🔄 Iniciando carga de: ${layerId}`)
        const data = await getGeometries(layerId)
        
        setGeometries(prev => ({
          ...prev,
          [layerId]: data
        }))
        
        console.log(`✅ Capa ${layerId} cargada:`, {
          features: data.features.length
        })
      } catch (error) {
        console.error(`❌ Error en capa ${layerId}:`, error)
      } finally {
        loadingRef.current[layerId] = false
        setLoading(prev => ({ ...prev, [layerId]: false }))
      }
    }

    Object.entries(layers).forEach(([layerId, layer]) => {
      if (layer.visible && !geometries[layerId]) {
        loadGeometry(layerId)
      }
    })
  }, [layers, geometries])

  const getLayerStyle = (layerId, feature) => {
    const layer = layers[layerId]
    const isActive = activeFeature && activeFeature.id === feature.id
    const adminLayers = ['departamentos', 'municipios', 'veredas']

    // Estilos específicos por tipo de capa
    if (adminLayers.includes(layerId)) {
      // Estilos para capas administrativas (mantener como está)
      return {
        fillColor: isActive ? layer.highlightColor : layer.color,
        weight: isActive ? 3 : 2,
        opacity: 1,
        color: isActive ? '#000' : 'white',
        dashArray: isActive ? '' : '3',
        fillOpacity: isActive ? 0.8 : (layer.opacity * 0.6)
      }
    } else {
      // Estilos para capas operativas
      switch(layerId) {
        case 'puntos_encuentro':
          return {
            radius: 8,
            fillColor: '#16a34a',
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: layer.opacity || 0.9,
            className: 'punto-encuentro-marker'
          }
        
        case 'senales_evacuacion':
          return {
            radius: 6,
            fillColor: '#dc2626',
            color: '#ffffff',
            weight: 2,
            opacity: 1,
            fillOpacity: layer.opacity || 0.9,
            className: 'senal-evacuacion-marker'
          }
        
        case 'rutas_evacuacion':
          return {
            color: '#f97316', // naranja
            weight: 4,
            opacity: 0.9,
            dashArray: '15, 10',
            lineCap: 'round',
            lineJoin: 'round',
            className: 'ruta-evacuacion-line'
          }
        
        case 'drenaje_doble':
          return {
            color: '#0ea5e9', // azul claro
            weight: 3,
            opacity: 0.8,
            className: 'drenaje-doble-line'
          }
        
        case 'drenaje_sencillo':
          return {
            color: '#38bdf8', // azul más claro
            weight: 1.5,
            opacity: 0.8,
            className: 'drenaje-sencillo-line'
          }
        
        case 'mancha_inundacion':
          return {
            fillColor: '#3b82f6',
            fillOpacity: 0.3,
            color: '#2563eb',
            weight: 1,
            className: 'mancha-inundacion-polygon'
          }
        
        case 'embalse':
          return {
            fillColor: '#0284c7',
            fillOpacity: 0.5,
            color: '#0369a1',
            weight: 2,
            className: 'embalse-polygon'
          }
        
        case 'obra_principal':
          return {
            fillColor: '#f59e0b',
            fillOpacity: 0.6,
            color: '#d97706',
            weight: 2,
            className: 'obra-principal-polygon'
          }
        
        case 'rios_principales':
          return {
            color: layer.color || '#0ea5e9',
            weight: 2,
            opacity: layer.opacity || 0.9,
            className: 'rios-principales-line',
            lineCap: 'round',
            lineJoin: 'round'
          }
        
        case 'vias':
          // Obtener el tipo de vía y limpiar el valor
          const tipoViaRaw = feature.properties?.tipo_via?.toString().trim() || '';
          // Extraer solo el número del tipo de vía
          const tipoNumero = tipoViaRaw.match(/\d+/)?.[0] || '4';
          const tipoKey = `Tipo ${tipoNumero}`;
          
          // Obtener la configuración del subtipo
          const subType = layer.subTypes?.[tipoKey];
          
          // Si el subtipo no está visible, ocultar la vía
          if (!subType?.visible) {
            return {
              opacity: 0,
              weight: 0
            };
          }

          // Aplicar el estilo del subtipo
          return {
            color: subType.color,
            weight: subType.weight,
            opacity: layer.opacity || 0.9,
            className: `vias-line tipo-${tipoNumero}`,
            lineCap: 'round',
            lineJoin: 'round'
          };
        
        default:
          return {
            fillColor: layer.color,
            weight: 2,
            opacity: 1,
            color: 'white',
            fillOpacity: layer.opacity
          }
      }
    }
  }

  const onEachFeature = (feature, layer, layerId) => {
    const adminLayers = ['departamentos', 'municipios', 'veredas']
    const operationalLayers = ['puntos_encuentro', 'senales_evacuacion', 'rutas_evacuacion']
    
    if (adminLayers.includes(layerId)) {
        // Lógica para capas administrativas
        feature.id = feature.id || `${layerId}-${feature.properties.nombre}-${Math.random()}`
        feature.layerId = layerId

        const tooltipContent = `
            <div class="custom-tooltip">
                <strong>${feature.properties.nombre}</strong>
                ${feature.properties.municipio ? `<br>Municipio: ${feature.properties.municipio}` : ''}
                ${feature.properties.departamento ? `<br>Departamento: ${feature.properties.departamento}` : ''}
            </div>
        `
        
        layer.bindTooltip(tooltipContent, {
            permanent: false,
            direction: 'auto',
            className: 'custom-tooltip',
            offset: [0, -10],
            opacity: 1,
            sticky: true
        })

        layer.on({
            mouseover: (e) => {
                const layer = e.target
                layer.setStyle({
                    weight: 3,
                    color: '#000',
                    dashArray: '',
                    fillOpacity: 0.8
                })
                layer.bringToFront()
            },
            mouseout: (e) => {
                const layer = e.target
                if (activeFeature?.id !== feature.id) {
                    layer.setStyle(getLayerStyle(feature.layerId, feature))
                }
            },
            click: (e) => {
                setActiveFeature(activeFeature?.id === feature.id ? null : feature)
                
                // Llamar a onFeatureSelect con tipo 'administrative'
                onFeatureSelect({
                    ...feature,
                    type: 'administrative',
                    level: feature.layerId,
                    properties: {
                        ...feature.properties,
                        id: feature.layerId === 'veredas' ? 
                            feature.properties.nombre : 
                            feature.properties.nombre
                    }
                })
            }
        })
    } else if (operationalLayers.includes(layerId)) {
        // Tooltips personalizados para capas operativas
        switch(layerId) {
            case 'puntos_encuentro':
                layer.bindTooltip(layers[layerId].name, {
                    permanent: false,
                    direction: 'top',
                    className: 'punto-encuentro-tooltip'
                });
                break;
            
            case 'senales_evacuacion':
                layer.bindTooltip(layers[layerId].name, {
                    permanent: false,
                    direction: 'top',
                    className: 'senal-evacuacion-tooltip'
                });
                break;
            
            default:
                layer.bindTooltip(layers[layerId].name, {
                    permanent: false,
                    direction: 'auto',
                    className: 'operational-tooltip'
                });
        }

        layer.on('click', () => {
            // Llamar a onFeatureSelect con tipo 'operational'
            onFeatureSelect({
                type: 'operational',
                layerId: layerId,
                data: feature.properties
            });
        });
    }

    if (layerId === 'puntos_encuentro') {
      console.log('Feature completo:', feature); // Debug log
      
      if (feature.properties) {
        console.log('Propiedades del punto:', feature.properties); // Debug log
        
        // Asegurarse de que los valores existan y estén limpios
        const nombre = feature.properties.nombre_pe ? feature.properties.nombre_pe.trim() : 'Sin nombre';
        const municipio = feature.properties.nombre_mun ? feature.properties.nombre_mun.trim() : 'N/A';
        const codigo = feature.properties.codigo_pe ? feature.properties.codigo_pe.trim() : 'N/A';
        const ruta = feature.properties.ruta_de_evacuacion ? feature.properties.ruta_de_evacuacion.trim() : 'N/A';
        const tiempo = feature.properties.tiempo_de_llegada ? feature.properties.tiempo_de_llegada.trim() : 'N/A';

        console.log('Valores procesados:', { nombre, municipio, codigo, ruta, tiempo }); // Debug log

        const tooltipContent = `
          <div class="custom-tooltip">
            <strong>${nombre}</strong>
            <div>Municipio: ${municipio}</div>
            <div>Código: ${codigo}</div>
            <div>Ruta: ${ruta}</div>
            <div>Tiempo de llegada: ${tiempo}</div>
          </div>
        `;

        // Eliminar tooltip anterior si existe
        if (layer.getTooltip()) {
          layer.unbindTooltip();
        }

        layer.bindTooltip(tooltipContent, {
          permanent: false,
          direction: 'top',
          offset: [0, -10],
          className: 'custom-tooltip'
        });

        layer.on('click', () => {
          console.log('Click en punto - datos completos:', feature.properties);
          if (onFeatureSelect) {
            onFeatureSelect({
              type: 'punto_encuentro',
              data: feature.properties
            });
          }
        });
      }
    } else if (layerId === 'senales_evacuacion') {
      if (feature.properties) {
        // Convertir todos los valores a string antes de usar trim()
        const tipo = feature.properties.tipo_senal ? String(feature.properties.tipo_senal).trim() : 'Sin tipo';
        const codigo = feature.properties.cod_senal ? String(feature.properties.cod_senal).trim() : 'N/A';
        const municipio = feature.properties.nombre_mun ? String(feature.properties.nombre_mun).trim() : 'N/A';
        const sector = feature.properties.nombre_sec ? String(feature.properties.nombre_sec).trim() : 'N/A';
        const estado = feature.properties.estado ? String(feature.properties.estado).trim() : 'N/A';

        // Log para depuración
        console.log('Valores originales:', {
          tipo: feature.properties.tipo_senal,
          codigo: feature.properties.cod_senal,
          municipio: feature.properties.nombre_mun,
          sector: feature.properties.nombre_sec,
          estado: feature.properties.estado
        });

        const tooltipContent = `
          <div class="custom-tooltip">
            <strong>${tipo}</strong>
            <div>Código: ${codigo}</div>
            <div>Municipio: ${municipio}</div>
            <div>Sector: ${sector}</div>
            <div>Estado: ${estado}</div>
          </div>
        `;

        if (layer.getTooltip()) {
          layer.unbindTooltip();
        }

        layer.bindTooltip(tooltipContent, {
          permanent: false,
          direction: 'top',
          offset: [0, -10],
          className: 'custom-tooltip'
        });

        layer.on('click', () => {
          if (onFeatureSelect) {
            onFeatureSelect({
              type: 'senal_evacuacion',
              data: feature.properties
            });
          }
        });
      }
    } else if (layerId === 'rutas_evacuacion') {
      if (feature.properties) {
        const nombre = feature.properties.nombre_rut ? String(feature.properties.nombre_rut).trim() : 'Sin nombre';
        const codigo = feature.properties.cod_ruta ? String(feature.properties.cod_ruta).trim() : 'N/A';
        const estado = feature.properties.estado_rut ? String(feature.properties.estado_rut).trim() : 'N/A';
        const tiempo = feature.properties.tiempo_rut ? String(feature.properties.tiempo_rut).trim() : 'N/A';
        const longitud = feature.properties.longitud_rut ? `${feature.properties.longitud_rut} m` : 'N/A';

        const tooltipContent = `
          <div class="custom-tooltip">
            <strong>${nombre}</strong>
            <div>Código: ${codigo}</div>
            <div>Estado: ${estado}</div>
            <div>Tiempo: ${tiempo}</div>
            <div>Longitud: ${longitud}</div>
          </div>
        `;

        if (layer.getTooltip()) {
          layer.unbindTooltip();
        }

        layer.bindTooltip(tooltipContent, {
          permanent: false,
          direction: 'top',
          offset: [0, -10],
          className: 'custom-tooltip'
        });

        layer.on('click', () => {
          if (onFeatureSelect) {
            onFeatureSelect({
              type: 'ruta_evacuacion',
              data: feature.properties
            });
          }
        });
      }
    } else if (layerId === 'rios_principales') {
      const nombre = feature.properties?.nombre_geografico || 'Sin nombre'
      layer.bindTooltip(
        `<div class="custom-tooltip"><strong>${nombre}</strong></div>`, 
        {
          permanent: false,
          direction: 'auto',
          className: 'rios-tooltip',
          sticky: true,
          opacity: 1,
          offset: [10, 0]
        }
      );
    } else if (layerId === 'vias') {
      const tipoViaRaw = feature.properties?.tipo_via?.toString().trim() || '';
      const tipoNumero = tipoViaRaw.match(/\d+/)?.[0] || '4';
      const tipoKey = `Tipo ${tipoNumero}`;
      
      const descripcionesTipo = {
        'Tipo 1': 'Vía Principal',
        'Tipo 2': 'Vía Secundaria',
        'Tipo 3': 'Vía Terciaria',
        'Tipo 4': 'Vía Rural'
      };

      const descripcion = descripcionesTipo[tipoKey] || 'Vía Sin Clasificar';
      
      layer.bindTooltip(
        `<div class="custom-tooltip">
          <strong>${descripcion}</strong>
          <div>Tipo ${tipoViaRaw}</div>
          <div class="text-xs text-gray-500">Escala 1:100.000</div>
        </div>`, 
        {
          permanent: false,
          direction: 'auto',
          className: 'vias-tooltip',
          sticky: true,
          opacity: 1,
          offset: [10, 0]
        }
      );
    }
  }

  return (
    <div className="map-container">
      {isInitialLoading ? (
        <LoadingSpinner />
      ) : (
        <>
          <MapContainer
            center={[4.5709, -74.2973]}
            zoom={5}
            style={{ height: "100%", width: "100%" }}
            zoomControl={false}
            ref={mapRef}
          >
            {/* Solo renderizar el mapa base activo desde layers.baseMaps */}
            {layers.baseMaps && Object.entries(layers.baseMaps).map(([id, map]) => (
              map.visible && (
                <TileLayer
                  key={id}
                  url={map.url}
                  attribution={map.attribution}
                />
              )
            ))}

            <ScaleControl position="bottomleft" />
            
            <PaneInitializer />
            <MapUpdater 
              layers={layers}
              geometries={geometries}
              getLayerStyle={getLayerStyle}
              onEachFeature={onEachFeature}
            />
          </MapContainer>
          {Object.values(loading).some(isLoading => isLoading) && <LoadingSpinner />}
        </>
      )}
    </div>
  )
})

export default Map; 