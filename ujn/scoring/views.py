import io
import json
import logging
import re
import zipfile
from collections import defaultdict, Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import qrcode
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from openpyxl import Workbook, load_workbook

from .models import Category, Judge, Participant, Score, SiteConfig

logger = logging.getLogger(__name__)

CLEAR_SCORES_PASSWORD = 'jndx'


def json_response(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def error_response(msg, status=400):
    return json_response({'error': msg}, status=status)


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on', 'y'}


def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_text(value):
    return str(value).strip() if value is not None else ''


def normalize_header(value):
    return normalize_text(value).replace(' ', '').lower()


def normalize_decimal(value, default=Decimal("0")):
    if value is None or value == '':
        return default
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return default


def quantize_score(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_score_value(value):
    if value is None:
        return None
    decimal_value = quantize_score(normalize_decimal(value))
    if decimal_value == decimal_value.to_integral_value():
        return int(decimal_value)
    return float(decimal_value)


def judge_display_name(judge_or_id):
    judge_id = judge_or_id.id if hasattr(judge_or_id, 'id') else judge_or_id
    return f'评委{judge_id}'


def format_score_rule_text(config):
    if config.score_value_type == 'integer':
        value_type_text = '整数'
    elif config.score_value_type == 'decimal':
        value_type_text = '小数（最多两位）'
    else:
        value_type_text = '整数或小数（最多两位）'
    duplicate_text = '允许重复打分' if config.allow_duplicate_scores else '不允许重复打分'
    extreme_text = '统计时去掉最高分和最低分' if config.exclude_extreme_scores else '统计时保留全部分数'
    return f'合法打分：{value_type_text}；{duplicate_text}；打分范围：{format_score_value(config.score_min)}-{format_score_value(config.score_max)}；{extreme_text}'


def serialize_site_config(config, include_private=False):
    data = {
        'site_name': config.site_name,
        'primary_color': config.primary_color,
        'score_min': format_score_value(config.score_min),
        'score_max': format_score_value(config.score_max),
        'score_value_type': config.score_value_type,
        'allow_duplicate_scores': config.allow_duplicate_scores,
        'allow_scoring': config.allow_scoring,
        'exclude_extreme_scores': config.exclude_extreme_scores,
        'background_image': config.background_image.url if config.background_image else None,
        'logo_image': config.logo_image.url if config.logo_image else None,
    }
    if include_private:
        data.update({
            'admin_password': config.admin_password,
            'base_url': config.base_url,
            'admin_url': config.get_admin_url(),
            'participant_sheet_name': config.participant_sheet_name,
            'category_field_name': config.category_field_name,
            'participant_field_name': config.participant_field_name,
            'order_field_name': config.order_field_name,
            'college_field_name': config.college_field_name,
        })
    return data


def render_qr_png_bytes(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def build_qr_response(url, filename):
    response = HttpResponse(render_qr_png_bytes(url), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


def sanitize_filename_component(value):
    sanitized = re.sub(r'[\\/:*?"<>|]+', '_', normalize_text(value))
    sanitized = re.sub(r'\s+', '_', sanitized).strip('._')
    return sanitized or 'judge'


def build_judge_qrcode_filename(pattern, judge, index, site_name):
    template = normalize_text(pattern) or '{index}_{judge_name}'
    filename = template.format(
        index=index,
        judge_id=judge.id,
        judge_name=judge.name,
        judge_display_name=judge_display_name(judge),
        site_name=site_name,
        token=judge.token,
    )
    return sanitize_filename_component(filename)


def apply_score_rule(raw_scores, exclude_extreme_scores=False):
    scores = list(raw_scores)
    if exclude_extreme_scores and len(scores) >= 3:
        ordered = sorted(scores)
        return ordered[1:-1], ordered[0], ordered[-1]
    return scores, None, None


def calculate_participant_statistics(participant, scores, exclude_extreme_scores=False):
    if not scores:
        return None

    effective_scores, dropped_low, dropped_high = apply_score_rule(scores, exclude_extreme_scores)
    raw_total = quantize_score(sum(scores, Decimal('0')))
    raw_average = quantize_score(raw_total / Decimal(len(scores))) if scores else Decimal('0')
    total = quantize_score(sum(effective_scores, Decimal('0')))
    average = quantize_score(total / Decimal(len(effective_scores))) if effective_scores else Decimal('0')

    return {
        'participant_id': participant.id,
        'participant_name': participant.name,
        'college': participant.college,
        'raw_scores': [format_score_value(item) for item in scores],
        'total': format_score_value(total),
        'average': format_score_value(average),
        'count': len(scores),
        'effective_count': len(effective_scores),
        'raw_total': format_score_value(raw_total),
        'raw_average': format_score_value(raw_average),
        'dropped_low': format_score_value(dropped_low),
        'dropped_high': format_score_value(dropped_high),
        'rule_applied': exclude_extreme_scores and len(scores) >= 3,
    }


def _verify_admin(request):
    """验证管理员密码"""
    password = request.GET.get('password') or request.POST.get('password')
    if not password:
        try:
            body = json.loads(request.body)
            password = body.get('password')
        except Exception:
            pass
    config = SiteConfig.get_config()
    return password == config.admin_password


def get_admin_password_from_request(request):
    return request.GET.get('password') or request.POST.get('password')


# ==================== 站点配置 ====================

@require_GET
def get_site_config(request):
    """获取站点公开配置"""
    config = SiteConfig.get_config()
    return json_response(serialize_site_config(config))


@require_GET
def get_admin_config(request):
    """获取管理员可编辑配置"""
    if not _verify_admin(request):
        return error_response('权限不足', 403)
    config = SiteConfig.get_config()
    return json_response(serialize_site_config(config, include_private=True))


@csrf_exempt
@require_POST
def update_admin_config(request):
    """更新管理员配置，支持表单和JSON"""
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    config = SiteConfig.get_config()
    payload = {}
    if request.content_type and 'application/json' in request.content_type:
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response('无效的JSON格式')
    else:
        payload = request.POST

    config.site_name = normalize_text(payload.get('site_name')) or config.site_name
    config.base_url = normalize_text(payload.get('base_url')) or config.base_url
    config.primary_color = normalize_text(payload.get('primary_color')) or config.primary_color
    config.score_min = normalize_decimal(payload.get('score_min'), config.score_min)
    config.score_max = normalize_decimal(payload.get('score_max'), config.score_max)
    score_value_type = normalize_text(payload.get('score_value_type')) or config.score_value_type
    if score_value_type in {'integer', 'decimal', 'integer_decimal'}:
        config.score_value_type = score_value_type
    config.allow_duplicate_scores = parse_bool(payload.get('allow_duplicate_scores'), config.allow_duplicate_scores)
    config.allow_scoring = parse_bool(payload.get('allow_scoring'), config.allow_scoring)
    config.exclude_extreme_scores = parse_bool(payload.get('exclude_extreme_scores'), config.exclude_extreme_scores)

    new_admin_password = normalize_text(payload.get('admin_password'))
    if new_admin_password:
        config.admin_password = new_admin_password

    config.participant_sheet_name = normalize_text(payload.get('participant_sheet_name')) or config.participant_sheet_name
    config.category_field_name = normalize_text(payload.get('category_field_name')) or config.category_field_name
    config.participant_field_name = normalize_text(payload.get('participant_field_name')) or config.participant_field_name
    config.order_field_name = normalize_text(payload.get('order_field_name')) or config.order_field_name

    if config.score_min >= config.score_max:
        return error_response('最高分必须大于最低分')

    if parse_bool(payload.get('clear_background'), False) and config.background_image:
        config.background_image.delete(save=False)
        config.background_image = None

    if request.FILES.get('background_image'):
        config.background_image = request.FILES['background_image']

    if request.FILES.get('logo_image'):
        config.logo_image = request.FILES['logo_image']

    config.save()
    return json_response({
        'success': True,
        'message': '配置已更新',
        'config': serialize_site_config(config, include_private=True),
    })


# ==================== 评委认证 ====================

@require_GET
def judge_auth(request, token):
    """通过token验证评委身份"""
    try:
        judge = Judge.objects.get(token=token, is_active=True)
    except Judge.DoesNotExist:
        return error_response('无效的评委链接', 404)

    judge_scores = Score.objects.filter(judge=judge).select_related('participant')
    submitted_category_ids = judge_scores.values_list('participant__category_id', flat=True).distinct()
    submitted_scores = defaultdict(dict)
    for score in judge_scores:
        submitted_scores[score.participant.category_id][score.participant_id] = format_score_value(score.score)

    return json_response({
        'judge_id': judge.id,
        'judge_name': judge_display_name(judge),
        'submitted_categories': list(submitted_category_ids),
        'submitted_scores': submitted_scores,
    })


# ==================== 获取数据 ====================

@require_GET
def get_categories(request):
    """获取所有比赛类别"""
    categories = Category.objects.prefetch_related('participants').all()
    result = []
    for cat in categories:
        result.append({
            'id': cat.id,
            'name': cat.name,
            'order': cat.order,
            'description': cat.description,
            'participant_count': cat.participants.count(),
        })
    return json_response({'categories': result})


@require_GET
def get_participants(request):
    """获取参赛选手列表，可按类别筛选"""
    category_id = request.GET.get('category_id')
    qs = Participant.objects.select_related('category').all()
    if category_id:
        qs = qs.filter(category_id=category_id)

    result = []
    for p in qs:
        result.append({
            'id': p.id,
            'name': p.name,
            'category_id': p.category_id,
            'category_name': p.category.name,
            'order': p.order,
            'description': p.description,
            'photo': p.photo.url if p.photo else None,
            'college': p.college,
        })
    return json_response({'participants': result})


# ==================== 评分操作 ====================

@csrf_exempt
@require_POST
def submit_scores(request):
    """提交评分"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response('无效的JSON格式')

    token = data.get('token')
    category_id = data.get('category_id')
    scores = data.get('scores')

    if not token or not category_id or not scores:
        return error_response('缺少必要数据: token, category_id, scores')

    try:
        judge = Judge.objects.get(token=token, is_active=True)
    except Judge.DoesNotExist:
        return error_response('无效的评委令牌', 403)

    config = SiteConfig.get_config()
    if not config.allow_scoring:
        return error_response('评分已关闭，请联系管理员', 403)

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return error_response('类别不存在')

    has_submitted = Score.objects.filter(
        judge=judge,
        participant__category=category
    ).exists()
    if has_submitted:
        return error_response(f'您已经提交过【{category.name}】的评分，不可重复提交', 409)

    category_participants = set(
        Participant.objects.filter(category=category).values_list('id', flat=True)
    )

    score_objects = []
    normalized_score_values = []
    for item in scores:
        pid = item.get('participant_id')
        score_val = item.get('score')

        if pid is None or score_val in (None, ''):
            return error_response('每条评分必须包含 participant_id 和 score')

        if pid not in category_participants:
            return error_response(f'参赛者ID {pid} 不属于类别【{category.name}】')

        try:
            decimal_score = quantize_score(Decimal(str(score_val).strip()))
        except (InvalidOperation, ValueError, TypeError):
            return error_response('分数格式无效')

        if config.score_value_type == 'integer' and decimal_score != decimal_score.to_integral_value():
            return error_response('当前只允许输入整数分')

        if config.score_value_type == 'decimal' and decimal_score == decimal_score.to_integral_value():
            return error_response('当前只允许输入小数分')

        if decimal_score < config.score_min or decimal_score > config.score_max:
            return error_response(f'分数必须在 {format_score_value(config.score_min)}-{format_score_value(config.score_max)} 之间')

        normalized_score_values.append(str(decimal_score))
        score_objects.append(Score(judge=judge, participant_id=pid, score=decimal_score))

    if len(score_objects) != len(category_participants):
        return error_response(f'需要为该类别的所有 {len(category_participants)} 名选手评分')

    if len({obj.participant_id for obj in score_objects}) != len(score_objects):
        return error_response('同一选手不能重复提交分数')

    if not config.allow_duplicate_scores:
        duplicates = [score for score, count in Counter(normalized_score_values).items() if count > 1]
        if duplicates:
            repeated = ', '.join(duplicates)
            return error_response(f'当前规则不允许重复打分，重复分数：{repeated}')

    Score.objects.bulk_create(score_objects)
    return json_response({'success': True, 'message': f'成功提交【{category.name}】的评分'})


# ==================== 管理员功能 ====================

@csrf_exempt
def verify_admin(request):
    if request.method == 'POST':
        if _verify_admin(request):
            return json_response({'success': True})
        return error_response('密码错误', 403)
    return error_response('方法不允许', 405)


@require_GET
def get_all_scores(request):
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    config = SiteConfig.get_config()
    all_scores = list(Score.objects.select_related('judge', 'participant', 'participant__category').all())
    categories = list(Category.objects.prefetch_related('participants').all())
    judges = list(Judge.objects.filter(is_active=True))

    scores_by_judge_category = defaultdict(dict)
    scores_by_participant = defaultdict(list)
    for score in all_scores:
        scores_by_judge_category[(score.judge_id, score.participant.category_id)][score.participant_id] = score.score
        scores_by_participant[score.participant_id].append(score.score)

    result = {
        'categories': [],
        'judges': [{'id': j.id, 'name': judge_display_name(j)} for j in judges],
        'scores': {},
        'statistics': {},
        'exclude_extreme_scores': config.exclude_extreme_scores,
        'calculation_rule': format_score_rule_text(config),
    }

    for cat in categories:
        participants = list(cat.participants.all())
        result['categories'].append({
            'id': cat.id,
            'name': cat.name,
            'participants': [{'id': p.id, 'name': p.name, 'order': p.order} for p in participants],
        })

        cat_scores = {}
        for judge in judges:
            judge_scores = scores_by_judge_category.get((judge.id, cat.id), {})
            if judge_scores:
                cat_scores[judge.id] = {participant_id: format_score_value(score) for participant_id, score in judge_scores.items()}
        result['scores'][cat.id] = cat_scores

        cat_stats = []
        for participant in participants:
            stat = calculate_participant_statistics(
                participant,
                scores_by_participant.get(participant.id, []),
                config.exclude_extreme_scores,
            )
            if stat:
                cat_stats.append(stat)
        cat_stats.sort(key=lambda item: (item['total'], item['average'], item['participant_name']), reverse=True)
        result['statistics'][cat.id] = cat_stats


    return json_response(result)


@require_GET
def export_excel(request):
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    config = SiteConfig.get_config()
    wb = Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])

    categories = Category.objects.prefetch_related('participants').all()
    judges = list(Judge.objects.filter(is_active=True).order_by('id'))
    all_scores = list(Score.objects.select_related('judge', 'participant', 'participant__category').all())

    scores_by_judge_participant = {(score.judge_id, score.participant_id): score.score for score in all_scores}
    scores_by_participant = defaultdict(list)
    for score in all_scores:
        scores_by_participant[score.participant_id].append(score.score)

    if not categories.exists():
        ws = wb.create_sheet(title='无数据')
        ws['A1'] = '暂无评分数据'
    else:
        for category in categories:
            participants = list(category.participants.all())
            ws = wb.create_sheet(title=category.name[:31])
            ws.append(['活动标题', config.site_name])
            ws.append(['统计规则', format_score_rule_text(config)])
            ws.append([])

            headers = ['评委'] + [f'{p.name}({p.college})' if p.college else p.name for p in participants]
            ws.append(headers)

            for judge in judges:
                row = [judge_display_name(judge)]
                for participant in participants:
                    score_value = scores_by_judge_participant.get((judge.id, participant.id), '')
                    row.append(format_score_value(score_value) if score_value != '' else '')
                ws.append(row)

            ws.append([])
            ws.append(['排名', '选手', '学院', '统计总分', '统计平均分', '原始总分', '原始平均分', '原始评分数', '有效评分数', '是否去掉极值'])

            ranking_stats = []
            for participant in participants:
                stat = calculate_participant_statistics(
                    participant,
                    scores_by_participant.get(participant.id, []),
                    config.exclude_extreme_scores,
                )
                if stat:
                    ranking_stats.append(stat)
            ranking_stats.sort(key=lambda item: (item['total'], item['average'], item['participant_name']), reverse=True)

            for index, stat in enumerate(ranking_stats, start=1):
                ws.append([
                    index,
                    stat['participant_name'],
                    stat['college'],
                    stat['total'],
                    stat['average'],
                    stat['raw_total'],
                    stat['raw_average'],
                    stat['count'],
                    stat['effective_count'],
                    '是' if stat['rule_applied'] else '否',
                ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="scores_export.xlsx"'
    return response


@require_GET
def download_import_template(request):
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    config = SiteConfig.get_config()
    wb = Workbook()
    participant_ws = wb.active
    participant_ws.title = config.participant_sheet_name[:31]
    participant_ws.append([
        config.category_field_name,
        config.participant_field_name,
        config.order_field_name,
        config.college_field_name,
    ])
    participant_ws.append(['才艺组', '选手A', 1, '计算机学院'])
    participant_ws.append(['才艺组', '选手B', 2, '外国语学院'])
    participant_ws.append(['演讲组', '选手C', 1, '经济学院'])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="import_template.xlsx"'
    return response


@csrf_exempt
@require_POST
def clear_scores(request):
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    clear_password = request.POST.get('clear_password') or request.GET.get('clear_password')
    if not clear_password:
        try:
            body = json.loads(request.body)
            clear_password = body.get('clear_password')
        except Exception:
            clear_password = None

    clear_password = normalize_text(clear_password)
    if not clear_password:
        return error_response('请输入清空评分密码', 400)

    if clear_password != CLEAR_SCORES_PASSWORD:
        return error_response('清空评分密码错误', 403)

    count = Score.objects.count()
    Score.objects.all().delete()
    return json_response({'success': True, 'message': f'已清空 {count} 条评分记录'})


# ==================== 评委管理 ====================

@require_GET
def get_judges(request):
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    judges = Judge.objects.all()
    result = []
    for judge in judges:
        result.append({
            'id': judge.id,
            'name': judge.name,
            'display_name': judge_display_name(judge),
            'token': str(judge.token),
            'is_active': judge.is_active,
            'scoring_url': judge.get_scoring_url(),
            'qrcode_url': f'/api/judge/{judge.token}/qrcode/',
            'created_at': judge.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return json_response({'judges': result})


@csrf_exempt
@require_POST
def batch_create_judges(request):
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response('无效的JSON格式')

    names = data.get('names', [])
    count = data.get('count', 0)

    created = []
    if names:
        for name in names:
            normalized_name = normalize_text(name)
            if not normalized_name:
                continue
            judge = Judge.objects.create(name=normalized_name)
            created.append({'id': judge.id, 'name': judge.name, 'token': str(judge.token)})
    elif count > 0:
        existing_count = Judge.objects.count()
        for index in range(count):
            judge = Judge.objects.create(name=f'评委{existing_count + index + 1}')
            created.append({'id': judge.id, 'name': judge.name, 'token': str(judge.token)})

    return json_response({'success': True, 'created': created, 'count': len(created)})


@csrf_exempt
@require_POST
def delete_judge(request, judge_id):
    """删除评委（管理员）"""
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    try:
        judge = Judge.objects.get(id=judge_id)
        judge_name = judge_display_name(judge)
        judge.delete()
        return json_response({'success': True, 'message': f'评委 {judge_name} 已删除'})
    except Judge.DoesNotExist:
        return error_response('评委不存在', 404)
    except Exception as e:
        logger.exception('删除评委失败')
        return error_response(f'删除失败: {str(e)}', 500)


# ==================== 数据导入 ====================

def get_header_index_map(sheet):
    headers = [normalize_text(cell) for cell in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), [])]
    normalized_map = {normalize_header(header): index for index, header in enumerate(headers) if header}
    return headers, normalized_map


@csrf_exempt
def import_data(request):
    """导入数据（管理员）- 仅导入选手数据，支持 Excel 和 JSON"""
    if request.method != 'POST':
        return error_response('方法不允许', 405)
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    config = SiteConfig.get_config()

    uploaded_file = request.FILES.get('file')
    if uploaded_file:
        try:
            workbook = load_workbook(uploaded_file, data_only=True)
        except Exception as exc:
            logger.exception('导入Excel失败')
            return error_response(f'无法读取Excel文件: {exc}')

        participant_sheet_name = config.participant_sheet_name
        participant_sheet = workbook[participant_sheet_name] if participant_sheet_name in workbook.sheetnames else workbook[workbook.sheetnames[0]]

        _, participant_header_map = get_header_index_map(participant_sheet)
        category_idx = participant_header_map.get(normalize_header(config.category_field_name))
        participant_idx = participant_header_map.get(normalize_header(config.participant_field_name))
        order_idx = participant_header_map.get(normalize_header(config.order_field_name))
        college_idx = participant_header_map.get(normalize_header(config.college_field_name))

        if category_idx is None or participant_idx is None:
            return error_response(
                f'Excel缺少必要字段：{config.category_field_name}、{config.participant_field_name}'
            )

        created_categories = 0
        created_participants = 0
        updated_participants = 0
        category_order_map = {}
        participant_sequence_map = defaultdict(int)

        for row in participant_sheet.iter_rows(min_row=2, values_only=True):
            values = list(row)
            category_name = normalize_text(values[category_idx] if len(values) > category_idx else '')
            participant_name = normalize_text(values[participant_idx] if len(values) > participant_idx else '')
            if not category_name and not participant_name:
                continue
            if not category_name or not participant_name:
                continue

            if category_name not in category_order_map:
                category_order_map[category_name] = len(category_order_map) + 1

            category, category_created = Category.objects.get_or_create(
                name=category_name,
                defaults={'order': category_order_map[category_name]}
            )
            if category_created:
                created_categories += 1

            participant_sequence_map[category_name] += 1
            participant_order = participant_sequence_map[category_name]
            if order_idx is not None and len(values) > order_idx:
                participant_order = to_int(values[order_idx], participant_order)
            
            college = ''
            if college_idx is not None and len(values) > college_idx:
                college = normalize_text(values[college_idx])

            # 检查是否已存在相同姓名、类别和序号的选手
            try:
                participant = Participant.objects.get(
                    name=participant_name,
                    category=category,
                    order=participant_order
                )
                if college:
                    participant.college = college
                    participant.save()
                participant_created = False
            except Participant.DoesNotExist:
                participant = Participant.objects.create(
                    name=participant_name,
                    category=category,
                    order=participant_order,
                    college=college
                )
                participant_created = True
                created_participants += 1

        return json_response({
            'success': True,
            'message': (
                f'Excel导入完成：新增{created_categories}个类别，新增{created_participants}名选手'
            ),
        })

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response('请上传Excel文件，或提交有效的JSON格式数据')

    # 处理手动导入的选手列表
    participants_data = data.get('participants', [])
    if participants_data:
        created_categories = 0
        created_participants = 0
        updated_participants = 0
        category_order_map = {}
        participant_sequence_map = defaultdict(int)

        for p_data in participants_data:
            category_name = normalize_text(p_data.get('category', ''))
            participant_name = normalize_text(p_data.get('name', ''))
            participant_order = p_data.get('order')
            college = normalize_text(p_data.get('college', ''))

            if not category_name or not participant_name:
                continue

            if category_name not in category_order_map:
                category_order_map[category_name] = len(category_order_map) + 1

            category, category_created = Category.objects.get_or_create(
                name=category_name,
                defaults={'order': category_order_map[category_name]}
            )
            if category_created:
                created_categories += 1

            participant_sequence_map[category_name] += 1
            if participant_order is None:
                participant_order = participant_sequence_map[category_name]

            # 检查是否已存在相同姓名、类别和序号的选手
            try:
                participant = Participant.objects.get(
                    name=participant_name,
                    category=category,
                    order=participant_order
                )
                if college:
                    participant.college = college
                    participant.save()
                participant_created = False
            except Participant.DoesNotExist:
                participant = Participant.objects.create(
                    name=participant_name,
                    category=category,
                    order=participant_order,
                    college=college
                )
                participant_created = True
                created_participants += 1

        return json_response({
            'success': True,
            'message': (
                f'手动导入完成：新增{created_categories}个类别，新增{created_participants}名选手'
            ),
        })

    # 处理原有的 categories 格式
    categories_data = data.get('categories', [])
    created_categories = 0
    created_participants = 0

    for cat_data in categories_data:
        cat_name = normalize_text(cat_data.get('name', ''))
        if not cat_name:
            continue
        category, category_created = Category.objects.get_or_create(
            name=cat_name,
            defaults={
                'order': cat_data.get('order', 0),
                'description': cat_data.get('description', ''),
            }
        )
        if category_created:
            created_categories += 1

        for idx, p_data in enumerate(cat_data.get('participants', []), start=1):
            participant_name = p_data if isinstance(p_data, str) else p_data.get('name', '')
            participant_name = normalize_text(participant_name)
            participant_order = p_data.get('order', idx) if isinstance(p_data, dict) else idx
            college = ''
            if isinstance(p_data, dict):
                college = normalize_text(p_data.get('college', ''))
            if not participant_name:
                continue
            # 检查是否已存在相同姓名、类别和序号的选手
            try:
                participant = Participant.objects.get(
                    name=participant_name,
                    category=category,
                    order=participant_order
                )
                if college:
                    participant.college = college
                    participant.save()
                participant_created = False
            except Participant.DoesNotExist:
                participant = Participant.objects.create(
                    name=participant_name,
                    category=category,
                    order=participant_order,
                    description=p_data.get('description', '') if isinstance(p_data, dict) else '',
                    college=college
                )
                participant_created = True
                created_participants += 1

    return json_response({
        'success': True,
        'message': f'导入完成：新增{created_categories}个类别，新增{created_participants}名选手',
    })


# ==================== 二维码 ====================

@require_GET
def generate_qrcode(request, token):
    try:
        judge = Judge.objects.get(token=token)
    except Judge.DoesNotExist:
        return error_response('评委不存在', 404)
    safe_name = judge_display_name(judge).replace(' ', '_')
    return build_qr_response(judge.get_scoring_url(), f'judge_{safe_name}_qr.png')


@require_GET
def export_all_judge_qrcodes(request):
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    judges = list(Judge.objects.all().order_by('id'))
    if not judges:
        return error_response('暂无评委可导出', 404)

    config = SiteConfig.get_config()
    pattern = normalize_text(request.GET.get('pattern')) or '{index}_{judge_name}'
    used_names = set()
    try:
        build_judge_qrcode_filename(pattern, judges[0], 1, config.site_name)
    except KeyError as exc:
        return error_response(f'命名规则包含不支持的占位符：{exc.args[0]}')
    except Exception:
        return error_response('二维码命名规则格式无效')
    output = io.BytesIO()

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for index, judge in enumerate(judges, start=1):
            base_name = build_judge_qrcode_filename(pattern, judge, index, config.site_name)
            filename = f'{base_name}.png'
            duplicate_index = 2
            while filename in used_names:
                filename = f'{base_name}_{duplicate_index}.png'
                duplicate_index += 1
            used_names.add(filename)
            archive.writestr(filename, render_qr_png_bytes(judge.get_scoring_url()))

    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="judge_qrcodes.zip"'
    return response


@require_GET
def generate_admin_qrcode(request):
    if not _verify_admin(request):
        return error_response('权限不足', 403)
    config = SiteConfig.get_config()
    return build_qr_response(config.get_admin_url(), 'admin_qr.png')


# ==================== 选手管理 ====================

@require_GET
def get_admin_participants(request):
    """获取所有选手列表（管理员）"""
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    participants = Participant.objects.select_related('category').all()
    result = []
    for p in participants:
        result.append({
            'id': p.id,
            'name': p.name,
            'category_id': p.category_id,
            'category_name': p.category.name,
            'order': p.order,
            'college': p.college,
        })
    return json_response({'participants': result})


@csrf_exempt
@require_POST
def delete_participant(request, participant_id):
    """删除选手（管理员）"""
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    try:
        participant = Participant.objects.get(id=participant_id)
        participant_name = participant.name
        participant.delete()
        return json_response({'success': True, 'message': f'选手 {participant_name} 已删除'})
    except Participant.DoesNotExist:
        return error_response('选手不存在', 404)
    except Exception as e:
        logger.exception('删除选手失败')
        return error_response(f'删除失败: {str(e)}', 500)


@csrf_exempt
@require_POST
def clear_participants(request):
    """清空所有选手（管理员）"""
    if not _verify_admin(request):
        return error_response('权限不足', 403)

    clear_password = request.POST.get('clear_password') or request.GET.get('clear_password')
    if not clear_password:
        try:
            body = json.loads(request.body)
            clear_password = body.get('clear_password')
        except Exception:
            clear_password = None

    clear_password = normalize_text(clear_password)
    if not clear_password:
        return error_response('请输入清空密码', 400)

    if clear_password != CLEAR_SCORES_PASSWORD:
        return error_response('清空密码错误', 403)

    count = Participant.objects.count()
    Participant.objects.all().delete()
    return json_response({'success': True, 'message': f'已清空 {count} 名选手'})
