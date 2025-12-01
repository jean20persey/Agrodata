# PASO 7.4: Módulo de Análisis y Diseño de Algoritmos
# Archivo: modulos/algoritmos.py

import time

class Algoritmos:
    """
    Clase con algoritmos de búsqueda y ordenamiento optimizados.
    Demuestra: Análisis y Diseño de Algoritmos
    """
    
    @staticmethod
    def busqueda_lineal(lista, objetivo, clave='id'):
        """
        Búsqueda lineal - O(n)
        Recorre toda la lista hasta encontrar el elemento.
        """
        inicio = time.time()
        
        for i, elemento in enumerate(lista):
            if elemento.get(clave) == objetivo:
                tiempo = time.time() - inicio
                return {'encontrado': True, 'indice': i, 'tiempo': tiempo}
        
        tiempo = time.time() - inicio
        return {'encontrado': False, 'indice': -1, 'tiempo': tiempo}
    
    @staticmethod
    def busqueda_binaria(lista_ordenada, objetivo, clave='id'):
        """
        Búsqueda binaria - O(log n)
        Requiere lista ordenada. Divide el espacio de búsqueda a la mitad.
        Mucho más eficiente que búsqueda lineal para listas grandes.
        """
        inicio = time.time()
        
        izq = 0
        der = len(lista_ordenada) - 1
        comparaciones = 0
        
        while izq <= der:
            comparaciones += 1
            medio = (izq + der) // 2
            valor_medio = lista_ordenada[medio].get(clave)
            
            if valor_medio == objetivo:
                tiempo = time.time() - inicio
                return {
                    'encontrado': True,
                    'indice': medio,
                    'tiempo': tiempo,
                    'comparaciones': comparaciones
                }
            elif valor_medio < objetivo:
                izq = medio + 1
            else:
                der = medio - 1
        
        tiempo = time.time() - inicio
        return {
            'encontrado': False,
            'indice': -1,
            'tiempo': tiempo,
            'comparaciones': comparaciones
        }
    
    @staticmethod
    def quicksort(lista, clave='rendimiento', ascendente=True):
        """
        Algoritmo QuickSort - O(n log n) en promedio
        Ordenamiento eficiente por división y conquista.
        
        Parámetros:
        - lista: lista de diccionarios a ordenar
        - clave: campo por el cual ordenar
        - ascendente: True para menor a mayor, False para mayor a menor
        """
        if len(lista) <= 1:
            return lista
        
        # Elegir pivote (elemento del medio)
        pivote = lista[len(lista) // 2].get(clave, 0)
        
        # Dividir en tres grupos
        menores = [x for x in lista if x.get(clave, 0) < pivote]
        iguales = [x for x in lista if x.get(clave, 0) == pivote]
        mayores = [x for x in lista if x.get(clave, 0) > pivote]
        
        # Recursión y combinación
        if ascendente:
            return (Algoritmos.quicksort(menores, clave, ascendente) + 
                   iguales + 
                   Algoritmos.quicksort(mayores, clave, ascendente))
        else:
            return (Algoritmos.quicksort(mayores, clave, ascendente) + 
                   iguales + 
                   Algoritmos.quicksort(menores, clave, ascendente))
    
    @staticmethod
    def merge_sort(lista, clave='fecha'):
        """
        Algoritmo MergeSort - O(n log n) garantizado
        Ordenamiento estable por fusión.
        Mejor que QuickSort en el peor caso.
        """
        if len(lista) <= 1:
            return lista
        
        # Dividir la lista a la mitad
        medio = len(lista) // 2
        izquierda = lista[:medio]
        derecha = lista[medio:]
        
        # Recursión
        izquierda = Algoritmos.merge_sort(izquierda, clave)
        derecha = Algoritmos.merge_sort(derecha, clave)
        
        # Fusionar
        return Algoritmos._merge(izquierda, derecha, clave)
    
    @staticmethod
    def _merge(izq, der, clave):
        """Función auxiliar para fusionar dos listas ordenadas"""
        resultado = []
        i = j = 0
        
        while i < len(izq) and j < len(der):
            if izq[i].get(clave, '') <= der[j].get(clave, ''):
                resultado.append(izq[i])
                i += 1
            else:
                resultado.append(der[j])
                j += 1
        
        resultado.extend(izq[i:])
        resultado.extend(der[j:])
        
        return resultado
    
    @staticmethod
    def comparar_algoritmos_busqueda(lista, objetivo):
        """
        Compara el rendimiento de búsqueda lineal vs binaria.
        Útil para demostrar diferencias de complejidad.
        """
        # Búsqueda lineal
        resultado_lineal = Algoritmos.busqueda_lineal(lista, objetivo, 'id_siembra')
        
        # Ordenar lista para búsqueda binaria
        lista_ordenada = sorted(lista, key=lambda x: x.get('id_siembra', 0))
        
        # Búsqueda binaria
        resultado_binaria = Algoritmos.busqueda_binaria(lista_ordenada, objetivo, 'id_siembra')
        
        return {
            'lineal': resultado_lineal,
            'binaria': resultado_binaria,
            'mejora': (resultado_lineal['tiempo'] / resultado_binaria['tiempo'] 
                      if resultado_binaria['tiempo'] > 0 else 0)
        }
    
    @staticmethod
    def ranking_lotes(lotes_data):
        """
        Genera ranking de mejores lotes por rendimiento usando QuickSort.
        Retorna top 5 lotes más productivos.
        """
        if not lotes_data:
            return []
        
        # Ordenar de mayor a menor rendimiento
        lotes_ordenados = Algoritmos.quicksort(lotes_data, 'rendimiento', ascendente=False)
        
        # Retornar top 5
        return lotes_ordenados[:5]
    
    @staticmethod
    def buscar_siembras_por_rango_fecha(siembras, fecha_inicio, fecha_fin):
        """
        Busca siembras en un rango de fechas usando búsqueda binaria.
        Lista debe estar ordenada por fecha.
        """
        # Ordenar por fecha
        siembras_ordenadas = Algoritmos.merge_sort(siembras, 'fecha_siembra')
        
        resultados = []
        for siembra in siembras_ordenadas:
            fecha = siembra.get('fecha_siembra', '')
            if fecha_inicio <= fecha <= fecha_fin:
                resultados.append(siembra)
            elif fecha > fecha_fin:
                break  # Ya no hay más en el rango
        
        return resultados