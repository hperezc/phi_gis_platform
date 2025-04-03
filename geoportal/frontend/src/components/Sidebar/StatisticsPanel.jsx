import React, { useEffect, useState } from 'react';
import { Statistics } from '../Statistics/Statistics';
import { api } from '../../services/api';
import { Spinner } from '../UI/Spinner';

export const StatisticsPanel = ({ selectedFeature, currentLevel }) => {
    const [statistics, setStatistics] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStatistics = async () => {
            if (!selectedFeature || !currentLevel) return;

            setLoading(true);
            setError(null);

            try {
                const geometryId = selectedFeature.properties.id || selectedFeature.properties.nombre;
                const data = await api.getStatistics(currentLevel, geometryId);
                setStatistics(data);
            } catch (err) {
                setError('Error al cargar las estadísticas');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchStatistics();
    }, [selectedFeature, currentLevel]);

    if (!selectedFeature) {
        return <div className="statistics-message">Selecciona una región para ver estadísticas</div>;
    }

    if (loading) {
        return <Spinner />;
    }

    if (error) {
        return <div className="statistics-error">{error}</div>;
    }

    return (
        <div className="statistics-panel">
            <h2>Estadísticas de {selectedFeature.properties.nombre}</h2>
            {statistics && <Statistics data={statistics} />}
        </div>
    );
}; 