import axios from 'axios'

const api = axios.create({
  baseURL: 'https://aplicativosgrd.crantioquia.org.co/api',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 15000, // 15 segundos
  withCredentials: false
})

export const alarmasService = {
  async getAlarmas(filters = {}) {
    try {
      console.log('🔍 Solicitando alarmas con filtros:', filters)
      const response = await api.get('/alarmas/sistema_alarmas', { params: filters })
      console.log('✅ Alarmas recibidas:', response.data)
      return response.data
    } catch (error) {
      console.error('❌ Error obteniendo alarmas:', error)
      throw error
    }
  },

  async getAlarmasFilters() {
    try {
      console.log('🔍 Solicitando filtros de alarmas')
      const response = await api.get('/alarmas/sistema_alarmas/filters')
      console.log('✅ Filtros de alarmas recibidos:', response.data)
      return response.data
    } catch (error) {
      console.error('❌ Error obteniendo filtros de alarmas:', error)
      throw error
    }
  },

  async getAlarmasCount() {
    try {
      console.log('�� Solicitando conteo de alarmas')
      const response = await api.get('/alarmas/sistema_alarmas/count')
      console.log('✅ Conteo de alarmas recibido:', response.data)
      return response.data
    } catch (error) {
      console.error('❌ Error obteniendo conteo de alarmas:', error)
      throw error
    }
  }
}
