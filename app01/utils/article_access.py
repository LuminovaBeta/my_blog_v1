from time import time

from django.utils.crypto import constant_time_compare, salted_hmac


ARTICLE_UNLOCK_TTL = 12 * 60 * 60
ARTICLE_UNLOCK_FAILURE_LIMIT = 5
ARTICLE_UNLOCK_FAILURE_WINDOW = 10 * 60
ARTICLE_UNLOCK_LOCK_SECONDS = 10 * 60


def _unlock_key(article_id):
    return f'article_unlock_{article_id}'


def _failure_key(article_id):
    return f'article_unlock_failures_{article_id}'


def _unlock_token(article):
    value = f'{article.pk}:{article.pwd or ""}'
    return salted_hmac('app01.article_unlock', value).hexdigest()


def has_article_access(request, article):
    """公开文章和管理员直接放行；受保护文章校验限时 Session 凭据。"""
    if not article.pwd or getattr(request.user, 'is_superuser', False):
        return True

    unlock_state = request.session.get(_unlock_key(article.pk))
    if not isinstance(unlock_state, dict):
        return False

    unlocked_at = unlock_state.get('unlocked_at', 0)
    token = unlock_state.get('token', '')
    if time() - unlocked_at > ARTICLE_UNLOCK_TTL:
        request.session.pop(_unlock_key(article.pk), None)
        return False
    return constant_time_compare(token, _unlock_token(article))


def unlock_article(request, article):
    request.session[_unlock_key(article.pk)] = {
        'token': _unlock_token(article),
        'unlocked_at': time(),
    }
    request.session.pop(_failure_key(article.pk), None)


def unlock_retry_after(request, article_id):
    state = request.session.get(_failure_key(article_id), {})
    locked_until = state.get('locked_until', 0) if isinstance(state, dict) else 0
    return max(0, int(locked_until - time()))


def record_unlock_failure(request, article_id):
    now = time()
    key = _failure_key(article_id)
    state = request.session.get(key, {})
    if not isinstance(state, dict) or now - state.get('window_started', 0) > ARTICLE_UNLOCK_FAILURE_WINDOW:
        state = {'count': 0, 'window_started': now, 'locked_until': 0}

    state['count'] += 1
    if state['count'] >= ARTICLE_UNLOCK_FAILURE_LIMIT:
        state['locked_until'] = now + ARTICLE_UNLOCK_LOCK_SECONDS
    request.session[key] = state
    return unlock_retry_after(request, article_id)
