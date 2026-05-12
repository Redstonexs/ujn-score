import io
import json
from decimal import Decimal

from django.test import Client, TestCase
from openpyxl import load_workbook

from . import views
from .models import Category, Judge, Participant, Score, SiteConfig


class ScoreRuleTests(TestCase):
    def test_calculation_drops_configured_extreme_counts(self):
        category = Category.objects.create(name='综合素质', order=1)
        participant = Participant.objects.create(name='选手A', category=category, order=1)

        stat = views.calculate_participant_statistics(
            participant,
            [Decimal('70'), Decimal('80'), Decimal('90'), Decimal('95'), Decimal('100')],
            exclude_extreme_scores=True,
            exclude_lowest_count=1,
            exclude_highest_count=2,
        )

        self.assertTrue(stat['rule_applied'])
        self.assertEqual(stat['dropped_lows'], [70])
        self.assertEqual(stat['dropped_highs'], [95, 100])
        self.assertEqual(stat['effective_count'], 2)
        self.assertEqual(stat['total'], 170)
        self.assertEqual(stat['average'], 85)

    def test_calculation_keeps_scores_when_not_enough_scores_remain(self):
        category = Category.objects.create(name='综合素质', order=1)
        participant = Participant.objects.create(name='选手A', category=category, order=1)

        stat = views.calculate_participant_statistics(
            participant,
            [Decimal('80'), Decimal('90'), Decimal('100')],
            exclude_extreme_scores=True,
            exclude_lowest_count=1,
            exclude_highest_count=2,
        )

        self.assertFalse(stat['rule_applied'])
        self.assertEqual(stat['dropped_lows'], [])
        self.assertEqual(stat['dropped_highs'], [])
        self.assertEqual(stat['effective_count'], 3)
        self.assertEqual(stat['total'], 270)


