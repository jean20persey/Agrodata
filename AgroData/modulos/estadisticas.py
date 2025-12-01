# PASO 7.1: Módulo de Estadística II
# Archivo: modulos/estadisticas.py

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Para usar sin interfaz gráfica
import matplotlib.pyplot as plt
from scipy import stats
import io
import base64

class EstadisticasAgricolas:
    """
    Clase para análisis estadístico de datos agrícolas.
    Demuestra: Estadística II
    """
    
    def __init__(self, conexion):
        self.conexion = conexion
    
    def estadisticas_descriptivas(self):
        """
        Calcula media, mediana, desviación estándar y varianza
        de los rendimientos por hectárea.
        """
        query = """
            SELECT 
                c.nombre as cultivo,
                s.area_sembrada,
                COALESCE(SUM(co.cantidad_kg), 0) as total_kg,
                COALESCE(SUM(co.cantidad_kg) / s.area_sembrada, 0) as rendimiento
            FROM siembra s
            JOIN cultivo c ON s.id_cultivo = c.id_cultivo
            LEFT JOIN cosecha co ON s.id_siembra = co.id_siembra
            WHERE s.area_sembrada > 0
            GROUP BY s.id_siembra
        """
        
        df = pd.read_sql(query, self.conexion)
        
        if len(df) == 0:
            return None
        
        # Cálculos estadísticos básicos
        estadisticas = {
            'media': df['rendimiento'].mean(),
            'mediana': df['rendimiento'].median(),
            'desviacion_std': df['rendimiento'].std(),
            'varianza': df['rendimiento'].var(),
            'minimo': df['rendimiento'].min(),
            'maximo': df['rendimiento'].max(),
            'total_siembras': len(df)
        }
        
        return estadisticas
    
    def correlacion_insumo_rendimiento(self):
        """
        Calcula la correlación de Pearson entre cantidad de fertilizante
        aplicado y rendimiento obtenido.
        Demuestra: Análisis de correlación
        """
        query = """
            SELECT 
                s.id_siembra,
                COALESCE(SUM(ai.cantidad_aplicada), 0) as fertilizante_total,
                COALESCE(SUM(co.cantidad_kg) / s.area_sembrada, 0) as rendimiento
            FROM siembra s
            LEFT JOIN aplicacion_insumo ai ON s.id_siembra = ai.id_siembra
            LEFT JOIN insumo i ON ai.id_insumo = i.id_insumo AND i.tipo = 'fertilizante'
            LEFT JOIN cosecha co ON s.id_siembra = co.id_siembra
            WHERE s.area_sembrada > 0
            GROUP BY s.id_siembra
            HAVING fertilizante_total > 0 AND rendimiento > 0
        """
        
        df = pd.read_sql(query, self.conexion)
        
        if len(df) < 2:
            return None
        
        # Correlación de Pearson
        correlacion = df['fertilizante_total'].corr(df['rendimiento'])
        
        # Regresión lineal simple
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df['fertilizante_total'], 
            df['rendimiento']
        )
        
        return {
            'correlacion': correlacion,
            'pendiente': slope,
            'intercepto': intercept,
            'r_cuadrado': r_value**2,
            'datos': df.to_dict('records')
        }
    
    def generar_grafico_rendimientos(self):
        """
        Genera gráfico de barras con rendimiento por cultivo.
        Demuestra: Visualización con Matplotlib
        """
        query = """
            SELECT 
                c.nombre as cultivo,
                AVG(co.cantidad_kg / s.area_sembrada) as rendimiento_promedio
            FROM siembra s
            JOIN cultivo c ON s.id_cultivo = c.id_cultivo
            JOIN cosecha co ON s.id_siembra = co.id_siembra
            WHERE s.area_sembrada > 0
            GROUP BY c.id_cultivo
        """
        
        df = pd.read_sql(query, self.conexion)
        
        if len(df) == 0:
            return None
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(df['cultivo'], df['rendimiento_promedio'], color='green', alpha=0.7)
        ax.set_xlabel('Cultivo', fontsize=12)
        ax.set_ylabel('Rendimiento (kg/ha)', fontsize=12)
        ax.set_title('Rendimiento Promedio por Cultivo', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Convertir a imagen base64 para mostrar en HTML
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        grafico_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return grafico_url
    
    def generar_grafico_correlacion(self):
        """
        Genera gráfico de dispersión mostrando correlación
        entre fertilizante y rendimiento.
        """
        datos = self.correlacion_insumo_rendimiento()
        
        if not datos:
            return None
        
        df = pd.DataFrame(datos['datos'])
        
        # Crear gráfico de dispersión
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(df['fertilizante_total'], df['rendimiento'], 
                  color='blue', alpha=0.6, s=100)
        
        # Línea de regresión
        x_line = np.linspace(df['fertilizante_total'].min(), 
                            df['fertilizante_total'].max(), 100)
        y_line = datos['pendiente'] * x_line + datos['intercepto']
        ax.plot(x_line, y_line, 'r--', label=f'R² = {datos["r_cuadrado"]:.3f}')
        
        ax.set_xlabel('Fertilizante Aplicado (kg)', fontsize=12)
        ax.set_ylabel('Rendimiento (kg/ha)', fontsize=12)
        ax.set_title('Correlación: Fertilizante vs Rendimiento', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # Convertir a base64
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        grafico_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        return grafico_url