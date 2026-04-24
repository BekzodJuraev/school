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
    path('warehouse/',views.Warehouse_View.as_view(),name='warehouse'),
    path('kassa/',views.Kassa_view.as_view(),name='kassa'),
    path('kassa_sadik/',views.Kassa_sadik_view.as_view(),name='kassa_sadik'),
    path('inventory/',views.Inventory_view.as_view(),name="inventory"),
    path('get-inventory/<int:room_id>/', views.get_room_inventory, name='get_inventory'),
    path('api/create-cabinet/', views.create_cabinet_api, name='create-cabinet'),
    path('api/create-item/', views.items_api, name='create-item'),
    path('api/delete-item/<int:item_id>/', views.items_api, name='delete-item'),
    path("student/<int:pk>/more/", views.student_more, name="student_more"),
    path('discount/',views.Discount_view.as_view(),name='discount'),
    path('printer/',views.Printer_checkView.as_view(),name='printer'),
    path('report/',views.ReportView.as_view(),name='report'),
    path('kitchen/',views.Kitchen_View.as_view(),name='kitchen')




]