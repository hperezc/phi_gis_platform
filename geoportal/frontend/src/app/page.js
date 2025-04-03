'use client'
import { useState, useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import { FaLayerGroup, FaSearch, FaChartBar, FaInfoCircle, FaBars, FaDownload, FaFilter } from 'react-icons/fa'
import LayersPanel from '../components/Panels/LayersPanel'
import SearchPanel from '../components/Panels/SearchPanel'
import { getGeometries } from '../services/api'
import { FilterProvider } from '../context/FilterContext'

// Importaciones dinámicas
const DynamicStatsPanel = dynamic(
  () => import('../components/Panels/StatsPanel'),
  {
    ssr: false,
    loading: () => (
      <div className="p-4">
        <div className="text-gray-600">Cargando estadísticas...</div>
      </div>
    ),
  }
)

const DynamicInfoPanel = dynamic(
  () => import('../components/Panels/InfoPanel'),
  {
    ssr: false,
    loading: () => (
      <div className="p-4">
        <div className="text-gray-600">Cargando información...</div>
      </div>
    ),
  }
)

// Carga dinámica del mapa y herramientas
const Map = dynamic(() => import('../components/Map/Map'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center">
      <div className="text-gray-600">Cargando mapa...</div>
    </div>
  ),
})

const MapTools = dynamic(() => import('../components/MapTools/MapTools'), {
  ssr: false
})

// Estado inicial de las capas
const initialLayers = {
  baseMaps: {
    satellite: {
      id: 'satellite',
      name: 'Satélite',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Tiles &copy; Esri',
      visible: true,
      description: 'Vista satelital del terreno'
    },
    osm: {
      id: 'osm',
      name: 'OpenStreetMap',
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; OpenStreetMap contributors',
      visible: false,
      description: 'Mapa base estándar'
    },
    terrain: {
      id: 'terrain',
      name: 'Terreno',
      url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
      visible: false,
      description: 'Mapa topográfico con curvas de nivel y relieve.',
      previewUrl: '/map-previews/terrain.png'
    },
    dark: {
      id: 'dark',
      name: 'Oscuro',
      url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      attribution: '&copy; <a href="https://carto.com">CARTO</a>',
      visible: false,
      description: 'Mapa estilo oscuro, ideal para visualización nocturna.',
      previewUrl: '/map-previews/dark.png'
    },
    light: {
      id: 'light',
      name: 'Claro',
      url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      attribution: '&copy; <a href="https://carto.com">CARTO</a>',
      visible: false,
      description: 'Mapa estilo claro con énfasis en la legibilidad.',
      previewUrl: '/map-previews/light.png'
    }
  },
  departamentos: { 
    id: 'departamentos', 
    visible: true, 
    opacity: 0.7, 
    color: '#2563eb',
    highlightColor: '#1e40af',
    name: 'Departamentos',
    description: 'División político-administrativa a nivel departamental',
    source: 'IGAC 2023'
  },
  municipios: { 
    id: 'municipios', 
    visible: false, 
    opacity: 0.7, 
    color: '#16a34a',
    highlightColor: '#15803d',
    name: 'Municipios',
    description: 'División político-administrativa a nivel municipal',
    source: 'IGAC 2023'
  },
  rios: {
    id: 'rios',
    visible: false,
    opacity: 0.7,
    color: '#0ea5e9',
    highlightColor: '#0369a1',
    name: 'Ríos Principales',
    description: 'Red hídrica principal',
    source: 'IDEAM 2023'
  },
  cuencas: {
    id: 'cuencas',
    visible: false,
    opacity: 0.7,
    color: '#6366f1',
    highlightColor: '#4338ca',
    name: 'Cuencas Hidrográficas',
    description: 'Delimitación de cuencas hidrográficas',
    source: 'IDEAM 2023'
  },
  veredas: { 
    id: 'veredas', 
    visible: false, 
    opacity: 0.7, 
    color: '#dc2626',
    highlightColor: '#b91c1c',
    name: 'Grupos de Interés',
    description: 'Actividades por grupo de interés y municipio',
    source: 'PHI 2023'
  },
  senales_evacuacion: {
    id: 'senales_evacuacion',
    visible: false,
    opacity: 0.9,
    color: '#dc2626',
    name: 'Señales de Evacuación',
    description: 'Señalización de rutas de evacuación',
    source: 'PHI 2023'
  },
  puntos_encuentro: {
    id: 'puntos_encuentro',
    visible: false,
    opacity: 0.9,
    color: '#16a34a',
    name: 'Puntos de Encuentro',
    description: 'Puntos de encuentro para evacuación',
    source: 'PHI 2023'
  },
  rutas_evacuacion: {
    id: 'rutas_evacuacion',
    visible: false,
    opacity: 0.9,
    color: '#f97316',
    name: 'Rutas de Evacuación',
    description: 'Rutas establecidas para evacuación',
    source: 'PHI 2023'
  },
  drenaje_doble: {
    id: 'drenaje_doble',
    visible: false,
    opacity: 0.7,
    color: '#0ea5e9',
    highlightColor: '#0369a1',
    name: 'Drenajes Principales',
    description: 'Red de drenajes principales del área de influencia',
    source: 'IGAC 2023'
  },
  drenaje_sencillo: {
    id: 'drenaje_sencillo',
    visible: false,
    opacity: 0.7,
    color: '#06b6d4',
    highlightColor: '#0891b2',
    name: 'Drenajes Secundarios',
    description: 'Red de drenajes secundarios del área de influencia',
    source: 'IGAC 2023'
  },
  mancha_inundacion: {
    id: 'mancha_inundacion',
    visible: false,
    opacity: 0.5,
    color: '#3b82f6',
    highlightColor: '#2563eb',
    name: 'Mancha de Inundación',
    description: 'Área potencial de inundación por escenario de rotura de presa',
    source: 'PHI 2023'
  },
  embalse: {
    id: 'embalse',
    visible: false,
    opacity: 0.7,
    color: '#0284c7',
    highlightColor: '#0369a1',
    name: 'Embalse',
    description: 'Embalse Hidroituango',
    source: 'PHI 2023'
  },
  obra_principal: {
    id: 'obra_principal',
    visible: false,
    opacity: 0.7,
    color: '#f59e0b',
    highlightColor: '#d97706',
    name: 'Obra Principal',
    description: 'Ubicación de la obra principal',
    source: 'PHI 2023'
  },
  rios_principales: {
    id: 'rios_principales',
    visible: false,
    opacity: 0.9,
    color: '#0ea5e9',
    name: 'Ríos Principales',
    description: 'Red hídrica principal del área de influencia',
    source: 'IGAC 2023'
  },
  vias: {
    id: 'vias',
    visible: false,
    opacity: 0.7,
    name: 'Red Vial',
    description: 'Red vial del área de influencia',
    source: 'IGAC 2023',
    subTypes: {
      'Tipo 1': {
        visible: true,
        color: '#f59e0b',
        weight: 5
      },
      'Tipo 2': {
        visible: true,
        color: '#d97706',
        weight: 4
      },
      'Tipo 3': {
        visible: true,
        color: '#92400e',
        weight: 3
      },
      'Tipo 4': {
        visible: true,
        color: '#78350f',
        weight: 2
      }
    }
  }
}

