// Run immediately to prevent FOUC
(function() {
    const currentTheme = localStorage.getItem('theme') || 'dark';
    if (currentTheme === 'light') {
        document.documentElement.classList.add('light-theme');
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    // We attach classes to body for easier CSS targeting without modifying root styles heavily
    const currentTheme = localStorage.getItem('theme') || 'dark';
    if (currentTheme === 'light') {
        document.body.classList.add('light-theme');
    }

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'theme-toggle-btn';
    toggleBtn.innerHTML = currentTheme === 'light' ? '🌙' : '☀️';
    toggleBtn.title = "Toggle Light/Dark Mode";
    
    // Inline styles for the button to guarantee it shows up properly everywhere
    toggleBtn.style.position = 'fixed';
    toggleBtn.style.bottom = '24px';
    toggleBtn.style.right = '24px';
    toggleBtn.style.width = '50px';
    toggleBtn.style.height = '50px';
    toggleBtn.style.borderRadius = '50%';
    toggleBtn.style.border = '1px solid rgba(120, 120, 120, 0.4)';
    toggleBtn.style.backdropFilter = 'blur(10px)';
    toggleBtn.style.fontSize = '24px';
    toggleBtn.style.display = 'flex';
    toggleBtn.style.alignItems = 'center';
    toggleBtn.style.justifyContent = 'center';
    toggleBtn.style.cursor = 'pointer';
    toggleBtn.style.zIndex = '9999';
    toggleBtn.style.transition = 'all 0.3s ease';
    toggleBtn.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
    
    // Determine background based on mode
    const updateBtnStyle = (isLight) => {
        if (isLight) {
            toggleBtn.style.background = 'rgba(255, 255, 255, 0.8)';
            toggleBtn.style.color = '#0f172a';
            toggleBtn.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
        } else {
            toggleBtn.style.background = 'rgba(15, 23, 42, 0.8)';
            toggleBtn.style.color = 'white';
            toggleBtn.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
        }
    };
    updateBtnStyle(currentTheme === 'light');

    toggleBtn.addEventListener('mouseenter', () => {
        toggleBtn.style.transform = 'scale(1.1)';
    });
    toggleBtn.addEventListener('mouseleave', () => {
        toggleBtn.style.transform = 'scale(1)';
    });

    document.body.appendChild(toggleBtn);

    toggleBtn.addEventListener('click', () => {
        const isLight = document.body.classList.toggle('light-theme');
        document.documentElement.classList.toggle('light-theme');
        if (isLight) {
            localStorage.setItem('theme', 'light');
            toggleBtn.innerHTML = '🌙';
            updateBtnStyle(true);
        } else {
            localStorage.setItem('theme', 'dark');
            toggleBtn.innerHTML = '☀️';
            updateBtnStyle(false);
        }
    });
});
