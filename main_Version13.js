const datos = [
  {
    barrio: "Vicente López",
    tipoOperacion: "venta",
    tipoPropiedad: "casa",
    precio: 250000,
    ambientes: 3,
    sitio: "Zonaprop",
    link: "https://www.zonaprop.com.ar/casa-en-venta-vicente-lopez.html",
    historialPrecios: [260000, 250000]
  },
  {
    barrio: "Vicente López",
    tipoOperacion: "venta",
    tipoPropiedad: "ph",
    precio: 330000,
    ambientes: 4,
    sitio: "Argenprop",
    link: "https://www.argenprop.com/ph-en-venta-vicente-lopez.html",
    historialPrecios: [335000, 330000]
  },
  {
    barrio: "Vicente López",
    tipoOperacion: "venta",
    tipoPropiedad: "terreno",
    precio: 370000,
    ambientes: null,
    sitio: "MercadoLibre",
    link: "https://inmuebles.mercadolibre.com.ar/terreno-en-venta-vicente-lopez",
    historialPrecios: [365000, 370000]
  },
  {
    barrio: "Florida",
    tipoOperacion: "venta",
    tipoPropiedad: "casa",
    precio: 230000,
    ambientes: 2,
    sitio: "Zonaprop",
    link: "https://www.zonaprop.com.ar/casa-en-venta-florida.html",
    historialPrecios: [230000, 230000]
  },
  {
    barrio: "Florida",
    tipoOperacion: "venta",
    tipoPropiedad: "ph",
    precio: 350000,
    ambientes: 3,
    sitio: "Argenprop",
    link: "https://www.argenprop.com/ph-en-venta-florida.html",
    historialPrecios: [355000, 350000]
  },
  {
    barrio: "Florida",
    tipoOperacion: "venta",
    tipoPropiedad: "terreno",
    precio: 300000,
    ambientes: null,
    sitio: "MercadoLibre",
    link: "https://inmuebles.mercadolibre.com.ar/terreno-en-venta-florida",
    historialPrecios: [310000, 300000]
  },
  {
    barrio: "La Lucila",
    tipoOperacion: "venta",
    tipoPropiedad: "casa",
    precio: 300000,
    ambientes: 4,
    sitio: "Zonaprop",
    link: "https://www.zonaprop.com.ar/casa-en-venta-la-lucila.html",
    historialPrecios: [295000, 300000]
  },
  {
    barrio: "La Lucila",
    tipoOperacion: "venta",
    tipoPropiedad: "ph",
    precio: 220000,
    ambientes: 2,
    sitio: "Argenprop",
    link: "https://www.argenprop.com/ph-en-venta-la-lucila.html",
    historialPrecios: [220000, 220000]
  },
  {
    barrio: "La Lucila",
    tipoOperacion: "venta",
    tipoPropiedad: "terreno",
    precio: 380000,
    ambientes: null,
    sitio: "MercadoLibre",
    link: "https://inmuebles.mercadolibre.com.ar/terreno-en-venta-la-lucila",
    historialPrecios: [385000, 380000]
  }
];

function variacionPrecio(historial) {
  const antes = historial[0], ahora = historial[historial.length - 1];
  if (antes < ahora) return "Subió";
  if (antes > ahora) return "Bajó";
  return "Sin cambios";
}

function mostrarDatos() {
  const barrioSeleccionado = document.getElementById('barrio').value;
  const tipoOperacionSeleccionado = document.getElementById('tipoOperacion').value;
  const tipoPropiedadSeleccionado = document.getElementById('tipoPropiedad').value;
  const precioMin = parseInt(document.getElementById('precioMin').value, 10);
  const precioMax = parseInt(document.getElementById('precioMax').value, 10);

  const filtrados = datos.filter(d =>
    d.barrio === barrioSeleccionado &&
    d.tipoOperacion === tipoOperacionSeleccionado &&
    d.tipoPropiedad === tipoPropiedadSeleccionado &&
    d.precio >= precioMin &&
    d.precio <= precioMax
  );

  const contenidoDiv = document.getElementById('contenido');

  if (filtrados.length === 0) {
    contenidoDiv.innerHTML = `<div class="alert alert-warning">No hay propiedades para los criterios seleccionados.</div>`;
    return;
  }

  contenidoDiv.innerHTML = `
    <div class="card">
      <div class="card-header bg-primary text-white">Propiedades en ${barrioSeleccionado}</div>
      <div class="card-body p-0">
        <table class="table mb-0 table-striped align-middle">
          <thead>
            <tr>
              <th>Sitio</th>
              <th>Barrio</th>
              <th>Tipo de operación</th>
              <th>Tipo de propiedad</th>
              <th>Ambientes</th>
              <th>Precio</th>
              <th>Variación 45 días</th>
            </tr>
          </thead>
          <tbody>
            ${filtrados.map(d =>
              `<tr>
                <td><a href="${d.link}" target="_blank">${d.sitio}</a></td>
                <td>${d.barrio}</td>
                <td>${d.tipoOperacion}</td>
                <td>${d.tipoPropiedad}</td>
                <td>${d.ambientes ?? '-'}</td>
                <td>USD ${d.precio.toLocaleString()}</td>
                <td>${variacionPrecio(d.historialPrecios)}</td>
              </tr>`
            ).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

document.querySelectorAll('#filtros select, #filtros input').forEach(el => {
  el.addEventListener('change', mostrarDatos);
  el.addEventListener('input', mostrarDatos);
});

mostrarDatos();