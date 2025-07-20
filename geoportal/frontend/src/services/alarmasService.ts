// Servicio para Sistema de Alarmas
export interface SistemaAlarma {
    ID_DEPARTA: string;
    DEPARTAMEN: string;
    MUNICIPIO: string;
    NOMBRE_SAT: string;
    ESTADO: string;
    ALCANCE: number;
    TIPO_ACTIV: string;
    RESPONSABL: string;
    LATITUD: string;
    LONGITUD: string;
}

const API_BASE_URL = 'http://localhost:8000/api';

export const alarmasService = {
    async getAlarmas(filters?: any): Promise<SistemaAlarma[]> {
        try {
            const params = new URLSearchParams();
            if (filters?.limit) params.append('limit', filters.limit.toString());
            if (filters?.departamento) params.append('departamento', filters.departamento);
            if (filters?.municipio) params.append('municipio', filters.municipio);
            if (filters?.estado) params.append('estado', filters.estado);
            if (filters?.tipo_activ) params.append('tipo_activ', filters.tipo_activ);

            const response = await fetch(`${API_BASE_URL}/alarmas/sistema_alarmas?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error obteniendo alarmas:', error);
            return [];
        }
    },

    async getFilterOptions(): Promise<any> {
        try {
            const response = await fetch(`${API_BASE_URL}/alarmas/sistema_alarmas/filters`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error obteniendo opciones de filtros:', error);
            return { departamentos: [], municipios: [], estados: [], tipos_activacion: [] };
        }
    }
};
