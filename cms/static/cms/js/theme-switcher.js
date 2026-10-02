(function () {
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
    const themes = ['auto', 'light', 'dark'];
    let preferredTheme = 'auto';
    try {
        const stored = localStorage.getItem('theme');
        if (themes.includes(stored)) preferredTheme = stored;
    } catch (_) {
        // Privacy settings may deny storage; keep the choice for this page.
    }

    const applyTheme = () => {
        const actual = preferredTheme === 'auto'
            ? (systemTheme.matches ? 'dark' : 'light') : preferredTheme;
        document.documentElement.setAttribute('data-bs-theme', actual);
        document.querySelectorAll('[data-theme-icon]').forEach((icon) => {
            icon.className = `bi ${preferredTheme === 'auto' ? 'bi-circle-half'
                : preferredTheme === 'dark' ? 'bi-moon-fill' : 'bi-sun-fill'}`;
        });
    };

    applyTheme();
    systemTheme.addEventListener('change', () => {
        if (preferredTheme === 'auto') applyTheme();
    });
    document.addEventListener('DOMContentLoaded', () => {
        applyTheme();
        document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
            button.addEventListener('click', () => {
                preferredTheme = themes[(themes.indexOf(preferredTheme) + 1) % themes.length];
                try {
                    localStorage.setItem('theme', preferredTheme);
                } catch (_) {
                    // Theme changes remain usable without persistent storage.
                }
                applyTheme();
            });
        });
    });
})();
