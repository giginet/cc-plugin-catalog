(function () {
    var theme;
    try { theme = localStorage.getItem('theme'); } catch (_) {}
    if (theme !== 'light' && theme !== 'dark') {
        theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    function apply(value) {
        document.documentElement.setAttribute('data-theme', value);
        document.documentElement.style.colorScheme = value;
        var button = document.getElementById('theme-toggle');
        if (button) button.setAttribute('aria-label', 'Switch to ' + (value === 'dark' ? 'light' : 'dark') + ' theme');
    }
    apply(theme);
    document.addEventListener('DOMContentLoaded', function () {
        apply(theme);
        document.getElementById('theme-toggle').addEventListener('click', function () {
            theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            apply(theme);
            try { localStorage.setItem('theme', theme); } catch (_) {}
        });
    });
})();
