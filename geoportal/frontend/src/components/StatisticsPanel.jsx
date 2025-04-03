import React from 'react';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const StatisticsPanel = ({ statistics }) => {
  console.log("Statistics recibidos en StatisticsPanel:", statistics);
  
  if (!statistics) return <div>Seleccione una región para ver estadísticas</div>;

  // Extraer y formatear datos de categorías
  const datosCategorias = statistics.categoria_actividad?.map(item => ({
    categoria: item.categoria || 'Sin categoría',
    total: parseInt(item.total) || 0,
    asistentes: parseInt(item.asistentes) || 0
  })) || [];

  console.log("Datos formateados de categorías:", datosCategorias);

  return (
    <div className="statistics-panel">
      <h3 className="text-lg font-semibold mb-4">Estadísticas</h3>
      
      {/* Resumen */}
      <div className="stats-summary mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="stat-card bg-blue-50 p-4 rounded-lg">
            <h4 className="text-sm text-gray-600">Total Actividades</h4>
            <p className="text-2xl font-bold text-blue-600">
              {statistics.resumen?.total_actividades || 0}
            </p>
          </div>
          <div className="stat-card bg-green-50 p-4 rounded-lg">
            <h4 className="text-sm text-gray-600">Total Asistentes</h4>
            <p className="text-2xl font-bold text-green-600">
              {statistics.resumen?.total_asistentes || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Gráfico por Categoría */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold mb-2">Actividades por Categoría</h4>
        <div className="h-[400px]"> {/* Contenedor con altura fija */}
          {datosCategorias.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={datosCategorias}
                layout="vertical"
                margin={{ top: 20, right: 30, left: 120, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis 
                  type="category" 
                  dataKey="categoria" 
                  width={100}
                  tick={{ 
                    fill: '#1e293b',
                    fontSize: 12,
                  }}
                />
                <Tooltip content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-white p-2 rounded shadow border">
                        <p className="font-medium">{label}</p>
                        <p>Actividades: {payload[0].value}</p>
                        <p>Asistentes: {payload[1].value}</p>
                      </div>
                    );
                  }
                  return null;
                }} />
                <Legend />
                <Bar dataKey="total" fill="#10b981" name="Actividades" />
                <Bar dataKey="asistentes" fill="#3b82f6" name="Asistentes" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              No hay datos disponibles
            </div>
          )}
        </div>
      </div>

      {/* ... resto del componente ... */}
    </div>
  );
};

export default StatisticsPanel; 