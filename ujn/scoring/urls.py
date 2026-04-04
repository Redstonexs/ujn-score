from django.urls import path

from . import views

urlpatterns = [
    # 公开接口
    path('config/', views.get_site_config, name='get_site_config'),
    path('categories/', views.get_categories, name='get_categories'),
    path('participants/', views.get_participants, name='get_participants'),

    # 评委接口
    path('judge/<uuid:token>/auth/', views.judge_auth, name='judge_auth'),
    path('judge/<uuid:token>/qrcode/', views.generate_qrcode, name='generate_qrcode'),
    path('submit/', views.submit_scores, name='submit_scores'),

    # 管理员接口
    path('admin/verify/', views.verify_admin, name='verify_admin'),
    path('admin/config/', views.get_admin_config, name='get_admin_config'),
    path('admin/config/update/', views.update_admin_config, name='update_admin_config'),
    path('admin/qrcode/', views.generate_admin_qrcode, name='generate_admin_qrcode'),
    path('admin/template/', views.download_import_template, name='download_import_template'),
    path('admin/scores/', views.get_all_scores, name='get_all_scores'),
    path('admin/export/', views.export_excel, name='export_excel'),
    path('admin/clear/', views.clear_scores, name='clear_scores'),
    path('admin/judges/', views.get_judges, name='get_judges'),
    path('admin/judges/batch/', views.batch_create_judges, name='batch_create_judges'),
    path('admin/judges/qrcodes/export/', views.export_all_judge_qrcodes, name='export_all_judge_qrcodes'),
    path('admin/judges/<int:judge_id>/delete/', views.delete_judge, name='delete_judge'),
    path('admin/import/', views.import_data, name='import_data'),
]
