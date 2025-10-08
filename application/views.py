from django.shortcuts import render
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.views.generic import View,ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView,FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render,redirect
from django.urls import reverse_lazy
from django.db import models
from django.shortcuts import get_object_or_404
from django.db.models.functions import Coalesce
from django.db.models import F, DecimalField, ExpressionWrapper
from django.views.decorators.http import require_GET
from rest_framework.response import Response
from rest_framework.views import APIView
import json
from django.http import HttpResponse
from rest_framework import status
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from collections import defaultdict
from django.db.models import Sum,Q,Count,F,Max,Prefetch
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from .models import Profile,Staff,SchoolClass,Student,Warehouse,Invoice,Payment
from django.utils import timezone


class Dashboard(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'dashboard.html'

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      current_month = timezone.now().month
      current_year = timezone.now().year
      context['student'] = Student.objects.filter(archive=False).count()
      context['staff'] = Staff.objects.all().count()
      context['teacher'] = Staff.objects.filter(position='teacher').count()
      context['sum'] = Payment.objects.filter(
         transaction_type='payment',
         created_at__year=current_year,
         created_at__month=current_month
      ).aggregate(total=Sum('sum'))['total'] or 0





      return context


def logout_view(request):
   logout(request)
   return redirect('main')

class Main(TemplateView):
   template_name = 'main.html'

class Login(TemplateView):
   template_name = 'login.html'

   def post(self, request, *args, **kwargs):
      username = request.POST.get('username')
      password = request.POST.get('password')
      next_url = request.GET.get('next')

      # Error handling
      errors = {}



      if not errors:
         user = authenticate(username=username, password=password)
         if user:
            login(request, user)
            return redirect(next_url if next_url else 'dashboard')
         else:
            errors['invalid'] = 'Неверное имя пользователя или пароль'


      return render(request, self.template_name, {'errors': errors})

class Warehouse_View(LoginRequiredMixin,TemplateView):
   template_name = 'warehouse.html'
   login_url = reverse_lazy('login')

   def post(self, request, *args, **kwargs):
      action=request.POST.get('action')
      pk = request.POST.get('pk')
      name = request.POST.get('name')
      price = request.POST.get('price') or 0
      category = request.POST.get('category')


      if action == 'add':
         Warehouse.objects.get_or_create(name=name,categories=category)

      elif action == 'delete':
         Warehouse.objects.filter(pk=pk).delete()

      elif action == 'edit':
         Warehouse.objects.filter(pk=pk).update(name=name,categories=category)

      elif action == 'add_invoice':
         warehouse=request.POST.get('warehouse')
         quantity=request.POST.get('quantity')
         type_invoice=request.POST.get('type_invoice')
         where = 'Склад' if type_invoice == 'Расход' else ''
         to='Склад' if type_invoice == 'Приход' else  request.POST.get('to')
         note=request.POST.get('note')
         Invoice.objects.create(warehouse_id=warehouse, quantity=quantity,price=price, type_invoice=type_invoice,where=where,to=to,comment=note)
         if type_invoice == 'Расход':
            Warehouse.objects.filter(pk=warehouse).update(quantity=F('quantity') - quantity)
         else:
            Warehouse.objects.filter(pk=warehouse).update(quantity=F('quantity') + quantity)










      return redirect(request.path)


   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)

      context['invoice'] = Invoice.objects.annotate(
         total=ExpressionWrapper(
            F('quantity') * F('price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
         )
      ).select_related('warehouse').order_by('-id')

      context['warehouse']=Warehouse.objects.all().order_by('-id')
      return context






class Register(TemplateView):
   template_name = 'register.html'

   def  post(self, request, *args, **kwargs):
      name = request.POST.get('name')
      lastname = request.POST.get('lastname')
      middle_name = request.POST.get('middle_name')
      login=request.POST.get('login')
      password=request.POST.get('password')
      position = request.POST.get('position')
      errors={}
      if User.objects.filter(username=login).exists():
         errors['username'] = "Пользователь с таким логином уже существует"

      if not password or len(password) < 6:
         errors['password'] = "Пароль должен содержать не менее 6 символов"



      if errors:
         return render(request, self.template_name, {'errors': errors, 'data': request.POST})
      user=User.objects.create_user(username=login,password=password)
      Profile.objects.create(
         username=user,
         name=name,
         lastname=lastname,
         middle_name=middle_name,
         position=position,

      )

      return redirect('login')

class ArchiveStudent(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'archive.html'
   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      id = request.POST.get('id')

      prikaz = request.POST.get('prikaz')
      prikaz_date = request.POST.get('prikaz_date')



      if action == 'delete':
         Student.objects.filter(id=id).update(prikaz=prikaz, prikaz_date=prikaz_date, archive=False)



      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      context['class'] = Student.objects.filter(archive=True).select_related('school_class')

      return context
class StudentView(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'student.html'

   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      id = request.POST.get('id')

      name = request.POST.get('name')
      lastname = request.POST.get('lastname')
      middle_name = request.POST.get('middle_name')
      position_gender = request.POST.get('position_gender')
      date_birth = request.POST.get('date_birth')
      phone = request.POST.get('phone')
      photo = request.FILES.get('photo')
      adres = request.POST.get('adres')
      passport = request.POST.get('passport')
      prikaz = request.POST.get('prikaz')
      prikaz_date = request.POST.get('prikaz_date')
      school_class = request.POST.get('school_class')
      document = request.FILES.get('document')

      if action == 'create':
         Student.objects.create(name=name,lastname=lastname,middle_name=middle_name,position_gender=position_gender,date_birth=date_birth,phone=phone,photo=photo,adres=adres,passport=passport,prikaz=prikaz,prikaz_date=prikaz_date,school_class_id=school_class,document=document)


      elif action == 'update':
         staff = Student.objects.filter(id=id).first()
         staff.name = name
         staff.lastname = lastname
         staff.middle_name = middle_name
         staff.position_gender = position_gender
         staff.date_birth = date_birth
         staff.phone = phone
         if 'photo' in request.FILES:
            staff.photo = request.FILES['photo']
         if 'document' in request.FILES:
            staff.document = request.FILES['document']
         staff.prikaz=prikaz
         staff.prikaz_date=prikaz_date
         staff.adres = adres
         staff.passport = passport
         staff.school_class_id=school_class
         staff.school_class.save()
         staff.save()


      elif action == 'delete':

         Student.objects.filter(id=id).update(prikaz_archive=prikaz,prikaz_date_archive=prikaz_date,archive=True)

      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      context['class'] = Student.objects.filter(archive=False).select_related('school_class')
      context['classes']=SchoolClass.objects.all()
      return context

class ClassView(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'class.html'


   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      name=request.POST.get('name')
      id=request.POST.get('id')
      if action == 'create':
         SchoolClass.objects.create(name=name)
      elif action == 'update':
         SchoolClass.objects.filter(id=id).update(name=name)


      elif action == 'delete':

         SchoolClass.objects.filter(id=id).delete()



      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      context['class']=SchoolClass.objects.all()
      return context


class StaffView(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'staff.html'


   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      name =request.POST.get('name')
      lastname = request.POST.get('lastname')
      middle_name = request.POST.get('middle_name')
      position = request.POST.get('position')
      position_gender = request.POST.get('position_gender')
      date_birth =request.POST.get('date_birth')
      phone =request.POST.get('phone')
      photo =request.FILES.get('photo')
      cv_rus = request.FILES.get('cv_rus')
      cv_uz = request.FILES.get('cv_uz')
      diplom = request.FILES.get('diplom')
      adres =request.POST.get('adres')
      passport = request.POST.get('passport')
      id = request.POST.get('id')

      if action == 'create':
         Staff.objects.create(name=name,lastname=lastname,middle_name=middle_name,position=position,position_gender=position_gender,date_birth=date_birth,phone=phone,
                              photo=photo,cv_rus=cv_rus,cv_uz=cv_uz,diplom=diplom,adres=adres,passport=passport)

      elif action == 'update':

         staff=Staff.objects.filter(id=id).first()
         staff.name=name
         staff.lastname = lastname
         staff.middle_name = middle_name
         staff.position = position
         staff.position_gender = position_gender
         staff.date_birth = date_birth
         staff.phone = phone
         if 'photo' in request.FILES:
            staff.photo = request.FILES['photo']
         if 'cv_rus' in request.FILES:
            staff.cv_rus = request.FILES['cv_rus']
         if 'cv_uz' in request.FILES:
            staff.cv_uz = request.FILES['cv_uz']
         if 'diplom' in request.FILES:
            staff.diplom = request.FILES['diplom']




         staff.adres = adres
         staff.passport = passport
         staff.save()

      elif action == 'delete':

         Staff.objects.filter(id=id).delete()



      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      context['staff']=Staff.objects.all()
      return context
class ApproveView(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'approve_staff.html'

   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      pk = request.POST.get('pk')

      if action == "approve":
         Profile.objects.filter(id=pk).update(approve=True)
      else:
         User.objects.filter(profile__id=pk).delete()
         # Profile.objects.filter(id=pk).delete()

      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      context['profile']=Profile.objects.all()
      return  context




class Kassa_view(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'kassa.html'


   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      type_of_payment=request.POST.get('type_of_payment')
      sum=request.POST.get('sum')
      student_pk=request.POST.get('student_id')
      transaction_type="payment"

      pk=request.POST.get('pk')

      if action == "payment":
         Payment.objects.create(sum=sum,type_of_payment=type_of_payment,transaction_type=transaction_type,student_id=student_pk)

      elif action == "delete":
         Payment.objects.filter(pk=pk).delete()

      elif action == "edit":
         Payment.objects.filter(pk=pk).update(sum=sum)




      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      today = now().date()

      students_with_debt = Payment.objects.filter(
         transaction_type="debt",
         created_at__year=today.year,
         created_at__month=today.month
      ).values_list("student_id", flat=True)


      students = Student.objects.exclude(id__in=students_with_debt)


      payments = [
         Payment(
            student=s,
            transaction_type="debt",
            sum=s.discount if s.discount else 3800000
         )
         for s in students
      ]

      Payment.objects.bulk_create(payments)


      context['students']=Student.objects.values('id','name','lastname','middle_name','school_class__name')
      current_month = timezone.now().month
      current_year = timezone.now().year
      context['payment']=Payment.objects.filter(transaction_type='payment').select_related('student__school_class')
      context['more'] = Payment.objects.select_related('student__school_class')
      context['debt']=Payment.objects.values('student__id', 'student__name','student__lastname','student__middle_name','student__school_class__name') \
    .annotate(
        total=(
                Coalesce(Sum('sum', filter=Q(transaction_type='debt')), 0, output_field=models.DecimalField()) -
                Coalesce(Sum('sum', filter=Q(transaction_type='payment')), 0, output_field=models.DecimalField())
        ),last_payment=Max('created_at',filter=Q(transaction_type='payment'))
    ).filter(total__gt=0)
      context['sum_month'] = Payment.objects.filter(
         transaction_type='payment',
         created_at__year=current_year,
         created_at__month=current_month
      ).aggregate(total=Sum('sum'))['total'] or 0
      context['sum_day'] = Payment.objects.filter(
         transaction_type='payment',
         created_at=today
      ).aggregate(total=Sum('sum'))['total'] or 0
      context['sum_year'] = Payment.objects.filter(
         transaction_type='payment',
         created_at__year=current_year,
      ).aggregate(total=Sum('sum'))['total'] or 0



      return  context


def student_more(request, pk):
   student = get_object_or_404(Student, pk=pk)
   transactions = Payment.objects.filter(student=student).order_by("created_at")
   total_payments=Payment.objects.filter(student=student,transaction_type="payment").aggregate(total=Sum('sum'))['total'] or 0
   total_debts=Payment.objects.filter(student=student,transaction_type="debt").aggregate(total=Sum('sum'))['total'] or 0

   payments = []
   debts = []


   for t in transactions:
      if t.transaction_type == "payment":
         payments.append({
            "date": t.created_at.strftime("%d.%m.%Y"),
            "type_of_payment": t.get_type_of_payment_display(),
            "sum": float(t.sum),
         })
      else:
         debts.append({
            "date": t.created_at.strftime("%d.%m.%Y"),
            "sum": float(t.sum),
         })


   return JsonResponse({
      "student_name": f"{student.lastname} {student.name} {student.middle_name}",
      "student_class": student.school_class.name,
      "payments": payments,
      "debts": debts,
      "total_payments": float(total_payments),
      "total_debts": float(total_debts),
      "balance": float(total_debts - total_payments),
   })
class Discount_view(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'discount.html'

   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      pk = request.POST.get('pk')
      today = now().date()
      if action == "discount":
         sum=request.POST.get('sum')
         student_pk = request.POST.get('student_id')

         Student.objects.filter(pk=student_pk).update(discount=sum)
         Payment.objects.filter(student_id=student_pk,transaction_type="debt",created_at__year=today.year,
         created_at__month=today.month).update(sum=sum)

      elif action == "delete":
         Student.objects.filter(pk=pk).update(discount=None)
         Payment.objects.filter(student_id=pk,transaction_type="debt",
         created_at__year=today.year,
         created_at__month=today.month).delete()

      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      context['students'] = Student.objects.values('id', 'name', 'lastname', 'middle_name', 'school_class__name')
      context['discount'] = Student.objects.filter(discount__isnull=False).select_related('school_class')

      return context


class Printer_checkView(TemplateView):
   template_name = 'printer.html'

class ReportView(LoginRequiredMixin,TemplateView):
   template_name = 'report.html'
   login_url = reverse_lazy('login')

# @csrf_exempt
# def turnstile_event_view(request):
#     if request.method == "POST":
#         print(request.body)
#
#     return JsonResponse({"Successe": "Good"}, status=200)


# class Main(TemplateView):
#     template_name = 'table.html'
#
#     def get_context_data(self, *, object_list=None, **kwargs):
#         context =super().get_context_data(**kwargs)
#         today = datetime.today()
#         year, month = today.year, today.month
#
#         # Define the start and end dates of the month
#         start_date = datetime(year, month, 1)
#         if month == 12:
#             end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
#         else:
#             end_date = datetime(year, month + 1, 1) - timedelta(days=1)
#
#         # Generate dates for the month, excluding Saturdays (weekday 5)
#         dates = []
#         current_date = start_date
#         while current_date <= end_date:
#             if current_date.weekday() != 6:  # Exclude Saturdays (Saturday = 5)
#                 dates.append(current_date.strftime("%d.%m.%Y"))
#             current_date += timedelta(days=1)
#         context['dates']=dates
#         context['teachers'] = Teachers.objects.prefetch_related("lessons").annotate(
#             total=Sum('lessons__hour', filter=Q(lessons__created_at__month=month))
#         )
#
#
#         return context
#
#
# def get_month_dates_keyboard():
#     today = datetime.today()
#     year, month = today.year, today.month
#
#     # Define the start and end dates of the month
#     start_date = datetime(year, month, 1)
#     end_date = datetime(year, month + 1, 1) - timedelta(days=1)  # Last day of the month
#
#     # Generate dates for the month, excluding Sundays (weekday 6)
#     dates = []
#     current_date = start_date
#     while current_date <= end_date:
#         if current_date.weekday() != 6:  # Exclude Sundays
#             dates.append(current_date.strftime("%d.%m.%Y"))
#         current_date += timedelta(days=1)
#
#     # Create Inline Keyboard Buttons
#     keyboard = []
#     row = []
#
#     for i, date in enumerate(dates):
#         row.append(InlineKeyboardButton(text=date, callback_data=f"date:{date}"))
#         if (i + 1) % 3 == 0:  # Arrange 3 buttons per row
#             keyboard.append(row)
#             row = []
#
#     if row:  # Append any remaining buttons
#         keyboard.append(row)
#
#     return InlineKeyboardMarkup(keyboard)
