// Actualizar el componente MapUpdater
const MapUpdater = ({ layers, geometries, getLayerStyle, onEachFeature }) => {
  return (
    <>
      {Object.entries(layers).map(([layerId, layer]) => {
        if (layer.visible && geometries[layerId] && layerId !== 'baseMaps') {
          if (['puntos_encuentro', 'senales_evacuacion'].includes(layerId)) {
            return geometries[layerId].features.map((feature, index) => (
              <CircleMarker
                key={`${layerId}-${index}`}
                center={[
                  feature.geometry.coordinates[1],
                  feature.geometry.coordinates[0]
                ]}
                {...getLayerStyle(layerId, feature)}
                eventHandlers={{
                  mouseover: (e) => {
                    const layer = e.target;
                    layer.setStyle({
                      radius: layerId === 'puntos_encuentro' ? 10 : 8,
                      fillOpacity: 1
                    });
                  },
                  mouseout: (e) => {
                    const layer = e.target;
                    layer.setStyle(getLayerStyle(layerId, feature));
                  },
                  click: (e) => onEachFeature(feature, e.target, layerId)
                }}
              />
            ));
          } else {
            return (
              <GeoJSON
                key={`${layerId}-${layer.visible}-${JSON.stringify(layer.subTypes)}`}
                data={geometries[layerId]}
                style={(feature) => getLayerStyle(layerId, feature)}
                onEachFeature={(feature, layer) => onEachFeature(feature, layer, layerId)}
                pane="vias"
              />
            );
          }
        }
        return null;
      })}
    </>
  );
}
