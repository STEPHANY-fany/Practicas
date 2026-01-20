# Practicas

## Grafo semántico de sinonimia y antonimia en español

En este trabajo se presenta la construcción de un **grafo semántico** que modela de manera visual las relaciones léxicas de **sinonimia** y **antonimia** en la lengua española.  
El grafo se genera de forma automática mediante la **extracción de información léxica**, y el **almacenamiento persistente** de palabras y relaciones en una base de datos, permitiendo su posterior visualización interactiva.

El objetivo principal del proyecto es facilitar la exploración visual de relaciones semánticas entre palabras, apoyando el análisis lingüístico y aplicaciones en procesamiento del lenguaje natural (PLN).

---

## Características principales

- Extracción automática de palabras, sinónimos y antónimos.
- Construcción de un grafo semántico usando nodos y relaciones.
- Persistencia de datos en base de datos.
- Visualización interactiva del grafo en HTML.
- Búsqueda dinámica de palabras dentro del grafo.

---

## Tecnologías utilizadas

- **Python** (extracción y procesamiento léxico)
- **NetworkX / PyVis** (modelado y visualización del grafo)
- **HTML + JavaScript** (interfaz interactiva)
- **Base de datos** (persistencia de palabras y relaciones)

---

## Estructura del proyecto



### Código agregado al archivo HTML

La siguiente sección debe agregarse **antes de la etiqueta `<body>`** en el archivo HTML del grafo:

```html
<div style="position: fixed; top: 15px; left: 15px; z-index: 999;">
  <input id="buscarNodo" placeholder="Buscar palabra..."
         style="padding:8px;font-size:14px;">
  <button onclick="buscar()">Buscar</button>
</div>

<script>
function buscar() {
  let palabra = document.getElementById("buscarNodo").value.toLowerCase();
  let nodes = network.body.data.nodes.get();

  nodes.forEach(n => {
    if (n.label.toLowerCase() === palabra) {
      network.focus(n.id, {scale: 1.8});
      network.selectNodes([n.id]);
    }
  });
}
</script>
