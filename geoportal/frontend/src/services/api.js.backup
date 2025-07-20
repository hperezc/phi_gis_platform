import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Cache para almacenar las geometrías ya cargadas
const geometryCache = new Map()

// Interceptor para logs detallados
api.interceptors.request.use(request => {
  console.log('🚀 Request:', {
    url: request.url,
    method: request.method,
    headers: request.headers
  })
  return request
})

api.interceptors.response.use(
  response => {
    console.log('✅ Response:', {
      status: response.status,
      data: response.data
    })
    return response
  },
  error => {
    console.error('❌ Error:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    })
    throw error
  }
)

export const getGeometries = async (level) => {
  try {
    // Log para depuración
    console.log(`🔍 Solicitando geometrías para nivel: ${level}`);
    
    const response = await api.get(`/geometries/${level}`);
    
    // Log para depuración
    console.log(`✅ Respuesta recibida para ${level}:`, response.data);
    
    if (response.data && response.data.features) {
      // Almacenar en caché
      geometryCache.set(level, response.data);
      return response.data;
    }
    
    throw new Error('Formato de respuesta inválido');
  } catch (error) {
    console.error(`❌ Error obteniendo geometrías para ${level}:`, error);
    throw error;
  }
}

export const getStatistics = async (level, geometryId, timeRange) => {
  try {
    const params = new URLSearchParams({
      geometry_id: geometryId,
      geometry_type: level
    });
    
    if (timeRange?.startDate) params.append('start_date', timeRange.startDate);
    if (timeRange?.endDate) params.append('end_date', timeRange.endDate);

    console.log(`📊 Solicitando estadísticas para ${level}/${geometryId}`);
    const response = await api.get(`/statistics/${level}/${geometryId}?${params.toString()}`);
    
    if (!response.data) {
      throw new Error('No se recibieron datos del servidor');
    }
    
    console.log(`✅ Estadísticas recibidas para ${level}/${geometryId}:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`❌ Error obteniendo estadísticas para ${level}/${geometryId}:`, {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    });
    throw new Error(
      error.response?.data?.detail || 
      'Error al obtener las estadísticas. Por favor, intenta de nuevo.'
    );
  }
}

export const getTableFields = async (tableName) => {
  try {
    console.log(`🔍 Solicitando campos para tabla: ${tableName}`);
    const response = await api.get(`/fields/${tableName}`);
    
    console.log(`✅ Campos obtenidos:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`❌ Error obteniendo campos para ${tableName}:`, error);
    throw new Error(
      error.response?.data?.detail || 
      'Error al obtener los campos. Por favor, intenta de nuevo.'
    );
  }
};

export const getFieldValues = async (tableName, fieldName) => {
  try {
    console.log(`🔍 Solicitando valores para ${tableName}.${fieldName}`);
    const response = await api.get(`/values/${tableName}/${fieldName}`);
    
    console.log(`✅ Valores obtenidos:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`❌ Error obteniendo valores para ${tableName}.${fieldName}:`, error);
    throw new Error(
      error.response?.data?.detail || 
      'Error al obtener los valores. Por favor, intenta de nuevo.'
    );
  }
}; 