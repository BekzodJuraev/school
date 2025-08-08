from django.urls import path
from . import views

urlpatterns=[
    path('', views.Main.as_view(), name='main'),
    path('login/', views.Login.as_view(), name='login'),
    path('register/', views.Register.as_view(), name='register'),
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
    path('logout/',views.logout_view,name='logout'),
    path('approve/',views.ApproveView.as_view(),name='approve'),
    path('staff/',views.StaffView.as_view(),name='staff'),
    path('class/',views.ClassView.as_view(),name='class'),
    path('student/',views.StudentView.as_view(),name='student'),
    path('archive/',views.ArchiveStudent.as_view(),name='archive'),
    path('warehouse/',views.Warehouse.as_view(),name='warehouse')



]