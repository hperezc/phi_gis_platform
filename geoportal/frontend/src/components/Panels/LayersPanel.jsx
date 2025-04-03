import { useState, useRef } from 'react'
import { createPortal } from 'react-dom'
import { 
  FaLayerGroup, 
  FaInfoCircle, 
  FaGlobe, 
  FaMap, 
  FaSatellite, 
  FaMoon, 
  FaSun,
  FaMapMarked,
  FaCity,
  FaHome,
  FaStream,
  FaCompass,
  FaMapMarkedAlt,
  FaTint,
  FaExclamationTriangle,
  FaMapMarkerAlt,
  FaRoute,
  FaIndustry,
  FaWater,
  FaChevronDown,
  FaRoad,
  FaWaterLadder,
  FaBuilding
} from 'react-icons/fa'
import { FaChevronDown as FaChevronDownFa6 } from 'react-icons/fa6'
import { 
  FaWaterLadder as FaWaterLadderFa6,
  FaIndustry as FaIndustryFa6
} from 'react-icons/fa6'

// Objeto para mapear los íconos de los grupos
const groupIcons = {
  base: FaCompass,
  admin: FaMapMarkedAlt,
  hydro: FaTint,
  infra: FaIndustry,
  evac: FaRoute,
  base_layers: FaMap
}

const LayerGroup = ({ title, children, isOpen, onToggle, groupId, icon }) => {
  const [showDescription, setShowDescription] = useState(false)
  const tooltipTriggerRef = useRef(null)
  const Icon = groupIcons[groupId] || FaLayerGroup
  
  // Descripciones de los grupos
  const groupDescriptions = {
    base: "Diferentes estilos de visualización del mapa base",
    admin: "Capas de la división político-administrativa del territorio",
    hydro: "Elementos hidrográficos y cuencas del territorio"
  }

  return (
    <div className="layer-group">
      <div 
        className="group-header"
        onClick={onToggle}
      >
        <div className="title">
          {icon}
          <span>{title}</span>
        </div>
        <FaChevronDownFa6
          className={`w-5 h-5 transition-transform ${
            isOpen ? 'transform rotate-180' : ''
          }`}
        />
      </div>
      {isOpen && (
        <div className="group-content">
          {children}
        </div>
      )}
    </div>
  )
}

// Objeto para mapear los íconos de los mapas base
const baseMapIcons = {
  satellite: FaSatellite,
  osm: FaMap,
  terrain: FaGlobe,
  dark: FaMoon,
  light: FaSun
}

const BaseMapItem = ({ map, onBaseMapChange, isActive }) => {
  const Icon = baseMapIcons[map.id] || FaMap

  return (
    <div className="layer-item flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-blue-700" />
        <span className="text-gray-700">{map.name}</span>
      </div>
      <input
        type="radio"
        checked={isActive}
        onChange={() => onBaseMapChange(map.id)}
        className="form-radio h-4 w-4 text-blue-700"
      />
    </div>
  )
}

// Objeto para mapear los íconos de las capas
const layerIcons = {
  departamentos: FaMapMarked,
  municipios: FaCity,
  veredas: FaHome,
  rios: FaStream,
  cuencas: FaTint,
  senales_evacuacion: FaExclamationTriangle,
  puntos_encuentro: FaMapMarkerAlt,
  rutas_evacuacion: FaRoute,
  drenaje_doble: FaStream,
  drenaje_sencillo: FaTint,
  mancha_inundacion: FaWater,
  embalse: FaWaterLadderFa6,
  rios_principales: FaStream,
  vias: FaRoad,
  obra_principal: FaBuilding
}

