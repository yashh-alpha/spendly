// main.js — students will add JavaScript here as features are built

// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', function() {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Modal functionality for "See how it works"
    const seeHowItWorksBtn = document.getElementById('seeHowItWorks');
    const modal = document.getElementById('videoModal');
    const modalBackdrop = document.querySelector('.modal-backdrop');
    const modalCloseBtn = document.querySelector('.modal-close');
    const modalVideo = document.getElementById('modalVideo');

    // Open modal on button click
    if (seeHowItWorksBtn) {
        seeHowItWorksBtn.addEventListener('click', function() {
            modal.style.display = 'flex';
            modalVideo.src = 'https://www.youtube.com/embed/placeholder';
        });
    }

    // Close modal on backdrop click
    if (modalBackdrop) {
        modalBackdrop.addEventListener('click', function() {
            modal.style.display = 'none';
            modalVideo.pause();
            modalVideo.src = '';
        });
    }

    // Close modal on close button click
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', function() {
            modal.style.display = 'none';
            modalVideo.pause();
            modalVideo.src = '';
        });
    }

    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            modalVideo.pause();
            modalVideo.src = '';
        }
    });

    // "Show more" / "Show less" toggle helper
    function setupShowMore(buttonId, hiddenSelector) {
        const btn = document.getElementById(buttonId);
        if (!btn) return;
        const hiddenRows = document.querySelectorAll(hiddenSelector);
        if (hiddenRows.length === 0) return;

        btn.addEventListener('click', function () {
            const isHidden = hiddenRows[0].classList.contains(hiddenSelector.replace('.', ''));
            hiddenRows.forEach(function (row) {
                row.classList.toggle(hiddenSelector.replace('.', ''), !isHidden);
            });
            btn.textContent = isHidden ? 'Show less' : 'Show more';
        });
    }

    // Transaction history table
    setupShowMore('txShowMoreBtn', '.tx-row-hidden');

    // Category breakdown list
    setupShowMore('catShowMoreBtn', '.cat-row-hidden');
});