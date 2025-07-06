from django.shortcuts import render
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.views.generic import View,ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView,FormView

from rest_framework.response import Response
from rest_framework.views import APIView
import json
import telegram
import requests

from rest_framework import status
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from collections import defaultdict
from django.db.models import Sum,Q
from django.http import HttpResponse


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
