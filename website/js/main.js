/**
 * SCORPION AI - Pandora's Castle
 * Main JavaScript File
 */

// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
    }
});

// Smooth Scroll for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Form Validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[\d\s\-+()]{7,}$/;
    return re.test(phone);
}

function validateForm(form) {
    let isValid = true;
    const errors = [];

    const name = form.querySelector('[name="name"]');
    const email = form.querySelector('[name="email"]');
    const phone = form.querySelector('[name="phone"]');
    const message = form.querySelector('[name="message"]');

    if (name && name.required && !name.value.trim()) {
        errors.push('Name is required');
        name.classList.add('border-red-500');
        isValid = false;
    } else if (name) {
        name.classList.remove('border-red-500');
    }

    if (email && email.required && !validateEmail(email.value)) {
        errors.push('Valid email is required');
        email.classList.add('border-red-500');
        isValid = false;
    } else if (email) {
        email.classList.remove('border-red-500');
    }

    if (phone && phone.value && !validatePhone(phone.value)) {
        errors.push('Valid phone number is required');
        phone.classList.add('border-red-500');
        isValid = false;
    } else if (phone) {
        phone.classList.remove('border-red-500');
    }

    if (message && message.required && !message.value.trim()) {
        errors.push('Message is required');
        message.classList.add('border-red-500');
        isValid = false;
    } else if (message) {
        message.classList.remove('border-red-500');
    }

    return { isValid, errors };
}

// Pricing Calculator
function calculateOwnership(monthlyRate, monthsPaid) {
    const totalCost = monthlyRate * 12;
    const amountPaid = monthlyRate * monthsPaid;
    const ownershipPercent = Math.min((monthsPaid / 12) * 100, 100);
    const remaining = Math.max(totalCost - amountPaid, 0);
    const monthsRemaining = Math.max(12 - monthsPaid, 0);

    return {
        totalCost,
        amountPaid,
        ownershipPercent,
        remaining,
        monthsRemaining,
        isOwned: monthsPaid >= 12
    };
}

// Format Currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Testimonial Slider (if multiple testimonials)
class TestimonialSlider {
    constructor(container) {
        this.container = container;
        this.slides = container.querySelectorAll('.testimonial-slide');
        this.currentIndex = 0;
        this.autoplayInterval = null;

        if (this.slides.length > 1) {
            this.init();
        }
    }

    init() {
        this.showSlide(0);
        this.startAutoplay();
    }

    showSlide(index) {
        this.slides.forEach((slide, i) => {
            slide.style.display = i === index ? 'block' : 'none';
        });
        this.currentIndex = index;
    }

    next() {
        const nextIndex = (this.currentIndex + 1) % this.slides.length;
        this.showSlide(nextIndex);
    }

    prev() {
        const prevIndex = (this.currentIndex - 1 + this.slides.length) % this.slides.length;
        this.showSlide(prevIndex);
    }

    startAutoplay() {
        this.autoplayInterval = setInterval(() => this.next(), 5000);
    }

    stopAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
        }
    }
}

// Initialize testimonial sliders
document.querySelectorAll('.testimonial-slider').forEach(slider => {
    new TestimonialSlider(slider);
});

// Intersection Observer for Animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in');
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements with animation class
document.querySelectorAll('.animate-on-scroll').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Navbar Scroll Effect
let lastScroll = 0;
const nav = document.querySelector('nav');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 100) {
        nav.classList.add('shadow-lg');
    } else {
        nav.classList.remove('shadow-lg');
    }

    lastScroll = currentScroll;
});

// Counter Animation
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// Initialize counters when in view
document.querySelectorAll('[data-counter]').forEach(counter => {
    observer.observe(counter);
    counter.addEventListener('animationstart', () => {
        const target = parseInt(counter.dataset.counter);
        animateCounter(counter, target);
    });
});

// Copy to Clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-xl shadow-lg z-50 transition-all transform translate-y-full opacity-0 ${
        type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-y-full', 'opacity-0');
    }, 100);

    // Animate out
    setTimeout(() => {
        toast.classList.add('translate-y-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Dark Mode Toggle (if needed)
function toggleDarkMode() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('darkMode', document.documentElement.classList.contains('dark'));
}

// Check for saved dark mode preference
if (localStorage.getItem('darkMode') === 'true') {
    document.documentElement.classList.add('dark');
}

// Lazy Loading Images
document.querySelectorAll('img[data-src]').forEach(img => {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    imageObserver.observe(img);
});

// Export functions for global use
window.SCORPION = {
    validateForm,
    validateEmail,
    validatePhone,
    calculateOwnership,
    formatCurrency,
    showToast,
    copyToClipboard,
    toggleDarkMode
};

console.log('🦂 SCORPION AI - Pandora\'s Castle initialized');
