// Modal toggle
function toggleModal(id) {
  const el = document.getElementById(id);
  el.classList.toggle('open');
}

// Close modal on outside click
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// Auto-dismiss alerts after 4s
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity 0.5s'; setTimeout(() => el.remove(), 500); }, 4000);
});

// Add enumerate support via Jinja2 loop (no JS needed)
// Chart.js default font
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = "'Segoe UI', sans-serif";
  Chart.defaults.font.size   = 12;
  Chart.defaults.color       = '#888';
}
