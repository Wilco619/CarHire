document.addEventListener('DOMContentLoaded', function() {
    // Menu toggle functionality
    const menuBtn = document.querySelector('.menu-btn');
    const navbar = document.querySelector('.navbar');
    const navLinks = document.querySelector('.nav-links');

    menuBtn.addEventListener('click', function() {
        navbar.classList.toggle('active');
        navLinks.classList.toggle('show');
        // Change icon based on menu state
        const icon = menuBtn.querySelector('i');
        if (navbar.classList.contains('active')) {
            icon.classList.remove('fa-bars');
            icon.classList.add('fa-times');
        } else {
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!navbar.contains(e.target) && !menuBtn.contains(e.target)) {
            navbar.classList.remove('active');
            navLinks.classList.remove('show');
            const icon = menuBtn.querySelector('i');
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    });

    // Close menu when window is resized past mobile breakpoint
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            navbar.classList.remove('active');
            const icon = menuBtn.querySelector('i');
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    });

    // Dropdown functionality for mobile
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const dropbtn = dropdown.querySelector('.dropbtn');
        
        dropbtn.addEventListener('click', function(e) {
            e.preventDefault();
            dropdown.classList.toggle('active');
        });
    });
});