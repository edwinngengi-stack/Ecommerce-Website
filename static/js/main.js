document.addEventListener('DOMContentLoaded', () => {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            el.style.opacity = '0';
            el.style.transform = 'translateY(-6px)';
            setTimeout(() => el.remove(), 400);
        }, 4200);
    });

    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('change', () => {
            if (parseInt(input.value) < 0) input.value = 0;
        });
    });
});
