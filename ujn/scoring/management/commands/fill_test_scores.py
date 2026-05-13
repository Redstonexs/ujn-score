import random
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.utils import OperationalError

from scoring.models import Category, Judge, Participant, Score, Vote
from scoring.sse import score_event_bus


class Command(BaseCommand):
    help = "为所有评委批量生成测试用评分/投票数据"

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed",
            type=int,
            default=2026,
            help="随机种子（默认: 2026）",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="生成前清空已有评分和投票记录",
        )

    def handle(self, *args, **options):
        rng = random.Random(options["seed"])

        try:
            judges = list(Judge.objects.filter(is_active=True).prefetch_related("allowed_categories"))
            categories = list(Category.objects.order_by("order", "id"))
        except OperationalError as exc:
            raise CommandError("数据库表不存在，请先执行 python manage.py migrate") from exc

        if not judges:
            self.stdout.write(self.style.WARNING("没有可用评委，请先创建评委数据。"))
            return
        if not categories:
            self.stdout.write(self.style.WARNING("没有比赛类别，请先创建类别和选手数据。"))
            return

        if options["clear"]:
            deleted_votes, _ = Vote.objects.all().delete()
            deleted_scores, _ = Score.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"已清空：{deleted_scores} 条评分，{deleted_votes} 条投票"))

        score_create = 0
        score_update = 0
        vote_create = 0

        with transaction.atomic():
            for judge in judges:
                allowed_category_ids = set(judge.allowed_categories.values_list("id", flat=True))
                judge_categories = categories
                if allowed_category_ids:
                    judge_categories = [cat for cat in categories if cat.id in allowed_category_ids]

                for category in judge_categories:
                    participants = list(Participant.objects.filter(category=category).order_by("order", "id"))
                    if not participants:
                        continue

                    # 默认按分数模式填充，便于快速回归测试
                    for participant in participants:
                        value = Decimal(rng.randint(70, 99))
                        obj, created = Score.objects.update_or_create(
                            judge=judge,
                            participant=participant,
                            defaults={"score": value},
                        )
                        if created:
                            score_create += 1
                        else:
                            score_update += 1

                    # 同时补充投票数据，兼容投票模式页面联调
                    max_select = min(3, len(participants))
                    selected = rng.sample(participants, k=max_select)
                    for idx, participant in enumerate(selected, start=1):
                        _, created = Vote.objects.update_or_create(
                            judge=judge,
                            category=category,
                            participant=participant,
                            defaults={"vote_order": idx},
                        )
                        if created:
                            vote_create += 1

        score_event_bus.notify()

        self.stdout.write(self.style.SUCCESS("测试打分数据生成完成。"))
        self.stdout.write(
            self.style.SUCCESS(
                f"评分：新增 {score_create} 条，更新 {score_update} 条；投票：新增 {vote_create} 条。"
            )
        )
