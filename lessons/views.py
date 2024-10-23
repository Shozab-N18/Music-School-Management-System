from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.contrib import messages

from .forms import LogInForm,SignUpForm,RequestForm,TermDatesForm,CreateAdminForm
from django.contrib.auth import authenticate,login,logout
from .models import UserRole, UserAccount, Lesson, LessonStatus, LessonType, Gender, Invoice, Transaction, InvoiceStatus,Term
from .helper import login_prohibited,check_valid_date,make_lesson_timetable_dictionary,get_student_and_child_objects,get_student_and_child_lessons,get_saved_lessons,get_admin_email,make_lesson_dictionary,check_correct_student_accessing_pending_lesson,check_correct_student_accessing_saved_lesson

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden
from django.db import IntegrityError
import datetime
from itertools import chain

# Create your views here.

from django.template.defaulttags import register


"""
functions to call in the templates for dictionaries storing the relevant keys
"""
@register.filter
def get_lesson_duration(dictionary):
    return dictionary.get("Lesson Duration")

@register.filter
def get_lesson(dictionary):
    return dictionary.get("Lesson")

@register.filter
def get_lesson_date(dictionary):
    return dictionary.get("Lesson Date")

@register.filter
def get_teacher(dictionary):
    return dictionary.get("Teacher")

@register.filter
def get_lesson_request(dictionary):
    return dictionary.get("Lesson Request")

@register.filter
def get_lesson_student(dictionary):
    return dictionary.get("Student")

#This function is call when student is trying to access the balance page from student feed
# This function will get all the invoices and transactions belongs to this student,
# If this student has any children, all of his children's invoices will be get is well
# The student's balance will also be update
# All of the above data will be pass into balance.html and print out
# If the user that trying to access this page is not identify as student, he will be redirect to home page
@login_required
def balance(request):
    if(request.user.is_authenticated and request.user.role == UserRole.STUDENT):
        if request.method == 'GET':
            student = request.user
            student_invoice = get_student_invoice(student) #this function filter out the invocie with the same student id as the current user
            student_transaction = get_student_transaction(student) #this function filter out the transaction with the same student id as the current user
            update_balance(student)
            student_balance = get_student_balance(student)
            child_invoices =  get_child_invoice(student)
            return render(request, 'balance.html', {'student': student, 'Invoice': student_invoice, 'Transaction': student_transaction, 'Balance': student_balance, 'child_invoices': child_invoices})
    else:
        return redirect('home')

# This function returns all invoices that belongs to the student(params) that insert as a parameter
# All invoices that filter out will be return
def get_student_invoice(student):
    return Invoice.objects.filter(student_ID = student.id)

# This function returns all transactions that belongs to this student(params).
# All transactionss that filter out will be return
def get_student_transaction(student):
    return Transaction.objects.filter( Student_ID_transaction = student.id)

# This function returns the balance of this student.
# The balance will be return
def get_student_balance(student):
    return UserAccount.objects.filter(id = student.id).values_list('balance', flat=True)

# this function filter out all children that belongs to this student(params)
# And then all invoices belong to those children will be filter out and insert into a list
# This list of invoices will be return
def get_child_invoice(student):
    list_of_child_invoice = []

    children = UserAccount.objects.filter(parent_of_user = student)
    for child in children:
        child_invoice = Invoice.objects.filter(student_ID = child.id)
        for invoice in child_invoice:
            list_of_child_invoice.append(invoice)

    return list_of_child_invoice


# This function update the student balance for the student(params)
# This function filter out all existing invoices that belongs to this student and this student's children
# This function also filter out all existing transactions that belongs to this student
# Then a balance will be calculate by adding up fees_amounts of all transactions and using this number to minus fees_amounts of all invoices
def update_balance(student):
    current_existing_invoice = Invoice.objects.filter(student_ID = student.id)
    current_existing_transaction = Transaction.objects.filter(Student_ID_transaction = student.id)
    child_invoices = get_child_invoice(student)
    invoice_fee_total = 0
    payment_fee_total = 0

    # Functions below are adding up fees for each invoices and transactions
    for invoice in current_existing_invoice:
        invoice_fee_total += invoice.fees_amount

    for child_invoice in child_invoices:
        invoice_fee_total += child_invoice.fees_amount

    for transaction in current_existing_transaction:
        payment_fee_total += transaction.transaction_amount

    student.balance = payment_fee_total - invoice_fee_total
    student.save()

# This function is call when student is trying to pay for he and his children's invoices
# If the user is identify as student, he will be able to go to the next step, or else he will be redirect to home page
# The function first detect if there are values exist in all require field, or else it will add an error message, and student will be redirect to balance page
# Then the function will try to find if there is any invoice in database that fit to the one student enter by comparing their reference number
# If there isn't any invoice with same reference number as the one student enter, an error message will be added, and student will be redirect to balance page
# If the invoice can be found in the database, this invoice will be check base on serval condition
# If any of it didn't meet, a correspond error message will be added, and student will be redirect to balance page
# If all of them met, the status of the invoice will be reset base on how much student paid for it, and student balance will be update, and a new transaction will be created
@login_required
def pay_for_invoice(request):
    if(request.user.is_authenticated and request.user.role == UserRole.STUDENT):
        if(request.method == 'POST'):
            # check all require fields are filled, if not error message will be added
            try:
                input_invoice_reference = request.POST.get('invocie_reference')
                input_amounts_pay = request.POST.get('amounts_pay')
                input_amounts_pay_int = int(input_amounts_pay)
            except ValueError:
                messages.add_message(request,messages.ERROR,"You cannot submit without enter a value!")
                return redirect('balance')

            student = request.user
            try:
                temp_invoice = Invoice.objects.get(reference_number = input_invoice_reference)
            except ObjectDoesNotExist:
                messages.add_message(request,messages.ERROR,"There isn't such invoice exist!")
                return redirect('balance')

            # check if this invoice belongs to this student or his children or not
            if(int(temp_invoice.student_ID) != int(student.id) and check_invoice_belong_to_child(temp_invoice, student) == False):
                messages.add_message(request,messages.ERROR,"this invoice does not belong to you or your children!")
            # check if this invoice is paid or not, if it is there's no point to pay for it any more
            elif(temp_invoice.invoice_status == InvoiceStatus.PAID):
                messages.add_message(request,messages.ERROR,"This invoice has already been paid!")
            # check if this invoice is deleted or not, if it is there's no point to pay for it any more
            elif(temp_invoice.invoice_status == InvoiceStatus.DELETED):
                messages.add_message(request,messages.ERROR,"This invoice has already been deleted!")
            # check if the number student insert for the amount they want to pay is less than 1, student is not allow to insert 0 or negative number
            elif(input_amounts_pay_int < 1):
                messages.add_message(request,messages.ERROR,"Transaction amount cannot be less than 1!")
            # check if the number student insert for the amount they want to pay is larger than 10000, student is not allow to insert number larger than 10000
            elif(input_amounts_pay_int > 10000):
                messages.add_message(request,messages.ERROR,"Transaction amount cannot be larger than 10000!")
            # update the status of the invoice, depends on how much student paid
            else:
                if(temp_invoice.amounts_need_to_pay <= input_amounts_pay_int):
                    temp_invoice.invoice_status = InvoiceStatus.PAID
                    temp_invoice.amounts_need_to_pay = 0
                elif(temp_invoice.amounts_need_to_pay > input_amounts_pay_int):
                    temp_invoice.invoice_status = InvoiceStatus.PARTIALLY_PAID
                    temp_invoice.amounts_need_to_pay -= input_amounts_pay_int
                # update the balance for student
                update_balance(student)
                student.save()
                temp_invoice.save()

                Transaction.objects.create(Student_ID_transaction = student.id, invoice_reference_transaction = input_invoice_reference, transaction_amount = input_amounts_pay_int)

            return redirect('balance')

        return redirect('balance')

    else:
        return redirect('home')

