(() => {
    const form = document.querySelector('[data-library-filter-form]');
    const results = document.querySelector('[data-library-results]');
    const errorMessage = document.querySelector('[data-library-filter-error]');
    if (!form || !results || !errorMessage) return;

    let activeRequest = null;
    let requestNumber = 0;

    function syncFormWithUrl() {
        const params = new URLSearchParams(window.location.search);
        for (const field of form.elements) {
            if (field.name) field.value = params.get(field.name) || '';
        }
    }

    function formUrl() {
        const url = new URL(form.action, window.location.href);
        url.search = '';
        url.hash = '';
        for (const [name, value] of new FormData(form)) {
            if (typeof value === 'string' && value.trim()) {
                url.searchParams.set(name, value.trim());
            }
        }
        return url;
    }

    async function loadResults(url, mode) {
        const target = new URL(url, window.location.href);
        if (target.origin !== window.location.origin || target.pathname !== window.location.pathname) return;

        if (activeRequest) activeRequest.abort();
        const controller = new AbortController();
        activeRequest = controller;
        const thisRequest = ++requestNumber;
        errorMessage.hidden = true;
        results.setAttribute('aria-busy', 'true');

        try {
            const response = await fetch(target, {
                credentials: 'same-origin',
                headers: { 'X-Library-Partial': 'results' },
                signal: controller.signal,
            });
            if (response.redirected) {
                window.location.assign(response.url);
                return;
            }
            if (!response.ok || response.headers.get('X-Library-Partial') !== 'results') {
                throw new Error('Could not load filtered results');
            }
            const html = await response.text();
            if (controller.signal.aborted) return;

            results.innerHTML = html;
            if (mode === 'push' && target.href !== window.location.href) {
                window.history.pushState({ libraryFilter: true }, '', target);
            }
        } catch (error) {
            if (error.name === 'AbortError') return;
            if (mode === 'pop') {
                window.location.assign(target.href);
                return;
            }
            syncFormWithUrl();
            errorMessage.hidden = false;
        } finally {
            if (thisRequest === requestNumber) {
                results.removeAttribute('aria-busy');
                activeRequest = null;
            }
        }
    }

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        loadResults(formUrl(), 'push');
    });

    results.addEventListener('click', (event) => {
        const link = event.target.closest('.library-pagination a');
        if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        if (link.target && link.target !== '_self') return;
        const url = new URL(link.href);
        if (url.origin !== window.location.origin || url.pathname !== window.location.pathname) return;
        event.preventDefault();
        loadResults(url, 'push');
    });

    window.addEventListener('popstate', () => {
        syncFormWithUrl();
        loadResults(window.location.href, 'pop');
    });
})();
