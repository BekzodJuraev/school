from django.shortcuts import render
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.views.generic import View,ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView,FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render,redirect
from django.urls import reverse_lazy
from django.db import models
from django.db import transaction
from django.db.models.deletion import ProtectedError
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
from django.db.models import Sum,Q,Count,F,Max,Prefetch,Value
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from .models import Profile,Staff,SchoolClass,Student,Warehouse,Invoice,Payment,Inventory,Inventory_cabinet,Inventory_items,Turniket,TrackingTurniket
from django.utils import timezone
from django.utils import timezone
from decimal import Decimal
class Dashboard(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'dashboard.html'

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      current_month = timezone.now().month
      current_year = timezone.now().year
      context['student'] = Student.objects.filter(archive=False).count()
      context['preschool'] = Student.objects.filter(archive=False,education_type="preschool").count()
      context['school'] = Student.objects.filter(archive=False,education_type="school").count()
      context['kinder'] = Student.objects.filter(archive=False,education_type="kindergarten").count()
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

class Kitchen_View(LoginRequiredMixin,TemplateView):
   template_name = 'kitchen.html'
   login_url = reverse_lazy('login')

   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      if request.content_type == 'application/json':
         try:
            data = json.loads(request.body)
            item_id = data.get('id')
            expense_quantity = data.get('quantity', 0)


            if not item_id or float(expense_quantity) <= 0:
               return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

            # Используем транзакцию, чтобы оба действия выполнились вместе
            active_arrivals = Invoice.objects.filter(
               warehouse_id=item_id,
               type_invoice="Приход",
               remaining_quantity__gt=0
            ).order_by('created_at')

            remaining_to_deduct = Decimal(str(expense_quantity))  # Сколько всего нужно списать
            where = "Склад"
            to = "Кухня"
            type_invoice = 'Расход'
            note = "Списание через таблицу кухни"

            with transaction.atomic():
               for arrival in active_arrivals:
                  if remaining_to_deduct <= 0:
                     break

                  # Проверяем, сколько можем забрать из этой партии
                  if arrival.remaining_quantity >= remaining_to_deduct:
                     # В этой партии достаточно товара
                     arrival.remaining_quantity = F('remaining_quantity') - remaining_to_deduct
                     arrival.save()

                     # Создаем запись расхода с ценой этой партии
                     Invoice.objects.create(
                        warehouse_id=item_id,
                        quantity=remaining_to_deduct,  # Списываем остаток запроса
                        price=arrival.price,
                        type_invoice=type_invoice,
                        where=where, to=to, comment=note
                     )
                     remaining_to_deduct = 0  # Всё списано
                  else:
                     # В этой партии мало товара, забираем всё что есть
                     can_take = arrival.remaining_quantity
                     arrival.remaining_quantity = 0
                     arrival.save()

                     # Создаем запись расхода на ту часть, которую забрали
                     Invoice.objects.create(
                        warehouse_id=item_id,
                        quantity=can_take,  # Списываем сколько было в этой партии
                        price=arrival.price,
                        type_invoice=type_invoice,
                        where=where, to=to, comment=note
                     )

                     remaining_to_deduct -= can_take




            return JsonResponse({'status': 'success'})

         except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



      if action == 'add_invoice':
         warehouse = request.POST.get('warehouse')
         quantity = request.POST.get('quantity')
         note = request.POST.get('note')

         # Invoice.objects.create(warehouse_id=warehouse, quantity=quantity, price=0, type_invoice='Расход',
         #                        where="Склад", to="Кухня", comment=note)
         # Warehouse.objects.filter(pk=warehouse).update(quantity=F('quantity') - quantity)

      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)

      today = timezone.now().date()
      yesterday = today- timedelta(days=1)

      context['invoice'] = Invoice.objects.filter(warehouse__categories__in=["Кухня","Хозтовары"],type_invoice='Расход').annotate(
         total=ExpressionWrapper(
            F('quantity') * F('price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
         )
      ).select_related('warehouse').order_by('-id')

      context['warehouse'] = Warehouse.objects.filter(
         categories__in=["Кухня", "Хозтовары"]
      ).annotate(
         # 1. ВСЕ ПРИХОДЫ И РАСХОДЫ (для итогового остатка на текущий момент)
         all_in=Coalesce(Sum('invoice__quantity', filter=Q(
            invoice__type_invoice="Приход"
         )), Value(0), output_field=DecimalField()),

         all_out=Coalesce(Sum('invoice__quantity', filter=Q(
            invoice__type_invoice="Расход"
         )), Value(0), output_field=DecimalField()),

         # Итоговый остаток сейчас (Конец дня)
         stock=F('all_in') - F('all_out'),

         # 2. ОБОРОТЫ ЗА СЕГОДНЯ
         prixod_today=Coalesce(Sum('invoice__quantity', filter=Q(
            invoice__type_invoice="Приход",
            invoice__created_at=today
         )), Value(0), output_field=DecimalField()),

         rasxod_today=Coalesce(Sum('invoice__quantity', filter=Q(
            invoice__type_invoice="Расход",
            invoice__created_at=today
         )), Value(0), output_field=DecimalField()),

         # 3. НАЧАЛО ДНЯ (Всё что было накоплено СТРОГО ДО СЕГОДНЯ)
         in_before=Coalesce(Sum('invoice__quantity', filter=Q(
            invoice__type_invoice="Приход",
            invoice__created_at__lt=today
         )), Value(0), output_field=DecimalField()),

         out_before=Coalesce(Sum('invoice__quantity', filter=Q(
            invoice__type_invoice="Расход",
            invoice__created_at__lt=today
         )), Value(0), output_field=DecimalField()),

         # Та самая стабильная цифра на 00:00
         today_stock=F('in_before') - F('out_before')

      ).order_by('-id')
      return context






class Warehouse_View(LoginRequiredMixin,TemplateView):
   template_name = 'warehouse.html'
   login_url = reverse_lazy('login')

   def post(self, request, *args, **kwargs):
      action=request.POST.get('action')
      pk = request.POST.get('pk')
      name = request.POST.get('name')
      price = request.POST.get('price') or 0
      category = request.POST.get('category')
      unit=request.POST.get('unit')



      if action == 'add':
         Warehouse.objects.get_or_create(name=name,categories=category,unit=unit)

      if action == 'delete':

         try:
            Warehouse.objects.filter(pk=pk).delete()
         except ProtectedError:
            return redirect(request.path)

      elif action == 'edit':
         Warehouse.objects.filter(pk=pk).update(name=name,categories=category,unit=unit)

      elif action == 'add_invoice':
         warehouse=request.POST.get('warehouse')
         quantity=request.POST.get('quantity')
         type_invoice=request.POST.get('type_invoice')
         type_of_payment = request.POST.get('type_of_payment')
         where = 'Склад' if type_invoice == 'Расход' else 'Поставщик'
         to='Склад' if type_invoice == 'Приход' else  request.POST.get('to')
         note=request.POST.get('note')

         if type_invoice == 'Расход':
            active_arrivals = Invoice.objects.filter(
               warehouse_id=warehouse,
               type_invoice="Приход",
               remaining_quantity__gt=0
            ).order_by('created_at')

            remaining_to_deduct = Decimal(str(quantity))  # Сколько всего нужно списать

            with transaction.atomic():
               for arrival in active_arrivals:
                  if remaining_to_deduct <= 0:
                     break

                  # Проверяем, сколько можем забрать из этой партии
                  if arrival.remaining_quantity >= remaining_to_deduct:

                     arrival.remaining_quantity = F('remaining_quantity') - remaining_to_deduct
                     arrival.save()

                     # Создаем запись расхода с ценой этой партии
                     Invoice.objects.create(
                        warehouse_id=warehouse,
                        quantity=remaining_to_deduct,  # Списываем остаток запроса
                        price=arrival.price,
                        type_invoice=type_invoice,
                        where=where, to=to, comment=note
                     )
                     remaining_to_deduct = 0  # Всё списано
                  else:
                     # В этой партии мало товара, забираем всё что есть
                     can_take = arrival.remaining_quantity
                     arrival.remaining_quantity = 0
                     arrival.save()

                     # Создаем запись расхода на ту часть, которую забрали
                     Invoice.objects.create(
                        warehouse_id=warehouse,
                        quantity=can_take,  # Списываем сколько было в этой партии
                        price=arrival.price,
                        type_invoice=type_invoice,
                        where=where, to=to, comment=note
                     )
                     # Уменьшаем общую потребность и идем к следующей партии
                     remaining_to_deduct -= can_take

         else:
            Invoice.objects.create(warehouse_id=warehouse, quantity=quantity, price=price, type_invoice=type_invoice,
                                   where=where, to=to, comment=note, type_of_payment=type_of_payment,remaining_quantity=quantity)

      return redirect(request.path)


   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)

      context['invoice'] = Invoice.objects.annotate(
         total=ExpressionWrapper(
            F('quantity') * F('price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
         )
      ).select_related('warehouse').order_by('-id')

      context['warehouse']=Warehouse.objects.annotate(

         a=Coalesce(Sum('invoice__quantity', filter=Q(invoice__type_invoice="Приход")), 0, output_field=models.DecimalField()),

         # 2. Считаем расходы, принудительно заменяя NULL на 0
         b=Coalesce(Sum('invoice__quantity', filter=Q(invoice__type_invoice="Расход")),0, output_field=models.DecimalField()),

         # 3. Вычитаем одно из другого
         stock=F('a') - F('b')).order_by('-id')
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
      type_education=request.POST.get("type_education")

      if action == 'create':
         Student.objects.create(name=name,lastname=lastname,middle_name=middle_name,position_gender=position_gender,date_birth=date_birth,phone=phone,photo=photo,adres=adres,passport=passport,prikaz=prikaz,prikaz_date=prikaz_date,school_class_id=school_class,document=document,education_type=type_education)


      elif action == 'update':
         staff = Student.objects.filter(id=id).first()
         staff.education_type = type_education
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
      note=request.POST.get('note')
      transaction_type="payment"

      pk=request.POST.get('pk')

      if action == "payment":
         Payment.objects.create(sum=sum,type_of_payment=type_of_payment,transaction_type=transaction_type,student_id=student_pk,comment=note)

      elif action == "delete":
         Payment.objects.filter(pk=pk).delete()

      elif action == "edit":
         Payment.objects.filter(pk=pk).update(sum=sum,comment=note)




      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      today = now().date()

      students_with_debt = Payment.objects.filter(
         transaction_type="debt",
         created_at__year=today.year,
         created_at__month=today.month,
      ).values_list("student_id", flat=True)


      students = Student.objects.filter(education_type="school").exclude(id__in=students_with_debt).exclude(archive=True)


      payments = [
         Payment(
            student=s,
            transaction_type="debt",
            sum=s.discount if s.discount else 3800000
         )
         for s in students
      ]

      Payment.objects.bulk_create(payments)


      context['students']=Student.objects.filter(education_type="school").values('id','name','lastname','middle_name','school_class__name')
      current_month = timezone.now().month
      current_year = timezone.now().year
      context['payment']=Payment.objects.filter(student__education_type="school",transaction_type='payment').select_related('student__school_class')
      context['more'] = Payment.objects.select_related('student__school_class')
      context['debt']=Payment.objects.filter(student__education_type="school").values('student__id', 'student__name','student__lastname','student__middle_name','student__school_class__name') \
    .annotate(
        total=(
                Coalesce(Sum('sum', filter=Q(transaction_type='debt')), 0, output_field=models.DecimalField()) -
                Coalesce(Sum('sum', filter=Q(transaction_type='payment')), 0, output_field=models.DecimalField())
        ),last_payment=Max('created_at',filter=Q(transaction_type='payment'))
    ).filter(total__gt=0)
      context['sum_month'] = Payment.objects.filter(
         student__education_type="school",
         transaction_type='payment',
         created_at__year=current_year,
         created_at__month=current_month
      ).aggregate(total=Sum('sum'))['total'] or 0
      context['sum_day'] = Payment.objects.filter(
         student__education_type="school",
         transaction_type='payment',
         created_at=today
      ).aggregate(total=Sum('sum'))['total'] or 0
      context['sum_year'] = Payment.objects.filter(
         student__education_type="school",
         transaction_type='payment',
         created_at__year=current_year,
      ).aggregate(total=Sum('sum'))['total'] or 0



      return  context


@csrf_exempt  # Для тестов, но лучше использовать CSRF-токен в fetch
def create_cabinet_api(request):
   if request.method == "POST":
      try:
         data = json.loads(request.body)
         room_name = data.get('name')
         class_id=data.get('class_id')

         if room_name:
            # Создаем запись в БД
            new_room = Inventory_cabinet.objects.create(name=room_name,school_class_id=class_id)

            return JsonResponse({
               'status': 'success',
               'id': new_room.id,
               'name': new_room.name
            })
      except Exception as e:
         return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

   return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)



