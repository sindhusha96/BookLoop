/**
 * BookLoop - Client-Side Interactive Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

  // Auto-dismiss standard alerts after 5 seconds
  setTimeout(() => {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
      const bsAlert = bootstrap.Alert.getInstance(alert) || new bootstrap.Alert(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    });
  }, 5000);

  // Dynamic Image Preview for Book Creation / Edit
  const imageInput = document.getElementById('cover_image');
  const previewContainer = document.getElementById('image-preview-wrapper');
  const previewImg = document.getElementById('image-preview');

  if (imageInput && previewContainer && previewImg) {
    imageInput.addEventListener('change', function(e) {
      const file = this.files[0];
      if (file) {
        // Validate file type and size (5MB max)
        const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
          alert('Please select a valid image file (JPG, PNG, or WEBP).');
          this.value = '';
          return;
        }
        if (file.size > 5 * 1024 * 1024) {
          alert('Image size exceeds 5MB limit. Please choose a smaller image.');
          this.value = '';
          return;
        }

        const reader = new FileReader();
        reader.onload = function(event) {
          previewImg.src = event.target.result;
          previewContainer.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Price field toggling based on listing type
  const listingTypeSelect = document.getElementById('listing_type');
  const priceInput = document.getElementById('price');
  const priceWrapper = document.getElementById('price-field-wrapper');

  function updatePriceState() {
    if (!listingTypeSelect || !priceInput) return;
    if (listingTypeSelect.value === 'Exchange') {
      priceInput.value = '0.00';
      priceInput.disabled = true;
      if (priceWrapper) {
        priceWrapper.classList.add('opacity-50');
      }
    } else {
      priceInput.disabled = false;
      if (priceWrapper) {
        priceWrapper.classList.remove('opacity-50');
      }
    }
  }

  if (listingTypeSelect) {
    listingTypeSelect.addEventListener('change', updatePriceState);
    updatePriceState();
  }

  // Wishlist AJAX Toggle
  const wishlistButtons = document.querySelectorAll('.btn-wishlist-toggle');
  wishlistButtons.forEach(button => {
    button.addEventListener('click', async function(e) {
      e.preventDefault();
      const bookId = this.dataset.bookId;
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

      try {
        const response = await fetch(`/dashboard/wishlist/toggle/${bookId}`, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken || '',
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          const icon = this.querySelector('i');
          const textSpan = this.querySelector('.wishlist-text');

          if (data.in_wishlist) {
            this.classList.add('active');
            if (icon) {
              icon.classList.remove('bi-heart');
              icon.classList.add('bi-heart-fill', 'text-danger');
            }
            if (textSpan) textSpan.textContent = 'Saved in Wishlist';
          } else {
            this.classList.remove('active');
            if (icon) {
              icon.classList.remove('bi-heart-fill', 'text-danger');
              icon.classList.add('bi-heart');
            }
            if (textSpan) textSpan.textContent = 'Save to Wishlist';
          }

          showToast(data.message, data.in_wishlist ? 'success' : 'info');
        } else if (response.status === 401) {
          window.location.href = '/auth/login';
        }
      } catch (err) {
        console.error('Wishlist error:', err);
      }
    });
  });

  // Simple Toast notification helper
  function showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toast-container';
      toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
      toastContainer.style.zIndex = '1090';
      document.body.appendChild(toastContainer);
    }

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'dark'} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          <i class="bi bi-info-circle me-2"></i> ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 3500 });
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => {
      toastEl.remove();
    });
  }
});