// Mantener solo la versión dinámica
const FilterPanel = dynamic(() => import('../components/Panels/FilterPanel'), {
  ssr: false,
  loading: () => (
    <div className="p-4">
      <div className="text-gray-600">Cargando filtros...</div>
    </div>
  ),
})

export default function Home() {
  const [activePanel, setActivePanel] = useState('layers')
  const [isPanelOpen, setIsPanelOpen] = useState(true)
  const [layers, setLayers] = useState(initialLayers)
  const [selectedFeature, setSelectedFeature] = useState(null)
  const [currentLevel, setCurrentLevel] = useState('departamentos')
  const [timeRange, setTimeRange] = useState({
    startDate: null,
    endDate: null
  })
  const [geometries, setGeometries] = useState({})
  const [loading, setLoading] = useState({})
  const [filteredFeatures, setFilteredFeatures] = useState(null)
  const mapRef = useRef(null)

  const loadGeometry = async (layerId) => {
    try {
      setLoading(prev => ({ ...prev, [layerId]: true }))
      console.log(`🔄 Cargando geometría para: ${layerId}`) // Debug log
      
      const data = await getGeometries(layerId)
      console.log(`📥 Datos recibidos para ${layerId}:`, data) // Debug log
      
      setGeometries(prev => ({
        ...prev,
        [layerId]: data
      }))
    } catch (error) {
      console.error(`Error cargando ${layerId}:`, error)
    } finally {
      setLoading(prev => ({ ...prev, [layerId]: false }))
    }
  }

  const handleLayerToggle = async (layerId) => {
    // Manejar subtipos de vías
    if (layerId.startsWith('vias-')) {
      const tipoVia = layerId.replace('vias-', '');
      setLayers(prev => ({
        ...prev,
        vias: {
          ...prev.vias,
          subTypes: {
            ...prev.vias.subTypes,
            [tipoVia]: {
              ...prev.vias.subTypes[tipoVia],
              visible: !prev.vias.subTypes[tipoVia].visible
            }
          }
        }
      }));
      return;
    }

    const newLayers = {
      ...layers,
      [layerId]: {
        ...layers[layerId],
        visible: !layers[layerId].visible
      }
    }
    setLayers(newLayers)

    // Cargar datos si la capa se está haciendo visible y no tenemos los datos
    if (newLayers[layerId].visible && !geometries[layerId]) {
      await loadGeometry(layerId)
    }
  }

  const handleOpacityChange = (layerId, opacity) => {
    setLayers(prev => ({
      ...prev,
      [layerId]: {
        ...prev[layerId],
        opacity
      }
    }))
  }

  const handleBaseMapChange = (mapId) => {
    setLayers(prev => ({
      ...prev,
      baseMaps: Object.fromEntries(
        Object.entries(prev.baseMaps).map(([id, map]) => [
          id,
          { ...map, visible: id === mapId }
        ])
      )
    }))
  }

  const handleSearch = async (term, filters) => {
    console.log('Búsqueda:', term, filters)
    // Implementar lógica de búsqueda
    return []
  }

  const handleLocationSelect = (location) => {
    console.log('Ubicación seleccionada:', location)
    // Implementar zoom a ubicación
  }

  const handleToolSelect = (toolId) => {
    console.log('Herramienta seleccionada:', toolId)
    // Implementar acciones de herramientas
  }

  const handleFeatureSelect = (feature) => {
    setSelectedFeature(feature)
    
    if (!isPanelOpen) {
        setIsPanelOpen(true)
    }
    
    // Determinar el panel basado en el tipo de feature
    if (feature.type === 'administrative') {
        setActivePanel('stats')
    } else if (feature.type === 'operational') {
        setActivePanel('search')
    }
  }

  const handleTogglePanel = () => {
    setIsPanelOpen(!isPanelOpen)
  }

  const handleFilterApply = (filteredData) => {
    setFilteredFeatures(filteredData);
  };

  const handleFilteredFeatureSelect = (feature) => {
    console.log('Selected feature:', feature);
    
    if (feature && feature.geometry) {
      try {
        const bounds = L.geoJSON(feature).getBounds();
        console.log('Bounds:', bounds);
        
        if (mapRef.current) {
          console.log('Zooming to bounds...');
          mapRef.current.fitBounds(bounds, { 
            padding: [50, 50],
            maxZoom: 18
          });
        } else {
          console.error('Map reference not available');
        }
      } catch (error) {
        console.error('Error handling feature selection:', error);
      }
    } else {
      console.error('Invalid feature or missing geometry:', feature);
    }
  };

  return (
    <FilterProvider>
      <main className="relative h-screen">
        <div className="sidebar">
          {/* Navegación del sidebar */}
          <div className="sidebar-nav">
            <button
              className={`nav-button ${activePanel === 'layers' ? 'active' : ''}`}
              onClick={() => setActivePanel('layers')}
              title="Capas"
            >
              <FaLayerGroup size={20} />
            </button>
            <button
              className={`nav-button ${activePanel === 'search' ? 'active' : ''}`}
              onClick={() => setActivePanel('search')}
              title="Búsqueda"
            >
              <FaSearch size={20} />
            </button>
            <button
              className={`nav-button ${activePanel === 'filter' ? 'active' : ''}`}
              onClick={() => setActivePanel('filter')}
              title="Filtros"
            >
              <FaFilter size={20} />
            </button>
            <button
              className={`nav-button ${activePanel === 'stats' ? 'active' : ''}`}
              onClick={() => setActivePanel('stats')}
              title="Estadísticas"
            >
              <FaChartBar size={20} />
            </button>
            <button
              className={`nav-button ${activePanel === 'info' ? 'active' : ''}`}
              onClick={() => setActivePanel('info')}
              title="Información"
            >
              <FaInfoCircle size={20} />
            </button>
          </div>

          {/* Contenido del panel */}
          {activePanel === 'layers' && (
            <LayersPanel 
              layers={layers}
              onLayerToggle={handleLayerToggle}
              onOpacityChange={handleOpacityChange}
              onBaseMapChange={handleBaseMapChange}
            />
          )}
          {activePanel === 'search' && (
            <SearchPanel 
              selectedFeature={selectedFeature}
              onSearch={handleSearch}
              onLocationSelect={handleLocationSelect}
            />
          )}
          {activePanel === 'stats' && (
            <DynamicStatsPanel 
              selectedFeature={selectedFeature}
              currentLevel={currentLevel}
            />
          )}
          {activePanel === 'info' && <DynamicInfoPanel />}
          {activePanel === 'filter' && (
            <FilterPanel 
              layers={layers}
              onFilterApply={handleFilterApply}
              onFeatureSelect={handleFilteredFeatureSelect}
            />
          )}
        </div>

        <div className="flex-1 relative">
          <div className="absolute inset-0">
            <Map 
              ref={mapRef}
              layers={layers} 
              onFeatureSelect={handleFeatureSelect}
              currentLevel={currentLevel}
              isPanelOpen={isPanelOpen}
            />
          </div>
        </div>
      </main>
    </FilterProvider>
  )
}
