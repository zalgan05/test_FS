from datetime import datetime, timedelta
import pytz
import requests
import logging
import time
from celery import shared_task, group
from celery.schedules import crontab
from .models import Mailing, Message, Client
from django.utils import timezone
from django.conf import settings

from notification_service.celery import app as celery_app

from .services import SendStatisticEmail

mailing_logger = logging.getLogger('mailing')
message_logger = logging.getLogger('message')
client_logger = logging.getLogger('client')


@shared_task
def send_messages_for_mailing(mailing_id):
    """Запускает отправку сообщений клиентам рассылки."""
    try:
        mailing = Mailing.objects.get(id=mailing_id)

        if mailing.filter_tag and mailing.filter_code_operator:
            clients = Client.objects.filter(
                tag=mailing.filter_tag,
                code_operator=mailing.filter_code_operator
            )
        elif mailing.filter_tag:
            clients = Client.objects.filter(tag=mailing.filter_tag)
        elif mailing.filter_code_operator:
            clients = Client.objects.filter(
                code_operator=mailing.filter_code_operator
            )

        mailing_logger.info(f'Рассылка {mailing_id} началась.')
        tasks = []
        for client in clients:
            if timezone.now() > mailing.end_date:
                mailing_logger.info(
                    f'Время действия рассылки {mailing_id} истекло. '
                    f'Отправка новых сообщений прекращена.'
                )
                break
            send_time = calculate_send_time(mailing, client)
            task = send_message.s(mailing.id, client.id)
            if send_time:
                task = task.set(eta=send_time)
            tasks.append(task)

        task_group = group(tasks)
        result = task_group.apply_async()

        while not result.ready():
            time.sleep(60)

        if result.successful():
            mailing_logger.info(
                f'Все сообщения рассылки {mailing_id} успешно отправлены.'
            )
        else:
            mailing_logger.warning(
                f'Несколько сообщений рассылки {mailing_id} не отправлены.'
            )

    except Exception as e:
        mailing_logger.error(
            f'В рассылке {mailing_id} произошла ошибка - {e}'
        )


@shared_task
def send_message(mailing_id, client_id):
    """Отправляет сообщение клиенту."""
    try:
        mailing = Mailing.objects.get(id=mailing_id)
        client = Client.objects.get(id=client_id)
        message = Message.objects.create(
            status=0,
            mailing=mailing,
            client=client
        )

        url = f'https://probe.fbrq.cloud/v1/send/{message.id}'
        headers = {'Authorization': f'Bearer {settings.API_TOKEN}'}
        data = {
            'id': message.id,
            'phone': int(client.phone_number),
            'text': mailing.text
        }

        while timezone.now() <= mailing.end_date:
            send_time = calculate_send_time(mailing, client)

            if send_time and send_time > timezone.now():
                time.sleep((send_time - timezone.now()).seconds)

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                message.status = 200
                message.send_date = timezone.now()
                message_logger.info(
                    f'Сообщение - {message.id} рассылки - '
                    f'{mailing_id} успешно отправлено '
                    f'клиенту {client_id}.'
                )
                client_logger.info(
                    f'Клиенту {client_id} отправлено сообщение {message.id}.'
                )
                break
            else:
                message.status = response.status_code
                message_logger.warning(
                    f'Ошибка запроса {response.status_code} при отправке '
                    f'сообщения {message.id} рассылки {mailing_id} '
                    f'клиенту {client_id}.'
                )
                message_logger.warning(response.text)

            time.sleep(60)
        else:
            message_logger.info(
                f'Время действия рассылки {mailing_id} истекло, '
                f'сообщение {message.id} не было отправлено '
                f'клиенту {client_id}.'
            )

        message.save()

    except Exception as e:
        message_logger.error(
            f'Сообщение {message.id}. Ошибка при отправке: {e}'
        )


def calculate_send_time(mailing, client):
    """Возвращает время отправки сообщения с учетом часового пояса клиента."""
    try:
        client_timezone = pytz.timezone(client.timezone)
        current_datetime = datetime.now(client_timezone)
        current_time = timezone.now().astimezone(client_timezone).time()
        client_datetime = datetime.combine(
            current_datetime.date(), current_time
        )

        start_datetime = datetime.combine(
            datetime.now().date(), mailing.start_time
        )

        if mailing.start_time <= current_time <= mailing.end_time:
            return
        elif current_time < mailing.start_time:
            time_difference = start_datetime - client_datetime
            send_time = (
                (datetime.now() + time_difference).astimezone(client_timezone)
            )
            message_logger.info(
                f'Сообщение клиенту - {client.id} рассылки - '
                f'{mailing.id} будет отправлено {send_time}'
            )
            return send_time
        elif current_time > mailing.end_time:
            time_difference = client_datetime - start_datetime
            send_time = (
                (datetime.now() + timedelta(days=1) - time_difference)
                .astimezone(client_timezone)
            )
            message_logger.info(
                f'Сообщение клиенту - {client.id} рассылки - '
                f'{mailing.id} будет отправлено {send_time}'
            )
            return send_time

    except Exception as e:
        message_logger.error(
            f'Ошибка при расчете времени отложенного сообщения '
            f'рассылки - {mailing.id}: {e}'
        )


@shared_task()
def send_mail_statistic():
    """Запуск сервиса отправки статистики по рассылкам на email"""
    command = SendStatisticEmail()
    command.handle()


celery_app.conf.beat_schedule = {
    'send_mail_statistic': {
        'task': 'notifications.tasks.send_mail_statistic',
        'schedule': crontab(hour=20, minute=00),
    },
}
