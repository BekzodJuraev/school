from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import AbstractUser

from datetime import date

TRACKING_START = date(2026, 5, 1)
class Profile(models.Model):
    POSITION_CHOICES = [
        ("admin", "Админ"),
        ("HR", "Отдел кадров"),
        ("supplier","Завхоз"),
        ('chief',"Повар"),
        ("zavuch", "Завуч"),


    ]
    username = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=200, null=True, blank=True, default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True, default=None)
    middle_name = models.CharField(max_length=200, null=True, blank=True, default=None)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, blank=True, null=True)
    approve=models.BooleanField(default=False)

    def __str__(self):
        return self.name
class SchoolClass(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name
class Student(models.Model):
    EDUCATION_TYPE_CHOICES = [
        ("school", "Школа"),
        ("kindergarten", "Садик"),
        ("preschool","Подготовка"),
    ]

    education_type = models.CharField(
        max_length=20,
        choices=EDUCATION_TYPE_CHOICES,
        default="school"
    )
    name = models.CharField(max_length=200, null=True, blank=True, default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True, default=None)
    middle_name = models.CharField(max_length=200, null=True, blank=True, default=None)
    phone = PhoneNumberField(blank=True, null=True)
    date_birth = models.DateField(null=True, blank=True, default=None)
    photo = models.ImageField(blank=True, null=True, upload_to='staff/')
    adres = models.CharField(max_length=200)
    passport = models.CharField(max_length=50)
    created_at = models.DateField(auto_now_add=True)
    prikaz=models.IntegerField(default=None)
    prikaz_date=models.DateField(blank=True,null=True)
    school_class = models.ForeignKey(SchoolClass, related_name='students',on_delete=models.SET_NULL, null=True, blank=True)
    Gender_CHOICES = [
        ("male", "Муж"),
        ("female", "Жен"),

    ]
    position_gender = models.CharField(max_length=20, choices=Gender_CHOICES, blank=True, null=True)

    prikaz_archive = models.IntegerField(default=None,blank=True,null=True)
    prikaz_date_archive = models.DateField(blank=True, null=True)
    archive=models.BooleanField(default=False)
    document = models.FileField(blank=True, null=True, upload_to='student/')
    discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True,null=True)
    def __str__(self):
        return f"{self.lastname} {self.name} - {self.school_class}"

class Staff(models.Model):
    POSITION_CHOICES = [
        ("teacher", "Учитель"),
        ("other", "Другое"),

    ]
    Gender_CHOICES = [
        ("male", "Муж"),
        ("female", "Жен"),

    ]

    name = models.CharField(max_length=200, null=True, blank=True, default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True, default=None)
    middle_name = models.CharField(max_length=200, null=True, blank=True, default=None)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, blank=True, null=True)
    position_gender = models.CharField(max_length=20, choices=Gender_CHOICES, blank=True, null=True)
    date_birth = models.DateField(null=True, blank=True, default=None)
    phone = PhoneNumberField(blank=True,null=True)
    photo=models.ImageField(blank=True,null=True,upload_to='staff/')
    cv_rus=models.FileField(blank=True,null=True,upload_to='staff/')
    cv_uz= models.FileField(blank=True,null=True,upload_to='staff/')
    diplom = models.FileField(blank=True,null=True,upload_to='staff/')
    adres=models.CharField(max_length=200)
    passport=models.CharField(max_length=50)
    created_at=models.DateField(auto_now_add=True)


class Warehouse(models.Model):
    created_at = models.DateField(auto_now_add=True)
    quantity=models.IntegerField(default=0)
    categories=models.CharField(max_length=100)
    name=models.CharField(max_length=200)
    UNIT_CHOICES = [
        ("шт", "Штука"),
        ("кг", "Килограмм"),
        ("г", "Грамм"),
        ("л", "Литр"),
        ("мл", "Миллитр"),
    ]
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="шт")



    def __str__(self):
        return self.name


class Invoice(models.Model):
    TYPE = [
        ("Приход", "plus"),
        ("Расход", "minus"),

    ]
    type_invoice= models.CharField(max_length=20, choices=TYPE)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='invoice',
        null=True
    )
    TYPE = [
        ("cash", "Наличные"),
        ("bank", "Банковские переводы"),
        ('card', 'Карта')

    ]
    type_of_payment = models.CharField(max_length=20, choices=TYPE, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    where=models.CharField(max_length=100)
    to = models.CharField(max_length=100)
    comment=models.CharField(max_length=200,null=True,blank=True)
    remaining_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class Inventory_cabinet(models.Model):
    name=models.CharField(max_length=100,unique=True)
    school_class = models.ForeignKey(SchoolClass, related_name='students_inventory',on_delete=models.SET_NULL, null=True, blank=True)



    def __str__(self):
        return self.name
class Inventory_items(models.Model):
    name=models.CharField(max_length=100,unique=True)
    def __str__(self):
        return self.name

class Inventory(models.Model):
    cabinet = models.ForeignKey(
        Inventory_cabinet,
        on_delete=models.CASCADE,
        related_name="items"
    )
    item_type = models.ForeignKey(
        Inventory_items,
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    archive=models.BooleanField(default=False)
    comment=models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateField(auto_now_add=True,null=True)


    def __str__(self):
        return f"{self.item_type.name} в {self.cabinet.name} ({self.quantity} ед.)"





class Payment(models.Model):
    DEBT = "debt"
    PAYMENT = "payment"

    TRANSACTION_TYPES = [
        (DEBT, "Начисление"),
        (PAYMENT, "Оплата"),
    ]
    TYPE = [
        ("cash", "Наличные"),
        ("bank", "Карта"),
        ('card','Банковские переводы')

    ]
    comment = models.CharField(max_length=200, null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES,null=True)
    student=models.ForeignKey(Student, related_name="payment_student",on_delete=models.CASCADE)
    type_of_payment=models.CharField(max_length=20, choices=TYPE,null=True,blank=True)
    sum = models.DecimalField(max_digits=30, decimal_places=2,default=0)
    created_at = models.DateField(null=True)



    def save(self, *args, **kwargs):
        if self.transaction_type == self.DEBT:
            today = date.today()
            already_debt = Payment.objects.filter(
                student=self.student,
                transaction_type=self.DEBT,
                created_at__year=today.year,
                created_at__month=today.month,
            ).exists()
            if already_debt:
                return
        super().save(*args, **kwargs)



    def __str__(self):
        return self.student.name


class Turniket(models.Model):
    TYPE = [
        ("worker", "Сотрудник"),
        ("student", "Ученик")

    ]
    user_id=models.IntegerField(unique=True)
    name=models.CharField(max_length=255)
    photo=models.ImageField(upload_to='face/')
    role=models.CharField(max_length=50, choices=TYPE)

    def __str__(self):
        return self.name


class TrackingTurniket(models.Model):
    TYPE = [
        ("in", "Вход"),
        ("out", "Выход")

    ]

    turniket=models.ForeignKey(Turniket, related_name="payment_student",on_delete=models.CASCADE)
    created_at=models.DateTimeField()
    enter = models.CharField(max_length=20, choices=TYPE)

    def save(self, *args, **kwargs):
        if self.created_at.date() < TRACKING_START:
            return  # ignore events before 01.05.2026

        already_exists = TrackingTurniket.objects.filter(
            turniket=self.turniket,
            created_at__year=self.created_at.year,
            created_at__month=self.created_at.month,
            created_at__day=self.created_at.day,
        ).exists()

        if not already_exists:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.turniket.name












