from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator,MaxValueValidator,MinValueValidator

from django.contrib.auth.base_user import BaseUserManager

from django.utils import timezone

from django.utils.translation import gettext_lazy as _

#imports for Request
from django.conf import settings

from django.core.exceptions import ObjectDoesNotExist

#Shows the status of the invoices
class InvoiceStatus(models.TextChoices):
    PAID = 'PAID', _('This invoices has been paid')
    UNPAID = 'UNPAID', _('This invoice has not been paid')
    PARTIALLY_PAID = 'PARTIALLY_PAID', _('This invoice has been partially paid')
    DELETED = 'DELETED', _('This invoice has been deleted')

#Enum type for the status of a lesson
class LessonStatus(models.TextChoices):
    SAVED = 'SA', _('The lesson has been saved')
    UNFULFILLED = 'PN', _('The lesson request is pending')
    FULLFILLED = 'BK', _('The lesson has been booked')

#Enum type for the type of lesson requested by the student
class LessonType(models.TextChoices):
    INSTRUMENT = 'INSTR', _('Learn To Play An Instrument'),
    THEORY = 'TH', _('Instrument Music Theory'),
    PRACTICE = 'PR', _('Instrument practice'),
    PERFORMANCE = 'PERF', _('Performance Preparation'),


#Enum type for the duration of a lesson
class LessonDuration(models.TextChoices):
    THIRTY = '30', _('30 minute lesson')
    FOURTY_FIVE = '45', _('45 minute lesson')
    HOUR = '60', _('1 hour lesson')

#Enum type for the different types of roles a user can have
class UserRole(models.TextChoices):
    STUDENT = 'STU', _('Student')
    ADMIN = 'ADM', _('Administrator')
    DIRECTOR = 'DIR', _('Director')
    TEACHER = 'TEA', _('Teacher')

#Enum type for the gender of the student user
class Gender(models.TextChoices):
    MALE = 'M' , _('Male')
    FEMALE = 'F', _('Female')
    PNOT = 'PNOT', _('Prefer Not To Say')

"""
Custom manager for the user account model for creating different types of user accounts, students,admins,directors and teachers
Allows different types of permissions to be assigned to each user type
"""
class UserAccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        '''Create and save a student with the given email, and
        password without a username
        '''
        if not email:
            raise ValueError('The given email must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    #creates a student user account, assigned STUDENT UserRole type
    def create_student(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_parent', False)
        extra_fields.setdefault('role', UserRole.STUDENT)
        return self._create_user(email, password, **extra_fields)

    #creates a child student user account, parameters include the UserAccount object which is the parent of the student to be created
    def create_child_student(self, email, password, **extra_fields):

        parent = extra_fields['parent_of_user']

        #checks to ensure that the parent_of_user object passed in is of type UserAccount
        if hasattr(parent,'email') is False:
            raise AttributeError('Provided parent field is not of type UserAccount')

        if parent.role != UserRole.STUDENT:
            raise AttributeError('Provided user is not a student')

        parent.is_parent = True
        parent.save()

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', UserRole.STUDENT)
        return self._create_user(email, password, **extra_fields)

    #creates an admin account, which has staff permissions, assigned ADMIN UserRole type
    def create_admin(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(
                'Admin must have is_staff=True.'
            )
        if extra_fields.get('is_superuser') is not False:
            raise ValueError(
                'Admin must have is_superuser=False.'
            )

        return self._create_user(email, password, **extra_fields)

    #creates a teacher user account, which has staff permissions, assigned TEACHER UserRole type
    def create_teacher(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', UserRole.TEACHER)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(
                'Teacher must have is_staff=True.'
            )
        if extra_fields.get('is_superuser') is not False:
            raise ValueError(
                'Teacher must have is_superuser=False.'
            )

        return self._create_user(email, password, **extra_fields)

    #creates a director user account, which has staff and super user permissions, assigned DIRECTOR UserRole type
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.DIRECTOR)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(
                'Superuser must have is_staff=True.'
            )
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Superuser must have is_superuser=True.'
            )

        return self._create_user(email, password, **extra_fields)

"""
UserAccount model refers to the different types of Users of the MSMS application
Uniquely identified by their email, two users cannot have the same email
Fields include their name, email , password, gender, role and balance
"""
class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)

    is_staff = models.BooleanField(
        default=False,
        help_text=(
            'Designates whether the user can log into '
            'this admin site.'
        ),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=(
            'Designates whether this user should be '
            'treated as active. Unselect this instead '
            'of deleting accounts.'
        ),
    )

    date_joined = models.DateTimeField(
        default=timezone.now,
    )

    #making the email the unique primary field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserAccountManager()

    is_parent = models.BooleanField(default = False, blank = False)

    #object referring to the parent of this student user
    parent_of_user = models.ForeignKey('self',related_name = 'parent',on_delete=models.CASCADE, blank = True, null = True)

    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        default=Gender.PNOT,
    )

    role = models.CharField(
        max_length=13,
        choices=UserRole.choices,
    )

    #balance shows the difference between existing transactions and invoices
    balance = models.IntegerField(
        default=0,
        blank = True,
        editable=False,
    )

    def get_student_balance(self):
        return f'{self.balance}'

    def get_student_id(self):
        return f'{self.id}'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
