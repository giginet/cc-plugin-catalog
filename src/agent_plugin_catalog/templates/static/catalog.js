(function () {
    'use strict';
    var search = document.getElementById('plugin-search');
    var grid = document.getElementById('plugin-grid');
    if (!search || !grid) return;
    var cards = Array.from(grid.querySelectorAll('.plugin-card'));
    var buttons = Array.from(document.querySelectorAll('.filter-btn'));
    var all = document.querySelector('.filter-all');
    var count = document.getElementById('result-count');
    var empty = document.getElementById('empty-state');
    var sort = document.getElementById('plugin-sort');
    var filters = { category: '', tool: '', tag: '' };

    function update(save) {
        var query = search.value.trim().toLowerCase();
        var visible = 0;
        cards.forEach(function (card) {
            var data = card.dataset;
            var text = [data.name, data.description, data.category, data.tags, data.keywords].join(' ').toLowerCase();
            var matches = (!query || text.indexOf(query) !== -1)
                && (!filters.category || data.category === filters.category)
                && (!filters.tool || data.tools.trim().split(/\s+/).includes(filters.tool))
                && (!filters.tag || JSON.parse(data.tags).includes(filters.tag));
            card.hidden = !matches;
            if (matches) visible++;
        });
        buttons.forEach(function (button) {
            var active = filters[button.dataset.filterType] === button.dataset.filterValue;
            button.classList.toggle('filter-active', active);
            button.setAttribute('aria-pressed', String(active));
        });
        var hasFilters = Object.values(filters).some(Boolean) || !!query;
        all.classList.toggle('filter-active', !hasFilters);
        all.setAttribute('aria-pressed', String(!hasFilters));
        var selected = document.getElementById('active-filters');
        selected.replaceChildren();
        Object.keys(filters).forEach(function (key) {
            if (!filters[key]) return;
            var chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'selected-filter';
            chip.textContent = key + ': ' + filters[key] + ' ×';
            chip.setAttribute('aria-label', 'Remove ' + key + ' filter: ' + filters[key]);
            chip.addEventListener('click', function () { filters[key] = ''; update(true); });
            selected.appendChild(chip);
        });
        selected.hidden = !selected.childElementCount;
        document.querySelector('.results-toolbar .reset-filters').hidden = !hasFilters;
        count.textContent = visible + ' of ' + cards.length;
        empty.hidden = visible !== 0;
        if (save) {
            var params = new URLSearchParams();
            Object.keys(filters).forEach(function (key) { if (filters[key]) params.set(key, filters[key]); });
            if (search.value) params.set('q', search.value);
            if (sort.value !== 'default') params.set('sort', sort.value);
            if (grid.dataset.view !== 'list') params.set('view', grid.dataset.view);
            var suffix = params.toString();
            history.replaceState(null, '', location.pathname + (suffix ? '?' + suffix : ''));
        }
    }
    function orderCards() {
        var ordered = cards.slice();
        if (sort.value === 'name') ordered.sort(function (a, b) { return a.dataset.name.localeCompare(b.dataset.name); });
        ordered.forEach(function (card) { grid.appendChild(card); });
    }
    function setView(view) {
        grid.dataset.view = view === 'grid' ? 'grid' : 'list';
        document.querySelectorAll('.view-btn').forEach(function (button) {
            var active = button.dataset.view === grid.dataset.view;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
    }
    function restore() {
        var params = new URLSearchParams(location.search);
        Object.keys(filters).forEach(function (key) { filters[key] = params.get(key) || ''; });
        search.value = params.get('q') || '';
        sort.value = params.get('sort') === 'name' ? 'name' : 'default';
        setView(params.get('view'));
        if (filters.tag && document.querySelector('.tag-filters')) document.querySelector('.tag-filters').open = true;
        orderCards();
        update(false);
    }
    function reset() {
        Object.keys(filters).forEach(function (key) { filters[key] = ''; });
        search.value = '';
        update(true);
    }
    buttons.forEach(function (button) {
        button.addEventListener('click', function () {
            var key = button.dataset.filterType;
            filters[key] = filters[key] === button.dataset.filterValue ? '' : button.dataset.filterValue;
            update(true);
        });
    });
    all.addEventListener('click', reset);
    document.querySelectorAll('.reset-filters').forEach(function (button) { button.addEventListener('click', reset); });
    document.querySelectorAll('.view-btn').forEach(function (button) {
        button.addEventListener('click', function () { setView(button.dataset.view); update(true); });
    });
    sort.addEventListener('change', function () { orderCards(); update(true); });
    search.addEventListener('input', function () { update(true); });
    document.addEventListener('keydown', function (event) {
        var editing = event.target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(event.target.tagName);
        if (event.key === '/' && !editing && !event.metaKey && !event.ctrlKey && !event.altKey) {
            event.preventDefault(); search.focus();
        }
        if (event.key === 'Escape' && document.activeElement === search) {
            search.value = ''; search.blur(); update(true);
        }
    });
    window.addEventListener('popstate', restore);
    restore();
})();
