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
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if 'user' in validated_data:
                user_id = validated_data.get('user')
                print("Ulla vantan\n" , validated_data)
                if isinstance(user_id, int):
                    validated_data['user'] = User.objects.get(id=user_id)
                elif not isinstance(user_id, User):
                    raise serializers.ValidationError("Invalid user data provided.")
            else:
                validated_data['user'] = request.user
        else:
            raise serializers.ValidationError("Authentication required to create a task.")
        
        return Task.objects.create(**validated_data)


    def update(self, instance, validated_data):
        # Update task instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# class GoogleCalendarEventSerializer(serializers.Serializer):
#     task_id = serializers.IntegerField(required=True)
#     access_token = serializers.CharField(required=True)
#     refresh_token = serializers.CharField(required=True)
#     token_expiry_time = serializers.IntegerField(required=True) 


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'password', 'mobile_number', 'first_name', 'last_name', 'email'
        )
        extra_kwargs = {
            'password': {'write_only': True}  # Password should not be readable
        }

    def create(self, validated_data):
        # Create user with encrypted password
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # Set password securely
        user.save()
        return user

    def validate_mobile_number(self, value):
        # Ensure the mobile number is 10 digits long
        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError("Mobile number must be 10 digits.")
        return value


class UpdateSerializer(serializers.ModelSerializer):
    class Meta: 
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'mobile_number', 'password', 'email'
        )
        extra_kwargs = {
            'password': {'write_only': True}  # Password should not be readable
        }

    def update(self, instance, validated_data):
        # Update user instance with validated data
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.mobile_number = validated_data.get('mobile_number', instance.mobile_number)
        
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password)  # Securely set password

        instance.save()
        return instance


class LoginSerializers(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=30, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:   
            raise serializers.ValidationError({"message": "Username and password must be present."})

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError({"message": "Invalid Credentials."})

        attrs['user'] = user  # Add user to the validated data
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user', 'bio', 'location', 'profile_picture', 'enable_email', 'enable_sms']
        read_only_fields = ['user']  # User field should be read-only


class PhoneNumberSerializer(serializers.ModelSerializer):
    mobile_number = serializers.CharField(max_length=50)

    class Meta:
        model = Profile  # Assuming the Profile model contains the mobile_number field
        fields = ('mobile_number',)

    def validate_mobile_number(self, value):
        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError("Mobile number must be 10 digits.")
        return value
    
class UserQuerySerializer(serializers.Serializer):
    text = serializers.CharField(required=True)

    class Meta:
        fields = ['text']