@csrf_exempt  # Для тестов, но лучше использовать CSRF-токен в fetch
def create_itemincabinet_api(request, cabinet_id=None, item_id=None):
   if request.method == "POST":
      try:
         data = json.loads(request.body)
         item_type_id = data.get('item_id')
         quantity = int(data.get('quantity', 1))

         # 1. Ищем ЛЮБУЮ существующую активную запись этого предмета в этом кабинете
         obj = Inventory.objects.filter(
            cabinet_id=cabinet_id,
            item_type_id=item_type_id,
            archive=False
         ).first()

         if obj:
            # Если нашли — просто плюсуем
            obj.quantity += quantity
            obj.save()
            created = False
         else:
            # Если вообще нет — создаем новую
            obj = Inventory.objects.create(
               cabinet_id=cabinet_id,
               item_type_id=item_type_id,
               quantity=quantity,
               archive=False
            )
            created = True

         return JsonResponse({
            'status': 'success',
            'id': obj.id,
            'name': obj.item_type.name,
            'quantity': obj.quantity,
            'is_new': created,
            'item_type_id': item_type_id  # Обязательно возвращаем это!
         })
      except Exception as e:
         return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

   # --- СПИСАНИЕ ПРЕДМЕТА (PATCH) ---
   elif request.method == "PATCH":
      try:
         data = json.loads(request.body)
         comment = data.get('comment', 'Причина не указана')
         qty_to_archive = int(data.get('quantity', 1))

         item = Inventory.objects.get(id=item_id)

         completely_removed = False
         remaining_qty = item.quantity - qty_to_archive

         if remaining_qty <= 0:
            # Списываем всю запись полностью
            item.archive = True
            item.comment = comment
            item.save()
            completely_removed = True
         else:

            # Уменьшаем количество текущей записи
            item.quantity = remaining_qty
            item.save()

            # (Опционально) Создаем отдельную архивную запись для истории
            # Чтобы в архиве было видно, что списано именно X штук
            Inventory.objects.create(
               cabinet=item.cabinet,
               item_type=item.item_type,
               quantity=qty_to_archive,
               archive=True,
               comment=comment
            )

         return JsonResponse({
            'status': 'success',
            'completely_removed': completely_removed,
            'remaining_qty': remaining_qty,
            'id': item_id
         })
      except Exception as e:
         return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

   return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def items_api(request, item_id=None): # Добавили item_id для удаления
    # --- СОЗДАНИЕ (POST) ---
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get('name')

            if name:
                new_item = Inventory_items.objects.create(name=name)
                return JsonResponse({
                    'status': 'success',
                    'id': new_item.id,
                    'name': new_item.name
                })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # --- УДАЛЕНИЕ (DELETE) ---
    elif request.method == "DELETE":
        try:
            # Если ID передан в URL или в теле запроса
            if not item_id:
                data = json.loads(request.body)
                item_id = data.get('id')

            is_used = Inventory.objects.filter(item_type_id=item_id).exists()

            if is_used:
               # Если товар где-то числится, возвращаем ошибку, а не успех
               return JsonResponse({
                  'status': 'error',
                  'message': 'Нельзя удалить: этот товар числится в кабинетах. Сначала спишите его оттуда.'
               }, status=400)  # 400 - Bad Request

            # 2. Если не используется — удаляем
            deleted_count, _ = Inventory_items.objects.filter(id=item_id).delete()



            return JsonResponse({'status': 'success', 'message': 'Item deleted'})
        except Inventory_items.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


