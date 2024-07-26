from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from account.models import Parent, Child, Student, School, Class
from subscription.models import Subscription, Plan
from django.core.exceptions import ObjectDoesNotExist
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
        user.save()
        send_activation_email.delay(user.id, password)
        return user

class SupervisorRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number']

    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid email format.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        password = generate_password()
        user = User.objects.create_user(
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number', ''),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role='supervisor'
        )
        user.set_password(password)
        user.save()
        send_activation_email.delay(user.id, password)
        return user

class ParentRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

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
        user_data = {
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'phone_number': validated_data.pop('phone_number'),
            'role': 'parent',
            'is_active': False
        }
        user = User.objects.create_user(**user_data)
        password = validated_data.pop('password')
        user.set_password(password)
        user.save()
        send_activation_email.delay(user.id, password)

        parent = Parent.objects.create(user=user, **validated_data)
        return parent

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = '__all__'

class SchoolSerializer(serializers.ModelSerializer):
    student_number = serializers.SerializerMethodField(read_only=True)
    supervisor = UserSerializer(read_only=True)
    
    class Meta:
        model = School
        fields = '__all__'
    
    def get_student_number(self, obj):
        return Student.objects.filter(school=obj).count()

class StudentRegistrationSerializer(serializers.ModelSerializer):
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), write_only=True)
    school_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), write_only=True)
    
    class Meta:
        model = Student
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'school', 'school_class', 'grade', 'gender')

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
        grade = validated_data.pop('grade')
        gender = validated_data.pop('gender')
        
        user_data = {
            key: validated_data.pop(key) for key in ['email', 'first_name', 'last_name', 'phone_number']
        }
        user = User.objects.create_user(**user_data, role='student')
        password = generate_password()
        user.set_password(password)
        user.save()
        send_activation_email.delay(user.id, password)

        student = Student.objects.create(user=user, school=school, school_class=school_class, grade=grade, gender=gender, **validated_data)
        return student

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    school_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = '__all__'

    def get_school_name(self, obj):
        return obj.school.name if obj.school else None

class StudentsListSerializer(serializers.ModelSerializer):
    school_name = serializers.SerializerMethodField()
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    id = serializers.IntegerField(source='user.id')

    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'email', 'grade', 'school_name', 'gender']

    def get_school_name(self, obj):
        return obj.school.name if obj.school else None

class ChildrenListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='parent.user.email')
    school_name = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(source='parent.user.id')

    class Meta:
        model = Child
        fields = ['id', 'parent_id', 'first_name', 'last_name', 'email', 'grade', 'school_name', 'gender']

    def get_school_name(self, obj):
        return "Индивидуальный аккаунт"

class SimpleStudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'email', 'grade', 'level', 'streak', 'cups', 'stars', 'gender', 'avatar', 'birth_date', 'last_task_completed_at', 'school_class', 'school']

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'

class ChildSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    tasks_completed = serializers.SerializerMethodField()
    has_subscription = serializers.SerializerMethodField()
    is_free_trial = serializers.SerializerMethodField()

    class Meta:
        model = Child
        fields = '__all__'

    def get_email(self, obj):
        return obj.parent.user.email
    
    def get_tasks_completed(self, obj):
        return obj.completed_tasks.count()

    def get_has_subscription(self, obj):
        subscription_active, _ = self.check_subscription_and_free_trial(obj)
        return subscription_active
    
    def get_is_free_trial(self, obj):
        _, is_free_trial = self.check_subscription_and_free_trial(obj)
        return is_free_trial

    def check_subscription_and_free_trial(self, obj):
        parent = obj.parent
        has_subscription = hasattr(parent.user, 'subscription')
        active_subscription = parent.user.subscription if has_subscription else None
        subscription_active = active_subscription.is_active if active_subscription else False
        is_free_trial = active_subscription.plan.duration == 'free-trial' if active_subscription else False
        return subscription_active, is_free_trial

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add any additional token customization here if needed
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        try:
            if self.user.is_student:
                student = Student.objects.get(user=self.user)
                avatar_url = student.avatar.url if student.avatar else None
                data['user'] = {
                    'id': self.user.id,
                    'email': self.user.email,
                    'first_name': self.user.first_name,
                    'last_name': self.user.last_name,
                    'role': self.user.role,
                    'grade': student.grade,
                    'gender': student.gender,
                    'language': student.language,
                    'avatar': avatar_url,
                    'level': student.level,
                    'streak': student.streak,
                    'cups': student.cups,
                    'stars': student.stars,
                    'is_superuser': self.user.is_superuser,
                    'is_staff': self.user.is_staff,
                }
            elif self.user.is_parent:
                parent = self.user.parent
                children = Child.objects.filter(parent=parent)
                data['user'] = {
                    'id': self.user.id,
                    'email': self.user.email,
                    'first_name': self.user.first_name,
                    'last_name': self.user.last_name,
                    'role': self.user.role,
                    'children': ChildSerializer(children, many=True).data,
                    'is_superuser': self.user.is_superuser,
                    'is_staff': self.user.is_staff,
                }
            elif self.user.is_superuser:
                data['user'] = {
                    'id': self.user.id,
                    'email': self.user.email,
                    'first_name': self.user.first_name,
                    'last_name': self.user.last_name,
                    'role': 'superadmin',
                    'is_superuser': self.user.is_superuser,
                    'is_staff': self.user.is_staff
                }
            elif self.user.is_supervisor:
                data['user'] = {
                    'id': self.user.id,
                    'email': self.user.email,
                    'first_name': self.user.first_name,
                    'last_name': self.user.last_name,
                    'role': self.user.role,
                    'is_superuser': self.user.is_superuser,
                    'is_staff': self.user.is_staff
                }
        
        except ObjectDoesNotExist:
            raise serializers.ValidationError("User data could not be retrieved.")

        return data
