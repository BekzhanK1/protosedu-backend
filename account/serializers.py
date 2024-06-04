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
        password = validated_data.pop('password')
        user.set_password(password)
        user.save()
        send_activation_email.delay(user.id, password)

        # Create parent profile
        parent = Parent.objects.create(user=user, **validated_data)
        return parent

        
class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = '__all__'
    
class SchoolSerializer(serializers.ModelSerializer):
    student_number = serializers.SerializerMethodField()
    class Meta:
        model = School
        fields = '__all__'
    
    def get_student_number(self, obj):
        return Student.objects.filter(school=obj).count()
        
        
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
    grade = serializers.IntegerField()
    school_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), write_only=True)
    
    class Meta:
        model = Student
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'school', 'school_class', 'grade')

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
        student = Student.objects.create(user=user, school = school, school_class = school_class, grade = grade, **validated_data)
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


    def get_school_name(self, obj):
        return obj.school.name if obj.school else None

    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'email', 'grade', 'school_name', 'gender']

class ChildrenListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='parent.user.email')
    id = serializers.IntegerField(source='parent.user.id')
    school_name = serializers.SerializerMethodField()

    class Meta:
        model = Child
        fields = ['id', 'first_name', 'last_name', 'email', 'grade', 'school_name', 'gender']

    def get_school_name(self, obj):
        return "Индивидуальный аккаунт"
class SimpleStudentSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    

    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'email', 'grade', 'level', 'streak', 'cups', 'stars', 'gender', 'avatar', 'birth_date', 'last_task_completed_at', 'school_class', 'school']
        
        
class ChildSerializer(serializers.ModelSerializer):
    # email = serializers.EmailField(source='parent.user.email')
    class Meta:
        model = Child       
        fields = '__all__'
        
    # def get_tasks_completed(self, obj):
    #     return obj.completed_tasks.count()
        
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)


        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user.is_student:
            student = Student.objects.get(user=self.user)
            grade = student.grade
            avatar_url = student.avatar.url if student.avatar else None
            data['user'] = {
                'user_id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'role': self.user.role,
                'grade': grade,
                'avatar': avatar_url,
                'level': student.level,
                'streak': student.streak,
                'cups': student.cups,
                'stars': student.stars,
                'is_superuser': self.user.is_superuser,
                'is_staff': self.user.is_staff

            }
        elif self.user.is_parent:
            parent = self.user.parent
            children = Child.objects.filter(parent = parent)
            data['user'] = {
                'user_id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'role': self.user.role,
                'children': ChildSerializer(children, many=True).data,
                'is_superuser': self.user.is_superuser,
                'is_staff': self.user.is_staff
            }
        else:
            data['user'] = {
                'user_id': self.user.id,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'role': self.user.role,
                'is_superuser': self.user.is_superuser,
                'is_staff': self.user.is_staff
            }

        return data