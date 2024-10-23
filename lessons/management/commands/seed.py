from django.core.management.base import BaseCommand, CommandError
from faker import Faker
from lessons.models import UserAccount, Lesson, UserRole, Gender, LessonType,LessonDuration,LessonStatus,Invoice, InvoiceStatus, Transaction,Term
import random
import string
import datetime
from datetime import date
from django.utils import timezone
from django.db import IntegrityError

letters = string.ascii_lowercase


class Command(BaseCommand):

    def __init__(self):
        super().__init__()
        self.faker = Faker()

    # Seeds the database with users
    def handle(self, *args, **options):

        # Add the set Student, Admin and Directors
        UserAccount.objects.create_admin(
            first_name="Petra",
            last_name="Pickles",
            email= "petra.pickles@example.org",
            password="Password123",
            gender ="F",
        )
        UserAccount.objects.create_superuser(
            first_name="Marty",
            last_name="Major",
            email= "marty.major@example.org",
            password="Password123",
            gender ="PNOT",
        )

        Term.objects.create(
            term_number=1,
            start_date = datetime.date(2022, 9,1),
            end_date = datetime.date(2022, 10,21),
        )

        Term.objects.create(
            term_number=2,
            start_date = datetime.date(2022, 10,31),
            end_date = datetime.date(2022, 12,16),
        )

        Term.objects.create(
            term_number=3,
            start_date = datetime.date(2023, 1,3),
            end_date = datetime.date(2023, 2,10),
        )

        Term.objects.create(
            term_number=4,
            start_date = datetime.date(2023, 2,20),
            end_date = datetime.date(2023, 3,31),
        )

        Term.objects.create(
            term_number=5,
            start_date = datetime.date(2023, 4,17),
            end_date = datetime.date(2023, 5,26),
        )

        Term.objects.create(
            term_number=6,
            start_date = datetime.date(2023, 6,5),
            end_date = datetime.date(2023, 7,21),
        )

        #restet fakers uniqueness every time we seed
        self.faker.unique.clear()

        # Seed the students

        for i in range(99):

            fname = self.faker.unique.first_name()
            lname = self.faker.unique.last_name()
            mails = ["gmail.com","yahoo.com","outlook.com","example.org"]
            random_password = ''.join(random.choice(letters) for i in range(10))
            genders = ['M','F','PNOT']

            self.student = UserAccount.objects.create_student(
                first_name=fname,
                last_name=lname,
                email= f'{fname[0].lower()}{lname.lower()}{random.randint(0,100)}@{mails[random.randint(0,3)]}',
                password=f'{random_password}',
                gender = f'{genders[random.randint(0,2)]}',
            )

            # seed the children
            for i in range(random.randint(0,2)):

                fname = self.faker.unique.first_name()
                lname = self.faker.unique.last_name()
                mails = ["gmail.com","yahoo.com","outlook.com","example.org"]
                random_password = ''.join(random.choice(letters) for i in range(10))
                genders = ['M','F','PNOT']

                UserAccount.objects.create_child_student(
                    parent_of_user = self.student,
                    first_name=fname,
                    last_name=self.student.last_name,
                    email= f'{fname[0].lower()}{lname.lower()}{random.randint(0,100)}@{mails[random.randint(0,3)]}',
                    password=f'{random_password}',
                    gender = f'{genders[random.randint(0,2)]}',
                )

        # Seed the teachers
        for i in range(5):
            fname = self.faker.unique.first_name()
            lname = self.faker.unique.last_name()
            mails = ["gmail.com","yahoo.com","outlook.com","example.org","icloud.com"]
            random_password = ''.join(random.choice(letters) for i in range(10))
            genders = ['M','F','PNOT']

            UserAccount.objects.create_teacher(
                first_name=fname,
                last_name=lname,
                email= f'{fname[0].lower()}{lname.lower()}{random.randint(0,100)}@{mails[random.randint(0,3)]}',
                password=f'{random_password}',
                gender = f'{genders[random.randint(0,2)]}',
            )

        # Seed the lessons for every student
        teachers = UserAccount.objects.filter(role=UserRole.TEACHER.value)
        students = UserAccount.objects.filter(role=UserRole.STUDENT.value)
        lesson_types = list(LessonType)
        Lesson_durations = list(LessonDuration)
        lesson_status = list(LessonStatus)

        # increases chances to get booked lessons
        lesson_status.remove(LessonStatus.SAVED)
        lesson_status.append(LessonStatus.FULLFILLED)
        lesson_status.append(LessonStatus.FULLFILLED)

        terms = list(Term.objects.all())

        for i in range(len(students)):

            current_term = terms[random.randint(0,len(terms)-1)]

            current_lesson_status = lesson_status[random.randint(0,len(lesson_status)-1)]

            for x in range(0,3):
                random_req_day = self.faker.date_between(start_date='-1y', end_date=current_term.end_date)

                for _ in range(random.randint(0,3)):

                    rand_teacher = teachers[random.randint(0,len(teachers)-1)]
                    rand_lesson_date_time = self.faker.date_time_between(tzinfo = timezone.utc,start_date=current_term.start_date, end_date=current_term.end_date)

                    # ensures sure lessons date fall within the term, and is not on a weekend, and on different time if on the same say
                    try:
                        Lesson.objects.create(
                            type = lesson_types[random.randint(0,len(lesson_types)-1)] ,
                            duration = Lesson_durations[random.randint(0,len(Lesson_durations)-1)] ,
                            lesson_date_time = rand_lesson_date_time,
                            teacher_id = rand_teacher,
                            student_id = students[i],
                            request_date = random_req_day,
                            lesson_status = lesson_status[random.randint(0,len(lesson_status)-1)],
                        )
                    except IntegrityError:
                        pass

        # Seed the admins
        for i in range(3):
            fname = self.faker.unique.first_name()
            lname = self.faker.unique.last_name()
            mails = ["gmail.com","yahoo.com","outlook.com","example.org"]
            random_password = ''.join(random.choice(letters) for i in range(10))
            genders = ['M','F','PNOT']

            UserAccount.objects.create_admin(
                first_name=fname,
                last_name=lname,
                email= f'{fname[0].lower()}{lname.lower()}{random.randint(0,100)}@{mails[random.randint(0,3)]}',
                password=f'{random_password}',
                gender = f'{genders[random.randint(0,2)]}',
            )

        # Seed the directors
        for i in range(1):
            fname = self.faker.unique.first_name()
            lname = self.faker.unique.last_name()
            mails = ["gmail.com","yahoo.com","outlook.com","example.org"]
            random_password = ''.join(random.choice(letters) for i in range(10))
            genders = ['M','F','PNOT']

            UserAccount.objects.create_superuser(
                first_name=fname,
                last_name=lname,
                email= f'{fname[0].lower()}{lname.lower()}{random.randint(0,100)}@{mails[random.randint(0,3)]}',
                password=f'{random_password}',
                gender = f'{genders[random.randint(0,2)]}',
            )


        #Add set lessons for student john doe, and corresponding lessons and children
        self.john_doe_student = UserAccount.objects.create_student(
            first_name="John",
            last_name="Doe",
            email= "john.doe@example.org",
            password="Password123",
            gender ="M",
        )


        # create request for John Doe (set of lessons)
        Lesson.objects.create(
            type = lesson_types[random.randint(0,len(lesson_types)-1)] ,
            duration = Lesson_durations[random.randint(0,len(Lesson_durations)-1)] ,
            lesson_date_time = datetime.datetime(2022, 12, 1, 12, 0, 0, 0).replace(tzinfo=timezone.utc),
            teacher_id = teachers[random.randint(0,len(teachers)-1)],
            student_id = self.john_doe_student,
            request_date = date(2022,10,25),
            lesson_status = LessonStatus.FULLFILLED,
        )

        Lesson.objects.create(
            type = lesson_types[random.randint(0,len(lesson_types)-1)] ,
            duration = Lesson_durations[random.randint(0,len(Lesson_durations)-1)] ,
            lesson_date_time = datetime.datetime(2022, 12, 5, 12, 0, 0, 0).replace(tzinfo=timezone.utc),
            teacher_id = teachers[random.randint(0,len(teachers)-1)],
            student_id = self.john_doe_student,
            request_date = date(2022,10,25),
            lesson_status = LessonStatus.FULLFILLED,
        )

        Lesson.objects.create(
            type = lesson_types[random.randint(0,len(lesson_types)-1)] ,
            duration = Lesson_durations[random.randint(0,len(Lesson_durations)-1)] ,
            lesson_date_time = datetime.datetime(2022, 12, 12, 12, 0, 0, 0).replace(tzinfo=timezone.utc),
            teacher_id = teachers[random.randint(0,len(teachers)-1)],
            student_id = self.john_doe_student,
            request_date = date(2022,10,25),
            lesson_status = LessonStatus.FULLFILLED,
        )

        self.alice_doe_child = UserAccount.objects.create_child_student(
            parent_of_user = self.john_doe_student,
            first_name= "Alice",
            last_name= "Doe",
            email= "alice.doe@example.org",
            password="Password123",
            gender = "F",
        )

        # create request for Alice Doe (set of lessons)
        Lesson.objects.create(
            type = lesson_types[random.randint(0,len(lesson_types)-1)] ,
            duration = Lesson_durations[random.randint(0,len(Lesson_durations)-1)] ,
            lesson_date_time = datetime.datetime(2023, 1, 21, 10, 0, 0, 0).replace(tzinfo=timezone.utc),
            teacher_id = teachers[random.randint(0,len(teachers)-1)],
            student_id = self.alice_doe_child,
            request_date = date(2022,12,25),
            lesson_status = LessonStatus.FULLFILLED,
        )

        Lesson.objects.create(
            type = lesson_types[random.randint(0,len(lesson_types)-1)] ,
            duration = Lesson_durations[random.randint(0,len(Lesson_durations)-1)] ,
            lesson_date_time = datetime.datetime(2023, 1, 12, 13, 0, 0, 0).replace(tzinfo=timezone.utc),
            teacher_id = teachers[random.randint(0,len(teachers)-1)],
            student_id = self.alice_doe_child,
            request_date = date(2022,12,25),
            lesson_status = LessonStatus.FULLFILLED,
        )

        self.bob_doe_child = UserAccount.objects.create_child_student(
            parent_of_user = self.john_doe_student,
            first_name= "Bob",
            last_name= "Doe",
            email= "bob.doe@example.org",
            password="Password123",
            gender = "M",
        )


        # create request for Bob Doe (set of lessons)
        Lesson.objects.create(
            type = lesson_types[random.randint(0,len(lesson_types)-1)] ,
            duration = Lesson_durations[random.randint(0,len(Lesson_durations)-1)] ,
            lesson_date_time = datetime.datetime(2023, 2, 26, 10, 0, 0, 0).replace(tzinfo=timezone.utc),
            teacher_id = teachers[random.randint(0,len(teachers)-1)],
            student_id = self.bob_doe_child,
            request_date = date(2023,1,1),
            lesson_status = LessonStatus.FULLFILLED,
        )

        Lesson.objects.create(
            type = lesson_types[random.randint(0,len(lesson_types)-1)] ,
            duration = Lesson_durations[random.randint(0,len(Lesson_durations)-1)] ,
            lesson_date_time = datetime.datetime(2023, 2, 28, 13, 0, 0, 0).replace(tzinfo=timezone.utc),
            teacher_id = teachers[random.randint(0,len(teachers)-1)],
            student_id = self.bob_doe_child,
            request_date = date(2022,1,1),
            lesson_status = LessonStatus.FULLFILLED,
        )

        # seed the invoices base on existing user and bookings
        students = UserAccount.objects.filter(role=UserRole.STUDENT.value)
        for i in range(len(students)): # this seeder function will seed invoice and transactions for all exisitng student
            student_Id = students[i].id
            students_id_string = str(student_Id) # turn the studen id to string so it will able to use for constructingt the reference number of the invoice

            # this filter out all the booked lesson for this student
            lessons_booked = Lesson.objects.filter(student_id = students[i], lesson_status = LessonStatus.FULLFILLED)
            for lesson in lessons_booked:
                # for each lesson, calculate the fees and contruct the reference number of the invoice
                fees = Invoice.calculate_fees_amount(lesson.duration)
                fees_int = int(fees)
                student_number_of_invoice_pre_exist = Invoice.objects.filter(student_ID = student_Id)
                reference_number_temp = Invoice.generate_new_invoice_reference_number(students_id_string, len(student_number_of_invoice_pre_exist))

                # the invoice status is random, there's low probably to create UNPAID and PARTIALLY_PAID invoice and a very low chance to create OVERPAID invoice
                # if the invoice status is not UNPAID, a transaction will also be created
                # if this student is a child of another student, then the transaction will be create under the parent as child shouldn't be able to pay for the invoice
                probability = random.randint(0, 12)
                probability_OVER_PAID = random.randint(0,3)
                if(probability == 3 or probability == 4): # unpaid invoice
                    Invoice.objects.create(reference_number =  reference_number_temp, student_ID = students_id_string, fees_amount = fees_int, invoice_status = InvoiceStatus.UNPAID, amounts_need_to_pay = fees_int, lesson_ID = lesson.lesson_id)
                elif(probability == 5 or probability == 6): # partially paid invoice
                    amount_paid = random.randint(10, fees_int - 1)
                    amount_needs_to_be_pay = fees_int - amount_paid
                    Invoice.objects.create(reference_number =  reference_number_temp, student_ID = students_id_string, fees_amount = fees_int, invoice_status = InvoiceStatus.PARTIALLY_PAID, amounts_need_to_pay = amount_needs_to_be_pay, lesson_ID = lesson.lesson_id)
                    if(students[i].parent_of_user):
                        Transaction.objects.create(Student_ID_transaction = str(students[i].parent_of_user.id), invoice_reference_transaction = reference_number_temp, transaction_amount = amount_paid)
                    else:
                        Transaction.objects.create(Student_ID_transaction = students_id_string, invoice_reference_transaction = reference_number_temp, transaction_amount = amount_paid)
                elif(probability == 7 and probability_OVER_PAID == 2): # overpaid invoice
                    amount_paid = random.randint(fees_int +100, fees_int + 200)
                    Invoice.objects.create(reference_number =  reference_number_temp, student_ID = students_id_string, fees_amount = fees_int, invoice_status = InvoiceStatus.PAID, amounts_need_to_pay = 0, lesson_ID = lesson.lesson_id)
                    if(students[i].parent_of_user):
                        Transaction.objects.create(Student_ID_transaction = str(students[i].parent_of_user.id), invoice_reference_transaction = reference_number_temp, transaction_amount = amount_paid)
                    else:
                        Transaction.objects.create(Student_ID_transaction = students_id_string, invoice_reference_transaction = reference_number_temp, transaction_amount = amount_paid)
                else:
                    Invoice.objects.create(reference_number =  reference_number_temp, student_ID = students_id_string, fees_amount = fees_int, invoice_status = InvoiceStatus.PAID, amounts_need_to_pay = 0, lesson_ID = lesson.lesson_id)
                    if(students[i].parent_of_user):
                        Transaction.objects.create(Student_ID_transaction = str(students[i].parent_of_user.id), invoice_reference_transaction = reference_number_temp, transaction_amount = fees_int)
                    else:
                        Transaction.objects.create(Student_ID_transaction = students_id_string, invoice_reference_transaction = reference_number_temp, transaction_amount = fees_int)

            # this calculate the balance for student, if this student has children, the children's invoice will also be use to calculte the balance
            if(students[i].parent_of_user):
                current_existing_invoice_parent = Invoice.objects.filter(student_ID = students[i].parent_of_user.id)

                list_of_child_invoice = []
                children = UserAccount.objects.filter(parent_of_user = students[i].parent_of_user)
                for child in children:
                    child_invoice = Invoice.objects.filter(student_ID = child.id)
                    for invoice in child_invoice:
                        list_of_child_invoice.append(invoice)

                current_existing_transaction = Transaction.objects.filter(Student_ID_transaction = students[i].parent_of_user.id)

                invoice_fee_total = 0
                payment_fee_total = 0

                for invoice in list_of_child_invoice:
                    invoice_fee_total += invoice.fees_amount

                for invoice in current_existing_invoice_parent:
                    invoice_fee_total += invoice.fees_amount

                for transaction in current_existing_transaction:
                    payment_fee_total += transaction.transaction_amount

                students[i].parent_of_user.balance = payment_fee_total - invoice_fee_total
                students[i].parent_of_user.save()
            else:
                current_existing_invoice = Invoice.objects.filter(student_ID = student_Id)
                current_existing_transaction = Transaction.objects.filter(Student_ID_transaction = student_Id)
                invoice_fee_total = 0
                payment_fee_total = 0

                for invoice in current_existing_invoice:
                    invoice_fee_total += invoice.fees_amount

                for transaction in current_existing_transaction:
                    payment_fee_total += transaction.transaction_amount

                students[i].balance = payment_fee_total - invoice_fee_total
                students[i].save()
