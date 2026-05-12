"""
SSE (Server-Sent Events) 模块 — 实时推送评分数据给管理员页面

使用内存事件总线 + Django StreamingHttpResponse 实现，无需额外依赖。
"""
import json
import logging
import threading
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.http import StreamingHttpResponse, JsonResponse

from .models import (
    Category, Judge, Score, SiteConfig, Vote,
)

logger = logging.getLogger(__name__)

# 心跳间隔（秒）
HEARTBEAT_INTERVAL = 30

# 事件等待超时（秒），略小于心跳间隔以确保及时发送心跳
WAIT_TIMEOUT = 25


class ScoreEventBus:
    """基于 threading.Event + 版本号的轻量级发布/订阅机制

    每当有评分/投票变化时调用 notify()，所有等待的 SSE 连接会被唤醒。
    """

    def __init__(self):
        self._version = 0
        self._event = threading.Event()
        self._lock = threading.Lock()

    @property
    def version(self):
        return self._version

    def notify(self):
        """通知所有等待的 SSE 连接有新数据"""
        with self._lock:
            self._version += 1
            # 唤醒所有 wait() 中的线程
            self._event.set()
            # 立即重置，以便下次 wait
            self._event = threading.Event()

    def wait(self, last_version, timeout=WAIT_TIMEOUT):
        """等待版本变化，返回当前版本号

        如果当前版本已经大于 last_version，立即返回。
        否则阻塞直到 notify() 被调用或超时。
        """
        if self._version > last_version:
            return self._version

        # 拿到当前的 event 引用（notify 时会替换为新的）
        event = self._event
        event.wait(timeout=timeout)
        return self._version


# 全局单例
score_event_bus = ScoreEventBus()


# ==================== 工具函数（从 views.py 复用逻辑，避免循环导入） ====================

def _normalize_decimal(value, default=Decimal("0")):
    from decimal import InvalidOperation
    if value is None or value == '':
        return default
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return default


