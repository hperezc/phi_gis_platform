import { useState, useEffect } from 'react';
import { FaFilter, FaSearch } from 'react-icons/fa';
import { getTableFields, getFieldValues } from '../../services/api';
import Notification from '../Notification';
import { useFilter } from '../../context/FilterContext';

const layerFields = {
  departamentos: [
    { id: 'departamento', label: 'Nombre Departamento' },
    { id: 'cod_depto', label: 'Código DANE' }
  ],
  municipios: [
    { id: 'municipio', label: 'Nombre Municipio' },
    { id: 'departamento', label: 'Departamento' },
    { id: 'cod_mpio', label: 'Código DANE' }
  ],
  veredas: [
    { id: 'nombre', label: 'Nombre Vereda' },
    { id: 'municipio', label: 'Municipio' },
    { id: 'departamento', label: 'Departamento' },
    { id: 'grupo_interes', label: 'Grupo de Interés' }
  ],
  puntos_encuentro: [
    { id: 'codigo_pe', label: 'Código' },
    { id: 'nombre_pe', label: 'Nombre' },
    { id: 'nombre_mun', label: 'Municipio' }
  ],
  senales_evacuacion: [
    { id: 'cod_señal', label: 'Código Señal' },
    { id: 'tipo_señal', label: 'Tipo de Señal' },
    { id: 'nombre_mun', label: 'Municipio' },
    { id: 'estado', label: 'Estado' }
  ],
  rutas_evacuacion: [
    { id: 'nombre_rut', label: 'Nombre Ruta' },
    { id: 'cod_ruta', label: 'Código' },
    { id: 'nombre_mun', label: 'Municipio' },
    { id: 'estado_rut', label: 'Estado' }
  ]
};

const operational_layers = [
  'departamentos',
  'municipios',
  'veredas',
  'puntos_encuentro',
  'senales_evacuacion',
  'rutas_evacuacion'
];

