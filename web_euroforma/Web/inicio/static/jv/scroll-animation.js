// Función que verifica si el elemento está en el viewport
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Mostrar u ocultar sección de reseñas
function toggleVisibilityOnScroll() {
    const reviewSection = document.querySelector('.google-reviews');
    if (reviewSection && isElementInViewport(reviewSection)) {
        reviewSection.classList.add('visible');
    } else if (reviewSection) {
        reviewSection.classList.remove('visible');
    }
}

// Mostrar u ocultar título <h1>
function toggleTitleVisibility() {
    const titles = document.querySelectorAll('.faq-title');
    titles.forEach((title) => {
        if (isElementInViewport(title)) {
            title.classList.add('visible');
        } else {
            title.classList.remove('visible');
        }
    });
}


// Mostrar u ocultar las categorías de FAQ con animación
function toggleFAQVisibility() {
    const faqCategories = document.querySelectorAll('.faq-category');
    faqCategories.forEach((category) => {
        if (isElementInViewport(category)) {
            category.classList.add('visible');
        } else {
            category.classList.remove('visible');
        }
    });
}

// Escuchar scroll y cargar
window.addEventListener('scroll', () => {
    toggleVisibilityOnScroll();
    toggleTitleVisibility();
    toggleFAQVisibility();
});

window.addEventListener('load', () => {
    toggleVisibilityOnScroll();
    toggleTitleVisibility();
    toggleFAQVisibility();
});
