import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from notifications.models import Mailing
from dotenv import load_dotenv

load_dotenv()

email_list = os.getenv('EMAIL_LIST').split(',')


class SendStatisticEmail(BaseCommand):
    """Сервис отправки ежедневной статистики по рассылкам."""

    help = 'Отправка ежедневной статистики по рассылкам.'

    def handle(self, *args, **kwargs):
        try:
            previous_day_start = timezone.now() - timezone.timedelta(days=1)
            previous_day_end = timezone.now()

            mailings = Mailing.objects.filter(
                messages__send_date__range=(
                    previous_day_start, previous_day_end
                )
            ).distinct()

            for mailing in mailings:
                successful_mailings_count = mailing.messages.filter(
                    status=200,
                    send_date__gte=previous_day_start,
                    send_date__lte=previous_day_end
                ).count()

                self.send_statistics(mailing, successful_mailings_count)

            self.stdout.write(self.style.SUCCESS('Статистика отправлена'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))

    def send_statistics(self, mailing, successful_mailings_count):
        """Отправляет статистику по рассылке на заданные email."""
        subject = f'Статистика по рассылке номер {mailing.id}'
        message = (
            f'За сутки - {successful_mailings_count} '
            f'успешно отправленных сообщений.'
        )

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            email_list,
            fail_silently=False,
        )
