function mostrarAlerta() {
  alert("¡Gracias por visitar nuestra página!");
}

document.getElementById('contactForm').addEventListener('submit', function(event) {
  event.preventDefault();

  let valido = true;

  const nombre = document.getElementById('nombre');
  const correo = document.getElementById('correo');
  const mensaje = document.getElementById('mensaje');

  if (!nombre.value.trim()) {
    nombre.classList.add('is-invalid');
    valido = false;
  } else {
    nombre.classList.remove('is-invalid');
  }

  if (!correo.value.match(/^[^@]+@[^@]+\.[a-zA-Z]{2,}$/)) {
    correo.classList.add('is-invalid');
    valido = false;
  } else {
    correo.classList.remove('is-invalid');
  }

  if (!mensaje.value.trim()) {
    mensaje.classList.add('is-invalid');
    valido = false;
  } else {
    mensaje.classList.remove('is-invalid');
  }

  if (valido) {
    alert('Formulario enviado correctamente.');
    this.reset();
  }
});