# This function checks if the invoice is belongs the student's children or not
# It filter out all children that belongs to this student by comparing the parent_of_user field of all students and the student(params)
# If yes then return Ture, else False
def check_invoice_belong_to_child(temp_invoice, student):
    children = UserAccount.objects.filter(parent_of_user = student)
    for child in children:
        if int(temp_invoice.student_ID) == int(child.id):
            return True
    return False

# This function create new invoice for the student
# Ths all pre exist invoices of this student will be get
# As this will be use to construct reference number of new invoices by using function generate_new_invoice_reference_number in Invoice model
# The the fees of this invoice will be calcualted by using calculate_fees_amount function from Invoice model
# At last, all the about data will be using to create a new invoice for this student
# And this student's balance will be update as a new invoice created
def create_new_invoice(student_id, lesson):
        student_number_of_invoice_pre_exist = Invoice.objects.filter(student_ID = student_id)
        try:
            student = UserAccount.objects.get(id=student_id)
        except ObjectDoesNotExist:
            return redirect('home')
        reference_number_temp = Invoice.generate_new_invoice_reference_number(str(student_id), len(student_number_of_invoice_pre_exist))
        lesson_duration = lesson.duration
        fees = Invoice.calculate_fees_amount(lesson_duration)
        fees = int(fees)
        Invoice.objects.create(reference_number =  reference_number_temp, student_ID = student_id, fees_amount = fees, invoice_status = InvoiceStatus.UNPAID, amounts_need_to_pay = fees, lesson_ID = lesson.lesson_id)
        update_balance(student)

# This function update invoice for student when the lesson of this invoice refers to has been modify
# The fees of the lesson will be recalculate if the duration of the lesson has been changed
# However if this booked lesson is created directly from django admin page
# Therefore the create_new_invocie function will not be call so in this case create new invoice will be done in here

def update_invoice(lesson):
    try:
        invoice = Invoice.objects.get(lesson_ID = lesson.lesson_id)
        student = UserAccount.objects.get(id=invoice.student_ID)

        fees = Invoice.calculate_fees_amount(lesson.duration)
        fees = int(fees)
        difference_between_invoice = fees - invoice.fees_amount
        invoice.fees_amount = fees
        invoice.amounts_need_to_pay += difference_between_invoice
        invoice.save()
        student = UserAccount.objects.get(id=invoice.student_ID)

        update_balance(student)
    except ObjectDoesNotExist: # this only happen in the case admin create lesson directly from django admin page
        fees = Invoice.calculate_fees_amount(lesson.duration)
        students_id_string = str(lesson.student_id.id)
        student_number_of_invoice_pre_exist = Invoice.objects.filter(student_ID = lesson.student_id.id)
        reference_number_temp = Invoice.generate_new_invoice_reference_number(students_id_string, len(student_number_of_invoice_pre_exist))
        Invoice.objects.create(reference_number =  reference_number_temp, student_ID = students_id_string, fees_amount = fees, invoice_status = InvoiceStatus.UNPAID, amounts_need_to_pay = fees, lesson_ID = lesson.lesson_id)

# This function will update the invoice status when lesson delete
# As there's only invoice for booked lesson, so there's a if loop to detect the status of the lesson
# If the deleted lesson is booked, then invoice status will be set as DELETD and the field will be modify
def update_invoice_when_delete(lesson):
    if(lesson.lesson_status == LessonStatus.FULLFILLED):
        try:
            invoice = Invoice.objects.get(lesson_ID = lesson.lesson_id)
        except ObjectDoesNotExist:
            return redirect('home')
        invoice.invoice_status = InvoiceStatus.DELETED
        invoice.amounts_need_to_pay = 0
        invoice.fees_amount = 0
        invoice.lesson_ID = ''
        invoice.save()


# This function will be call in admin page when press a button to display all students' transactions
# This function only works when the user is identify as an Admin or a Director, or else the user will be redirect to home page
# This function also calculate a total of the transaction_amounts of all transactions students made
# Both total and transactions will be pass into transaction_history.html and dispaly in a table
@login_required
def get_all_transactions(request):
    try:
        if(request.user.is_authenticated and (request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR)):
            all_transactions = Transaction.objects.all()
            total = 0
            for each_transaction in all_transactions:
                    total+= each_transaction.transaction_amount

            return render(request,'transaction_history.html', {'all_transactions': all_transactions, 'total':total})
        else:
            return redirect('home')
    except ObjectDoesNotExist:
        messages.add_message(request,messages.ERROR,"No such student exist!")
        return redirect('home')

