(function() {
    const getStoredTheme = () => localStorage.getItem('theme');
    const setStoredTheme = theme => localStorage.setItem('theme', theme);

    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme();
        if (storedTheme) return storedTheme;
        return 'auto';
    };

    const getSystemTheme = () => {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    const setTheme = (theme) => {
        const actualTheme = theme === 'auto' ? getSystemTheme() : theme;
        document.documentElement.setAttribute('data-bs-theme', actualTheme);

        const icon = document.getElementById('theme-icon');
        if (icon) {
            if (theme === 'auto') {
                icon.className = 'bi bi-circle-half';
            } else {
                icon.className = theme === 'dark' ? 'bi bi-moon-fill' : 'bi bi-sun-fill';
            }
        }
    };

    // Применяем тему немедленно
    setTheme(getPreferredTheme());

    // Слушаем системные изменения
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (getStoredTheme() === 'auto' || !getStoredTheme()) {
            setTheme('auto');
        }
    });

    window.toggleTheme = function() {
        const storedTheme = getPreferredTheme();
        let newTheme;

        if (storedTheme === 'auto') {
            newTheme = 'light';
        } else if (storedTheme === 'light') {
            newTheme = 'dark';
        } else {
            newTheme = 'auto';
        }

        setStoredTheme(newTheme);
        setTheme(newTheme);
    };

    // Повторная проверка после загрузки DOM
    document.addEventListener('DOMContentLoaded', () => setTheme(getPreferredTheme()));
})();
