from django.core.management.base import BaseCommand
from scoring.models import Score


class Command(BaseCommand):
    help = '清空所有评分记录'

    def handle(self, *args, **options):
        count = Score.objects.count()
        Score.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'已清空 {count} 条评分记录'))