# This function will be call in admin page when press a button to display all students' invoices
# This function only works when the user is identify as an Admin or a Director, or else the user will be redirect to home page
# All invoices will be pass into invoices_history.html and dispaly in a table
@login_required
def get_all_invocies(request):
    try:
        if(request.user.is_authenticated and (request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR)):
            all_invoices = Invoice.objects.all()

            return render(request,'invoices_history.html', {'all_invoices': all_invoices})
        else:
            return redirect('home')
    except ObjectDoesNotExist:
        messages.add_message(request,messages.ERROR,"No such student exist!")
        return redirect('home')

# This function will be call when admin or director try to see all invoices and transactions that belongs to this student
# This function will get all invoices and transactions that belongs to this student and pass them into student_invoices_and_transactions.html
# Those data will be display as two tables in the page
@login_required
def get_student_invoices_and_transactions(request, student_id):
    try:
        if(request.user.is_authenticated and (request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR)):
            student = UserAccount.objects.get(id=student_id)
            all_invoices = Invoice.objects.filter(student_ID = student_id)
            all_transactions = Transaction.objects.filter(Student_ID_transaction = student_id)

            return render(request, 'student_invoices_and_transactions.html', {'student': student, 'all_invoices': all_invoices, 'all_transactions':all_transactions})
        else:
            return redirect('home')
    except ObjectDoesNotExist:
        messages.add_message(request,messages.ERROR,"No such student exist!")
        return redirect('home')



# Admin functionality view functions


def get_parent(student):
    for eachuser in UserAccount.objects.filter(is_parent = True):
        child_students = UserAccount.objects.filter(parent_of_user = eachuser)
        for eachchild in child_students:
            if(eachchild.id == student.id):
                return eachuser
    return None


@login_required
def student_requests(request,student_id):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if request.method == 'GET':
            try:
                student = UserAccount.objects.get(id=student_id)
                family = get_student_and_child_objects(student)

                user_lesson_dictionary = {}

                for eachuser in family:
                    lessons = Lesson.objects.filter(student_id = eachuser).order_by('request_date')
                    user_lesson_dictionary.update({ eachuser : lessons})

                return render(request,'admin_student_requests_page.html',{'user_lesson_dictionary':user_lesson_dictionary, 'student':student})
            except ObjectDoesNotExist:
                messages.add_message(request, messages.ERROR, 'Student does not exist!')
                return redirect('admin_feed')
        else:
            return redirect('admin_feed')
    else:
        return redirect('home')

@login_required
def admin_update_request_page(request, lesson_id):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if request.method == 'GET':
            try:
                lesson = Lesson.objects.get(lesson_id=lesson_id)
                data = {
                    'type' : lesson.type,
                    'duration': lesson.duration,
                    'lesson_date_time': lesson.lesson_date_time,
                    'teachers' : lesson.teacher_id
                    }
                form = RequestForm(data)
                return render(request,'admin_update_request.html', {'form': form , 'lesson': lesson})
            except ObjectDoesNotExist:
                messages.add_message(request, messages.ERROR, 'Something went wrong!')
                return redirect('admin_feed')
        else:
            return redirect('admin_feed')
    else:
        return redirect('home')

@login_required
def admin_update_request(request, lesson_id):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if request.method == 'POST':
            try:
                lesson = Lesson.objects.get(lesson_id=lesson_id)
                form = RequestForm(request.POST)

                if form.is_valid():
                    type = form.cleaned_data.get('type')
                    duration = form.cleaned_data.get('duration')
                    lesson_date_time = form.cleaned_data.get('lesson_date_time')
                    teacher_id = form.cleaned_data.get('teachers')

                    if (lesson.type == type and lesson.duration == duration and lesson.lesson_date_time == lesson_date_time and lesson.teacher_id == teacher_id):
                        messages.add_message(request, messages.ERROR, 'Lesson details are the same as before!')
                        return render(request,'admin_update_request.html', {'form': form , 'lesson': lesson})
                    else:
                        lesson.type = type
                        lesson.duration = duration
                        lesson.lesson_date_time = lesson_date_time
                        lesson.teacher_id = teacher_id
                        lesson.save()

                        # update_invoice function won' be call for pending lesson, as invoice does not exist at this time
                        if lesson.lesson_status == LessonStatus.FULLFILLED:
                            update_invoice(lesson)

                        messages.add_message(request, messages.SUCCESS, 'Lesson was successfully updated!')

                        student = UserAccount.objects.get(id=lesson.student_id.id)

                        parent = get_parent(student)

                        if (parent != None):
                            return redirect('student_requests',parent.id)
                        else:
                            return redirect('student_requests',student.id)
                else:
                    messages.add_message(request, messages.ERROR, 'Invalid form data!')
                    return redirect('admin_feed')

            except ObjectDoesNotExist:
                messages.add_message(request, messages.ERROR, 'Lesson not found!')
                return redirect('admin_feed')
        else:
            return redirect('admin_feed')
    else:
        return redirect('home')

@login_required
def admin_confirm_booking(request, lesson_id):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if request.method == 'GET':
            try:
                lesson = Lesson.objects.get(lesson_id=lesson_id)
                if(lesson.lesson_status == LessonStatus.FULLFILLED):
                    messages.add_message(request, messages.INFO, 'Already booked!')
                else:
                    lesson.lesson_status = LessonStatus.FULLFILLED
                    lesson.save()
                    messages.add_message(request, messages.SUCCESS, 'Successfully Booked!')
                    create_new_invoice(lesson.student_id.id, lesson)

                student = UserAccount.objects.get(id=lesson.student_id.id)

                parent = get_parent(student)

                if (parent != None):
                    return redirect('student_requests',parent.id)
                else:
                    return redirect('student_requests',student.id)

            except ObjectDoesNotExist:
                messages.add_message(request, messages.ERROR, 'Lesson not found !')
                return redirect('admin_feed')
        else:
            return redirect('admin_feed')
    else:
        return redirect('home')


@login_required
def delete_lesson(request, lesson_id):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if request.method == 'GET':
            try:
                lesson = Lesson.objects.get(lesson_id=lesson_id)
                if lesson is not None:
                    update_invoice_when_delete(lesson)
                    lesson.delete()

                    messages.add_message(request, messages.SUCCESS, 'Lesson was successfully deleted!')

                    student = UserAccount.objects.get(id=lesson.student_id.id)

                    parent = get_parent(student)

                    if (parent != None):
                        return redirect('student_requests',parent.id)
                    else:
                        return redirect('student_requests',student.id)
            except ObjectDoesNotExist:
                messages.add_message(request, messages.ERROR, 'The lesson you tried to delete does not exist!')
                return redirect('admin_feed')
        else:
            return redirect('admin_feed')
    else:
        return redirect('home')