// Actualizar las descripciones de las capas administrativas
const layerDescriptions = {
  departamentos: {
    description: "División político-administrativa de primer nivel que representa los departamentos del área de influencia del proyecto. Incluye los límites administrativos oficiales y la información territorial asociada.",
    source: "Instituto Geográfico Agustín Codazzi (IGAC)",
    lastUpdate: "2024",
    category: "División Administrativa"
  },
  municipios: {
    description: "División político-administrativa de segundo nivel que comprende los municipios del área de influencia del PHI. Incluye los límites municipales oficiales, nombres y códigos territoriales.",
    source: "Instituto Geográfico Agustín Codazzi (IGAC)",
    lastUpdate: "2024",
    category: "División Administrativa"
  },
  veredas: {
    description: "División territorial rural que representa las veredas dentro del área de influencia del proyecto. Esta capa es fundamental para la gestión territorial a nivel local y la identificación de comunidades.",
    source: "Instituto Geográfico Agustín Codazzi (IGAC)",
    lastUpdate: "2024",
    category: "División Administrativa"
  },
  rios: {
    description: "Red hídrica principal del área de influencia del PHI, incluyendo el río Cauca y sus principales afluentes. Fundamental para el análisis hidrológico y la gestión del riesgo.",
    source: "Instituto Geográfico Agustín Codazzi (IGAC)",
    lastUpdate: "2024",
    category: "Hidrología"
  },
  cuencas: {
    description: "Delimitación de las cuencas hidrográficas y sistemas de drenaje en el área de influencia del proyecto. Incluye las subcuencas que aportan al embalse del PHI.",
    source: "Instituto Geográfico Agustín Codazzi (IGAC)",
    lastUpdate: "2024",
    category: "Hidrología"
  },
  obra_principal: {
    description: "Ubicación y delimitación de la obra principal del Proyecto Hidroeléctrico Ituango",
    source: "PHI 2023",
    lastUpdate: "2023",
    category: "Infraestructura PHI",
    details: {
      tipo: "Presa y obras anexas",
      altura: "225 metros",
      longitud: "500 metros"
    }
  },
  embalse: {
    description: "Área de inundación del embalse del Proyecto Hidroeléctrico Ituango, con una capacidad total de 2,720 millones de metros cúbicos y una superficie de 3,800 hectáreas.",
    source: "EPM - Proyecto Hidroeléctrico Ituango",
    lastUpdate: "2024"
  },
  senales_evacuacion: {
    description: "Red de señalización para rutas de evacuación, incluyendo indicadores direccionales, puntos de encuentro y señales de advertencia en caso de emergencia.",
    source: "Plan de Gestión del Riesgo PHI",
    lastUpdate: "2024",
    category: "Seguridad"
  },
  puntos_encuentro: {
    description: "Ubicaciones designadas como puntos seguros de reunión en caso de evacuación. Estos puntos están estratégicamente ubicados en zonas elevadas y de fácil acceso.",
    source: "Plan de Gestión del Riesgo PHI",
    lastUpdate: "2024",
    category: "Seguridad"
  },
  rutas_evacuacion: {
    description: "Rutas predefinidas y señalizadas para la evacuación segura de la población en caso de emergencia. Incluye vías principales y alternativas.",
    source: "Plan de Gestión del Riesgo PHI",
    lastUpdate: "2024",
    category: "Seguridad"
  },
  drenaje_doble: {
    description: "Red hidrográfica principal que incluye ríos y cuerpos de agua de doble margen. Representa los cauces más significativos del área de influencia, incluyendo el río Cauca y sus principales tributarios.",
    source: "Instituto Geográfico Agustín Codazzi (IGAC)",
    lastUpdate: "2024",
    category: "Hidrología"
  },
  drenaje_sencillo: {
    description: "Red hidrográfica secundaria que incluye quebradas, arroyos y cauces menores. Complementa la red de drenaje principal y es esencial para la comprensión del sistema hídrico local.",
    source: "Instituto Geográfico Agustín Codazzi (IGAC)",
    lastUpdate: "2024",
    category: "Hidrología"
  },
  mancha_inundacion: {
    description: "Áreas potencialmente inundables por escenario de rotura de presa, con un caudal máximo de 368.000 m³/s. Incluye la modelación hidráulica del tránsito de la onda de creciente, zonas de afectación y tiempos de llegada de la onda.",
    source: "EPM - Estudios Técnicos PHI",
    lastUpdate: "2024",
    category: "Riesgo Hidrológico",
    details: {
      caudal: "368.000 m³/s",
      escenario: "Rotura de Presa"
    }
  },
  rios_principales: {
    description: "Red hídrica principal que incluye los ríos más importantes del área de influencia del proyecto",
    source: "IGAC 2023",
    lastUpdate: "2023",
    category: "Hidrografía",
    details: {
      escala: "1:100.000",
      tipo: "Red hídrica principal"
    }
  },
  vias: {
    description: "Red vial clasificada según su importancia y características técnicas",
    source: "IGAC 2023",
    lastUpdate: "2023",
    category: "Infraestructura vial",
    details: {
      escala: "1:100.000",
      tipos: [
        "Tipo 1: Vías principales pavimentadas",
        "Tipo 2: Vías secundarias pavimentadas",
        "Tipo 3: Vías terciarias",
        "Tipo 4: Vías rurales"
      ]
    }
  }
}

