
// Configuración de la capa Sistema de Alarmas
export const sistemaAlarmasConfig = {
    id: 'sistema_alarmas',
    name: 'Sistema de Alarmas',
    type: 'point',
    visible: false,
    style: {
        color: '#ff4444',
        size: 8,
        symbol: 'circle',
        opacity: 0.8
    },
    popup: {
        title: 'Sistema de Alarmas',
        fields: [
            { key: 'NOMBRE_SAT', label: 'Nombre SAT' },
            { key: 'DEPARTAMEN', label: 'Departamento' },
            { key: 'MUNICIPIO', label: 'Municipio' },
            { key: 'ESTADO', label: 'Estado' },
            { key: 'ALCANCE', label: 'Alcance (m)' },
            { key: 'TIPO_ACTIV', label: 'Tipo Activación' },
            { key: 'RESPONSABL', label: 'Responsable' }
        ]
    },
    filters: [
        { key: 'DEPARTAMEN', label: 'Departamento', type: 'select' },
        { key: 'MUNICIPIO', label: 'Municipio', type: 'select' },
        { key: 'ESTADO', label: 'Estado', type: 'select' },
        { key: 'TIPO_ACTIV', label: 'Tipo Activación', type: 'select' }
    ]
};
