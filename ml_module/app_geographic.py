def show_detailed_analysis(df: pd.DataFrame):
    """Muestra análisis detallado con gráficos mejorados e informativos"""
    try:
        # Crear dos columnas para mostrar métricas generales
        col1, col2 = st.columns(2)
        
        with col1:
            # Métricas generales
            st.write("### 📈 Métricas Generales")
            total_actividades = int(df['num_actividades'].sum())
            total_asistentes = int(df['total_asistentes'].sum())
            promedio_eficiencia = float(df['eficiencia_actividad'].mean())
            
            st.metric(
                "Total Actividades", 
                f"{total_actividades:,}",
                f"{len(df)} municipios"
            )
            st.metric(
                "Total Asistentes", 
                f"{total_asistentes:,}",
                f"{promedio_eficiencia:.1f} asistentes/actividad"
            )
            
            # Distribución por departamento
            st.write("### 🗺️ Distribución por Departamento")
            
            # ... (mantener el resto del código de visualizaciones departamentales)
            
        with col2:
            # ... (mantener el código de visualizaciones de top municipios)
            
        # REMOVER LA SECCIÓN DE PRIORIZACIÓN DE GRUPOS DE INTERÉS DUPLICADA
        # Eliminar o comentar el código que genera la primera tabla de priorización
        
        # Mantener solo las visualizaciones generales y dejar que la priorización 
        # de grupos de interés se maneje exclusivamente en show_interest_group_prioritization
        
        # ... (mantener el resto de las visualizaciones generales)
        
    except Exception as e:
        logger.error(f"Error en análisis detallado: {str(e)}")
        st.error(f"Error en análisis detallado: {str(e)}")

def main():
    try:
        # ... (código existente)
        
        # Modificar la estructura de pestañas para separar mejor el análisis
        if st.session_state.analysis_done and st.session_state.results is not None:
            results = st.session_state.results
            maps = st.session_state.maps
            viz_data = st.session_state.viz_data
            
            # Reorganizar las pestañas para mejor separación de contenido
            tab_geo, tab_grupos, tab_detalle = st.tabs([
                "Análisis Geográfico",
                "Priorización de Grupos", 
                "Análisis Detallado"
            ])
            
            with tab_geo:
                try:
                    show_analysis(results, viz_data, maps)
                except Exception as e:
                    logger.error(f"Error mostrando análisis geográfico: {str(e)}")
                    st.error(f"Error mostrando análisis geográfico: {str(e)}")
            
            with tab_grupos:
                try:
                    # Mover la priorización de grupos a su propia pestaña
                    show_interest_group_prioritization(results)
                except Exception as e:
                    logger.error(f"Error mostrando priorización de grupos: {str(e)}")
                    st.error(f"Error mostrando priorización de grupos: {str(e)}")
            
            with tab_detalle:
                try:
                    st.subheader("📋 Análisis Detallado por Municipio", divider="blue")
                    show_detailed_analysis(results['data'])
                except Exception as e:
                    logger.error(f"Error mostrando análisis detallado: {str(e)}")
                    st.error(f"Error mostrando análisis detallado: {str(e)}")
                    
        # ... (resto del código existente)
        
    except Exception as e:
        logger.error(f"Error en la aplicación: {str(e)}")
        st.error("Ocurrió un error inesperado. Por favor, intenta de nuevo.") 