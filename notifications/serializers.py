from rest_framework import serializers

from .models import Client, Mailing, Message


class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = '__all__'

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        code_operator = attrs.get('code_operator')

        if (
            not phone_number.startswith('7') or
            len(phone_number) != 11
        ):
            raise serializers.ValidationError({
                'phone_number': [
                    'Введите корректный номер телефона в формате 7XXXXXXXXXX'
                ]
            })

        if str(code_operator) != phone_number[1:4]:
            raise serializers.ValidationError({
                'code_operator': 'Код оператора не совпадает с кодом в номере'
            })
        return attrs


class MailingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Mailing
        fields = '__all__'

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        filter_tag = attrs.get('filter_tag')
        filter_code_operator = attrs.get('filter_code_operator')

        if self.partial:
            existing_start_date = self.instance.start_date
            existing_end_date = self.instance.end_date
            existing_start_time = self.instance.start_time
            existing_end_time = self.instance.end_time

            if start_date is not None or end_date is not None:
                if start_date is None and end_date < existing_start_date:
                    raise serializers.ValidationError({
                        'end_date': [
                            'Дата конца рассылки не может быть меньше начала'
                        ]
                    })
                elif end_date is None and start_date > existing_end_date:
                    raise serializers.ValidationError({
                        'start_date': [
                            'Дата начала рассылки не может быть больше конца'
                        ]
                    })
                elif start_date and end_date and start_date >= end_date:
                    raise serializers.ValidationError({
                        'end_date': [
                            'Дата конца рассылки не может быть меньше начала'
                        ]
                    })

            if start_time is not None and end_time is not None:
                if start_time is None and end_time < existing_start_time:
                    raise serializers.ValidationError({
                        'end_time': [
                            'Время конца рассылки не может быть меньше начала'
                        ]
                    })
                elif end_time is None and start_time > existing_end_time:
                    raise serializers.ValidationError({
                        'start_time': [
                            'Время начала рассылки не может быть больше конца'
                        ]
                    })
                elif start_time and end_time and start_time >= end_time:
                    raise serializers.ValidationError({
                        'end_time': [
                            'Время конца рассылки не может быть меньше начала'
                        ]
                    })

            return attrs

        if start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'Дата конца рассылки не может быть меньше начала'
            })

        if start_time and not end_time or end_time and not start_time:
            raise serializers.ValidationError(
                'Временной интервал рассылки должен иметь два значения.'
            )

        if start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': 'Время конца рассылки не может быть меньше начала'
            })

        if not (filter_tag or filter_code_operator):
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один параметр фильтра'
            )

        return attrs


class StatisticSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = '__all__'
