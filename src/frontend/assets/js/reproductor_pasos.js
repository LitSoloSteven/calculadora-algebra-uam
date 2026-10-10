/** Interacciones compartidas de explicación y feedback del reproductor. */
window.scalarisPasos = {
  revelar(id, texto) {
    const elemento = document.getElementById(id);
    if (!elemento) return;
    if (window.scalarisMotionOK && window.scalarisMotionOK() && window.typewriterEffect) {
      window.typewriterEffect(id, texto, 12);
      return;
    }
    elemento.textContent = texto;
  },
  destellar(id) {
    const elemento = document.getElementById(id);
    if (!elemento || !window.scalarisMotionOK || !window.scalarisMotionOK()) return;
    elemento.animate(
      [{ opacity: 0.55, transform: 'translateY(6px)' }, { opacity: 1, transform: 'translateY(0)' }],
      { duration: 180, easing: 'cubic-bezier(0.32, 0.72, 0, 1)' }
    );
  }
};
