import uuid
from decimal import Decimal
from django.db import models


class SiteConfig(models.Model):
    """站点全局配置（单例模式）"""
    SCORE_VALUE_TYPE_CHOICES = (
        ("integer", "整数"),
        ("decimal", "小数"),
        ("integer_decimal", "整数和小数"),
    )

    site_name = models.CharField(max_length=200, default="评分系统", verbose_name="活动标题")
    background_image = models.ImageField(upload_to='backgrounds/', blank=True, null=True, verbose_name="背景图片")
    logo_image = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo图片")
    primary_color = models.CharField(max_length=20, default="#1890ff", verbose_name="主题色")
    admin_password = models.CharField(max_length=100, default="admin123", verbose_name="管理密码")
    score_min = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("1.00"), verbose_name="最低分")
    score_max = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("100.00"), verbose_name="最高分")
    score_value_type = models.CharField(
        max_length=20,
        choices=SCORE_VALUE_TYPE_CHOICES,
        default="integer",
        verbose_name="合法打分类型",
    )
    allow_duplicate_scores = models.BooleanField(default=True, verbose_name="允许重复打分")
    allow_scoring = models.BooleanField(default=True, verbose_name="允许评分")
    exclude_extreme_scores = models.BooleanField(
        default=False,
        verbose_name="统计时去掉最高分和最低分",
        help_text="开启后，统计总分与平均分时会在有效评分数大于等于3时去掉一条最高分和一条最低分。",
    )
    base_url = models.CharField(
        max_length=500,
        default="http://localhost:5173",
        verbose_name="前端基础URL",
        help_text="用于生成管理员与评委二维码链接，例如 https://score.example.com",
    )
    participant_sheet_name = models.CharField(
        max_length=100,
        default="选手数据",
        verbose_name="Excel选手Sheet名称",
    )
    judge_sheet_name = models.CharField(
        max_length=100,
        default="评委数据",
        verbose_name="Excel评委Sheet名称",
    )
    category_field_name = models.CharField(
        max_length=100,
        default="类别",
        verbose_name="类别字段名",
    )
    participant_field_name = models.CharField(
        max_length=100,
        default="选手",
        verbose_name="选手字段名",
    )
    judge_field_name = models.CharField(
        max_length=100,
        default="评委",
        verbose_name="评委字段名",
    )
    order_field_name = models.CharField(
        max_length=100,
        default="序号",
        verbose_name="序号字段名",
    )
    description_field_name = models.CharField(
        max_length=100,
        default="备注",
        verbose_name="备注字段名",
    )

    class Meta:
        verbose_name = "站点配置"
        verbose_name_plural = "站点配置"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def get_frontend_base(self):
        return self.base_url.rstrip('/')

    def get_admin_url(self):
        return f"{self.get_frontend_base()}/manage"


class Category(models.Model):
    """比赛类别"""
    name = models.CharField(max_length=100, unique=True, verbose_name="类别名称")
    order = models.IntegerField(default=0, verbose_name="排序")
    description = models.TextField(blank=True, default="", verbose_name="类别描述")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "比赛类别"
        verbose_name_plural = "比赛类别"

    def __str__(self):
        return self.name


class Participant(models.Model):
    """参赛选手"""
    name = models.CharField(max_length=100, verbose_name="选手姓名")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='participants', verbose_name="所属类别"
    )
    order = models.IntegerField(default=0, verbose_name="序号")
    description = models.TextField(blank=True, default="", verbose_name="选手描述")
    photo = models.ImageField(upload_to='participants/', blank=True, null=True, verbose_name="选手照片")

    class Meta:
        ordering = ['category__order', 'order', 'id']
        verbose_name = "参赛选手"
        verbose_name_plural = "参赛选手"

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Judge(models.Model):
    """评委"""
    name = models.CharField(max_length=100, verbose_name="评委姓名")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="访问令牌")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ['id']
        verbose_name = "评委"
        verbose_name_plural = "评委"

    def __str__(self):
        return self.name

    def get_scoring_url(self):
        config = SiteConfig.get_config()
        return f"{config.get_frontend_base()}/judge/{self.token}"


class Score(models.Model):
    """评分记录"""
    judge = models.ForeignKey(
        Judge, on_delete=models.CASCADE,
        related_name='scores', verbose_name="评委"
    )
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE,
        related_name='scores', verbose_name="参赛选手"
    )
    score = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="分数")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评分时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        unique_together = ['judge', 'participant']
        ordering = ['judge', 'participant']
        verbose_name = "评分记录"
        verbose_name_plural = "评分记录"

    def __str__(self):
        return f"{self.judge.name} → {self.participant.name}: {self.score}"
