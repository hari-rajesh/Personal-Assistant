from rest_framework import serializers
from .models import CustomUser, Task

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user



class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id', 
            'user', 
            'title', 
            'description', 
            'priority', 
            'category',  # New field for task categories
            'status',    # New field for task status
            'recurrence', # New field for recurring tasks
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
        instance.category = validated_data.get('category', instance.category)  # Handle category update
        instance.status = validated_data.get('status', instance.status)        # Handle status update
        instance.recurrence = validated_data.get('recurrence', instance.recurrence) # Handle recurrence update
        instance.deadline = validated_data.get('deadline', instance.deadline)
        instance.save()
        return instance

    