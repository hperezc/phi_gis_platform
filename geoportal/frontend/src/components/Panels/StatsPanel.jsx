'use client'
import { useEffect, useState } from 'react'
import { getStatistics } from '../../services/api'
import { 
  Card,
  Title,
  Text,
  TabGroup as TremorTabGroup,
  TabList as TremorTabList,
  Tab as TremorTab,
  TabPanel as TremorTabPanel,
  TabPanels as TremorTabPanels,
  AreaChart,
  BarChart as TremorBarChart,
  DonutChart,
  Grid,
  Metric
} from '@tremor/react'
import { 
  PieChart, 
  Pie, 
  Cell, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  BarChart,
  Bar,
  Legend,
  LineChart, 
  Line 
} from 'recharts'
import { 
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title as ChartTitle,
  Tooltip as ChartTooltip,
  Legend as ChartLegend
} from 'chart.js'
import { Bar as ChartBar } from 'react-chartjs-2'
import { Tab, TabList, TabPanel, TabPanels } from '@headlessui/react'
import { FaChartBar, FaChartPie, FaChartLine } from 'react-icons/fa'

// Registrar los componentes necesarios de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ChartTitle,
  ChartTooltip,
  ChartLegend
)

// Paleta de colores moderna
const COLORS = [
  '#3b82f6', // azul
  '#10b981', // verde esmeralda
  '#f59e0b', // ámbar
  '#ef4444', // rojo
  '#8b5cf6', // violeta
  '#06b6d4', // cyan
  '#ec4899', // rosa
  '#f97316'  // naranja
];

// Modificar el componente DonutChart existente
const CustomDonutChart = ({ data }) => {
  // Validar y formatear datos
  const formattedData = data
    .filter(item => item && item.nombre && item.total)
    .map(item => ({
      nombre: item.nombre,
      total: parseInt(item.total),
      asistentes: parseInt(item.asistentes || 0)
    }));

  if (!formattedData.length) {
    return <Text>No hay datos disponibles</Text>;
  }

  return (
    <ResponsiveContainer width="100%" height={350}>
      <PieChart>
        <Pie
          data={formattedData}
          dataKey="total"
          nameKey="nombre"
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={120}
          paddingAngle={2}
        >
          {formattedData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={COLORS[index % COLORS.length]}
            />
          ))}
        </Pie>
        <Tooltip 
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="donut-tooltip">
                  <p className="tooltip-label">{data.nombre}</p>
                  <p className="tooltip-value">
                    Total: {new Intl.NumberFormat('es-CO').format(data.total)}
                  </p>
                  <p className="tooltip-value">
                    Asistentes: {new Intl.NumberFormat('es-CO').format(data.asistentes)}
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

// Modificar el componente de gráfico de barras
const CustomBarChart = ({ data }) => {
  if (!data || data.length === 0) {
    return <Text>No hay datos disponibles</Text>;
  }

  const sortedData = [...data].sort((a, b) => b.total - a.total);

  const chartData = {
    labels: sortedData.map(item => item.categoria),
    datasets: [
      {
        label: 'Actividades',
        data: sortedData.map(item => item.total),
        backgroundColor: '#3b82f6',
        borderRadius: 6,
        borderSkipped: false,
      },
      {
        label: 'Asistentes',
        data: sortedData.map(item => item.asistentes),
        backgroundColor: '#10b981',
        borderRadius: 6,
        borderSkipped: false,
      }
    ]
  };

  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: {
          display: false
        }
      },
      y: {
        ticks: {
          font: {
            size: 9,
          },
          autoSkip: false,
          maxRotation: 0,
          minRotation: 0,
          callback: function(value) {
            const label = this.getLabelForValue(value);
            if (label.length > 35) {
              return label.substr(0, 35) + '...';
            }
            return label;
          }
        },
        grid: {
          display: false
        }
      }
    }
  };

  return (
    <div style={{ height: '450px', width: '100%' }}>
      <ChartBar data={chartData} options={options} />
    </div>
  );
};