# Term view functions

@login_required
def term_management_page(request):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        terms_list = Term.objects.all().order_by('term_number').values()
        return render(request,'term_management.html', {'terms_list': terms_list})
    else:
        return redirect('home')

@login_required
def add_term_page(request):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if len(Term.objects.all()) < 6:
            form = TermDatesForm()
            return render(request, 'create_term_form.html', {'form':form})
        else:
            messages.add_message(request,messages.ERROR, "Cannot have more than 6 terms in a year, please edit or delete existing terms!")
            return term_management_page(request)
    else:
        return redirect('home')

@login_required
def create_term(request):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if(request.method == 'POST'):
            form = TermDatesForm(request.POST)
            if form.is_valid():
                term_number = form.cleaned_data.get('term_number')
                start_date = form.cleaned_data.get('start_date')
                end_date = form.cleaned_data.get('end_date')

                if(start_date == None or end_date == None):
                    messages.add_message(request, messages.ERROR, "Dates must not be left empty!")
                    return render(request, 'create_term_form.html', {'form':form})

                if(start_date > end_date or end_date < start_date):
                    messages.add_message(request, messages.ERROR, "This term's end date and start date overlap with one another!")
                    return render(request, 'create_term_form.html', {'form':form})

                if(start_date == end_date):
                    messages.add_message(request, messages.ERROR, "Term cannot start and end on the same day!")
                    return render(request, 'create_term_form.html', {'form':form})


                if(term_number!=1):

                    if(len(Term.objects.filter(term_number=term_number)) !=0):
                        messages.add_message(request, messages.ERROR, 'There already exists a term with this term number!')
                        return render(request,'create_term_form.html', {'form': form})

                    if (len(Term.objects.filter(term_number=term_number-1)) !=0):

                        previous_term = Term.objects.get(term_number=term_number-1)

                        if(start_date <= previous_term.end_date):
                            messages.add_message(request, messages.ERROR, "This term's start date overlaps with the previous term's ending date!")
                            return render(request, 'create_term_form.html', {'form':form})

                if(term_number!= 6):
                    if(len(Term.objects.filter(term_number=term_number+1)) !=0):
                        next_term = Term.objects.get(term_number=term_number+1)

                        if(end_date >= next_term.start_date):
                            messages.add_message(request, messages.ERROR, "This term's end date overlaps with the next term's starting date!")
                            return render(request, 'create_term_form.html', {'form':form})

                form.save()
                messages.add_message(request,messages.SUCCESS, "Successfully added term!")
                return redirect('term_management')
            else:
                messages.add_message(request,messages.ERROR, "Invalid form input, Validator is set to only accept term numbers from 1 to 6!")
                return redirect('term_management')
        else:
            return redirect('term_management')
    else:
        return redirect('home')


@login_required
def edit_term_details_page(request,term_number):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if(request.method == 'GET'):
            try:
                term = Term.objects.get(term_number=term_number)

                try:
                    previous_term = Term.objects.get(term_number=str(int(term_number)-1))
                except ObjectDoesNotExist:
                    previous_term = None

                try:
                    next_term = Term.objects.get(term_number=str(int(term_number)+1))
                except ObjectDoesNotExist:
                    next_term = None

                data = {
                    'term_number': term.term_number,
                    'start_date': term.start_date,
                    'end_date': term.end_date,
                    }

                form = TermDatesForm(data)
                return render(request,'edit_term_form.html', {'form': form, 'term':term,'previous_term':previous_term,'next_term':next_term})
            except ObjectDoesNotExist:
                return redirect('term_management')
        else:
            return redirect('term_management')
    else:
        return redirect('home')

@login_required
def update_term_details(request,term_number):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if(request.method == 'POST'):
            try:
                term = Term.objects.get(term_number=term_number)
                form = TermDatesForm(request.POST)

                if form.is_valid():
                    term_number_in = form.cleaned_data.get('term_number')
                    start_date = form.cleaned_data.get('start_date')
                    end_date = form.cleaned_data.get('end_date')

                    if(start_date == None or end_date == None):
                        messages.add_message(request, messages.ERROR, "Dates must not be left empty!")
                        return render(request, 'create_term_form.html', {'form':form})

                    if(int(term_number) != int(term_number_in) and len(Term.objects.filter(term_number=term_number_in)) !=0):
                            messages.add_message(request, messages.ERROR, 'There already exists a term with this term number!')
                            return redirect(request,'edit_term_form.html', {'form': form})


                    try:
                        previous_term = Term.objects.get(term_number=str(int(term_number_in)-1))

                        if(int(term_number_in)-1 == int(term_number)):
                            previous_term = None

                        if(previous_term != None and start_date < previous_term.end_date and term_number != term_number_in):
                            messages.add_message(request, messages.ERROR, "Term's start date overlaps with the previous term's end date for the chosen term number! Try changing the term number or fix term overlap before attempting to alter term number.")
                            return render(request,'edit_term_form.html', {'form': form, 'term':term,'previous_term':previous_term})#,'next_term':next_term})

                        if(previous_term != None and start_date < previous_term.end_date):
                            messages.add_message(request, messages.ERROR, "This term's start date overlaps with the previous term's ending date!")
                            return render(request,'edit_term_form.html', {'form': form, 'term':term,'previous_term':previous_term})#,'next_term':next_term})


                    except ObjectDoesNotExist:
                        previous_term = None

                    try:
                        next_term = Term.objects.get(term_number=str(int(term_number_in)+1))

                        if(int(term_number_in)+1 == int(term_number)):
                            next_term = None

                        if(next_term!= None and end_date > next_term.start_date and term_number != term_number_in):
                            messages.add_message(request, messages.ERROR, "Term's end date overlaps with the next term's start date for the chosen term number. Try changing the term number or fix term overlap before attempting to alter term number!")
                            return render(request,'edit_term_form.html', {'form': form, 'term':term,'previous_term':previous_term,'next_term':next_term})

                        if(next_term!= None and end_date > next_term.start_date):
                            messages.add_message(request, messages.ERROR, "This term's end date overlaps with the next term's starting date!")
                            return render(request,'edit_term_form.html', {'form': form, 'term':term,'previous_term':previous_term,'next_term':next_term})

                    except ObjectDoesNotExist:
                        next_term = None

                    if(previous_term !=None and next_term !=None  and end_date > next_term.start_date and start_date < previous_term.end_date):
                        messages.add_message(request, messages.ERROR, "This term's end date and start date overlap with other terms!")
                        return render(request,'edit_term_form.html', {'form': form, 'term':term,'previous_term':previous_term,'next_term':next_term})

                    if (term.start_date == start_date and term.end_date == end_date and term.term_number == term_number_in):
                        messages.add_message(request, messages.ERROR, 'Term details are the same as before!')
                        return render(request,'edit_term_form.html', {'form': form, 'term':term,'previous_term':previous_term,'next_term':next_term})

                    if(start_date > end_date or end_date < start_date):
                        messages.add_message(request, messages.ERROR, "This term's end date and start date overlap with one another!")
                        return render(request,'edit_term_form.html', {'form': form, 'term':term,'previous_term':previous_term,'next_term':next_term})

                    term.term_number = term_number_in
                    term.start_date = start_date
                    term.end_date = end_date
                    term.save()

                    messages.add_message(request, messages.SUCCESS, 'Term details were successfully updated!')
                    return redirect('term_management')
                else:
                    messages.add_message(request, messages.ERROR, 'The input data is invalid. Only term numbers 1-6 are accepted')
                    return redirect('term_management')

            except ObjectDoesNotExist:
                messages.add_message(request, messages.ERROR, 'Unexpected Error')
                return redirect('term_management')
        else:
            return redirect('term_management')
    else:
        return redirect('home')