class RankingDisplayTests(TestCase):
    def setUp(self):
        views._rate_limit_store.clear()
        config = SiteConfig.get_config()
        config.admin_password = 'admin123'
        config.exclude_extreme_scores = True
        config.exclude_lowest_count = 2
        config.exclude_highest_count = 2
        config.save()

        self.category = Category.objects.create(name='综合素质', order=1)
        self.participant = Participant.objects.create(
            name='选手A',
            category=self.category,
            order=1,
            college='文学院',
        )
        self.judges = [
            Judge.objects.create(name=f'评委{i}', order=i)
            for i in range(1, 6)
        ]
        for judge, score in zip(self.judges, [3, 5, 51, 87, 100]):
            Score.objects.create(judge=judge, participant=self.participant, score=score)

    def test_admin_scores_returns_raw_judge_count_and_dropped_scores(self):
        response = self.client.get('/api/admin/scores/', {'password': 'admin123'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        stat = data['statistics'][str(self.category.id)][0]
        self.assertEqual(stat['count'], 5)
        self.assertEqual(stat['effective_count'], 1)
        self.assertEqual(stat['dropped_lows'], [3, 5])
        self.assertEqual(stat['dropped_highs'], [87, 100])
        self.assertEqual(stat['total'], 51)

    def test_export_ranking_labels_judge_count_and_dropped_scores(self):
        response = self.client.get('/api/admin/export/', {'password': 'admin123'})

        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(io.BytesIO(response.content), data_only=True)
        sheet = workbook[self.category.name]
        headers = [cell.value for cell in sheet[4]]
        row = [cell.value for cell in sheet[5]]

        self.assertEqual(
            headers,
            [
                '排名', '选手序号', '选手', '学院', '统计总分', '统计平均分',
                '原始总分', '原始平均分', '评委数', '统计计分数',
                '去掉最低分', '去掉最高分', '是否去掉极值',
            ],
        )
        self.assertEqual(row[8], 5)
        self.assertEqual(row[9], 1)
        self.assertEqual(row[10], '3、5')
        self.assertEqual(row[11], '87、100')


class JudgeCategoryAccessTests(TestCase):
    def setUp(self):
        views._rate_limit_store.clear()
        config = SiteConfig.get_config()
        config.admin_password = 'admin123'
        config.scoring_mode = 'score'
        config.save()

        self.score_category = Category.objects.create(name='评分项目', order=1)
        self.vote_category = Category.objects.create(
            name='投票项目',
            order=2,
            scoring_mode='vote',
            vote_select_count=1,
        )
        self.score_participant = Participant.objects.create(
            name='评分选手',
            category=self.score_category,
            order=1,
        )
        self.vote_participant = Participant.objects.create(
            name='投票选手',
            category=self.vote_category,
            order=1,
        )
        self.judge = Judge.objects.create(name='评委A', order=1)
        self.judge.allowed_categories.add(self.score_category)

    def test_judge_auth_and_categories_are_limited_to_allowed_categories(self):
        auth_response = self.client.get(f'/api/judge/{self.judge.token}/auth/')
        categories_response = self.client.get(
            '/api/categories/',
            {'token': str(self.judge.token)},
        )

        self.assertEqual(auth_response.status_code, 200)
        auth_data = auth_response.json()
        self.assertFalse(auth_data['all_categories_allowed'])
        self.assertEqual(auth_data['allowed_category_ids'], [self.score_category.id])
        self.assertEqual(
            list(map(int, auth_data['category_modes'].keys())),
            [self.score_category.id],
        )

        self.assertEqual(categories_response.status_code, 200)
        category_ids = [item['id'] for item in categories_response.json()['categories']]
        self.assertEqual(category_ids, [self.score_category.id])

    def test_submit_score_rejects_unallowed_category(self):
        payload = {
            'token': str(self.judge.token),
            'category_id': self.vote_category.id,
            'scores': [
                {'participant_id': self.vote_participant.id, 'score': 88},
            ],
        }

        response = self.client.post(
            '/api/submit/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn('没有权限', response.json()['error'])
        self.assertFalse(Score.objects.filter(judge=self.judge).exists())

    def test_submit_vote_rejects_unallowed_category(self):
        payload = {
            'token': str(self.judge.token),
            'category_id': self.vote_category.id,
            'votes': [{'participant_id': self.vote_participant.id}],
        }

        response = self.client.post(
            '/api/submit/vote/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn('没有权限', response.json()['error'])

    def test_admin_can_update_judge_allowed_categories(self):
        response = self.client.post(
            f'/api/admin/judges/{self.judge.id}/update/?password=admin123',
            data=json.dumps({
                'name': self.judge.name,
                'order': self.judge.order,
                'allowed_category_ids': [self.vote_category.id],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.judge.refresh_from_db()
        self.assertEqual(
            list(self.judge.allowed_categories.values_list('id', flat=True)),
            [self.vote_category.id],
        )
        data = response.json()['judge']
        self.assertFalse(data['all_categories_allowed'])
        self.assertEqual(data['allowed_category_ids'], [self.vote_category.id])

    def test_admin_can_batch_update_judge_allowed_categories(self):
        other_judge = Judge.objects.create(name='评委B', order=2)
        other_judge.allowed_categories.add(self.vote_category)

        response = self.client.post(
            '/api/admin/judges/permissions/batch/?password=admin123',
            data=json.dumps({
                'judge_ids': [self.judge.id, other_judge.id],
                'allowed_category_ids': [self.vote_category.id],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 2)
        self.assertEqual(
            list(self.judge.allowed_categories.values_list('id', flat=True)),
            [self.vote_category.id],
        )
        self.assertEqual(
            list(other_judge.allowed_categories.values_list('id', flat=True)),
            [self.vote_category.id],
        )

    def test_admin_can_batch_allow_all_categories_with_empty_category_list(self):
        other_judge = Judge.objects.create(name='评委B', order=2)
        other_judge.allowed_categories.add(self.vote_category)

        response = self.client.post(
            '/api/admin/judges/permissions/batch/?password=admin123',
            data=json.dumps({
                'judge_ids': [self.judge.id, other_judge.id],
                'allowed_category_ids': [],
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.judge.allowed_categories.count(), 0)
        self.assertEqual(other_judge.allowed_categories.count(), 0)
        for item in response.json()['judges']:
            self.assertTrue(item['all_categories_allowed'])


class JudgeSubmissionStateTests(TestCase):
    def setUp(self):
        views._rate_limit_store.clear()
        self.category = Category.objects.create(name='综合素质', order=1)
        self.participant_a = Participant.objects.create(
            name='选手A',
            category=self.category,
            order=1,
        )
        self.participant_b = Participant.objects.create(
            name='选手B',
            category=self.category,
            order=2,
        )
        self.judge = Judge.objects.create(name='评委A', order=1)

    def test_judge_auth_returns_persisted_scores(self):
        Score.objects.create(
            judge=self.judge,
            participant=self.participant_a,
            score='88',
        )
        Score.objects.create(
            judge=self.judge,
            participant=self.participant_b,
            score='91',
        )

        response = self.client.get(f'/api/judge/{self.judge.token}/auth/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        category_key = str(self.category.id)
        self.assertEqual(data['submitted_categories'], [self.category.id])
        self.assertEqual(
            data['submitted_scores'][category_key][str(self.participant_a.id)],
            88,
        )
        self.assertEqual(
            data['submitted_scores'][category_key][str(self.participant_b.id)],
            91,
        )

    def test_submit_scores_can_be_read_back_from_another_client(self):
        payload = {
            'token': str(self.judge.token),
            'category_id': self.category.id,
            'scores': [
                {'participant_id': self.participant_a.id, 'score': 88},
                {'participant_id': self.participant_b.id, 'score': 91},
            ],
        }

        response = self.client.post(
            '/api/submit/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        category_key = str(self.category.id)
        self.assertEqual(
            data['submitted_scores'][category_key][str(self.participant_a.id)],
            88,
        )

        other_device = Client()
        auth_response = other_device.get(f'/api/judge/{self.judge.token}/auth/')

        self.assertEqual(auth_response.status_code, 200)
        auth_data = auth_response.json()
        self.assertEqual(auth_data['submitted_categories'], [self.category.id])
        self.assertEqual(
            auth_data['submitted_scores'][category_key][str(self.participant_a.id)],
            88,
        )
        self.assertEqual(
            auth_data['submitted_scores'][category_key][str(self.participant_b.id)],
            91,
        )
