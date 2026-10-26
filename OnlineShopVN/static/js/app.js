document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-dismiss-flash]').forEach((button) => {
    button.addEventListener('click', () => button.closest('.flash')?.remove());
  });

  const menuToggle = document.querySelector('[data-menu-toggle]');
  const navMenu = document.querySelector('[data-nav-menu]');
  if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', () => {
      const opened = navMenu.classList.toggle('mobile-open');
      menuToggle.setAttribute('aria-expanded', String(opened));
      menuToggle.textContent = opened ? '×' : '☰';
    });
  }

  document.querySelectorAll('[data-fill-coupon]').forEach((button) => {
    button.addEventListener('click', () => {
      const input = document.querySelector('.coupon-form input[name="coupon_code"]');
      if (input) {
        input.value = button.getAttribute('data-fill-coupon') || '';
        input.focus();
      }
    });
  });

  const quantityInput = document.querySelector('[data-qty-input]');
  if (quantityInput) {
    const minus = document.querySelector('[data-qty-minus]');
    const plus = document.querySelector('[data-qty-plus]');
    const getBounds = () => ({
      min: Number(quantityInput.min || 1),
      max: Number(quantityInput.max || 99),
      current: Number(quantityInput.value || 1),
    });
    minus?.addEventListener('click', () => {
      const b = getBounds();
      quantityInput.value = String(Math.max(b.min, b.current - 1));
    });
    plus?.addEventListener('click', () => {
      const b = getBounds();
      quantityInput.value = String(Math.min(b.max, b.current + 1));
    });
    quantityInput.addEventListener('change', () => {
      const b = getBounds();
      quantityInput.value = String(Math.min(b.max, Math.max(b.min, b.current || b.min)));
    });
  }

  document.querySelectorAll('[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const message = form.getAttribute('data-confirm') || 'Bạn có chắc muốn thực hiện thao tác này?';
      if (!window.confirm(message)) event.preventDefault();
    });
  });

  document.querySelectorAll('[data-table-search]').forEach((input) => {
    input.addEventListener('input', () => {
      const table = document.getElementById(input.getAttribute('data-table-search'));
      if (!table) return;
      const query = input.value.trim().toLocaleLowerCase('vi');
      table.querySelectorAll('tbody tr').forEach((row) => {
        row.hidden = !row.innerText.toLocaleLowerCase('vi').includes(query);
      });
    });
  });

  document.querySelectorAll('img').forEach((img) => {
    img.addEventListener('error', () => {
      if (img.dataset.fallbackDone) return;
      img.dataset.fallbackDone = '1';
      img.src = 'https://placehold.co/600x600/f2efff/7256d8?text=May+Mart';
    });
  });
});