@login_required
def delete_term(request, term_number):
    if (request.user.is_authenticated and request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR):
        if request.method == 'GET':
            try:
                term = Term.objects.get(term_number=term_number)
                if term is not None:
                    term.delete()
                    messages.add_message(request, messages.SUCCESS, 'Term was successfully deleted!')
                    return redirect('term_management')
            except ObjectDoesNotExist:
                    messages.add_message(request, messages.ERROR, 'Term does not exist!')
                    return redirect('term_management')
        else:
            return redirect('term_management')
    else:
        return redirect('home')

# ---------------------------------------------

"""
@params: Either a post or get request to the url student_feed associated to student_feed function in views

@Description: Function called when a student logs into the system accessing the student feed page
              Displays to the student their pending requested lessons which can be viewd,deleted or edited
              Displays to the student their booked lessons which cannot be deleted or edited
              The above extends to any of the students' childrens' lesson
              The requested lessons are grouped by request date [The day the request was made]
              POST Requests to this page are forbidden
              Only Student UserAccounts can acces this functionality
@return: Renders or redirects to another specified view with relevant messages
"""
@login_required
def student_feed(request):
    if (request.user.is_authenticated and request.user.role == UserRole.STUDENT):
        if request.method == 'GET':
            greeting_str = f'Welcome back {request.user}, this is your feed!'

            #get any unfullfilled or fullfilled lessons for both the student and its children
            fullfilled_lessons = make_lesson_timetable_dictionary(request.user)
            unfulfilled_requests = make_lesson_dictionary(request.user,"Lesson Request")

            admin = get_admin_email()

            admin_email_str = ''

            #admin to contact
            if admin:
                admin_email_str = f'To Further Edit Bookings Contact {admin.email}'
            else:
                admin_email_str = f'No Admins Available To Contact'

            return render(request,'student_feed.html', {'admin_email': admin_email_str,'unfulfilled_requests':unfulfilled_requests, 'fullfilled_lessons':fullfilled_lessons, 'greeting':greeting_str})
        else:
            return HttpResponseForbidden()
    else:
        return redirect('home')

"""
@params: Either a post or get request to the url requests_page associated to requests_page function in views

@Description: Function called when a student attempts to request page which provides functionalities to create and request lessons
              Displays to the student any saved lessons they have already made and yet to be requested
              POST Requests to this page are forbidden
              Only Student UserAccounts can acces this functionality

@return: Renders or redirects to another specified view with relevant messages
"""
@login_required
def requests_page(request):
    if (request.user.is_authenticated and request.user.role == UserRole.STUDENT):
        if request.method == 'GET':
            if(len(Term.objects.all()) == 0):
                messages.add_message(request, messages.ERROR, 'Please wait for the admin to add term dates')
                # return redirect('student_feed')
            student = request.user
            students_option = get_student_and_child_objects(student)
            savedLessons = get_saved_lessons(student)
            form = RequestForm()
            return render(request,'requests_page.html', {'form': form , 'lessons': savedLessons, 'students_option':students_option})
        else:
            return HttpResponseForbidden()
    else:
        return redirect('home')

@login_required
def admin_feed(request):

    if (request.user.is_authenticated and (request.user.role == UserRole.ADMIN or request.user.role == UserRole.DIRECTOR)):
        student = UserAccount.objects.filter(role=UserRole.STUDENT.value,is_parent = False)
        parents = UserAccount.objects.filter(role=UserRole.STUDENT,is_parent = True)

        fulfilled_lessons = Lesson.objects.filter(lesson_status = LessonStatus.FULLFILLED)

        unfulfilled_lessons = Lesson.objects.filter(lesson_status = LessonStatus.UNFULFILLED)

        return render(request,'admin_feed.html',{'student':student,'parents':parents,'fulfilled_lessons':fulfilled_lessons,'unfulfilled_lessons':unfulfilled_lessons})
    else:
        # return redirect('log_in')
        return redirect('home')


"""
@Description: Function is called to render the director_feed template
- only logged in directors can use this funcion
"""
@login_required
def director_feed(request):
    if request.user.is_authenticated and request.user.role == UserRole.DIRECTOR:
        return render(request,'director_feed.html')
    else:
        return redirect('home')

"""
@Description: Function is called to render the director_manage_roles template
- only logged in directors can use this funcion
"""
@login_required
def director_manage_roles(request):
    if request.user.is_authenticated and request.user.role == UserRole.DIRECTOR:
        admins = UserAccount.objects.filter(role = UserRole.ADMIN)
        directors = UserAccount.objects.filter(role = UserRole.DIRECTOR)
        return render(request,'director_manage_roles.html',{'admins':admins, 'directors':directors})
    else:
        return redirect("home")


