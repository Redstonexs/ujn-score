from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Judge, Participant, Score, SiteConfig


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = (
        'site_name',
        'primary_color',
        'score_min',
        'score_max',
        'allow_scoring',
        'exclude_extreme_scores',
        'admin_url_link',
    )
    readonly_fields = ('admin_url_link',)
    fieldsets = (
        ('基础设置', {
            'fields': ('site_name', 'base_url', 'admin_url_link', 'primary_color', 'admin_password')
        }),
        ('外观设置', {
            'fields': ('background_image', 'logo_image')
        }),
        ('评分设置', {
            'fields': ('score_min', 'score_max', 'allow_scoring', 'exclude_extreme_scores')
        }),
        ('字段配置（手动输入）', {
            'fields': (
                'participant_sheet_name',
                'judge_sheet_name',
                'category_field_name',
                'participant_field_name',
                'judge_field_name',
                'order_field_name',
            )
        }),
    )

    def admin_url_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.get_admin_url(), obj.get_admin_url())
    admin_url_link.short_description = '管理员入口'

    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 3
    fields = ('name', 'order', 'description', 'photo')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'participant_count', 'description')
    ordering = ('order',)
    inlines = [ParticipantInline]

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = '选手数量'


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('category__order', 'order')


@admin.register(Judge)
class JudgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'token', 'is_active', 'scoring_url_link', 'qrcode_link', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('token', 'scoring_url_display', 'qrcode_preview')
    actions = ['activate_judges', 'deactivate_judges']

    def scoring_url_link(self, obj):
        url = obj.get_scoring_url()
        return format_html('<a href="{}" target="_blank">打开链接</a>', url)
    scoring_url_link.short_description = '评分链接'

    def scoring_url_display(self, obj):
        url = obj.get_scoring_url()
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    scoring_url_display.short_description = '评分链接'

    def qrcode_link(self, obj):
        return format_html(
            '<a href="/api/judge/{}/qrcode/" target="_blank">查看二维码</a>',
            obj.token
        )
    qrcode_link.short_description = '二维码'

    def qrcode_preview(self, obj):
        return format_html(
            '<img src="/api/judge/{}/qrcode/" width="200" height="200" />',
            obj.token
        )
    qrcode_preview.short_description = '二维码预览'

    def activate_judges(self, request, queryset):
        queryset.update(is_active=True)
    activate_judges.short_description = '启用选中的评委'

    def deactivate_judges(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_judges.short_description = '禁用选中的评委'


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('judge', 'participant', 'score', 'created_at')
    list_filter = ('judge', 'participant__category')
    search_fields = ('judge__name', 'participant__name')
    readonly_fields = ('created_at', 'updated_at')


admin.site.site_header = '评分系统管理后台'
admin.site.site_title = '评分系统'
admin.site.index_title = '管理面板'
