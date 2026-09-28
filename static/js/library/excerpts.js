// Filters only the illustrative independent excerpts already present in the HTML.
(() => {
    const page = document.getElementById('excerpt-page');
    if (!page) return;

    const search = page.querySelector('#excerpt-search');
    const category = page.querySelector('#excerpt-category');
    const source = page.querySelector('#excerpt-source');
    const cards = [...page.querySelectorAll('[data-excerpt-card]')];
    const count = page.querySelector('#excerpt-visible-count');
    const empty = page.querySelector('#excerpt-no-results');

    function filterCards() {
        const query = search.value.trim().toLocaleLowerCase();
        let visible = 0;
        for (const card of cards) {
            const matchesCategory = category.value === 'all' || card.dataset.category === category.value;
            const matchesSource = source.value === 'all' || card.dataset.source === source.value;
            const matchesText = !query || card.textContent.toLocaleLowerCase().includes(query);
            card.hidden = !(matchesCategory && matchesSource && matchesText);
            if (!card.hidden) visible += 1;
        }
        count.textContent = String(visible);
        empty.hidden = visible !== 0;
    }

    search.addEventListener('input', filterCards);
    category.addEventListener('change', filterCards);
    source.addEventListener('change', filterCards);
    page.querySelector('#excerpt-reset').addEventListener('click', () => {
        search.value = '';
        category.value = 'all';
        source.value = 'all';
        filterCards();
        search.focus();
    });
})();