"""
Lesson model refers to the single lesson requested by the student user
It can have varying information such as the type of lessons, its duration , the teacher related to the lesson and the student that requested it
Lessons have varying status, SAVED when the lesson is first created by the user , UNFULFILLED when it is requested by the user and FULLFILLED when it is booked by an admin
Lessons are UNIQUELY identified by when they have been requested, the date and time the lesson is requested for and the student that requested the lesson
Lessons are also assigned the TERM they fall in
"""
class Lesson(models.Model):
    lesson_id = models.BigAutoField(primary_key=True)

    request_date = models.DateField('Request Date', default=timezone.now)

    type = models.CharField(
        max_length=30,
        choices=LessonType.choices,
        default=LessonType.INSTRUMENT,
        blank = False
    )

    duration = models.CharField(
        max_length = 20,
        choices = LessonDuration.choices,
        default = LessonDuration.THIRTY,
        blank = False
    )

    lesson_date_time = models.DateTimeField('Lesson Date And Time', blank = False)

    teacher_id = models.ForeignKey(UserAccount,on_delete=models.CASCADE, related_name = 'teacher')

    student_id = models.ForeignKey(UserAccount, on_delete = models.CASCADE, related_name = 'student')

    lesson_status = models.CharField(max_length=30,choices = LessonStatus.choices, default = LessonStatus.SAVED, blank = False)

    term = models.CharField(max_length=3,default = 'N/A')


    def save(self, *args,**kwargs):

        terms_list = Term.objects.all()

        for eachterm in terms_list :

            #Calculate mid-term date
            start = eachterm.start_date
            end = eachterm.end_date
            mid_term_date = start + (end - start)/2
            close_to_end_of_term = end-(end - mid_term_date)/6

            try:
                next_term = Term.objects.get(term_number = eachterm.term_number + 1)
            except ObjectDoesNotExist:
                next_term = None

            #Display term number only if the lesson starts before mid-term
            if(eachterm.start_date <= self.lesson_date_time.date()  <= close_to_end_of_term):
                self.term = 'Term : ' + str(eachterm.term_number) #+ '            For reference : ' + str(self.lesson_date_time.date())
                break
            #Set term date for next term if the current term is close to finishing
            elif (next_term != None and close_to_end_of_term <= self.lesson_date_time.date()  < next_term.start_date):
                term = eachterm.term_number + 1
                self.term = 'Term : ' + str(term) + '(Close to next term)'#               For reference : ' + str(self.lesson_date_time.date())
                break
            #Set term date for next term if the current term is close to finishing and the is no next term set
            elif(next_term == None and close_to_end_of_term <= self.lesson_date_time.date()  < end):
                self.term = 'Term : ' + str(eachterm.term_number) + '(Close to next term but no next term)'#       For reference : ' + str(self.lesson_date_time.date())
                break
            # else:#If lesson is not before mid term and is not close to end of term
            #     self.term = 'N/A'

        super(Lesson,self).save(*args, **kwargs)



    class Meta:
        unique_together = (('request_date', 'lesson_date_time', 'student_id'),)

    def is_equal(self,other_lesson):
        return ((self.lesson_id == other_lesson.lesson_id) and (self.request_date == other_lesson.request_date) and (self.lesson_date_time == other_lesson.lesson_date_time) and (self.student_id == other_lesson.student_id))

