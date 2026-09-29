// Student Portal - Interactive Features

document.addEventListener('DOMContentLoaded', function() {
    // Header scroll effect
    const header = document.querySelector('.header');
    let lastScroll = 0;

    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Animate stat numbers on scroll
    const statNumbers = document.querySelectorAll('.stat-number');
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px'
    };

    const animateNumbers = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const text = element.textContent;
                const number = parseFloat(text.replace(/[^\d.]/g, ''));
                const suffix = text.replace(/[\d.,]/g, '');

                animateValue(element, 0, number, 1500, suffix);
                observer.unobserve(element);
            }
        });
    };

    const numberObserver = new IntersectionObserver(animateNumbers, observerOptions);
    statNumbers.forEach(num => numberObserver.observe(num));

    function animateValue(element, start, end, duration, suffix) {
        const startTime = performance.now();
        const isInteger = Number.isInteger(end);

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easeOutCubic(progress);
            const current = start + (end - start) * easedProgress;

            if (isInteger) {
                element.textContent = Math.floor(current).toLocaleString() + suffix;
            } else {
                element.textContent = current.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + suffix;
            }

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    function easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    // Add hover effects to cards
    const cards = document.querySelectorAll('.info-card, .feature-item, .stat-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
        });
    });

    // Active nav link highlight based on scroll position
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    window.addEventListener('scroll', function() {
        let current = '';
        const scrollPos = window.pageYOffset + 100;

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });

    // Add section IDs for nav highlighting
    const infoSection = document.querySelector('.info-section');
    const featuresSection = document.querySelector('.features-section');
    if (infoSection) infoSection.id = 'gioi-thieu';
    if (featuresSection) featuresSection.id = 'tinh-nang';

    // Parallax effect for hero
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.3;
            hero.style.backgroundPositionY = rate + 'px';
        });
    }

    // Keyboard navigation for cards
    document.querySelectorAll('.info-card, .feature-item').forEach(card => {
        card.setAttribute('tabindex', '0');
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });

    console.log('Student Portal initialized successfully!');
});