"""
@Description: Function is called to promote a registered user based on his email into a director.
Currently logged in director can't promote himself to director.
- only logged in directors can use this funcion
"""
@login_required
def promote_director(request,current_user_email):
    if request.user.is_authenticated and request.user.role == UserRole.DIRECTOR:

        if (request.user.email == current_user_email):
            messages.add_message(request,messages.ERROR,"You cannot promote yourself!")
            return redirect('director_manage_roles')
        else:

            try:
                user = UserAccount.objects.get(email=current_user_email)
            except ObjectDoesNotExist:
                messages.add_message(request,messages.ERROR,f"{current_user_email} does not exist")
                return redirect("director_manage_roles")

            user.role = UserRole.DIRECTOR
            user.is_staff = True
            user.is_superuser = True
            user.save()

            messages.add_message(request,messages.SUCCESS,f"{current_user_email} now has the role director")
            return redirect('director_manage_roles')
    else:
        return redirect("home")

"""
@Description: Function is called to promote a registered user based on his email into an admin.
Currently logged in director can't promote himself to admin.
- only logged in directors can use this funcion
"""
@login_required
def promote_admin(request,current_user_email):

    if request.user.is_authenticated and request.user.role == UserRole.DIRECTOR:

        if (request.user.email == current_user_email):
            messages.add_message(request,messages.ERROR,"You cannot demote yourself!")
            return redirect('director_manage_roles')
        else:

            try:
                user = UserAccount.objects.get(email=current_user_email)
            except ObjectDoesNotExist:
                messages.add_message(request,messages.ERROR,f"{current_user_email} does not exist")
                return redirect("director_manage_roles")

            user = UserAccount.objects.get(email=current_user_email)
            user.role = UserRole.ADMIN
            user.is_staff = True
            user.is_superuser = False
            user.save()
            messages.add_message(request,messages.SUCCESS,f"{current_user_email} now has the role admin")
            return redirect("director_manage_roles")
    else:

        return redirect("home")



"""
@Description: Function is called to disable a registered user based on his email.
Currently logged in director can't disable himself.
- only logged in directors can use this funcion
"""
@login_required
def disable_user(request,current_user_email):
    if request.user.is_authenticated and request.user.role == UserRole.DIRECTOR:
        if (request.user.email == current_user_email):
            messages.add_message(request,messages.ERROR,"You cannot disable yourself!")
            return redirect(director_manage_roles)
        else:

            try:
                user = UserAccount.objects.get(email=current_user_email)
            except ObjectDoesNotExist:
                messages.add_message(request,messages.ERROR,f"{current_user_email} does not exist")
                return redirect("director_manage_roles")

            if (user.is_active == True):
                user.is_active = False
                user.save()
                messages.add_message(request,messages.SUCCESS,f"{current_user_email} has been sucessfuly disabled!")
            else:
                user.is_active = True
                user.save()
                messages.add_message(request,messages.SUCCESS,f"{current_user_email} has been sucessfuly enabled!")

            return redirect(director_manage_roles)
    else:
        return redirect("home")


"""
@Description: Function is called to delete a registered user based on his email.
Currently logged in director can't delete himself.
- only logged in directors can use this funcion
"""
@login_required
def delete_user(request,current_user_email):
    if request.user.is_authenticated and request.user.role == UserRole.DIRECTOR:
        if (request.user.email == current_user_email):
            messages.add_message(request,messages.ERROR,"You cannot delete yourself!")
            return redirect(director_manage_roles)
        else:

            try:
                user = UserAccount.objects.get(email=current_user_email)
            except ObjectDoesNotExist:
                messages.add_message(request,messages.ERROR,f"{current_user_email} does not exist")
                return redirect("director_manage_roles")

            user.delete()
            messages.add_message(request,messages.SUCCESS,f"{current_user_email} has been sucessfuly deleted!")
            return redirect(director_manage_roles)
    else:
        return redirect("home")

"""
@Description: Function is called to render the create director_create_admin template.
Form is saved when there is post request, otherwise an empty form is rendered
- only logged in directors can use this funcion
"""
@login_required
def create_admin_page(request):
    if request.user.is_authenticated and request.user.role == UserRole.DIRECTOR:

        if request.method == 'POST':
            form = CreateAdminForm(request.POST)
            if form.is_valid():
                admin = form.save()
                return redirect('director_manage_roles')
        else:
            form = CreateAdminForm()

        return render(request,'director_create_admin.html',{'form': form})
    else:
        return redirect("home")

"""
@Description: Function is called to update a user based on his ID based on the information of
the CreateAdminForm. Currently log in director can update himself and other registered admins/directors.
- only logged in directors can use this funcion
"""
@login_required
def update_user(request,current_user_id):

    if request.user.is_authenticated and request.user.role == UserRole.DIRECTOR:

        try:
            user = UserAccount.objects.get(id=current_user_id)
        except ObjectDoesNotExist:
            messages.add_message(request,messages.ERROR,f"{request.user.email} does not exist")
            return redirect("director_manage_roles")


        form = CreateAdminForm(instance=user)

        if request.method == 'POST':
            form = CreateAdminForm(request.POST, instance = user)
            if form.is_valid():
                email = form.cleaned_data.get('email')
                fname = form.cleaned_data.get('first_name')
                lname = form.cleaned_data.get('last_name')
                gender = form.cleaned_data.get('gender')

                new_password = form.cleaned_data.get('new_password')

                user.email = email
                user.first_name = fname
                user.last_name = lname
                user.gender = gender

                user.set_password(new_password)
                user.save()

                # current user logged out if he edits himself
                if (int(request.user.id) == int(current_user_id)):
                    messages.add_message(request,messages.SUCCESS,f"You cant't edit yourself!")
                    return log_out(request)

                messages.add_message(request,messages.SUCCESS,f"{user.email} has been sucessfuly updated!")
                return redirect('director_manage_roles')

        return render(request,'director_update_user.html', {'form': form , 'user': user})


