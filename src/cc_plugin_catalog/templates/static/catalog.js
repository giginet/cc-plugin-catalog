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
    var filters = { category: '', tool: '', tags: new Set() };

    function addSelectedFilter(container, key, value, remove) {
        var chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'selected-filter';
        chip.textContent = key + ': ' + value + ' ×';
        chip.setAttribute('aria-label', 'Remove ' + key + ' filter: ' + value);
        chip.addEventListener('click', function () { remove(); update(true); });
        container.appendChild(chip);
    }

    function update(save) {
        var query = search.value.trim().toLowerCase();
        var visible = 0;
        cards.forEach(function (card) {
            var data = card.dataset;
            var text = [data.name, data.description, data.category, data.tags, data.keywords].join(' ').toLowerCase();
            var matches = (!query || text.indexOf(query) !== -1)
                && (!filters.category || data.category === filters.category)
                && (!filters.tool || data.tools.trim().split(/\s+/).includes(filters.tool))
                && (!filters.tags.size || JSON.parse(data.tags).some(function (tag) { return filters.tags.has(tag); }));
            card.hidden = !matches;
            if (matches) visible++;
        });
        buttons.forEach(function (button) {
            var active = button.dataset.filterType === 'tag'
                ? filters.tags.has(button.dataset.filterValue)
                : filters[button.dataset.filterType] === button.dataset.filterValue;
            button.classList.toggle('filter-active', active);
            button.setAttribute('aria-pressed', String(active));
        });
        var hasFilters = !!(filters.category || filters.tool || filters.tags.size || query);
        all.classList.toggle('filter-active', !hasFilters);
        all.setAttribute('aria-pressed', String(!hasFilters));
        var selected = document.getElementById('active-filters');
        selected.replaceChildren();
        ['category', 'tool'].forEach(function (key) {
            if (!filters[key]) return;
            addSelectedFilter(selected, key, filters[key], function () { filters[key] = ''; });
        });
        filters.tags.forEach(function (tag) {
            addSelectedFilter(selected, 'tag', tag, function () { filters.tags.delete(tag); });
        });
        selected.hidden = !selected.childElementCount;
        document.querySelector('.results-toolbar .reset-filters').hidden = !hasFilters;
        count.textContent = visible + ' of ' + cards.length;
        empty.hidden = visible !== 0;
        if (save) {
            var params = new URLSearchParams();
            ['category', 'tool'].forEach(function (key) { if (filters[key]) params.set(key, filters[key]); });
            filters.tags.forEach(function (tag) { params.append('tag', tag); });
            if (search.value) params.set('q', search.value);
            if (sort.value !== 'default') params.set('sort', sort.value);
            if (grid.dataset.view !== 'grid') params.set('view', grid.dataset.view);
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
        grid.dataset.view = view === 'list' ? 'list' : 'grid';
        document.querySelectorAll('.view-btn').forEach(function (button) {
            var active = button.dataset.view === grid.dataset.view;
            button.classList.toggle('active', active);
            button.setAttribute('aria-pressed', String(active));
        });
    }
    function restore() {
        var params = new URLSearchParams(location.search);
        filters.category = params.get('category') || '';
        filters.tool = params.get('tool') || '';
        filters.tags = new Set(params.getAll('tag'));
        search.value = params.get('q') || '';
        sort.value = params.get('sort') === 'name' ? 'name' : 'default';
        setView(params.get('view'));
        orderCards();
        update(false);
    }
    function reset() {
        filters.category = '';
        filters.tool = '';
        filters.tags.clear();
        search.value = '';
        update(true);
    }
    buttons.forEach(function (button) {
        button.addEventListener('click', function () {
            var key = button.dataset.filterType;
            var value = button.dataset.filterValue;
            if (key === 'tag') {
                if (filters.tags.has(value)) filters.tags.delete(value);
                else filters.tags.add(value);
            } else {
                filters[key] = filters[key] === value ? '' : value;
            }
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