// Componente Tooltip que usa portal
const Tooltip = ({ content, show, targetRef }) => {
  if (!show || !targetRef.current) return null

  const rect = targetRef.current.getBoundingClientRect()
  const style = {
    position: 'fixed',
    left: `${rect.left + rect.width / 2}px`,
    top: `${rect.bottom + 10}px`,
    transform: 'translateX(-50%)',
  }

  return createPortal(
    <div className="tooltip-content" style={style}>
      {content}
    </div>,
    document.body
  )
}

const LayerItem = ({ layer, onToggle, onOpacityChange }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const tooltipTriggerRef = useRef(null);
  const Icon = layerIcons[layer.id] || FaLayerGroup;
  const layerInfo = layerDescriptions[layer.id] || {};
  
  // Agregar manejo de subtipos para vías
  const renderSubTypes = () => {
    if (layer.id === 'vias' && layer.subTypes) {
      const descripcionesTipo = {
        'Tipo 1': 'Vía Principal',
        'Tipo 2': 'Vía Secundaria',
        'Tipo 3': 'Vía Terciaria',
        'Tipo 4': 'Vía Rural'
      };

      return (
        <div className="ml-6 mt-2 space-y-2">
          {Object.entries(layer.subTypes).map(([type, config]) => (
            <div key={type} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.visible}
                  onChange={() => onToggle(`vias-${type}`)}
                  className="form-checkbox h-4 w-4"
                />
                <span className="text-sm text-gray-600">
                  {descripcionesTipo[type] || type}
                </span>
              </div>
              <div 
                className="w-6 rounded"
                style={{ 
                  backgroundColor: config.color,
                  height: `${config.weight}px`
                }}
              />
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderTooltipContent = (layer, layerInfo) => {
    return (
      <div className="tooltip-inner">
        <h4 className="font-medium text-gray-900 mb-2">{layer.name}</h4>
        <p className="text-gray-600 mb-3">{layerInfo.description}</p>
        <div className="space-y-2">
          {layerInfo.category && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="font-medium">Categoría:</span>
              <span>{layerInfo.category}</span>
            </div>
          )}
          {layerInfo.source && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="font-medium">Fuente:</span>
              <span>{layerInfo.source}</span>
            </div>
          )}
          {layerInfo.lastUpdate && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="font-medium">Actualización:</span>
              <span>{layerInfo.lastUpdate}</span>
            </div>
          )}
          {layerInfo.details && Object.entries(layerInfo.details).map(([key, value]) => (
            <div key={key} className="text-xs text-gray-500">
              {Array.isArray(value) ? (
                <div>
                  <span className="font-medium capitalize">{key}:</span>
                  <ul className="mt-1 ml-2">
                    {value.map((item, index) => (
                      <li key={index} className="text-xs">{item}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="font-medium capitalize">{key}:</span>
                  <span>{value}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="layer-item">
      <div className="flex items-center justify-between mb-2">
        <div className="checkbox-container">
          <input
            type="checkbox"
            checked={layer.visible}
            onChange={() => onToggle(layer.id)}
            className="custom-checkbox"
          />
          <div className="flex items-center gap-2">
            {Icon && <Icon className="w-4 h-4 text-blue-700" />}
            <span className="text-gray-700">{layer.name}</span>
          </div>
        </div>
        <div
          ref={tooltipTriggerRef}
          className="info-icon-wrapper"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <FaInfoCircle className="w-4 h-4 text-blue-600 opacity-60 hover:opacity-100 transition-opacity" />
        </div>
      </div>
      {layer.visible && (
        <div className="opacity-slider-container mt-2">
          <input
            type="range"
            min="0"
            max="100"
            value={layer.opacity * 100}
            onChange={(e) => onOpacityChange(layer.id, e.target.value / 100)}
            className="w-full"
          />
          <span className="text-xs text-gray-500 ml-2">{Math.round(layer.opacity * 100)}%</span>
        </div>
      )}
      <Tooltip
        show={showTooltip}
        targetRef={tooltipTriggerRef}
        content={renderTooltipContent(layer, layerInfo)}
      />
      {layer.visible && renderSubTypes()}
    </div>
  );
};

export const LayersPanel = ({ layers, onLayerToggle, onOpacityChange, onBaseMapChange }) => {
  const [openGroups, setOpenGroups] = useState(['base', 'admin', 'infra', 'evac', 'hydro', 'base_layers'])

  const toggleGroup = (groupId) => {
    setOpenGroups(prev => 
      prev.includes(groupId) 
        ? prev.filter(id => id !== groupId)
        : [...prev, groupId]
    )
  }

  return (
    <div className="layers-panel">
      <div className="panel-header">
        <h2 className="text-lg font-semibold">Control de Capas</h2>
      </div>
      
      <div className="layers-content">
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <FaLayerGroup className="text-primary text-xl" />
            <h2 className="text-lg font-semibold text-gray-900">Capas del Mapa</h2>
          </div>

          <div className="space-y-3">
            <LayerGroup
              title="Mapas Base"
              isOpen={openGroups.includes('base')}
              onToggle={() => toggleGroup('base')}
              groupId="base"
              icon={<FaGlobe className="w-4 h-4 text-blue-700" />}
            >
              <div className="space-y-1">
                {Object.entries(layers.baseMaps).map(([id, map]) => (
                  <BaseMapItem
                    key={id}
                    map={map}
                    isActive={map.visible}
                    onBaseMapChange={onBaseMapChange}
                  />
                ))}
              </div>
            </LayerGroup>

            <LayerGroup
              title="División Administrativa"
              isOpen={openGroups.includes('admin')}
              onToggle={() => toggleGroup('admin')}
              groupId="admin"
              icon={<FaMapMarked className="w-4 h-4 text-blue-700" />}
            >
              {['departamentos', 'municipios', 'veredas'].map(layerId => 
                layers[layerId] && (
                  <LayerItem
                    key={layerId}
                    layer={layers[layerId]}
                    onToggle={onLayerToggle}
                    onOpacityChange={onOpacityChange}
                  />
                )
              )}
            </LayerGroup>

            <LayerGroup
              title="Infraestructura PHI"
              isOpen={openGroups.includes('infra')}
              onToggle={() => toggleGroup('infra')}
              groupId="infra"
              icon={<FaIndustryFa6 className="w-4 h-4 text-blue-700" />}
            >
              {['obra_principal', 'embalse'].map(layerId => 
                layers[layerId] && (
                  <LayerItem
                    key={layerId}
                    layer={layers[layerId]}
                    onToggle={onLayerToggle}
                    onOpacityChange={onOpacityChange}
                  />
                )
              )}
            </LayerGroup>

            <LayerGroup
              title="Sistema de Evacuación"
              isOpen={openGroups.includes('evac')}
              onToggle={() => toggleGroup('evac')}
              groupId="evac"
              icon={<FaRoute className="w-4 h-4 text-blue-700" />}
            >
              {['senales_evacuacion', 'puntos_encuentro', 'rutas_evacuacion'].map(layerId => 
                layers[layerId] && (
                  <LayerItem
                    key={layerId}
                    layer={layers[layerId]}
                    onToggle={onLayerToggle}
                    onOpacityChange={onOpacityChange}
                  />
                )
              )}
            </LayerGroup>

            <LayerGroup
              title="Hidrología"
              isOpen={openGroups.includes('hydro')}
              onToggle={() => toggleGroup('hydro')}
              groupId="hydro"
              icon={<FaWater className="w-4 h-4 text-blue-700" />}
            >
              {['mancha_inundacion'].map(layerId => 
                layers[layerId] && (
                  <LayerItem
                    key={layerId}
                    layer={layers[layerId]}
                    onToggle={onLayerToggle}
                    onOpacityChange={onOpacityChange}
                  />
                )
              )}
            </LayerGroup>

            <LayerGroup
              title="Capas Base"
              isOpen={openGroups.includes('base_layers')}
              onToggle={() => toggleGroup('base_layers')}
              groupId="base_layers"
              icon={<FaMap className="w-4 h-4 text-blue-700" />}
            >
              {['rios_principales', 'vias'].map(layerId => 
                layers[layerId] && (
                  <LayerItem
                    key={layerId}
                    layer={layers[layerId]}
                    onToggle={onLayerToggle}
                    onOpacityChange={onOpacityChange}
                  />
                )
              )}
            </LayerGroup>
          </div>

          {/* Leyenda al final */}
          <div className="legend-container">
            <h3 className="font-medium text-gray-700 mb-2">Leyenda</h3>
            <div className="space-y-2">
              {Object.entries(layers)
                .filter(([id, layer]) => id !== 'baseMaps' && layer.visible)
                .map(([id, layer]) => {
                  // Renderizado especial para vías
                  if (id === 'vias') {
                    return Object.entries(layer.subTypes)
                      .filter(([_, config]) => config.visible)
                      .map(([type, config]) => (
                        <div key={`via-${type}`} className="flex items-center space-x-2">
                          <div
                            className="w-6 rounded"
                            style={{ 
                              backgroundColor: config.color,
                              height: `${config.weight}px`
                            }}
                          />
                          <span className="text-sm text-gray-600">{`${layer.name} - ${type}`}</span>
                        </div>
                      ));
                  }
                  
                  // Renderizado especial para puntos
                  if (['puntos_encuentro', 'senales_evacuacion'].includes(id)) {
                    return (
                      <div key={id} className="flex items-center space-x-2">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ 
                            backgroundColor: id === 'puntos_encuentro' ? '#16a34a' : '#dc2626',
                            border: '2px solid white',
                            boxShadow: '0 0 0 1px rgba(0,0,0,0.2)'
                          }}
                        />
                        <span className="text-sm text-gray-600">{layer.name}</span>
                      </div>
                    );
                  }

                  // Renderizado especial para líneas
                  if (['rutas_evacuacion', 'rios_principales'].includes(id)) {
                    return (
                      <div key={id} className="flex items-center space-x-2">
                        <div
                          className="w-6 h-0 border-t-2"
                          style={{ 
                            borderColor: layer.color,
                            borderStyle: id === 'rutas_evacuacion' ? 'dashed' : 'solid'
                          }}
                        />
                        <span className="text-sm text-gray-600">{layer.name}</span>
                      </div>
                    );
                  }

                  // Renderizado por defecto para polígonos
                  return (
                    <div key={id} className="flex items-center space-x-2">
                      <div
                        className="w-4 h-4 rounded"
                        style={{ 
                          backgroundColor: layer.color,
                          opacity: layer.opacity
                        }}
                      />
                      <span className="text-sm text-gray-600">{layer.name}</span>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LayersPanel 