const CustomStackedBarChart = ({ data }) => {
  console.log('Datos recibidos en CustomStackedBarChart:', data);
  
  if (!data || !data.zonas_geograficas || data.zonas_geograficas.length === 0) {
    return <Text>No hay datos disponibles</Text>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <TremorBarChart
        data={data.zonas_geograficas}
        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
      >
        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
        <XAxis 
          dataKey="nombre" 
          angle={-45}
          textAnchor="end"
          height={60}
          interval={0}
          tick={{ fontSize: 12 }}
        />
        <YAxis />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              return (
                <div className="bg-white p-2 rounded shadow-lg border">
                  <p className="font-medium">{payload[0].payload.nombre}</p>
                  <p className="text-sm">
                    Total Actividades: {new Intl.NumberFormat('es-CO').format(payload[0].payload.total)}
                  </p>
                  <p className="text-sm">
                    Total Asistentes: {new Intl.NumberFormat('es-CO').format(payload[0].payload.asistentes)}
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <RechartsBar dataKey="total" name="Actividades" fill="#8884d8" />
        <RechartsBar dataKey="asistentes" name="Asistentes" fill="#82ca9d" />
      </TremorBarChart>
    </ResponsiveContainer>
  );
};

// Añade esta función de formateo de datos antes del return
const formatTemporalData = (data) => {
  if (!data) return [];
  
  // Agrupar por año
  const groupedByYear = data.reduce((acc, item) => {
    const year = new Date(item.mes).getFullYear();
    if (!acc[year]) {
      acc[year] = {
        total: 0,
        asistentes: 0
      };
    }
    acc[year].total += item.total;
    acc[year].asistentes += item.asistentes;
    return acc;
  }, {});

  // Convertir a array y ordenar
  return Object.entries(groupedByYear)
    .map(([year, data]) => ({
      categoria: year,
      total: data.total,
      asistentes: data.asistentes
    }))
    .sort((a, b) => a.categoria - b.categoria);
};

// Añadir este nuevo componente
const CustomHorizontalBarChart = ({ data }) => {
  console.log("Datos recibidos en el gráfico:", data);

  if (!data || !Array.isArray(data) || data.length === 0) {
    return <Text>No hay datos disponibles</Text>;
  }

  const formattedData = data
    .filter(item => item && item.categoria && item.categoria !== 'Sin datos')
    .map(item => ({
      categoria: item.categoria,
      total: parseInt(item.total || 0),
      asistentes: parseInt(item.asistentes || 0)
    }))
    .sort((a, b) => b.total - a.total);

  console.log("Datos formateados:", formattedData);

  return (
    <ResponsiveContainer width="100%" height={350}>
      <TremorBarChart
        data={formattedData}
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
        <Tooltip />
        <Legend />
        <RechartsBar dataKey="total" fill="#10b981" name="Actividades" />
        <RechartsBar dataKey="asistentes" fill="#3b82f6" name="Asistentes" />
      </TremorBarChart>
    </ResponsiveContainer>
  );
};

const StatsPanel = ({ selectedFeature, currentLevel }) => {
  const [stats, setStats] = useState(null)
  const [selectedTab, setSelectedTab] = useState(0)
  
  useEffect(() => {
    // Mover la creación del stylesheet aquí
    const styleSheet = document.createElement("style")
    styleSheet.innerText = styles
    document.head.appendChild(styleSheet)

    return () => {
      document.head.removeChild(styleSheet)
    }
  }, [])

  const tabs = [
    { 
      name: 'Temporal', 
      icon: FaChartLine,
      description: 'Muestra la evolución de actividades y asistentes en el tiempo. La línea verde indica actividades y la azul asistentes.'
    },
    { 
      name: 'Grupos', 
      icon: FaChartPie,
      description: 'Visualiza la distribución por grupos de interés. Cada segmento representa la proporción de actividades por grupo.'
    },
    { 
      name: 'Categorías', 
      icon: FaChartBar,
      description: 'Muestra la distribución de actividades y asistentes por categoría, ordenadas de mayor a menor.'
    }
  ]

  useEffect(() => {
    const loadStats = async () => {
      if (!selectedFeature) return;
      try {
        const data = await getStatistics(
          selectedFeature.level,
          selectedFeature.properties.id,
          currentLevel
        );
        console.log('Estructura de datos de categorías:', {
          categoria_actividad: data.categoria_actividad,
          estructura_completa: JSON.stringify(data, null, 2)
        });
        console.log('Datos completos recibidos:', JSON.stringify(data, null, 2));
        console.log('Datos de categorías:', data.categoria_actividad);
        setStats(data);
      } catch (err) {
        console.error('Error cargando estadísticas:', err);
      }
    };

    loadStats();
  }, [selectedFeature, currentLevel]);

  if (!selectedFeature) {
    return (
      <div className="p-4">
        <Text>Selecciona una región en el mapa para ver sus estadísticas</Text>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-4">
        <Text>No hay datos disponibles</Text>
      </div>
    );
  }

  // Verificar que los datos estén en el formato correcto
  if (stats) {
    console.log('Datos temporales:', stats.temporal);
    console.log('Grupos de interés:', stats.grupos_interes);
    console.log('Zonas geográficas:', stats.zonas_geograficas);
  }

  // Asegurarse de que stats.categoria_actividad existe y tiene datos
  const categoriasData = stats?.categoria_actividad || [];
  console.log("Datos de categorías:", categoriasData);

  const renderGruposChart = () => {
    if (!stats?.grupos_interes || stats.grupos_interes.length === 0) {
      return <Text>No hay datos disponibles</Text>;
    }

    if (selectedFeature?.level === 'veredas') {
      // Calcular totales para porcentajes
      const totalActividades = stats.grupos_interes.reduce((sum, item) => sum + item.total, 0);
      const totalAsistentes = stats.grupos_interes.reduce((sum, item) => sum + item.asistentes, 0);

      // Añadir porcentajes a los datos
      const dataWithPercentages = stats.grupos_interes.map(item => ({
        ...item,
        porcentajeActividades: ((item.total / totalActividades) * 100).toFixed(1),
        porcentajeAsistentes: ((item.asistentes / totalAsistentes) * 100).toFixed(1)
      }));

      return (
        <div className="flex flex-col space-y-4">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={dataWithPercentages}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
              <XAxis 
                dataKey="nombre" 
                angle={-45}
                textAnchor="end"
                height={60}
                interval={0}
                tick={{ fontSize: 12 }}
              />
              <YAxis />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-white p-3 rounded-lg shadow-lg border">
                        <p className="font-medium text-gray-900">{payload[0].payload.nombre}</p>
                        <div className="space-y-1 mt-2">
                          <p className="text-sm">
                            <span className="font-medium text-blue-600">Actividades:</span>{' '}
                            {new Intl.NumberFormat('es-CO').format(payload[0].payload.total)}{' '}
                            <span className="text-gray-500">
                              ({payload[0].payload.porcentajeActividades}%)
                            </span>
                          </p>
                          <p className="text-sm">
                            <span className="font-medium text-green-600">Asistentes:</span>{' '}
                            {new Intl.NumberFormat('es-CO').format(payload[0].payload.asistentes)}{' '}
                            <span className="text-gray-500">
                              ({payload[0].payload.porcentajeAsistentes}%)
                            </span>
                          </p>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend />
              <Bar 
                dataKey="total" 
                fill="#3b82f6" 
                name="Actividades"
                radius={[4, 4, 0, 0]}
              />
              <Bar 
                dataKey="asistentes" 
                fill="#10b981" 
                name="Asistentes"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>

          {/* Tabla resumen con porcentajes */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">
              Resumen por Municipio
            </h4>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Municipio</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Actividades</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">% Act.</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">Asistentes</th>
                    <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">% Asis.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {dataWithPercentages.map((item, index) => (
                    <tr key={index} className="text-sm">
                      <td className="px-3 py-2 text-gray-900">{item.nombre}</td>
                      <td className="px-3 py-2 text-right text-gray-900">
                        {new Intl.NumberFormat('es-CO').format(item.total)}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-500">
                        {item.porcentajeActividades}%
                      </td>
                      <td className="px-3 py-2 text-right text-gray-900">
                        {new Intl.NumberFormat('es-CO').format(item.asistentes)}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-500">
                        {item.porcentajeAsistentes}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      );
    }

    // Mantener el gráfico de donut para otros niveles
    return <CustomDonutChart data={stats.grupos_interes} />;
  };

  return (
    <div className="statistics-panel">
      <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
        <div className="stats-tabs">
          <TabList className="stats-tab-list">
            {tabs.map((tab, index) => {
              const Icon = tab.icon
              return (
                <Tab
                  key={index}
                  className={({ selected }) =>
                    `stats-tab ${selected ? 'active' : ''}`
                  }
                >
                  <div className="flex items-center justify-center gap-2">
                    <Icon className="w-4 h-4" />
                    <span>{tab.name}</span>
                  </div>
                </Tab>
              )
            })}
          </TabList>
        </div>

        <div className="stats-content">
          <TabPanels>
            <TabPanel>
              <Card className="chart-container">
                <Title>Evolución Temporal</Title>
                {stats?.temporal && stats.temporal.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart
                        data={formatTemporalData(stats.temporal)}
                        margin={{
                          top: 20,
                          right: 15,
                          left: 10,
                          bottom: 60
                        }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(203, 213, 225, 0.2)" />
                        <XAxis 
                          dataKey="categoria"
                          tick={{ 
                            fill: '#1e293b', 
                            fontSize: 11,
                            angle: -45,
                            textAnchor: 'end',
                            dy: 10
                          }}
                          tickFormatter={(value) => value.split('-')[0]}
                          interval={0}
                          height={60}
                        />
                        <YAxis 
                          tick={{ fill: '#1e293b', fontSize: 12 }}
                          tickFormatter={(value) => new Intl.NumberFormat('es-CO').format(value)}
                          width={50}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="total"
                          stroke="#10b981"
                          strokeWidth={2}
                          dot={{ r: 3, strokeWidth: 2 }}
                          activeDot={{ r: 5, strokeWidth: 2 }}
                          name="Total Actividades"
                        />
                        <Line
                          type="monotone"
                          dataKey="asistentes"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={{ r: 3, strokeWidth: 2 }}
                          activeDot={{ r: 5, strokeWidth: 2 }}
                          name="Total Asistentes"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">
                        {tabs[0].description}
                      </p>
                      <ul className="mt-2 space-y-1 text-xs text-gray-500">
                        <li>La línea verde representa el número total de actividades realizadas</li>
                        <li>La línea azul muestra el total de asistentes en cada período</li>
                        <li>Los puntos permiten ver valores específicos al pasar el cursor</li>
                      </ul>
                    </div>
                  </>
                ) : (
                  <Text>No hay datos temporales disponibles</Text>
                )}
              </Card>
            </TabPanel>

            <TabPanel>
              <Card className="chart-container">
                <Title>
                  {selectedFeature?.level === 'veredas' 
                    ? 'Distribución por Municipios' 
                    : 'Distribución por Grupos de Interés'}
                </Title>
                {stats?.grupos_interes && stats.grupos_interes.length > 0 ? (
                  <>
                    {renderGruposChart()}
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">
                        {selectedFeature?.level === 'veredas'
                          ? 'Muestra la distribución de actividades y asistentes por municipio para el grupo de interés seleccionado.'
                          : 'Visualiza la distribución por grupos de interés. Cada segmento representa la proporción de actividades por grupo.'}
                      </p>
                    </div>
                  </>
                ) : (
                  <Text>No hay datos de grupos disponibles</Text>
                )}
              </Card>
            </TabPanel>

            <TabPanel>
              <Card className="chart-container">
                <Title>Distribución por Categorías</Title>
                {stats?.categoria_actividad && stats.categoria_actividad.length > 0 ? (
                  <>
                    <CustomBarChart data={stats.categoria_actividad} />
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">
                        {tabs[2].description}
                      </p>
                      <ul className="mt-2 space-y-1 text-xs text-gray-500">
                        <li>Verde: número de actividades</li>
                        <li>Azul: número de asistentes</li>
                        <li>Ordenado de mayor a menor</li>
                        <li>Hover para ver detalles</li>
                      </ul>
                    </div>
                  </>
                ) : (
                  <Text>No hay datos de categorías disponibles</Text>
                )}
              </Card>
            </TabPanel>

            <TabPanel>
              <Card>
                <Title>Resumen por Zonas Geográficas</Title>
                {stats?.zonas_geograficas && stats.zonas_geograficas.length > 0 ? (
                  <CustomStackedBarChart data={stats} />
                ) : (
                  <Text>No hay datos de zonas geográficas disponibles</Text>
                )}
              </Card>
            </TabPanel>
          </TabPanels>
        </div>
      </Tab.Group>
    </div>
  );
};

// Componente para el tooltip personalizado
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip blur-backdrop">
        <p className="tooltip-label">{`Año ${label}`}</p>
        <p className="tooltip-value">
          Actividades: {new Intl.NumberFormat('es-CO').format(payload[0].value)}
        </p>
        <p className="tooltip-value">
          Asistentes: {new Intl.NumberFormat('es-CO').format(payload[1].value)}
        </p>
      </div>
    );
  }
  return null;
};

// Agregar estilos CSS necesarios
const styles = `
  .stats-panel {
    min-height: 400px;
  }
  
  .recharts-wrapper {
    margin: 0 auto;
  }
  
  .recharts-bar-rectangle {
    fill-opacity: 0.8;
  }
  
  .recharts-bar-rectangle:hover {
    fill-opacity: 1;
  }
`;

// Exportación por defecto en lugar de nombrada
export default StatsPanel 