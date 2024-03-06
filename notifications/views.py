import logging
from rest_framework import viewsets
from django.db import models
from django.db.models import Count
from drf_spectacular.utils import (
    extend_schema, extend_schema_view
)
from rest_framework.decorators import action
from rest_framework.response import Response

from notifications.models import Client, Mailing
from .serializers import (
    ClientSerializer,
    MailingSerializer,
    StatisticSerializer
)
from .tasks import send_messages_for_mailing

mailing_logger = logging.getLogger('mailing')
message_logger = logging.getLogger('message')
client_logger = logging.getLogger('client')


@extend_schema(tags=['Клиенты'])
@extend_schema_view(
    list=extend_schema(summary='Просмотр списка клиентов'),
    retrieve=extend_schema(summary='Получение данных одного клиента'),
    create=extend_schema(summary='Добавление нового клиента'),
    partial_update=extend_schema(summary='Обновление данных клиента'),
    destroy=extend_schema(summary='Удаление клиента')
)
class ClientViewSet(viewsets.ModelViewSet):
    """API-вью для работы с клиентами."""

    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def perform_create(self, serializer):
        response = super().perform_create(serializer)

        client_id = serializer.instance.id
        client_logger.info(
            f'Создан клиент под номером id: {client_id}'
        )
        return response

    def perform_update(self, serializer):
        instance = serializer.instance
        client_id = instance.id
        client_logger.info(f'Изменены данные клиента {client_id}')
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        client_id = instance.id
        client_logger.info(f'Удален клиент {client_id}')
        return super().perform_destroy(instance)


@extend_schema(tags=['Рассылки'])
@extend_schema_view(
    list=extend_schema(summary='Просмотр всех рассылок'),
    retrieve=extend_schema(summary='Получение данных одной рассылки'),
    create=extend_schema(summary='Создание новой рассылки',),
    partial_update=extend_schema(summary='Обновление рассылки'),
    destroy=extend_schema(summary='Удаление рассылки')
)
class MailingViewSet(viewsets.ModelViewSet):
    """API-вью для работы с рассылками."""

    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer

    def perform_create(self, serializer):
        response = super().perform_create(serializer)

        mailing_id = serializer.instance.id
        mailing_logger.info(
            f'Создана рассылка под номером {mailing_id}',
        )
        mailing = serializer.save()
        send_messages_for_mailing.apply_async(
            args=[mailing.id], eta=mailing.start_date
        )
        return response

    def perform_update(self, serializer):
        instance = serializer.instance
        mailing_id = instance.id
        mailing_logger.info(f'Изменена рассылка {mailing_id}')
        mailing = serializer.save()
        send_messages_for_mailing.apply_async(
            args=[mailing.id], eta=mailing.start_date
        )
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        mailing_id = instance.id
        mailing_logger.info(f'Удалена рыссылка {mailing_id}')
        return super().perform_destroy(instance)

    @extend_schema(
        tags=['Статистика'],
        summary='Получить статистику по всем рассылкам',
        responses={
            200: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string'},
                        'total_messages': {'type': 'integer'},
                        'successful_messages': {'type': 'integer'},
                        'failed_messages': {'type': 'integer'},
                    }
                }
            }
        },
    )
    @action(detail=False, methods=['GET'])
    def statistics(self, request):
        """Возвращает статистику по всем рассылкам."""
        statistics = Mailing.objects.annotate(
            total_messages=Count('messages'),
            successful_messages=Count(
                'messages', filter=models.Q(messages__status=200)
            ),
            failed_messages=Count(
                'messages', filter=~models.Q(messages__status=200)
            )
        ).values(
            'id', 'total_messages', 'successful_messages', 'failed_messages'
        )

        return Response(statistics)

    @extend_schema(
        tags=['Статистика'],
        summary='Получить статистику по одной рассылке',
        responses={
            200: StatisticSerializer(many=True)
        },
    )
    @action(detail=True, methods=['GET'])
    def detail_statistics(self, request, pk=None):
        """Возвращает статистику по конкретной рассылке."""
        mailing = self.get_object()
        messages = mailing.messages.all()
        serializer = StatisticSerializer(
            messages, many=True
        )
        return Response(serializer.data)