def get_room_inventory(request, room_id):
   # 1. Находим кабинет
   cabinet = get_object_or_404(Inventory_cabinet, id=room_id)

   # 2. Получаем предметы этого кабинета
   items = Inventory.objects.filter(cabinet=cabinet, archive=False).select_related('item_type')

   # 3. Считаем детей через связанный school_class
   # Если класс привязан к кабинету, считаем количество его учеников
   students_count = 0
   if cabinet.school_class:
      students_count = Student.objects.filter(school_class=cabinet.school_class).count()

   data = []
   for i in items:
      data.append({
         'name': i.item_type.name,
         'quantity': i.quantity,
         'id': i.id,
         'item_type_id': i.item_type.id
      })

   return JsonResponse({
      'status': 'success',
      'cabinet_id': cabinet.id,
      'students_count': students_count,
      'items': data
   })


def get_cabinet_stats(request, room_id):
   cabinet = Inventory_cabinet.objects.annotate(
      total_item=Count('items', filter=Q(items__archive=False))
   ).filter(id=room_id).first()

   if cabinet:
      return JsonResponse({
         'status': 'success',
         'total_item': cabinet.total_item
      })
   return JsonResponse({'status': 'error'}, status=404)
class Inventory_view(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'inventory.html'

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      context['classes']=SchoolClass.objects.all()
      context['cabinet']=Inventory_cabinet.objects.prefetch_related(
    "items"
).annotate(
    total_item=Count('items', filter=Q(items__archive=False))
).order_by("-id")

      context['items']=Inventory_items.objects.all().order_by("-id")
      context['archive']=Inventory.objects.filter(archive=True).select_related("cabinet","item_type")
      context['total_cabinet']=Inventory_cabinet.objects.all().count()
      context['total_items']=Inventory.objects.filter(archive=False).values("item_type__name").aggregate(total_items=Sum("quantity"))['total_items'] or 0
      context['total_archive'] = \
      Inventory.objects.filter(archive=True).values("item_type__name").aggregate(total_items=Sum("quantity"))[
         'total_items'] or 0



      return context


class Turniket_view(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'turniket.html'

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)

      context['tracking']=TrackingTurniket.objects.all().select_related('turniket')


      return context

class Kassa_lager_view(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'kassa_lager.html'

class Kassa_sadik_view(LoginRequiredMixin,TemplateView):
   login_url = reverse_lazy('login')
   template_name = 'kassa_sadik.html'


   def post(self, request, *args, **kwargs):
      action = request.POST.get('action')
      type_of_payment=request.POST.get('type_of_payment')
      sum=request.POST.get('sum')
      student_pk=request.POST.get('student_id')
      note=request.POST.get('note')
      transaction_type="payment"
      created_at=request.POST.get('payment_date')


      pk=request.POST.get('pk')

      if action == "payment":
         Payment.objects.create(sum=sum,type_of_payment=type_of_payment,created_at=created_at,transaction_type=transaction_type,student_id=student_pk,comment=note)

      elif action == "delete":
         Payment.objects.filter(pk=pk).delete()

      elif action == "edit":

         Payment.objects.filter(pk=pk).update(sum=sum,created_at=created_at,type_of_payment=type_of_payment,comment=note)




      return redirect(request.path)

   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)
      today = now().date()

      students_with_debt = Payment.objects.filter(
         transaction_type="debt",
         created_at__year=today.year,
         created_at__month=today.month,
      ).values_list("student_id", flat=True)


      students = Student.objects.filter(education_type__in=['kindergarten','preschool']).exclude(id__in=students_with_debt).exclude(archive=True)

      def caluclate(s):
         if s.discount:
            return s.discount
         elif s.education_type == "kindergarten":
            return 2200000
         else:
            return 2800000


      payments = [
         Payment(
            student=s,
            transaction_type="debt",
            sum=caluclate(s)
         )
         for s in students
      ]

      Payment.objects.bulk_create(payments)


      context['students']=Student.objects.filter(education_type__in=['kindergarten','preschool']).values('id','name','lastname','middle_name','school_class__name')
      current_month = timezone.now().month
      current_year = timezone.now().year
      context['payment']=Payment.objects.filter(student__education_type__in=['kindergarten','preschool'],transaction_type='payment').select_related('student__school_class').order_by("-id")
      context['more'] = Payment.objects.select_related('student__school_class')
      context['debt']=Payment.objects.filter(student__education_type__in=['kindergarten','preschool']).values('student__id', 'student__name','student__lastname','student__middle_name','student__school_class__name') \
    .annotate(
        total=(
                Coalesce(Sum('sum', filter=Q(transaction_type='debt')), 0, output_field=models.DecimalField()) -
                Coalesce(Sum('sum', filter=Q(transaction_type='payment')), 0, output_field=models.DecimalField())
        ),last_payment=Max('created_at',filter=Q(transaction_type='payment'))
    ).filter(total__gt=0)
      context['sum_month'] = Payment.objects.filter(
         student__education_type__in=['kindergarten', 'preschool'],
         transaction_type='payment',
         created_at__year=current_year,
         created_at__month=current_month
      ).aggregate(total=Sum('sum'))['total'] or 0
      context['sum_day'] = Payment.objects.filter(
         student__education_type__in=['kindergarten', 'preschool'],
         transaction_type='payment',
         created_at=today
      ).aggregate(total=Sum('sum'))['total'] or 0
      context['sum_year'] = Payment.objects.filter(
         student__education_type__in=['kindergarten', 'preschool'],
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
   months_ru = {
      "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
      "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
      "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
   }



   for t in transactions:
      if t.transaction_type == "payment":
         payments.append({
            "date": t.created_at.strftime("%d.%m.%Y"),
            "type_of_payment": t.get_type_of_payment_display(),
            "sum": float(t.sum),
            "note":t.comment,
         })
      else:

         debts.append({
            "date": t.created_at.strftime("%d.%m.%Y"),
            "sum": float(t.sum),
            "month": months_ru.get(t.created_at.strftime("%m"))
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


   def get_context_data(self, *, object_list=None, **kwargs):
      context = super().get_context_data(**kwargs)

      def get_students_with_balance(edu_type, is_archive=False):
         return Student.objects.filter(
            education_type=edu_type,
            archive=is_archive
         ).annotate(
            total_debts=Coalesce(
               Sum('payment_student__sum', filter=Q(payment_student__transaction_type='debt')),
               0,
               output_field=models.DecimalField()
            ),
            total_payments=Coalesce(
               Sum('payment_student__sum', filter=Q(payment_student__transaction_type='payment')),
               0,
               output_field=models.DecimalField()
            )
         ).annotate(
            balance=F('total_debts') - F('total_payments')
         )


      # Твой запрос для контекста
      context['classes'] = SchoolClass.objects.filter(
         students__education_type='school',
         students__archive=False
      ).distinct().prefetch_related(
         Prefetch(
            'students',
            queryset=get_students_with_balance('school')
         )
      ).order_by('name')

      # 2. ПОДГОТОВКА (Preschool)
      context['preschool'] = SchoolClass.objects.filter(
         students__education_type='preschool',
         students__archive=False
      ).distinct().prefetch_related(
         Prefetch(
            'students',
            queryset=get_students_with_balance('preschool')
         )
      ).order_by('name')

      # 3. САДИК (Kinder)
      context['kinder'] = SchoolClass.objects.filter(
         students__education_type='kindergarten',
         students__archive=False
      ).distinct().prefetch_related(
         Prefetch(
            'students',
            queryset=get_students_with_balance('kindergarten')
         )
      ).order_by('name')

      prefetch_archived = Prefetch(
         'students',
         queryset=Student.objects.filter(archive=True)
      )

      # 2. Базовый QuerySet для всех архивных классов
      # Фильтруем классы, в которых есть хотя бы один архивный ученик
      def get_archive_by_type(edu_type):
         return SchoolClass.objects.filter(
            students__archive=True,
            students__education_type=edu_type
         ).distinct().prefetch_related(
            Prefetch(
               'students',
               queryset=Student.objects.filter(archive=True, education_type=edu_type)
            )
         ).order_by('name')

   # 1. Распределяем архив по категориям
      context['archive_school'] = get_archive_by_type('school')
      context['archive_kinder'] = get_archive_by_type('kindergarten')
      context['archive_prep'] = get_archive_by_type('preschool')

      return context



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


@csrf_exempt
@require_POST
def hikvision_event(request):
    try:
        data = json.loads(request.POST.get("event_log", "{}"))
    except Exception:
        return JsonResponse({"status": "invalid_json"}, status=400)

    event = data.get("AccessControllerEvent", {})
    employee_no = event.get("employeeNoString")


    # No person recognized — skip silently

    if not employee_no:
        return JsonResponse({"status": "no_person"}, status=200)  # 200 so camera stops retrying

    try:
        event_time = datetime.fromisoformat(data.get("dateTime", ""))
    except Exception:
        event_time = datetime.now()

    try:

       turniket = Turniket.objects.get(user_id=int(employee_no))
       tracking = TrackingTurniket.objects.create(
          turniket=turniket,
          created_at=event_time,
          enter="in",
       )
       # print("CREATED:", tracking.turniket.name)
       # print("DATE FROM CAMERA:", datetime.fromisoformat(data.get("dateTime", "")))
       # print("EVENT TIME SAVED:", event_time)
       # print("─" * 30)
    except Turniket.DoesNotExist:

        return JsonResponse({"status": "unknown_employee"}, status=200)

    return JsonResponse({"status": "ok"})


def turniket_data(request):
   date = request.GET.get('date')
   qs = TrackingTurniket.objects.select_related('turniket')

   if date:
      qs = qs.filter(created_at__date=date)

   data = []
   for item in qs.order_by('-created_at'):
      local_time = timezone.localtime(item.created_at)
      data.append({
         'date': local_time.strftime('%d.%m.%Y'),
         'time': local_time.strftime('%H:%M:%S'),
         'name': item.turniket.name,
         'photo': item.turniket.photo.url if item.turniket.photo else None,
         'enter': item.enter,
      })

   return JsonResponse(data, safe=False)