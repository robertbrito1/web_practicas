let currentIndex = 0;
const carousel = document.getElementById('carousel');
const dots = document.getElementById('dots').children;
const total = carousel.children.length;

function updateCarousel() {
  carousel.style.transform = `translateX(-${currentIndex * 190}px)`;
  for (let i = 0; i < dots.length; i++) {
    dots[i].classList.remove('active');
  }
  dots[currentIndex].classList.add('active');
}

function nextSlide() {
  if (currentIndex < total - 1) {
    currentIndex++;
    updateCarousel();
  }
}

function prevSlide() {
  if (currentIndex > 0) {
    currentIndex--;
    updateCarousel();
  }
}
