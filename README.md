# Practicas
En este trabajo se presenta la construcción de un grafo semántico que modela de manera visual las relaciones léxicas de sinonimia y antonimia en la lengua española. El grafo se genera de forma automática mediante la extracción de información léxica y el almacenamiento persistente de palabras y relaciones en una base de datos


#Sección a agregar en el archivo html dle grafo 

Agregar antes de la sección body 

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
