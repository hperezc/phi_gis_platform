import React from 'react';
import { StatisticsPanel } from './StatisticsPanel';
// ... otros imports ...

export const Sidebar = ({ 
    selectedFeature, 
    currentLevel,
    // ... otras props existentes ...
}) => {
    return (
        <div className="sidebar">
            <div className="sidebar-content">
                {/* ... otros componentes existentes ... */}
                
                <div className="sidebar-section">
                    <h2>Estadísticas</h2>
                    <StatisticsPanel 
                        selectedFeature={selectedFeature}
                        currentLevel={currentLevel}
                    />
                </div>
            </div>
        </div>
    );
}; 