"""
@Description: Function is called to render the home page, and redirect users to their corresponding feed pages
based on their roles. Children are not allowed to log into the application.
"""
@login_prohibited
def home(request):
    if request.method == 'POST':
        form = LogInForm(request.POST)
        email = request.POST.get("email")
        password = request.POST.get("password")
        if  form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            role = form.cleaned_data.get('role')
            user = authenticate(email=email, password=password)
            if user is not None:
                #only parent users can log in
                if user.parent_of_user is None:
                    login(request,user)

                     # redirects the user based on his role
                    if (user.role == UserRole.ADMIN.value):
                        return redirect('admin_feed')
                    elif (user.role == UserRole.DIRECTOR.value):
                        redirect_url = request.POST.get('next') or 'director_feed'
                        return redirect(redirect_url)
                    else:
                        redirect_url = request.POST.get('next') or 'student_feed'
                        return redirect(redirect_url)
                else:
                    messages.add_message(request,messages.ERROR,"Child credentials cannot be used to access the application")
                    form = LogInForm()
                    next = request.GET.get('next') or ''
                    return render(request,'home.html', {'form' : form, 'next' : next})

        messages.add_message(request,messages.ERROR,"The credentials provided is invalid!")
    form = LogInForm()
    next = request.GET.get('next') or ''
    return render(request,'home.html', {'form' : form, 'next' : next})


def log_out(request):
    logout(request)
    return redirect('home')

"""
@params: Either a post or get request to the url sign_up_child associated to sign_up_child function in views

@Description: Function called when a student attempts to sign up their child as a student user to the system
              This child and parent are related by the parent_of_user field in the UserAccount models
              POST Requests create the new Child Student using the data from the POST request
              Child Students are identified by their email -> no two UserAccount models can have the same email but can have the same name
              Only Student UserAccounts can acces this functionality
              Child Student UserAccounts cannnot access the available application's functionalities but their parents can for them
@return: Renders or redirects to another specified view with relevant messages
"""
def sign_up_child(request):
    if request.user.is_authenticated and request.user.role == UserRole.STUDENT:
        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                student = form.save_child(request.user)
                return redirect('student_feed')
            else:
                new_form = SignUpForm()
                messages.add_message(request,messages.ERROR,"These account details already exist for another child")
                return render(request, 'sign_up_child.html', {'form': new_form})
        else:
            form = SignUpForm()
            return render(request, 'sign_up_child.html', {'form': form})
    else:
        return redirect('home')

@login_prohibited
def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            student = form.save()
            login(request, student)
            return redirect('student_feed')
    else:
        form = SignUpForm()
    return render(request, 'sign_up.html', {'form': form})

"""
@params: Either a post or get request to the url new_lesson associated to new_lesson function in views

@Description: Function called when a student attempts to create a new lesson they wish to request
              Lessons are uniquely identified by their request_date,lesson_Date_time and student_id, enforcing this as the primary key to avoid duplicates
              The student utilising this functionality can request lessons for themselves and for their children
              POST Requests create the new Child Student
              GET requests render the requests_page template
              Child Students are identified by their email -> no two UserAccount models can have the same email but can have the same name
              Only Student UserAccounts can acces this functionality

@return: Renders or redirects to another specified view with relevant messages
"""
def new_lesson(request):
    if (request.user.is_authenticated and request.user.role == UserRole.STUDENT):

        if request.method == 'POST':
            request_form = RequestForm(request.POST)
            if request_form.is_valid():

                if(len(Term.objects.all()) == 0):
                    messages.add_message(request, messages.ERROR, 'Please wait for the admin to add term dates')
                    return redirect('requests_page')

                try:
                    actual_student = UserAccount.objects.get(email = request.POST['selectedStudent'])
                except ObjectDoesNotExist:
                    messages.add_message(request,messages.ERROR,"Selected user account does not exist")
                    students_option = get_student_and_child_objects(request.user)
                    return render(request,'requests_page.html', {'form' : request_form , 'lessons': get_saved_lessons(request.user), 'students_option':students_option})

                if check_valid_date(request_form.cleaned_data.get('lesson_date_time').date()) is False:
                    messages.add_message(request,messages.ERROR,"The lesson date provided is beyond the term dates available")
                    students_option = get_student_and_child_objects(request.user)
                    return render(request,'requests_page.html', {'form' : request_form , 'lessons': get_saved_lessons(request.user), 'students_option':students_option})

                try:
                    request_form.save(actual_student)
                except IntegrityError:
                    messages.add_message(request,messages.ERROR,"Lesson information provided already exists")
                    students_option = get_student_and_child_objects(request.user)
                    return render(request,'requests_page.html', {'form' : request_form , 'lessons': get_saved_lessons(request.user), 'students_option':students_option})

                messages.add_message(request,messages.SUCCESS,"Lesson has been created")
                return redirect('requests_page')
            else:
                messages.add_message(request,messages.ERROR,"The lesson information provided is invalid!")
                students_option = get_student_and_child_objects(request.user)
                return render(request,'requests_page.html', {'form' : request_form , 'lessons': get_saved_lessons(request.user), 'students_option':students_option})
        else:
            return redirect('requests_page')

    else:
        return redirect('home')

"""
@params: Either a post or get request to the url save_lessons associated to save_lessons function in views

@Description: Function called when a student attempts save and request the lessons they have created
              Lessons are uniquely identified by their request_date,lesson_Date_time and student_id, enforcing this as the primary key to avoid duplicates
              The student utilising this functionality can save lessons for themselves and for their children
              POST Requests makes all saved lessons attributed to the student and any of their children into unfullfilled lessons
              GET requests render the requests_page template with any saved lessons
              Only Student UserAccounts can acces this functionality

@return: Renders or redirects to another specified view with relevant messages
"""
def save_lessons(request):
    if (request.user.is_authenticated and request.user.role == UserRole.STUDENT):
        current_student = request.user
        if request.method == 'POST':
            all_unsaved_lessons = get_saved_lessons(current_student)

            if len(all_unsaved_lessons) == 0:
                messages.add_message(request,messages.ERROR,"Lessons should be saved before attempting to request")
                return redirect('requests_page')

            for eachLesson in all_unsaved_lessons:
                eachLesson.lesson_status = LessonStatus.UNFULFILLED
                eachLesson.save()

            messages.add_message(request,messages.SUCCESS, "Lesson requests are now pending for validation by admin")
            return redirect('student_feed')
        else:
            return redirect('requests_page')
    else:

        return redirect('home')


