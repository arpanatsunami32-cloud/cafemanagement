// main.js — Client-side interactions for Cafe Management System

// ── Auto-dismiss flash messages after 3 seconds ──────────────
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(flash => {
    setTimeout(() => {
      flash.style.transition = 'opacity 0.4s ease';
      flash.style.opacity = '0';
      setTimeout(() => flash.remove(), 400);
    }, 3000);
  });
});

// ── Modal Open/Close ──────────────────────────────────────────
// Opens a modal by its ID
function openModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) {
    overlay.classList.add('open');
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
  }
}

// Closes a modal by its ID
function closeModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Close modal when clicking outside (on the overlay)
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// ── Populate Edit Modals ──────────────────────────────────────
// Pre-fills edit form fields with data from the row being edited

function editMenuItem(id, name, price, category, description, available) {
  document.getElementById('edit_item_id').value = id;
  document.getElementById('edit_item_name').value = name;
  document.getElementById('edit_price').value = price;
  document.getElementById('edit_category').value = category;
  document.getElementById('edit_description').value = description;
  document.getElementById('edit_available').checked = available === 'True';
  // Update form action to point to the right item
  document.getElementById('edit_item_form').action = `/menu/edit/${id}`;
  openModal('modal-edit-item');
}

function editStaff(id, name, position, contact) {
  document.getElementById('edit_staff_id').value = id;
  document.getElementById('edit_staff_name').value = name;
  document.getElementById('edit_staff_position').value = position;
  document.getElementById('edit_staff_contact').value = contact;
  document.getElementById('edit_staff_form').action = `/staff/edit/${id}`;
  openModal('modal-edit-staff');
}

// ── Confirm Delete ────────────────────────────────────────────
// Stop event propagation so the modal-overlay click listener
// doesn't fire and swallow the action. Then confirm and submit.
function confirmDelete(formId, event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }
  if (confirm('Are you sure you want to delete this?')) {
    const form = document.getElementById(formId);
    if (form) {
      form.submit();
    } else {
      console.error('Delete form not found: ' + formId);
    }
  }
}

// ── Filter Buttons (Orders page) ─────────────────────────────
function filterOrders(status) {
  const url = new URL(window.location.href);
  if (status) {
    url.searchParams.set('status', status);
  } else {
    url.searchParams.delete('status');
  }
  window.location.href = url.toString();
}
