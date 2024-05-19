from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from account.models import *
from .tasks import send_activation_email
from .utils import generate_password



User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'role']

class StaffRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number', ''),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_staff=True
        )
        password = generate_password()
        user.set_password(password)
        send_activation_email.delay(user.id, password)
        user.save()
        return user

        

        
class ParentRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()

    class Meta:
        model = Parent
        fields = ['email', 'password', 'first_name', 'last_name', 'phone_number']


    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid email format.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        # Create user
        user_data = {
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'phone_number': validated_data.pop('phone_number'),
            'role': 'parent',
            'is_active': False
        }
        user = User.objects.create_user(**user_data)
        user.set_password(validated_data.pop('password'))
        user.save()
        send_activation_email.delay(user.id)

        # Create parent profile
        parent = Parent.objects.create(user=user, **validated_data)
        return parent

        
class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = '__all__'
    
class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'
        
        
class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'


class StudentRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=17, required=False, allow_blank=True)
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), write_only=True)
    school_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), write_only=True)
    
    class Meta:
        model = Student
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'school', 'school_class')

    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid email format.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        school = validated_data.pop('school')
        school_class = validated_data.pop('school_class')
        # Create user
        user_data = {
            key: validated_data.pop(key) for key in ['email', 'first_name', 'last_name', 'phone_number']
        }
        user = User.objects.create_user(**user_data, role='student')
        password = generate_password()
        user.set_password(password)
        user.save()
        send_activation_email.delay(user.id, password)

        # Create student associated with this user
        student = Student.objects.create(user=user, school = school, school_class = school_class, **validated_data)
        return student
    
class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Student
        fields = '__all__'
        
        
class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child       
        fields = '__all__'
        
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)


        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user.is_student:
            entity_id = Student.objects.get(user=self.user).pk
        elif self.user.is_parent:
            entity_id = Parent.objects.get(user=self.user).pk
        elif self.user.is_staff:
            entity_id = None

        data['user'] = {
            'user_id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'entity_id': entity_id,
            'is_superuser': self.user.is_superuser,
            'is_staff': self.user.is_staff
        }

        return data