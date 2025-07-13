// Arreglo de productos iniciales
let productos = [
  {
    nombre: "Lapicero Azul",
    precio: "$0.50",
    descripcion: "Ideal para escritura diaria."
  },
  {
    nombre: "Cuaderno Profesional",
    precio: "$2.00",
    descripcion: "96 hojas cuadriculadas."
  },
  {
    nombre: "Resaltador Amarillo",
    precio: "$0.80",
    descripcion: "Perfecto para subrayar textos importantes."
  }
];

// Función para renderizar los productos en la lista <ul>
function renderizarProductos() {
  const lista = document.getElementById("lista-productos");
  lista.innerHTML = ""; // Limpiar contenido anterior

  productos.forEach((producto) => {
    const item = document.createElement("li");
    item.innerHTML = `
      <strong>${producto.nombre}</strong> - ${producto.precio}<br />
      <em>${producto.descripcion}</em>
    `;
    lista.appendChild(item);
  });
}

// Evento para agregar un nuevo producto
document.getElementById("btn-agregar").addEventListener("click", () => {
  // Producto de ejemplo (se puede cambiar para usar prompt o formularios)
  const nuevoProducto = {
    nombre: "Producto Nuevo",
    precio: "$1.00",
    descripcion: "Descripción del producto nuevo."
  };

  productos.push(nuevoProducto);
  renderizarProductos(); // Volver a renderizar la lista
});

// Renderizar automáticamente al cargar la página
window.addEventListener("DOMContentLoaded", renderizarProductos);