export default function FilterPanel({ layers, onFilterApply, onFeatureSelect }) {
  const { lastFilter, updateLastFilter } = useFilter();
  const [selectedLayer, setSelectedLayer] = useState(lastFilter.layer);
  const [availableFields, setAvailableFields] = useState([]);
  const [selectedField, setSelectedField] = useState(lastFilter.field);
  const [availableValues, setAvailableValues] = useState([]);
  const [filterValue, setFilterValue] = useState(lastFilter.value);
  const [filteredFeatures, setFilteredFeatures] = useState(lastFilter.results);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  // Cargar campos cuando se selecciona una capa
  useEffect(() => {
    if (selectedLayer) {
      const loadFields = async () => {
        setLoading(true);
        try {
          const fields = await getTableFields(selectedLayer);
          setAvailableFields(fields);
        } catch (error) {
          console.error('Error cargando campos:', error);
          setError(error.message);
        } finally {
          setLoading(false);
        }
      };
      loadFields();
    }
  }, [selectedLayer]);

  // Cargar valores cuando se selecciona un campo
  useEffect(() => {
    if (selectedLayer && selectedField) {
      const loadValues = async () => {
        setLoading(true);
        try {
          const values = await getFieldValues(selectedLayer, selectedField);
          setAvailableValues(values);
        } catch (error) {
          console.error('Error cargando valores:', error);
        }
        setLoading(false);
      };
      loadValues();
    }
  }, [selectedLayer, selectedField]);

  // Efecto para aplicar el último filtro al montar el componente
  useEffect(() => {
    if (lastFilter.layer && lastFilter.field && lastFilter.value) {
      handleFilter();
    }
  }, []);

  const handleFilter = async () => {
    if (!selectedLayer || !selectedField || !filterValue) return;
    
    setLoading(true);
    setNotification(null);
    
    try {
      const baseURL = 'http://localhost:8000/api';
      const response = await fetch(
        `${baseURL}/filter/${selectedLayer}?field=${selectedField}&value=${filterValue}`,
        {
          headers: {
            'Accept': 'application/json'
          }
        }
      );
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al filtrar los datos');
      }

      if (data && data.features) {
        setFilteredFeatures(data.features);
        
        // Guardar el filtro actual en el contexto
        updateLastFilter({
          layer: selectedLayer,
          field: selectedField,
          value: filterValue,
          results: data.features
        });
        
        if (data.features.length > 0) {
          onFilterApply(data);
          onFeatureSelect(data.features[0]);
          setNotification({
            message: `Se encontraron ${data.features.length} resultados`,
            type: 'success'
          });
        } else {
          setNotification({
            message: 'No se encontraron resultados para el filtro aplicado',
            type: 'info'
          });
        }
      } else {
        throw new Error('Formato de respuesta inválido');
      }
    } catch (error) {
      console.error('Error al filtrar:', error);
      setNotification({
        message: error.message || 'Error al aplicar el filtro',
        type: 'error'
      });
      setFilteredFeatures([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeatureClick = (feature) => {
    onFeatureSelect(feature);
  };

  const handleLayerChange = async (layerId) => {
    setSelectedLayer(layerId);
    setSelectedField('');
    setFilterValue('');
    setFilteredFeatures([]);
    setNotification(null);
    
    if (layerId) {
      setLoading(true);
      try {
        const fields = await getTableFields(layerId);
        if (fields && fields.length > 0) {
          setAvailableFields(fields);
        } else {
          setNotification({
            message: 'No se encontraron campos para esta capa',
            type: 'error'
          });
        }
      } catch (error) {
        console.error('Error cargando campos:', error);
        setNotification({
          message: 'Error al cargar los campos de la capa',
          type: 'error'
        });
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="filter-panel h-full">
      <div className="p-6 space-y-6">
        {notification && (
          <Notification
            {...notification}
            onClose={() => setNotification(null)}
          />
        )}
        
        {/* Encabezado del panel */}
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Filtros</h3>
          <p className="text-sm text-gray-600">
            Seleccione una capa y sus criterios de filtrado
          </p>
        </div>
        
        {/* Selector de capa con icono */}
        <div className="space-y-4">
          <div className="filter-group">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Capa a filtrar
            </label>
            <div className="relative">
              <select 
                value={selectedLayer}
                onChange={(e) => handleLayerChange(e.target.value)}
                className="w-full p-3 rounded-lg shadow-sm 
                           bg-white/10 backdrop-blur-sm
                           border border-white/20 
                           text-gray-800 font-medium
                           focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           transition-all duration-200"
                disabled={loading}
              >
                <option value="">Seleccione una capa</option>
                {Object.entries(layers)
                  .filter(([id]) => id !== 'baseMaps' && operational_layers.includes(id))
                  .map(([id, layer]) => (
                    <option key={id} value={id}>{layer.name}</option>
                  ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Campo a filtrar */}
          {selectedLayer && (
            <div className="filter-group animate-fadeIn">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Campo de búsqueda
              </label>
              <div className="relative">
                <select
                  value={selectedField}
                  onChange={(e) => setSelectedField(e.target.value)}
                  className="w-full p-3 rounded-lg shadow-sm 
                             bg-white/10 backdrop-blur-sm
                             border border-white/20 
                             text-gray-800 font-medium
                             focus:ring-2 focus:ring-blue-500 focus:border-transparent
                             transition-all duration-200"
                  disabled={loading}
                >
                  <option value="">Seleccione un campo</option>
                  {availableFields.map(field => (
                    <option key={field.id} value={field.id}>{field.label}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Selector de valor */}
          {selectedField && (
            <div className="filter-group animate-fadeIn">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Valor a buscar
              </label>
              <div className="relative">
                <select
                  value={filterValue}
                  onChange={(e) => setFilterValue(e.target.value)}
                  className="w-full p-3 rounded-lg shadow-sm 
                             bg-white/10 backdrop-blur-sm
                             border border-white/20 
                             text-gray-800 font-medium
                             focus:ring-2 focus:ring-blue-500 focus:border-transparent
                             transition-all duration-200"
                  disabled={loading}
                >
                  <option value="">Seleccione un valor</option>
                  {availableValues.map((value, index) => (
                    <option key={index} value={value}>{value}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleFilter}
                className="filter-button w-full p-3 rounded-lg text-white font-medium
                           transition-all duration-200 disabled:opacity-50
                           disabled:cursor-not-allowed"
                disabled={loading || !filterValue}
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Aplicando filtro...
                  </span>
                ) : 'Aplicar Filtro'}
              </button>
            </div>
          )}
        </div>

        {/* Lista de resultados */}
        {filteredFeatures.length > 0 && (
          <div className="mt-6 animate-fadeIn">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-800">
                Resultados encontrados
              </h4>
              <span className="px-3 py-1 bg-blue-500/20 text-blue-800 rounded-full text-sm font-medium">
                {filteredFeatures.length}
              </span>
            </div>
            <div className="results-container">
              <div className="max-h-60 overflow-y-auto">
                {filteredFeatures.map((feature, index) => (
                  <div
                    key={index}
                    className="result-item p-3 cursor-pointer transition-all duration-150"
                    onClick={() => handleFeatureClick(feature)}
                  >
                    <span className="text-sm font-medium">
                      {feature.properties[selectedField]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 