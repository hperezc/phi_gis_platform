import { useState } from 'react'
import { 
  FaRuler, 
  FaDrawPolygon, 
  FaPrint, 
  FaShare, 
  FaSave,
  FaCompress,
  FaSearchPlus,
  FaSearchMinus
} from 'react-icons/fa'

const MapTools = ({ onToolSelect }) => {
  const [activeTool, setActiveTool] = useState(null)

  const tools = [
    { id: 'measure', icon: FaRuler, name: 'Medir' },
    { id: 'draw', icon: FaDrawPolygon, name: 'Dibujar' },
    { id: 'print', icon: FaPrint, name: 'Imprimir' },
    { id: 'share', icon: FaShare, name: 'Compartir' },
    { id: 'export', icon: FaSave, name: 'Exportar' },
    { id: 'zoom-in', icon: FaSearchPlus, name: 'Acercar' },
    { id: 'zoom-out', icon: FaSearchMinus, name: 'Alejar' },
    { id: 'extent', icon: FaCompress, name: 'Extensión total' }
  ]

  const handleToolClick = (toolId) => {
    setActiveTool(toolId === activeTool ? null : toolId)
    onToolSelect(toolId)
  }

  return (
    <div className="map-tools">
      <div className="p-2 grid grid-cols-2 gap-1">
        {tools.map(tool => (
          <button
            key={tool.id}
            onClick={() => handleToolClick(tool.id)}
            className={`tool-button ${activeTool === tool.id ? 'bg-primary text-white' : 'text-gray-600'}`}
            title={tool.name}
          >
            <tool.icon className="w-5 h-5" />
            <span className="text-xs mt-1">{tool.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default MapTools 