"""
@params: request: Either a post or get request , lesson_id: The Lesson model object to render for editing

@Description: Function to render a RequestForm to edit an UNFULLFILLED Lesson of the student users' choice
              Request form is rendered with the data of the lesson passed as a parameter bound
              Function only accessible to students
@return: Renders or redirects to another specified view with relevant messages
"""
def render_edit_request(request,lesson_id):
    try:
        to_edit_lesson = Lesson.objects.get(lesson_id = int(lesson_id))
    except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, "Incorrect lesson ID passed")
        return redirect('student_feed')

    #data of the lesson passed as a parameter
    data = {'type': to_edit_lesson.type,
            'duration': to_edit_lesson.duration,
            'lesson_date_time': to_edit_lesson.lesson_date_time,
            'teachers': to_edit_lesson.teacher_id}

    form = RequestForm(data)
    return render(request,'edit_request.html', {'form' : form, 'lesson_id':lesson_id})

"""
@params: request: Either a post or get request to the edit_lesson url associated to the edit_lesson view, lesson_id: The Lesson model object to render for editing

@Description: Function to peform the edit on lesson model object passed as parameter with the data provided by the Student User in the POST request
              If this view is accessed with a GET request the requests_page is rendered
              Function only accessible to students
              The date entered must be valid by being within the term date range and cannot be less then the CURRENT_DATE in SETTINGS
              Upon Succesfull edit the application is redirected to the student_feed
              Function checks that the lesson attempted to be edited is one of the students or their children

@return: Renders or redirects to another specified view with relevant messages
"""
def edit_lesson(request,lesson_id):
    if (request.user.is_authenticated and request.user.role == UserRole.STUDENT):
        current_student = request.user

        try:
            to_edit_lesson = Lesson.objects.get(lesson_id = int(lesson_id))
        except ObjectDoesNotExist:
            messages.add_message(request, messages.ERROR, "Incorrect lesson ID passed")
            return redirect('student_feed')

        if check_correct_student_accessing_pending_lesson(current_student,to_edit_lesson) is False:
            messages.add_message(request, messages.WARNING, "Attempted Edit Is Not Permitted")
            return redirect('student_feed')

        if request.method == 'POST':
            request_form = RequestForm(request.POST)

            if request_form.is_valid():

                if check_valid_date(request_form.cleaned_data.get('lesson_date_time').date()) is False:
                    messages.add_message(request,messages.ERROR,"The lesson date provided is beyond the term dates available")
                    return render_edit_request(request,lesson_id)

                try:
                    request_form.update_lesson(to_edit_lesson)
                except IntegrityError:
                    messages.add_message(request,messages.ERROR,"Duplicate lessons are not allowed")
                    return render_edit_request(request,lesson_id)

                messages.add_message(request,messages.SUCCESS,"Succesfully edited lesson")
                return redirect('student_feed')
            else:
                messages.add_message(request,messages.ERROR,"Form is not valid")
                return render_edit_request(request,lesson_id)
        else:
            return render_edit_request(request,lesson_id)
    else:
        return redirect('home')

"""
@params: request: Either a post or get request to the delete_pending url associated to the delete_pending view, lesson_id: The Lesson model object to render for deletion

@Description: Function to peform the deletion of the UNFULLFILLED lesson model object passed as parameter with a POST request
              If this view is accessed with a GET request the student_feed is rendered
              Function only accessible to students
              Upon Succesfull deletion the application is redirected to the student_feed
              Function checks that the lesson attempted to be deleted is one of the students or their children

@return: Renders or redirects to another specified view with relevant messages
"""
def delete_pending(request,lesson_id):
    if request.user.is_authenticated and request.user.role == UserRole.STUDENT:
        current_student = request.user
        #if check_correct_student_accessing_lesson(current_student,lesson_id):
        if request.method == 'POST':
                try:
                    lesson_to_delete = Lesson.objects.get(lesson_id = int(lesson_id))
                except ObjectDoesNotExist:
                    messages.add_message(request, messages.ERROR, "Incorrect lesson ID passed")
                    return redirect('student_feed')

                if check_correct_student_accessing_pending_lesson(current_student,lesson_to_delete) is False:
                    messages.add_message(request, messages.WARNING, "Attempted Deletion Not Permitted")
                    return redirect('student_feed')

                lesson_to_delete.delete()
                messages.add_message(request, messages.SUCCESS, "Lesson request deleted")
                return redirect('student_feed')

        else:
            return redirect('student_feed')
    else:
        # return redirect('log_in')
        return redirect('home')

"""
@params: request: Either a post or get request to the delete_saved url associated to the delete_saved view, lesson_id: The Lesson model object to render for deletion

@Description: Function to peform the deletion of the SAVED lesson model object passed as parameter with a POST request
              If this view is accessed with a GET request the student_feed is rendered
              Function only accessible to students
              Upon Succesfull deletion the application is redirected to the student_feed
              Function checks that the lesson attempted to be deleted is one of the students or their children

@return: Renders or redirects to another specified view with relevant messages
"""
def delete_saved(request,lesson_id):
    if request.user.is_authenticated and request.user.role == UserRole.STUDENT:
        current_student = request.user
        #if check_correct_student_accessing_lesson(current_student,lesson_id):
        if request.method == 'POST':
            request_form = RequestForm()
            students_option = get_student_and_child_objects(request.user)

            try:
                lesson_to_delete = Lesson.objects.get(lesson_id = int(lesson_id))
            except ObjectDoesNotExist:
                messages.add_message(request, messages.ERROR, "Incorrect lesson ID passed")
                return render(request,'requests_page.html', {'form' : request_form , 'lessons': get_saved_lessons(request.user), 'students_option':students_option})

            if check_correct_student_accessing_saved_lesson(current_student,lesson_to_delete) is False:
                messages.add_message(request, messages.WARNING, "Attempted Deletion Not Permitted")
                return render(request,'requests_page.html', {'form' : request_form , 'lessons': get_saved_lessons(request.user), 'students_option':students_option})

            lesson_to_delete.delete()
            messages.add_message(request, messages.SUCCESS, "Saved lesson deleted")
            return redirect('requests_page')

        else:
            return redirect('requests_page')
    else:
        # return redirect('log_in')
        return redirect('home')
