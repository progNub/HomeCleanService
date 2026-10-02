document.querySelectorAll('[data-reviews]').forEach((container) => {
    const slider = container.querySelector('[data-reviews-track]');
    if (!slider) return;
    container.querySelectorAll('[data-reviews-direction]').forEach((button) => {
        button.addEventListener('click', () => {
            const card = slider.querySelector('.review-slide');
            const distance = card ? card.getBoundingClientRect().width : slider.clientWidth;
            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            slider.scrollBy({
                left: Number(button.dataset.reviewsDirection) * distance,
                behavior: reducedMotion ? 'instant' : 'smooth',
            });
        });
    });
});
