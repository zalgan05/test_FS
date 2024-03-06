import pytz
from django.db import models
# from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

# from phonenumber_field.modelfields import PhoneNumberField


MAX_LENGTH = 100


class Mailing(models.Model):
    """Модель для хранения информации рассылок."""

    name = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        null=True,
    )
    text = models.TextField()
    start_date = models.DateTimeField(
        blank=False,
        null=False,
    )
    end_date = models.DateTimeField(
        blank=False,
        null=False,
    )
    start_time = models.TimeField(
        blank=True,
        null=True,
    )
    end_time = models.TimeField(
        blank=True,
        null=True,
    )
    filter_tag = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        null=True,
    )
    filter_code_operator = models.IntegerField(
        blank=True,
        null=True,
    )

    def clean(self) -> None:
        if self.filter_tag is None and self.filter_code_operator is None:
            raise ValidationError(
                'Введите хотя бы один параметр фильтрации рассылки'
            )
        if (
            (self.start_time and not self.end_time) or
            (self.end_time and not self.start_time)
        ):
            raise ValidationError(
                'Временной интервал должен быть задан двумя значениями.'
            )

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)


class Message(models.Model):
    """Модель для хранения информации о сообщениях рассылок."""

    send_date = models.DateTimeField(
        blank=True,
        null=True
    )
    status = models.IntegerField()
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='clients'
    )


class Client(models.Model):
    """Модель для хранения информации о клиентах."""

    TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))

    phone_number = models.CharField(max_length=12, unique=True)
    code_operator = models.IntegerField(
        validators=[
            MinValueValidator(900),
            MaxValueValidator(999)
        ]
    )
    tag = models.CharField(max_length=MAX_LENGTH)
    timezone = models.CharField(max_length=32, choices=TIMEZONES)

    def clean(self) -> None:
        if self.phone_number:
            if (
                not self.phone_number.startswith('7') or
                len(self.phone_number) != 11
            ):
                raise ValidationError(
                    'Введите корректный номер телефона в формате 7XXXXXXXXXX'
                )

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)
