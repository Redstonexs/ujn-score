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
    SCORING_MODE_CHOICES = (
        ("score", "分数模式"),
        ("vote", "投票模式"),
    )

    site_name = models.CharField(max_length=200, default="评分系统", verbose_name="活动标题")
    background_image = models.ImageField(upload_to='backgrounds/', blank=True, null=True, verbose_name="背景图片")
    logo_image = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo图片")
    primary_color = models.CharField(max_length=20, default="#1890ff", verbose_name="主题色")
    # 注意：admin_password 为明文存储。这是有意为之的设计取舍——
    # 此密码为应用级管理密码（非用户凭据），需要在前端管理面板中回显。
    # 如需更高安全性，可改用 Django 的 make_password/check_password 机制，
    # 但需同步修改前端管理面板的密码显示和验证逻辑。
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
        help_text="开启后，统计总分与平均分时按配置数量去掉最低分和最高分。",
    )
    exclude_lowest_count = models.PositiveIntegerField(
        default=1,
        verbose_name="去掉最低分数量",
    )
    exclude_highest_count = models.PositiveIntegerField(
        default=1,
        verbose_name="去掉最高分数量",
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
    college_field_name = models.CharField(
        max_length=100,
        default="学院",
        verbose_name="学院字段名",
    )
    scoring_mode = models.CharField(
        max_length=20,
        choices=SCORING_MODE_CHOICES,
        default="score",
        verbose_name="全局打分模式",
    )
    vote_total_count = models.IntegerField(
        default=10,
        verbose_name="默认投票总数",
        help_text="从多少人中选择",
    )
    vote_select_count = models.IntegerField(
        default=3,
        verbose_name="默认选择人数",
        help_text="选择多少人",
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
    SCORE_VALUE_TYPE_CHOICES = (
        ("integer", "整数"),
        ("decimal", "小数"),
        ("integer_decimal", "整数和小数"),
    )
    SCORING_MODE_CHOICES = (
        ("default", "使用全局设置"),
        ("score", "分数模式"),
        ("vote", "投票模式"),
    )
    name = models.CharField(max_length=100, unique=True, verbose_name="类别名称")
    order = models.IntegerField(default=0, verbose_name="排序")
    description = models.TextField(blank=True, default="", verbose_name="类别描述")
    scoring_mode = models.CharField(
        max_length=20,
        choices=SCORING_MODE_CHOICES,
        default="default",
        verbose_name="打分模式",
    )
    # 投票模式相关字段
    vote_total_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="投票总数",
        help_text="从多少人中选择",
    )
    vote_select_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="选择人数",
        help_text="选择多少人",
    )
    # 分数模式相关字段
    score_min = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="最低分"
    )
    score_max = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name="最高分"
    )
    score_value_type = models.CharField(
        max_length=20,
        choices=SCORE_VALUE_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name="合法打分类型",
    )
    allow_duplicate_scores = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="允许重复打分",
    )
    exclude_extreme_scores = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="统计时去掉最高分和最低分",
    )
    exclude_lowest_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="去掉最低分数量",
    )
    exclude_highest_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="去掉最高分数量",
    )

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
    college = models.CharField(max_length=200, blank=True, default="", verbose_name="学院")

    class Meta:
        ordering = ['category__order', 'order', 'id']
        verbose_name = "参赛选手"
        verbose_name_plural = "参赛选手"

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Judge(models.Model):
    """评委"""
    order = models.IntegerField(default=1, verbose_name="序号")
    name = models.CharField(max_length=100, verbose_name="评委姓名")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="访问令牌")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ['order', 'id']
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


class Vote(models.Model):
    """投票记录"""
    judge = models.ForeignKey(
        Judge, on_delete=models.CASCADE,
        related_name='votes', verbose_name="评委"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='votes', verbose_name="所属类别"
    )
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE,
        related_name='votes', verbose_name="被选中的参赛选手"
    )
    vote_order = models.IntegerField(default=0, verbose_name="投票排序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投票时间")

    class Meta:
        unique_together = ['judge', 'category', 'participant']
        ordering = ['judge', 'category', 'vote_order']
        verbose_name = "投票记录"
        verbose_name_plural = "投票记录"

    def __str__(self):
        return f"{self.judge.name} → {self.category.name} → {self.participant.name}"
