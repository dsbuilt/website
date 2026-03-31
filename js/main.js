document.addEventListener('DOMContentLoaded', () => {
  /* ------------------------------------------------
     1. Mobile Navigation Toggle
  ------------------------------------------------ */
  const navbar = document.getElementById('navbar');
  const burger = document.getElementById('navbar-burger');
  const navLinks = navbar ? navbar.querySelectorAll('a') : [];

  const openMenu = () => {
    navbar.classList.add('navbar--open');
    burger.setAttribute('aria-expanded', 'true');
    navbar.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  };

  const closeMenu = () => {
    navbar.classList.remove('navbar--open');
    burger.setAttribute('aria-expanded', 'false');
    navbar.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  if (burger && navbar) {
    burger.addEventListener('click', () => {
      const isOpen = navbar.classList.contains('navbar--open');
      isOpen ? closeMenu() : openMenu();
    });

    navLinks.forEach((link) => {
      link.addEventListener('click', () => {
        if (navbar.classList.contains('navbar--open')) closeMenu();
      });
    });
  }

  /* ------------------------------------------------
     2. Navbar Scroll Behaviour
  ------------------------------------------------ */
  if (navbar) {
    let ticking = false;

    const onScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          if (window.scrollY > 50) {
            navbar.classList.add('navbar--scrolled');
          } else {
            navbar.classList.remove('navbar--scrolled');
          }
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ------------------------------------------------
     3. Hero Image Slider with Slide Pager
  ------------------------------------------------ */
  const heroSlider = document.getElementById('heroSlider');

  if (heroSlider) {
    const slides = heroSlider.querySelectorAll('.heroSlider-slide');
    const pagerItems = heroSlider.querySelectorAll('.slidePager-item');
    let currentIndex = 0;
    let autoplayTimer = null;
    const SLIDE_DURATION = 5000; // matches CSS transition: transform 5s linear

    const goToSlide = (index) => {
      // Remove active from current
      slides[currentIndex].classList.remove('is-active');
      if (pagerItems[currentIndex]) {
        pagerItems[currentIndex].classList.remove('is-selected');
        // Force reflow to restart CSS animation
        void pagerItems[currentIndex].offsetWidth;
      }

      currentIndex = index % slides.length;

      // Activate new slide
      slides[currentIndex].classList.add('is-active');
      if (pagerItems[currentIndex]) {
        pagerItems[currentIndex].classList.add('is-selected');
      }
    };

    const nextSlide = () => goToSlide(currentIndex + 1);

    const startAutoPlay = () => {
      stopAutoPlay();
      if (slides.length > 1) {
        autoplayTimer = setInterval(nextSlide, SLIDE_DURATION);
      }
    };

    const stopAutoPlay = () => {
      if (autoplayTimer) {
        clearInterval(autoplayTimer);
        autoplayTimer = null;
      }
    };

    // Pager click handlers
    pagerItems.forEach((item) => {
      item.addEventListener('click', () => {
        const slideIndex = parseInt(item.dataset.slide, 10);
        if (slideIndex !== currentIndex) {
          goToSlide(slideIndex);
          startAutoPlay(); // restart timer after manual navigation
        }
      });
    });

    // Kick-start the first pager item's progress bar animation
    if (pagerItems[0]) {
      pagerItems[0].classList.remove('is-selected');
      void pagerItems[0].offsetWidth;
      pagerItems[0].classList.add('is-selected');
    }

    // Start autoplay
    startAutoPlay();
  }

  /* ------------------------------------------------
     4. Project Filter
  ------------------------------------------------ */
  const filterContainer = document.getElementById('previewFilter');
  const grid = document.getElementById('previewGrid');

  if (filterContainer && grid) {
    const buttons = filterContainer.querySelectorAll('[data-filter]');
    const items = grid.querySelectorAll('[data-category]');

    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const filter = btn.dataset.filter;

        buttons.forEach((b) => {
          b.classList.remove('is-active');
          b.setAttribute('aria-checked', 'false');
        });
        btn.classList.add('is-active');
        btn.setAttribute('aria-checked', 'true');

        items.forEach((item) => {
          const matches = filter === 'all' || item.dataset.category === filter;
          if (matches) {
            item.classList.remove('is-hidden');
          } else {
            item.classList.add('is-hidden');
          }
        });
      });
    });
  }

  /* ------------------------------------------------
     5. Smooth Scroll
  ------------------------------------------------ */
  const NAVBAR_HEIGHT = 60;

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const id = anchor.getAttribute('href');
      if (id === '#') return;

      const target = document.querySelector(id);
      if (!target) return;

      e.preventDefault();
      const top = target.getBoundingClientRect().top + window.scrollY - NAVBAR_HEIGHT;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });

  /* ------------------------------------------------
     6. Contact Form (Formspree via fetch)
  ------------------------------------------------ */
  const form = document.querySelector('form[action*="formspree"]');
  const status = document.getElementById('contact-form-status');

  if (form && status) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      status.textContent = 'Sending…';

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' },
      })
        .then((res) => {
          if (res.ok) {
            status.textContent = 'Thanks! Your message has been sent.';
            form.reset();
          } else {
            return res.json().then((data) => {
              const errors = data.errors
                ? data.errors.map((err) => err.message).join(', ')
                : 'Something went wrong.';
              status.textContent = errors;
            });
          }
      })
        .catch(() => {
          status.textContent = 'Unable to send — please try again later.';
        });
    });
  }

  /* ------------------------------------------------
     7. Project Gallery Rows
  ------------------------------------------------ */
  const projectMediaContainers = document.querySelectorAll('.projectSingle-media[data-project-folder]');

  projectMediaContainers.forEach((container) => {
    const folder = container.dataset.projectFolder;
    const title = container.dataset.projectTitle || 'Project';
    const galleryCount = Number(container.dataset.galleryCount || '0');
    const videoCount = Number(container.dataset.videoCount || '0');
    const poster = `../images/projects/${folder}/cover.jpg`;

    for (let index = 1; index <= videoCount; index += 1) {
      const wrapper = document.createElement('div');
      wrapper.className = 'video-embed';

      const video = document.createElement('video');
      video.controls = true;
      video.preload = 'metadata';
      video.playsInline = true;
      video.poster = poster;

      const source = document.createElement('source');
      source.src = `../images/projects/${folder}/video-${index}.mp4`;
      source.type = 'video/mp4';

      video.appendChild(source);
      wrapper.appendChild(video);
      container.appendChild(wrapper);
    }

    if (galleryCount > 0) {
      const gallery = document.createElement('div');
      gallery.className = 'projectSingle-gallery';

      for (let index = 1; index <= galleryCount; index += 1) {
        const image = document.createElement('img');
        image.src = `../images/projects/${folder}/gallery-${index}.jpg`;
        image.alt = `${title} - Image ${index}`;
        gallery.appendChild(image);
      }

      container.appendChild(gallery);
    }
  });

  const projectGalleries = document.querySelectorAll('.projectSingle-gallery');

  const getGalleryOrientation = (image) => {
    if (!image.naturalWidth || !image.naturalHeight) {
      return 'portrait';
    }

    return image.naturalWidth > image.naturalHeight ? 'landscape' : 'portrait';
  };

  const buildGalleryRows = (gallery) => {
    const images = Array.from(gallery.querySelectorAll('img'));
    if (!images.length) return;

    gallery.innerHTML = '';

    for (let index = 0; index < images.length; index += 1) {
      const image = images[index];
      const orientation = getGalleryOrientation(image);
      const row = document.createElement('div');
      row.className = 'projectSingle-gallery-row';

      if (orientation === 'landscape') {
        row.classList.add('projectSingle-gallery-row--full');
        row.appendChild(image);
        gallery.appendChild(row);
        continue;
      }

      row.classList.add('projectSingle-gallery-row--pair');
      row.appendChild(image);

      const nextImage = images[index + 1];
      if (nextImage && getGalleryOrientation(nextImage) === 'portrait') {
        row.appendChild(nextImage);
        index += 1;
      } else {
        row.classList.add('projectSingle-gallery-row--single');
      }

      gallery.appendChild(row);
    }
  };

  projectGalleries.forEach((gallery) => {
    const images = Array.from(gallery.querySelectorAll('img'));
    if (!images.length) return;

    let pending = images.length;

    const onReady = () => {
      pending -= 1;
      if (pending === 0) {
        buildGalleryRows(gallery);
      }
    };

    images.forEach((image) => {
      if (image.complete) {
        onReady();
        return;
      }

      image.addEventListener('load', onReady, { once: true });
      image.addEventListener('error', onReady, { once: true });
    });
  });

  /* ------------------------------------------------
     8. Back to Top Button
  ------------------------------------------------ */
  const backToTop = document.createElement('button');
  backToTop.className = 'backToTop';
  backToTop.setAttribute('aria-label', 'Back to top');
  backToTop.innerHTML = '&#8593;';
  document.body.appendChild(backToTop);

  const toggleBackToTop = () => {
    if (window.scrollY > 300) {
      backToTop.classList.add('is-visible');
    } else {
      backToTop.classList.remove('is-visible');
    }
  };

  window.addEventListener('scroll', toggleBackToTop, { passive: true });

  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
});
