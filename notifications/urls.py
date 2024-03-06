from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClientViewSet, MailingViewSet


router = DefaultRouter()
router.register('clients', ClientViewSet, basename='client')
router.register('mailings', MailingViewSet, basename='mailing')
# router.register('statistics', StatisticViewSet, basename='statistic')

urlpatterns = [
    path('', include(router.urls))
]
