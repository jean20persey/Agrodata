# PASO 7.3: Módulo de Métodos Numéricos
# Archivo: modulos/metodos_numericos.py

import numpy as np
from scipy import interpolate

class MetodosNumericos:
    """
    Clase para aplicar métodos numéricos en predicciones agrícolas.
    Demuestra: Métodos Numéricos
    """
    
    @staticmethod
    def interpolacion_lagrange(fechas, producciones, fecha_nueva):
        """
        Interpolación de Lagrange para estimar producción en una fecha.
        
        Parámetros:
        - fechas: lista de días desde siembra (ej: [30, 60, 90])
        - producciones: lista de kg cosechados en esas fechas
        - fecha_nueva: día para el cual queremos estimar
        
        Retorna: producción estimada en kg
        
        Demuestra: Interpolación polinomial
        """
        n = len(fechas)
        resultado = 0.0
        
        # Fórmula de Lagrange
        for i in range(n):
            termino = producciones[i]
            for j in range(n):
                if i != j:
                    termino *= (fecha_nueva - fechas[j]) / (fechas[i] - fechas[j])
            resultado += termino
        
        return max(0, resultado)  # No puede ser negativo
    
    @staticmethod
    def interpolacion_cubica(fechas, producciones, fecha_nueva):
        """
        Interpolación cúbica (spline) para estimaciones más suaves.
        Usa scipy para mayor precisión.
        
        Demuestra: Splines cúbicos
        """
        if len(fechas) < 3:
            return None

        # 1) Agregar puntos con el mismo día (x) promediando su producción (y)
        #    y ordenar por día para cumplir requisitos de interp1d
        acumulado = {}
        conteo = {}
        for x, y in zip(fechas, producciones):
            if x is None or y is None:
                continue
            x = float(x)
            y = float(y)
            acumulado[x] = acumulado.get(x, 0.0) + y
            conteo[x] = conteo.get(x, 0) + 1

        if not acumulado:
            return None

        x_uniq = sorted(acumulado.keys())
        y_uniq = [acumulado[x] / conteo[x] for x in x_uniq]

        # 2) Si hay menos de 3 puntos únicos, usar aproximación más simple
        if len(x_uniq) < 3:
            try:
                # Interpolación lineal con numpy
                estim = float(np.interp(fecha_nueva, x_uniq, y_uniq))
                return max(0, estim)
            except Exception:
                return None

        # 3) Interpolación cúbica con puntos únicos y ordenados
        f_cubica = interpolate.interp1d(x_uniq, y_uniq, kind='cubic', fill_value='extrapolate')
        estimacion = float(f_cubica(fecha_nueva))
        return max(0, estimacion)
    
    @staticmethod
    def metodo_biseccion(func, a, b, tolerancia=0.01, max_iter=100):
        """
        Método de bisección para encontrar raíces de ecuaciones.
        Útil para calcular punto de equilibrio (costos = ingresos).
        
        Parámetros:
        - func: función f(x) = 0 que queremos resolver
        - a, b: intervalo inicial [a, b]
        - tolerancia: error máximo aceptable
        - max_iter: máximo número de iteraciones
        
        Retorna: valor de x donde f(x) ≈ 0
        
        Demuestra: Métodos numéricos para ecuaciones no lineales
        """
        if func(a) * func(b) > 0:
            return None  # No hay cambio de signo
        
        iteracion = 0
        while (b - a) / 2 > tolerancia and iteracion < max_iter:
            c = (a + b) / 2
            if func(c) == 0:
                return c
            elif func(a) * func(c) < 0:
                b = c
            else:
                a = c
            iteracion += 1
        
        return (a + b) / 2
    
    @staticmethod
    def calcular_punto_equilibrio(costo_fijo, costo_variable, precio_venta):
        """
        Calcula cantidad a producir para alcanzar punto de equilibrio.
        Usa método de bisección.
        
        Fórmula: Ingresos - Costos = 0
        precio_venta * Q - (costo_fijo + costo_variable * Q) = 0
        
        Retorna: cantidad en kg necesaria para no tener pérdidas
        """
        # Definir función: Ingreso - Costo = 0
        def funcion_equilibrio(cantidad):
            ingresos = precio_venta * cantidad
            costos = costo_fijo + (costo_variable * cantidad)
            return ingresos - costos
        
        # Buscar en rango [0, 10000] kg
        punto = MetodosNumericos.metodo_biseccion(funcion_equilibrio, 0, 10000)
        return punto
    
    @staticmethod
    def proyectar_produccion(datos_historicos, dias_futuros):
        """
        Proyecta producción futura usando interpolación.
        
        Parámetros:
        - datos_historicos: lista de diccionarios con 'dia' y 'kg'
        - dias_futuros: lista de días para proyectar
        
        Retorna: lista de proyecciones
        """
        if len(datos_historicos) < 2:
            return None
        
        fechas = [d['dia'] for d in datos_historicos]
        producciones = [d['kg'] for d in datos_historicos]
        
        proyecciones = []
        for dia in dias_futuros:
            if len(fechas) >= 3:
                # Usar interpolación cúbica si hay suficientes datos
                estimacion = MetodosNumericos.interpolacion_cubica(
                    fechas, producciones, dia
                )
            else:
                # Usar Lagrange para pocos datos
                estimacion = MetodosNumericos.interpolacion_lagrange(
                    fechas, producciones, dia
                )
            
            proyecciones.append({
                'dia': dia,
                'kg_estimado': round(estimacion, 2) if estimacion else 0
            })
        
        return proyecciones
    
    @staticmethod
    def calcular_tendencia_lineal(fechas, valores):
        """
        Calcula tendencia lineal usando mínimos cuadrados.
        
        Retorna: pendiente y ordenada al origen
        Demuestra: Ajuste de curvas
        """
        n = len(fechas)
        if n < 2:
            return None, None
        
        # Convertir a arrays numpy
        x = np.array(fechas)
        y = np.array(valores)
        
        # Calcular pendiente (m) y ordenada (b) de y = mx + b
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerador = np.sum((x - x_mean) * (y - y_mean))
        denominador = np.sum((x - x_mean) ** 2)
        
        if denominador == 0:
            return None, None
        
        m = numerador / denominador
        b = y_mean - m * x_mean
        
        return m, b