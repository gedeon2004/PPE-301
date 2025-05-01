// Animation GSAP pour les liens de navigation sur survol
const navLinks = document.querySelectorAll('.nav-link');
navLinks.forEach(link => {
    link.addEventListener('mouseenter', () => {
        gsap.to(link, { scale: 1.1, duration: 0.3 });
    });

    link.addEventListener('mouseleave', () => {
        gsap.to(link, { scale: 1, duration: 0.3 });
    });
});

// Animation de défilement pour afficher des éléments
gsap.from(".animate__animated", {
    opacity: 0,
    y: 50,
    stagger: 0.1,
    duration: 1,
    ease: "easeOut"
});
