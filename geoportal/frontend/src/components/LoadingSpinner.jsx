const LoadingSpinner = () => {
  return (
    <div className="loading-overlay">
      <div className="loading-spinner">
        <div className="spinner-ring"></div>
        <span className="text-gray-700 font-medium">Cargando...</span>
      </div>
    </div>
  );
};

export default LoadingSpinner; 