# Invoice models refers to invoices student for their lessons has when their lesson status is booked
# reference_number field specify a unique reference number for each invoice, and the reference number is construct base on their student number and number of invoices pre exist, this field cannot be blank
# student_Id field refers to the student id of the student who own this invoice
# fees_amount field refers to the total amounts of the fees of this invoice
# invoices_status field refers to the status of this invoices, can be PAID, UNPAID, PARTIALLY_PAID and DELETED
# amounts_need_to_pay refers to the amount left for student to pay for this invoice
# lesson_ID refers to the lesson this invoice pay for
class Invoice(models.Model):
    reference_number = models.CharField(
        max_length=30,
        unique=True,
        blank=False,
        validators=[RegexValidator(
            regex = r'^\d*\d-\d\d\d\d*$',
            message='Reference number must all be number and consist of - in between followed by at least three numbers'
        )]
    )

    student_ID = models.CharField(
        max_length = 30,
        blank=False,
        validators=[RegexValidator(
            regex = r'^\d+$',
            message='Student ID must all be number'
        )]
    )

    fees_amount = models.IntegerField(
        blank=False,
        validators=[
            MaxValueValidator(10000),
            MinValueValidator(1),
        ]
    )

    invoice_status = models.CharField(
        max_length=30,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.UNPAID,
        blank = False,
    )

    amounts_need_to_pay = models.IntegerField(
        blank=False,
        default = 0,
        validators=[
            MaxValueValidator(10000),
            MinValueValidator(0),
        ]
    )

    lesson_ID = models.CharField(
        unique = False,
        max_length = 30,
        blank=True,
        validators=[RegexValidator(
            regex = r'^\d+$',
            message='Lesson ID must all be number'
        )]
    )

    # This function is use to construct reference number for invoice
    # The reference number is create base on the student id and the number of pre exist invoices for this student
    # The contructed invoice reference number will then be return
    def generate_new_invoice_reference_number(student_id, number_of_exist_invoice):
        number_of_exist_invoice +=1
        if(number_of_exist_invoice < 10):
            reference_number = student_id + '-' + '00' + str(number_of_exist_invoice) # student 1 with 2 exist invoice get a new reference_number 1-003
        elif(number_of_exist_invoice < 100):
            reference_number = student_id + '-' + '0' + str(number_of_exist_invoice) # student 1 with 10 exist invoice get a new reference_number 1-011
        else:
            reference_number = student_id + '-' + str(number_of_exist_invoice) # student 1 with 788 exist invoice get a new reference_number 1-789

        return f'{reference_number}'

    # This function calculate the fees amount of the invoice
    # The way we do it is easy, it is all base on the duration of the lesson
    # The fees of the lesson will then be return
    def calculate_fees_amount(lesson_duration):
        #30 mins lesson cost 15, 45 mins lesson cost 18,  1 hr lesson cost 20, no matter the date and teacher
        if(lesson_duration == LessonDuration.THIRTY):
            fees = 15
        elif(lesson_duration == LessonDuration.FOURTY_FIVE):
            fees = 18
        else:
            fees = 20
        return f'{fees}'

# Transaction models refers to the transaction student made outside the system for the not fully paid invoice
# Student_ID_transaction refers to the student id of the student who made the transaction
# invoice_reference_transaction refers to the invoice this transaction paid for, this field can't be unique as student can pay for same invoice multiple times
# transaction_amount refers to the amount of the money student paid outside the system
class Transaction(models.Model):
    Student_ID_transaction = models.CharField(
        max_length = 30,
        blank=False,
        validators=[RegexValidator(
            regex = r'^\d+$',
            message='Student ID must all be number'
        )]
    )

    invoice_reference_transaction = models.CharField(
        max_length=30,
        unique=False,
        blank=True,
        validators=[RegexValidator(
            regex = r'^\d*\d-\d\d\d\d*$',
            message='Reference number must all be number and consist of - in between followed by at least three numbers'
        )]
    )

    transaction_amount = models.IntegerField(
        blank=False,
        default= 1,
        validators=[
            MaxValueValidator(10000),
            MinValueValidator(1),
        ]
    )

class Term(models.Model):
    term_number =  models.IntegerField(
        # blank = True,
        # editable=False,
        # unique=True,
        validators=[
            MaxValueValidator(6),
            MinValueValidator(1),
        ]
    )

    start_date = models.DateField(
        auto_now=False,
        auto_now_add=False,
        blank=True,
        null=True
    )
    end_date = models.DateField(
        auto_now=False,
        auto_now_add=False,
        blank=True,
        null=True
    )


    def create_term(self, term_number, start_date, end_date):
        '''Create and save a term with the given term_number, start_date and end_date'''

        if not term_number:
            raise ValueError('The given term_number must be set')
        if not term_number:
            raise ValueError('The given start_date must be set')
        if not term_number:
            raise ValueError('The given end_date must be set')

        # user = self.model(email=email, **extra_fields)
        term = self.model(term_number=term_number, start_date=start_date,end_date=end_date)
        term.save(using=self._db)
        return term
