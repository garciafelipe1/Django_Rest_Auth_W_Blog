from rest_framework import serializers
from djoser.serializers import UserCreateSerializer

from django.contrib.auth import get_user_model

User= get_user_model()

class UserCreateSerializer(UserCreateSerializer):
    qr_code=serializers.URLField(source='get_qr_code')   
    class Meta(UserCreateSerializer.Meta):
        model = User
        field= '__all__'
    
class UserSerializer(serializers.ModelSerializer):
    qr_code=serializers.URLField(source='get_qr_code')   
    
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'updated_at',
            'two_factor_enabled',
            'otpauth_url',
            'login_otp',
            'login_otp_used',
            'qr_code',
            'otp_created_at',
        ]

class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'updated_at',
            
        ]
        