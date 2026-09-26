/* Article export is isolated from the shared backend editor state. */
window.ArticleBackup = {
    template: '#article-backup-template',
    delimiters: ['[[', ']]'],
    data() {
        const articles = JSON.parse(document.getElementById('backup-article-data').textContent);
        const initialId = Number(new URLSearchParams(window.location.search).get('article'));
        const index = articles.findIndex(article => article.id === initialId);
        return {
            articles,
            selected: index >= 0 ? [initialId] : [],
            search: '',
            page: index >= 0 ? Math.floor(index / 10) + 1 : 1,
            pageSize: 10,
            busy: false,
            error: '',
        };
    },
    computed: {
        filtered() {
            const query = this.search.trim().toLocaleLowerCase();
            return this.articles.filter(article => article.title.toLocaleLowerCase().includes(query));
        },
        pageItems() {
            return this.filtered.slice((this.page - 1) * this.pageSize, this.page * this.pageSize);
        },
        pageSelected() {
            return this.pageItems.length > 0 && this.pageItems.every(article => this.selected.includes(article.id));
        },
        pageIndeterminate() {
            return !this.pageSelected && this.pageItems.some(article => this.selected.includes(article.id));
        },
        selectedProtected() {
            return this.articles.filter(article => this.selected.includes(article.id) && article.has_password).length;
        },
    },
    watch: {
        search() { this.page = 1; },
    },
    methods: {
        togglePage(checked) {
            const pageIds = this.pageItems.map(article => article.id);
            this.selected = checked
                ? Array.from(new Set([...this.selected, ...pageIds]))
                : this.selected.filter(id => !pageIds.includes(id));
        },
        async download(scope, ids = this.selected) {
            if (this.busy) return;
            const selectedIds = [...ids];
            const targets = scope === 'all' ? this.articles : this.articles.filter(article => selectedIds.includes(article.id));
            if (!targets.length) return;
            let message = `将导出${scope === 'all' ? '全部' : '选中的'} ${targets.length} 篇已保存文章，包含本地图片。外链和缺失图片请查看包内 README。`;
            if (targets.some(article => article.has_password)) {
                message += ' 所选内容包含密码文章，下载后正文为明文，压缩包不受文章密码保护，请妥善保管。';
            }
            this.busy = true;
            this.error = '';
            try {
                await ElementPlus.ElMessageBox.confirm(message, '下载文章备份', {
                    confirmButtonText: '确认下载', cancelButtonText: '取消', type: 'warning',
                });
                const body = new URLSearchParams({scope});
                if (scope === 'selected') body.set('article_ids', selectedIds.join(','));
                const token = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const response = await fetch('/api/article/export/', {
                    method: 'POST', credentials: 'same-origin',
                    headers: {'X-CSRFToken': token}, body,
                });
                if (!response.ok) {
                    const detail = await response.json().catch(() => null);
                    throw new Error(detail?.msg || '导出失败，请刷新页面后重试。');
                }
                if (!response.headers.get('Content-Type')?.includes('application/zip')) {
                    throw new Error('未收到备份文件，请刷新页面并检查登录状态。');
                }
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                const disposition = response.headers.get('Content-Disposition') || '';
                link.download = disposition.match(/filename="?([^";]+)"?/)?.[1] || 'article_backup.zip';
                link.href = url;
                document.body.appendChild(link);
                link.click();
                link.remove();
                setTimeout(() => URL.revokeObjectURL(url), 60000);
                ElementPlus.ElMessage.success('备份文件已生成，请在浏览器下载列表中查看。');
            } catch (error) {
                if (error !== 'cancel' && error !== 'close') {
                    this.error = error.message || '下载中断，请检查网络后重试。';
                }
            } finally {
                this.busy = false;
            }
        },
    },
};
