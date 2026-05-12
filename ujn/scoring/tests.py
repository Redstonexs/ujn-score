import json
from decimal import Decimal

from django.test import Client, TestCase

from . import views
from .models import Category, Judge, Participant, Score


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
