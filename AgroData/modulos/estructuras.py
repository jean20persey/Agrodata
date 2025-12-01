# PASO 7.2: Módulo de Estructura de Datos
# Archivo: modulos/estructuras.py

class NodoSiembra:
    """
    Nodo para lista enlazada de siembras.
    Demuestra: Estructura de Datos - Lista Enlazada
    """
    def __init__(self, datos_siembra):
        self.datos = datos_siembra
        self.siguiente = None

class ListaEnlazadaSiembras:
    """
    Lista enlazada para gestionar historial de siembras.
    Permite insertar, buscar y recorrer siembras de forma eficiente.
    """
    def __init__(self):
        self.cabeza = None
        self.tamaño = 0
    
    def agregar_siembra(self, datos_siembra):
        """Agrega una siembra al inicio de la lista - O(1)"""
        nuevo_nodo = NodoSiembra(datos_siembra)
        nuevo_nodo.siguiente = self.cabeza
        self.cabeza = nuevo_nodo
        self.tamaño += 1
    
    def buscar_por_id(self, id_siembra):
        """Busca una siembra por ID - O(n)"""
        actual = self.cabeza
        while actual:
            if actual.datos['id_siembra'] == id_siembra:
                return actual.datos
            actual = actual.siguiente
        return None
    
    def obtener_todas(self):
        """Retorna todas las siembras como lista - O(n)"""
        siembras = []
        actual = self.cabeza
        while actual:
            siembras.append(actual.datos)
            actual = actual.siguiente
        return siembras
    
    def eliminar_siembra(self, id_siembra):
        """Elimina una siembra por ID - O(n)"""
        if not self.cabeza:
            return False
        
        # Si es el primer nodo
        if self.cabeza.datos['id_siembra'] == id_siembra:
            self.cabeza = self.cabeza.siguiente
            self.tamaño -= 1
            return True
        
        # Buscar en el resto de la lista
        actual = self.cabeza
        while actual.siguiente:
            if actual.siguiente.datos['id_siembra'] == id_siembra:
                actual.siguiente = actual.siguiente.siguiente
                self.tamaño -= 1
                return True
            actual = actual.siguiente
        
        return False


class NodoArbol:
    """
    Nodo para árbol binario de búsqueda.
    Demuestra: Estructura de Datos - Árbol Binario
    """
    def __init__(self, cultivo, rendimiento):
        self.cultivo = cultivo
        self.rendimiento = rendimiento
        self.izquierdo = None
        self.derecho = None

class ArbolBinarioCultivos:
    """
    Árbol binario de búsqueda para organizar cultivos por rendimiento.
    Permite búsquedas eficientes - O(log n) en promedio.
    """
    def __init__(self):
        self.raiz = None
    
    def insertar(self, cultivo, rendimiento):
        """Inserta un cultivo en el árbol ordenado por rendimiento"""
        if not self.raiz:
            self.raiz = NodoArbol(cultivo, rendimiento)
        else:
            self._insertar_recursivo(self.raiz, cultivo, rendimiento)
    
    def _insertar_recursivo(self, nodo, cultivo, rendimiento):
        """Función auxiliar recursiva para insertar"""
        if rendimiento < nodo.rendimiento:
            if nodo.izquierdo is None:
                nodo.izquierdo = NodoArbol(cultivo, rendimiento)
            else:
                self._insertar_recursivo(nodo.izquierdo, cultivo, rendimiento)
        else:
            if nodo.derecho is None:
                nodo.derecho = NodoArbol(cultivo, rendimiento)
            else:
                self._insertar_recursivo(nodo.derecho, cultivo, rendimiento)
    
    def buscar(self, rendimiento_objetivo):
        """Busca cultivos con rendimiento específico - O(log n)"""
        return self._buscar_recursivo(self.raiz, rendimiento_objetivo)
    
    def _buscar_recursivo(self, nodo, rendimiento_objetivo):
        """Función auxiliar recursiva para buscar"""
        if nodo is None:
            return None
        
        if abs(nodo.rendimiento - rendimiento_objetivo) < 100:  # Tolerancia
            return {'cultivo': nodo.cultivo, 'rendimiento': nodo.rendimiento}
        
        if rendimiento_objetivo < nodo.rendimiento:
            return self._buscar_recursivo(nodo.izquierdo, rendimiento_objetivo)
        else:
            return self._buscar_recursivo(nodo.derecho, rendimiento_objetivo)
    
    def recorrido_inorden(self):
        """Recorre el árbol en orden (menor a mayor rendimiento)"""
        resultado = []
        self._inorden_recursivo(self.raiz, resultado)
        return resultado
    
    def _inorden_recursivo(self, nodo, resultado):
        """Función auxiliar para recorrido inorden"""
        if nodo:
            self._inorden_recursivo(nodo.izquierdo, resultado)
            resultado.append({'cultivo': nodo.cultivo, 'rendimiento': nodo.rendimiento})
            self._inorden_recursivo(nodo.derecho, resultado)


class ColaPrioridadAlertas:
    """
    Cola de prioridad (Min-Heap) para gestionar alertas.
    Demuestra: Estructura de Datos - Heap
    Las alertas con mayor prioridad (menor número) se procesan primero.
    """
    def __init__(self):
        self.heap = []
    
    def agregar_alerta(self, prioridad, mensaje, id_siembra):
        """Agrega una alerta con prioridad - O(log n)"""
        alerta = {
            'prioridad': prioridad,
            'mensaje': mensaje,
            'id_siembra': id_siembra
        }
        self.heap.append(alerta)
        self._subir(len(self.heap) - 1)
    
    def _subir(self, indice):
        """Mueve un elemento hacia arriba para mantener propiedad del heap"""
        padre = (indice - 1) // 2
        if indice > 0 and self.heap[indice]['prioridad'] < self.heap[padre]['prioridad']:
            self.heap[indice], self.heap[padre] = self.heap[padre], self.heap[indice]
            self._subir(padre)
    
    def extraer_alerta_urgente(self):
        """Extrae la alerta más urgente (mayor prioridad) - O(log n)"""
        if not self.heap:
            return None
        
        if len(self.heap) == 1:
            return self.heap.pop()
        
        alerta_urgente = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._bajar(0)
        
        return alerta_urgente
    
    def _bajar(self, indice):
        """Mueve un elemento hacia abajo para mantener propiedad del heap"""
        menor = indice
        izq = 2 * indice + 1
        der = 2 * indice + 2
        
        if izq < len(self.heap) and self.heap[izq]['prioridad'] < self.heap[menor]['prioridad']:
            menor = izq
        
        if der < len(self.heap) and self.heap[der]['prioridad'] < self.heap[menor]['prioridad']:
            menor = der
        
        if menor != indice:
            self.heap[indice], self.heap[menor] = self.heap[menor], self.heap[indice]
            self._bajar(menor)
    
    def obtener_todas(self):
        """Retorna todas las alertas sin extraerlas"""
        return sorted(self.heap, key=lambda x: x['prioridad'])
    
    def esta_vacia(self):
        """Verifica si la cola está vacía"""
        return len(self.heap) == 0