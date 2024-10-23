from django.core.management.base import BaseCommand, CommandError
from faker import Faker
from lessons.models import UserAccount, Invoice, Transaction, Term

class Command(BaseCommand):
    # Delete all users, except for email admin@example.org
    # Delete all invoices that generate base on existing user and bookings
    def handle(self, *args, **options):
        users = UserAccount.objects.all()
        for i in range(len(users)):

            if users[i].email != "admin@example.org":
                users[i].delete()

        invoices = Invoice.objects.all()
        for i in range(len(invoices)):
            invoices[i].delete()

        transactions = Transaction.objects.all()
        for i in range(len(transactions)):
            transactions[i].delete()

        terms_list = Term.objects.all()
        for i in range(len(terms_list)):
            terms_list[i].delete()
