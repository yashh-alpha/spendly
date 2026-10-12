// main.js — students will add JavaScript here as features are built

// Modal functionality for "See how it works"

document.addEventListener('DOMContentLoaded', function() {
    const seeHowItWorksBtn = document.getElementById('seeHowItWorks');
    const modal = document.getElementById('videoModal');
    const modalBackdrop = document.querySelector('.modal-backdrop');
    const modalCloseBtn = document.querySelector('.modal-close');
    const modalVideo = document.getElementById('modalVideo');

    // Open modal on button click
    seeHowItWorksBtn.addEventListener('click', function() {
        modal.style.display = 'flex';
        modalVideo.src = 'https://www.youtube.com/embed/placeholder';
    });

    // Close modal on backdrop click
    modalBackdrop.addEventListener('click', function() {
        modal.style.display = 'none';
        modalVideo.pause();
        modalVideo.src = '';
    });

    // Close modal on close button click
    modalCloseBtn.addEventListener('click', function() {
        modal.style.display = 'none';
        modalVideo.pause();
        modalVideo.src = '';
    });

    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            modalVideo.pause();
            modalVideo.src = '';
        }
    });
});