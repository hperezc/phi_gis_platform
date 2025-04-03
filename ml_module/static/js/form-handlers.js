// Funciones para cargar datos
async function cargarZonasGeograficas() {
    try {
        const response = await fetch('/ml/zonas-geograficas');
        const data = await response.json();
        
        if (data.status === 'success') {
            const select = document.getElementById('zona-geografica-select');
            select.innerHTML = '<option value="">Seleccione una zona geográfica</option>';
            
            data.data.zonas_geograficas.forEach(zona => {
                const option = document.createElement('option');
                option.value = zona;
                option.textContent = zona;
                select.appendChild(option);
            });

            // Habilitar solo el select de zona geográfica
            document.getElementById('zona-geografica-select').disabled = false;
            document.getElementById('departamento-select').disabled = true;
            document.getElementById('municipio-select').disabled = true;
        }
    } catch (error) {
        console.error('Error cargando zonas geográficas:', error);
    }
}

async function cargarDepartamentos(zona) {
    try {
        const response = await fetch(`/ml/departamentos?zona_geografica=${encodeURIComponent(zona)}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            const select = document.getElementById('departamento-select');
            select.innerHTML = '<option value="">Seleccione un departamento</option>';
            
            data.data.departamentos.forEach(departamento => {
                const option = document.createElement('option');
                option.value = departamento;
                option.textContent = departamento;
                select.appendChild(option);
            });

            // Habilitar select de departamento
            document.getElementById('departamento-select').disabled = false;
            // Deshabilitar y limpiar select de municipio
            const municipioSelect = document.getElementById('municipio-select');
            municipioSelect.disabled = true;
            municipioSelect.innerHTML = '<option value="">Seleccione un municipio</option>';
        }
    } catch (error) {
        console.error('Error cargando departamentos:', error);
    }
}

async function cargarMunicipios(departamento, zona) {
    try {
        const params = new URLSearchParams({
            departamento: departamento,
            zona_geografica: zona
        });
        
        const response = await fetch(`/ml/municipios?${params}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            const select = document.getElementById('municipio-select');
            select.innerHTML = '<option value="">Seleccione un municipio</option>';
            
            data.data.municipios.forEach(municipio => {
                const option = document.createElement('option');
                option.value = municipio;
                option.textContent = municipio;
                select.appendChild(option);
            });

            // Habilitar select de municipio
            document.getElementById('municipio-select').disabled = false;
        }
    } catch (error) {
        console.error('Error cargando municipios:', error);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Cargar zonas geográficas al iniciar
    cargarZonasGeograficas();

    // Listener para cambio de zona geográfica
    document.getElementById('zona-geografica-select').addEventListener('change', function(e) {
        const zona = e.target.value;
        if (zona) {
            cargarDepartamentos(zona);
        } else {
            // Deshabilitar y limpiar selects dependientes
            const departamentoSelect = document.getElementById('departamento-select');
            const municipioSelect = document.getElementById('municipio-select');
            
            departamentoSelect.disabled = true;
            departamentoSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
            
            municipioSelect.disabled = true;
            municipioSelect.innerHTML = '<option value="">Seleccione un municipio</option>';
        }
    });

    // Listener para cambio de departamento
    document.getElementById('departamento-select').addEventListener('change', function(e) {
        const departamento = e.target.value;
        const zona = document.getElementById('zona-geografica-select').value;
        
        if (departamento && zona) {
            cargarMunicipios(departamento, zona);
        } else {
            // Deshabilitar y limpiar select de municipio
            const municipioSelect = document.getElementById('municipio-select');
            municipioSelect.disabled = true;
            municipioSelect.innerHTML = '<option value="">Seleccione un municipio</option>';
        }
    });
}); 