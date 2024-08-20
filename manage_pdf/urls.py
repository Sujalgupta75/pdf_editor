from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'manage_pdf'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_pdf', views.upload_pdf, name='upload_pdf'),  # Corrected function name
    path('split_pdf', views.split_pdf, name="split_pdf"),
    path('pdf_download/', views.pdf_download, name='pdf_download'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('upload_pdfs', views.upload_pdfs, name='upload_pdfs'),
    path('merge_pdf/', views.merge_pdf, name='merge_pdf'),  # Added merge_pdf view
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
