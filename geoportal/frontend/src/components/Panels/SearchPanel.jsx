import { useState, useEffect } from 'react'
import { FaSearch, FaFilter, FaMapMarkerAlt, FaClock, FaRoute } from 'react-icons/fa'

const SearchPanel = ({ onSearch, onLocationSelect, selectedFeature }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    departamento: '',
    municipio: '',
    tipo: 'todos'
  })
  const [showFilters, setShowFilters] = useState(false)
  const [results, setResults] = useState([])

  const handleSearch = async (e) => {
    e.preventDefault()
    const searchResults = await onSearch(searchTerm, filters)
    setResults(searchResults)
  }

  const renderPuntoEncuentro = (data) => {
    if (!data) return null;
    
    return (
      <div className="punto-encuentro-info">
        <h3 className="info-title">
          <FaMapMarkerAlt className="inline-block mr-2" />
          Punto de Encuentro
        </h3>
        
        <div className="info-section">
          <div className="info-row">
            <div>
              <label>Nombre:</label>
              <span>{data.nombre_pe || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Código:</label>
              <span>{data.codigo_pe || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Tiempo de llegada:</label>
              <span>{data.tiempo_de_llegada || 'No especificado'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Ruta de evacuación:</label>
              <span>{data.ruta_de_evacuacion || 'No especificada'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Recorrido máximo:</label>
              <span>{data.recorrido_maximo || 'No especificado'}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderSenalEvacuacion = (data) => {
    if (!data) return null;
    
    return (
      <div className="senal-evacuacion-info">
        <h3 className="info-title">
          <FaMapMarkerAlt className="inline-block mr-2" />
          Señal de Evacuación
        </h3>
        
        <div className="info-section">
          <div className="info-row">
            <div>
              <label>Tipo:</label>
              <span>{data.tipo_senal || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Código:</label>
              <span>{data.cod_senal || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Municipio:</label>
              <span>{data.nombre_mun || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Sector:</label>
              <span>{data.nombre_sec || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Estado:</label>
              <span>{data.estado || 'No especificado'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Código PE:</label>
              <span>{data.cod_pe || 'No disponible'}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderRutaEvacuacion = (data) => {
    if (!data) return null;
    
    return (
      <div className="ruta-evacuacion-info">
        <h3 className="info-title">
          <FaRoute className="inline-block mr-2" />
          Ruta de Evacuación
        </h3>
        
        <div className="info-section">
          <div className="info-row">
            <div>
              <label>Nombre:</label>
              <span>{data.nombre_rut || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Código:</label>
              <span>{data.cod_ruta || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Estado:</label>
              <span>{data.estado_rut || 'No especificado'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Municipio:</label>
              <span>{data.nombre_mun || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Sector:</label>
              <span>{data.nombre_sec || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Tiempo:</label>
              <span>{data.tiempo_rut || 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Longitud:</label>
              <span>{data.longitud_rut ? `${data.longitud_rut} m` : 'No disponible'}</span>
            </div>
          </div>

          <div className="info-row">
            <div>
              <label>Descripción:</label>
              <span>{data.descrip_rut || 'No disponible'}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="search-panel">
      {/* Mostrar información del punto o señal seleccionada */}
      {selectedFeature?.type === 'punto_encuentro' && (
        renderPuntoEncuentro(selectedFeature.data)
      )}
      {selectedFeature?.type === 'senal_evacuacion' && (
        renderSenalEvacuacion(selectedFeature.data)
      )}
      {selectedFeature?.type === 'ruta_evacuacion' && (
        renderRutaEvacuacion(selectedFeature.data)
      )}

      <div className="search-section">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Búsqueda</h2>
          <button 
            onClick={() => setShowFilters(!showFilters)}
            className="text-gray-500 hover:text-blue-600 transition-colors"
          >
            <FaFilter size={16} />
          </button>
        </div>

        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar ubicación..."
              className="w-full p-2 pl-10 border rounded-lg"
            />
            <FaSearch className="absolute left-3 top-3 text-gray-400" />
          </div>

          {showFilters && (
            <div className="space-y-3 p-3 bg-gray-50 rounded-lg">
              <select
                value={filters.departamento}
                onChange={(e) => setFilters(prev => ({ ...prev, departamento: e.target.value }))}
                className="w-full p-2 border rounded"
              >
                <option value="">Todos los departamentos</option>
                {/* Opciones de departamentos */}
              </select>

              <select
                value={filters.municipio}
                onChange={(e) => setFilters(prev => ({ ...prev, municipio: e.target.value }))}
                className="w-full p-2 border rounded"
              >
                <option value="">Todos los municipios</option>
                {/* Opciones de municipios */}
              </select>

              <select
                value={filters.tipo}
                onChange={(e) => setFilters(prev => ({ ...prev, tipo: e.target.value }))}
                className="w-full p-2 border rounded"
              >
                <option value="todos">Todos los tipos</option>
                <option value="municipio">Municipios</option>
                <option value="vereda">Veredas</option>
                <option value="rio">Ríos</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600"
          >
            Buscar
          </button>
        </form>

        {results.length > 0 && (
          <div className="mt-4">
            <h3 className="font-semibold mb-2">Resultados</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {results.map(result => (
                <button
                  key={result.id}
                  onClick={() => onLocationSelect(result)}
                  className="w-full p-3 text-left border rounded hover:bg-gray-50 flex items-start space-x-3"
                >
                  <FaMapMarkerAlt className="w-5 h-5 text-red-500 mt-1" />
                  <div>
                    <div className="font-medium">{result.name}</div>
                    <div className="text-sm text-gray-500">{result.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SearchPanel 