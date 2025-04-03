import { useState } from 'react'
import { FaLayerGroup } from 'react-icons/fa'

const BaseMapControl = ({ baseMaps, onBaseMapChange }) => {
  const [isOpen, setIsOpen] = useState(false)

  const handleBaseMapChange = (mapId) => {
    onBaseMapChange(mapId)
    setIsOpen(false)
  }

  return (
    <div className="absolute bottom-5 right-5 z-[1000]">
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="bg-white p-2 rounded-lg shadow-lg hover:bg-gray-50 focus:outline-none"
          title="Cambiar mapa base"
        >
          <FaLayerGroup className="w-5 h-5 text-gray-600" />
        </button>

        {isOpen && (
          <div className="absolute bottom-full right-0 mb-2 bg-white rounded-lg shadow-lg overflow-hidden">
            {Object.entries(baseMaps).map(([id, map]) => (
              <button
                key={id}
                onClick={() => handleBaseMapChange(id)}
                className={`
                  w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2
                  ${map.visible ? 'bg-blue-50 text-blue-600' : 'text-gray-700'}
                `}
              >
                <div className="w-4 h-4 border rounded">
                  {map.visible && (
                    <div className="w-full h-full bg-blue-600 rounded-sm" />
                  )}
                </div>
                <span>{map.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default BaseMapControl 