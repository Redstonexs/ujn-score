from django.core.management.base import BaseCommand
from scoring.models import SiteConfig, Category, Participant, Judge


class Command(BaseCommand):
    help = '初始化测试数据（类别、选手、评委）'

    def handle(self, *args, **options):
        # 创建站点配置
        config = SiteConfig.get_config()
        config.site_name = "评分系统"
        config.save()
        self.stdout.write(self.style.SUCCESS('站点配置已创建'))

        # 创建类别和选手
        test_data = {
            '弘毅之星': ['张三', '李四', '王五', '赵六', '钱七'],
            '博学之星': ['孙八', '周九', '吴十', '郑一', '王二'],
            '求真之星': ['李三', '张四', '刘五', '陈六', '杨七'],
            '至善之星': ['黄八', '周二', '吴三', '郑四', '王六'],
        }

        for idx, (cat_name, participants) in enumerate(test_data.items()):
            category, created = Category.objects.get_or_create(
                name=cat_name, defaults={'order': idx + 1}
            )
            status = '创建' if created else '已存在'
            self.stdout.write(f'类别 [{cat_name}] {status}')

            for p_idx, p_name in enumerate(participants):
                p, created = Participant.objects.get_or_create(
                    name=p_name, category=category,
                    defaults={'order': p_idx + 1}
                )
                if created:
                    self.stdout.write(f'  选手 [{p_name}] 创建成功')

        # 创建测试评委
        for i in range(1, 6):
            judge, created = Judge.objects.get_or_create(
                name=f'测试评委{i}'
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'评委 [{judge.name}] 创建成功，链接: {judge.get_scoring_url()}'
                ))

        self.stdout.write(self.style.SUCCESS('\n测试数据初始化完成！'))