def _quantize_score(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_score_value(value):
    if value is None:
        return None
    decimal_value = _quantize_score(_normalize_decimal(value))
    if decimal_value == decimal_value.to_integral_value():
        return int(decimal_value)
    return float(decimal_value)


def _get_category_scoring_mode(category):
    if category.scoring_mode == 'default':
        config = SiteConfig.get_config()
        return config.scoring_mode
    return category.scoring_mode


def _get_category_vote_params(category):
    config = SiteConfig.get_config()
    participant_count = category.participants.count()
    if category.scoring_mode == 'default':
        select = config.vote_select_count
        return participant_count, select
    elif category.scoring_mode == 'vote':
        select = category.vote_select_count or config.vote_select_count
        return participant_count, select
    return None, None


def _get_category_score_params(category):
    config = SiteConfig.get_config()
    if category.scoring_mode == 'default':
        return (
            config.score_min, config.score_max, config.score_value_type,
            config.allow_duplicate_scores, config.exclude_extreme_scores,
            config.exclude_lowest_count, config.exclude_highest_count,
        )
    elif category.scoring_mode == 'score':
        return (
            category.score_min or config.score_min,
            category.score_max or config.score_max,
            category.score_value_type or config.score_value_type,
            category.allow_duplicate_scores if category.allow_duplicate_scores is not None else config.allow_duplicate_scores,
            category.exclude_extreme_scores if category.exclude_extreme_scores is not None else config.exclude_extreme_scores,
            category.exclude_lowest_count if category.exclude_lowest_count is not None else config.exclude_lowest_count,
            category.exclude_highest_count if category.exclude_highest_count is not None else config.exclude_highest_count,
        )
    return (
        config.score_min, config.score_max, config.score_value_type,
        config.allow_duplicate_scores, config.exclude_extreme_scores,
        config.exclude_lowest_count, config.exclude_highest_count,
    )


def _format_extreme_rule_text(exclude_extreme_scores, exclude_lowest_count=1, exclude_highest_count=1):
    if not exclude_extreme_scores:
        return '统计时保留全部分数'

    lowest_count = max(0, _to_int(exclude_lowest_count, 1))
    highest_count = max(0, _to_int(exclude_highest_count, 1))
    total_drop_count = lowest_count + highest_count
    if total_drop_count <= 0:
        return '统计时保留全部分数'

    parts = []
    if lowest_count:
        parts.append(f'{lowest_count} 个最低分')
    if highest_count:
        parts.append(f'{highest_count} 个最高分')
    return f'统计时去掉{"、".join(parts)}（评分数需大于 {total_drop_count} 时生效）'


def _format_score_rule_text(config):
    if config.score_value_type == 'integer':
        value_type_text = '整数'
    elif config.score_value_type == 'decimal':
        value_type_text = '小数（最多两位）'
    else:
        value_type_text = '整数或小数（最多两位）'
    duplicate_text = '允许重复打分' if config.allow_duplicate_scores else '不允许重复打分'
    extreme_text = _format_extreme_rule_text(
        config.exclude_extreme_scores,
        config.exclude_lowest_count,
        config.exclude_highest_count,
    )
    return f'合法打分：{value_type_text}；{duplicate_text}；打分范围：{_format_score_value(config.score_min)}-{_format_score_value(config.score_max)}；{extreme_text}'


def _format_category_rule_text(category, config):
    mode = _get_category_scoring_mode(category)
    if mode == 'vote':
        vote_total_count, vote_select_count = _get_category_vote_params(category)
        return f'投票模式：从 {vote_total_count} 人中选择 {vote_select_count} 人'
    else:
        (
            score_min,
            score_max,
            score_value_type,
            allow_duplicate_scores,
            exclude_extreme_scores,
            exclude_lowest_count,
            exclude_highest_count,
        ) = _get_category_score_params(category)
        if score_value_type == 'integer':
            value_type_text = '整数'
        elif score_value_type == 'decimal':
            value_type_text = '小数（最多两位）'
        else:
            value_type_text = '整数或小数（最多两位）'
        duplicate_text = '允许重复打分' if allow_duplicate_scores else '不允许重复打分'
        extreme_text = _format_extreme_rule_text(
            exclude_extreme_scores,
            exclude_lowest_count,
            exclude_highest_count,
        )
        return f'合法打分：{value_type_text}；{duplicate_text}；打分范围：{_format_score_value(score_min)}-{_format_score_value(score_max)}；{extreme_text}'


def _apply_score_rule(
    raw_scores,
    exclude_extreme_scores=False,
    exclude_lowest_count=1,
    exclude_highest_count=1,
):
    scores = list(raw_scores)
    lowest_count = max(0, _to_int(exclude_lowest_count, 1))
    highest_count = max(0, _to_int(exclude_highest_count, 1))
    total_drop_count = lowest_count + highest_count
    if exclude_extreme_scores and total_drop_count > 0 and len(scores) > total_drop_count:
        ordered = sorted(scores)
        high_start = len(ordered) - highest_count if highest_count else len(ordered)
        return ordered[lowest_count:high_start], ordered[:lowest_count], ordered[high_start:]
    return scores, [], []


def _calculate_participant_statistics(
    participant,
    scores,
    exclude_extreme_scores=False,
    exclude_lowest_count=1,
    exclude_highest_count=1,
):
    if not scores:
        return None

    effective_scores, dropped_lows, dropped_highs = _apply_score_rule(
        scores,
        exclude_extreme_scores,
        exclude_lowest_count,
        exclude_highest_count,
    )
    rule_applied = len(dropped_lows) > 0 or len(dropped_highs) > 0
    raw_total = _quantize_score(sum(scores, Decimal('0')))
    raw_average = _quantize_score(raw_total / Decimal(len(scores))) if scores else Decimal('0')
    total = _quantize_score(sum(effective_scores, Decimal('0')))
    average = _quantize_score(total / Decimal(len(effective_scores))) if effective_scores else Decimal('0')

    return {
        'participant_id': participant.id,
        'participant_name': participant.name,
        'college': participant.college,
        'raw_scores': [_format_score_value(item) for item in scores],
        'total': _format_score_value(total),
        'average': _format_score_value(average),
        'count': len(scores),
        'effective_count': len(effective_scores),
        'raw_total': _format_score_value(raw_total),
        'raw_average': _format_score_value(raw_average),
        'dropped_low': _format_score_value(dropped_lows[0]) if dropped_lows else None,
        'dropped_high': _format_score_value(dropped_highs[-1]) if dropped_highs else None,
        'dropped_lows': [_format_score_value(item) for item in dropped_lows],
        'dropped_highs': [_format_score_value(item) for item in dropped_highs],
        'dropped_low_count': len(dropped_lows),
        'dropped_high_count': len(dropped_highs),
        'rule_applied': rule_applied,
    }


def _error_response(msg, status=400):
    return JsonResponse({'error': msg}, status=status, json_dumps_params={'ensure_ascii': False})


def _verify_admin_from_request(request):
    """独立的管理员验证，避免从 views.py 导入"""
    import json as json_mod
    password = None
    password = request.META.get('HTTP_X_ADMIN_PASSWORD')
    if not password:
        password = request.POST.get('password')
    if not password:
        try:
            body = json_mod.loads(request.body)
            password = body.get('password')
        except Exception:
            pass
    if not password:
        password = request.GET.get('password')
    config = SiteConfig.get_config()
    return password == config.admin_password


# ==================== 核心功能 ====================


def build_scores_data():
    """构建完整的评分/投票数据字典

    抽取自 views.get_all_scores，供 SSE 和 REST 两个端点复用。
    """
    config = SiteConfig.get_config()
    all_scores = list(
        Score.objects.select_related('judge', 'participant', 'participant__category').all()
    )
    all_votes = list(
        Vote.objects.select_related('judge', 'participant', 'category').all()
    )
    categories = list(Category.objects.prefetch_related('participants').all())
    judges = list(Judge.objects.filter(is_active=True).order_by('order', 'id'))

    # 处理分数模式数据
    scores_by_judge_category = defaultdict(dict)
    scores_by_participant = defaultdict(list)
    for score in all_scores:
        scores_by_judge_category[
            (score.judge_id, score.participant.category_id)
        ][score.participant_id] = score.score
        scores_by_participant[score.participant_id].append(score.score)

    # 处理投票模式数据
    votes_by_judge_category = defaultdict(list)
    votes_by_participant = defaultdict(int)
    for vote in all_votes:
        votes_by_judge_category[(vote.judge_id, vote.category_id)].append({
            'participant_id': vote.participant_id,
            'vote_order': vote.vote_order,
        })
        votes_by_participant[vote.participant_id] += 1

    result = {
        'categories': [],
        'judges': [{'id': j.id, 'order': j.order, 'name': j.name} for j in judges],
        'scores': {},
        'votes': {},
        'statistics': {},
        'exclude_extreme_scores': config.exclude_extreme_scores,
        'exclude_lowest_count': config.exclude_lowest_count,
        'exclude_highest_count': config.exclude_highest_count,
        'calculation_rule': _format_score_rule_text(config),
        'category_rules': {},
    }

    for cat in categories:
        participants = list(cat.participants.all())
        mode = _get_category_scoring_mode(cat)
        result['categories'].append({
            'id': cat.id,
            'name': cat.name,
            'mode': mode,
            'participants': [
                {'id': p.id, 'name': p.name, 'order': p.order, 'college': p.college}
                for p in participants
            ],
        })
        result['category_rules'][cat.id] = _format_category_rule_text(cat, config)

        if mode == 'vote':
            cat_votes = {}
            for judge in judges:
                judge_votes = votes_by_judge_category.get((judge.id, cat.id), [])
                if judge_votes:
                    cat_votes[judge.id] = judge_votes
            result['votes'][cat.id] = cat_votes

            cat_stats = []
            for participant in participants:
                vote_count = votes_by_participant.get(participant.id, 0)
                cat_stats.append({
                    'participant_id': participant.id,
                    'participant_name': participant.name,
                    'college': participant.college,
                    'vote_count': vote_count,
                })
            cat_stats.sort(
                key=lambda item: (item['vote_count'], item['participant_name']),
                reverse=True,
            )
            result['statistics'][cat.id] = cat_stats
        else:
            cat_scores = {}
            for judge in judges:
                judge_scores = scores_by_judge_category.get((judge.id, cat.id), {})
                if judge_scores:
                    cat_scores[judge.id] = {
                        participant_id: _format_score_value(score)
                        for participant_id, score in judge_scores.items()
                    }
            result['scores'][cat.id] = cat_scores

            cat_stats = []
            (
                _,
                _,
                _,
                _,
                category_exclude_extreme,
                exclude_lowest_count,
                exclude_highest_count,
            ) = _get_category_score_params(cat)
            for participant in participants:
                stat = _calculate_participant_statistics(
                    participant,
                    scores_by_participant.get(participant.id, []),
                    category_exclude_extreme,
                    exclude_lowest_count,
                    exclude_highest_count,
                )
                if stat:
                    cat_stats.append(stat)
            cat_stats.sort(
                key=lambda item: (item['total'], item['average'], item['participant_name']),
                reverse=True,
            )
            result['statistics'][cat.id] = cat_stats

    return result


def _format_sse(event, data):
    """格式化为 SSE 协议文本"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _event_stream(request):
    """SSE 事件流生成器"""
    bus = score_event_bus
    last_version = -1  # 强制首次立即推送

    try:
        while True:
            current_version = bus.version

            # 版本有变化（或首次连接），推送数据
            if current_version > last_version:
                try:
                    data = build_scores_data()
                    event_type = 'init' if last_version == -1 else 'update'
                    yield _format_sse(event_type, data)
                    last_version = current_version
                except Exception:
                    logger.exception("SSE: 构建评分数据失败")
                    yield _format_sse('error', {'message': '服务器内部错误'})
                    break
            else:
                # 发送心跳保持连接
                yield ": heartbeat\n\n"

            # 等待下一次数据变化或超时
            bus.wait(last_version, timeout=WAIT_TIMEOUT)

    except GeneratorExit:
        logger.debug("SSE: 客户端断开连接")
    except Exception:
        logger.exception("SSE: 事件流异常")


def score_events_stream(request):
    """SSE 端点 — 实时推送评分数据给管理员

    GET /api/admin/scores/stream/?password=xxx
    """
    if request.method != 'GET':
        return _error_response('方法不允许', 405)

    if not _verify_admin_from_request(request):
        return _error_response('权限不足', 403)

    response = StreamingHttpResponse(
        _event_stream(request),
        content_type='text/event-stream',
    )
    # SSE 所需的响应头
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # 禁用 Nginx 缓冲
    response['Connection'] = 'keep-alive'
    # CORS 支持（django-cors-headers 可能已处理，显式添加以确保 SSE 兼容）
    response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
    return response
