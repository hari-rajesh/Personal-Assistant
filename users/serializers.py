from rest_framework import serializers
from .models import User, Task, Profile
from django.contrib.auth import authenticate

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id', 
            'user', 
            'title', 
            'description', 
            'priority', 
            'category',  
            'status',    
            'recurrence', 
            'deadline', 
            'created_at', 
            'updated_at'
        )
        read_only_fields = ('user', 'created_at', 'updated_at')

    def create(self, validated_data):
        return Task.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.category = validated_data.get('category', instance.category)
        instance.status = validated_data.get('status', instance.status)
        instance.recurrence = validated_data.get('recurrence', instance.recurrence)
        instance.deadline = validated_data.get('deadline', instance.deadline)
        instance.save()
        return instance

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'password', 'mobile_number', 'first_name', 'last_name', 'email'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            mobile_number=validated_data['mobile_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        password=validated_data['password']
        user.set_password(password)
        user.save()
        return user

    def validate_mobile_number(self, value):
        if len(value) != 10:
            raise serializers.ValidationError("Mobile number must be 10 digits.")
        return value

class UpdateSerializer(serializers.ModelSerializer):
    class Meta: 
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'mobile_number', 'password', 'email'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.mobile_number = validated_data.get('mobile_number', instance.mobile_number)
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)

        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=30, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                attrs['user'] = user
            else:
                raise serializers.ValidationError({"message": "Invalid Credentials"})
        else:
            raise serializers.ValidationError({"message": "Username and password must be present"})
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user', 'bio', 'location', 'profile_picture', 'enable_email', 'enable_sms']
        read_only_fields = ['user']  # Set user as read-only so it can't be modified directly
