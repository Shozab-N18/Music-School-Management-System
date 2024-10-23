from lessons.models import Lesson,UserAccount,UserRole, Gender,LessonStatus,LessonType,LessonDuration, InvoiceStatus

"""helpers to test validity of TextChoices for various models"""
def is_valid_gender(UserAccount):
    return UserAccount.gender in {
        Gender.MALE,
        Gender.FEMALE,
        Gender.PNOT,
        }

def is_valid_role(UserAccount):
    return UserAccount.role in {
        UserRole.STUDENT,
        UserRole.ADMIN,
        UserRole.DIRECTOR,
        UserRole.TEACHER,
        }

def is_valid_lessonStatus(Lesson):
    return Lesson.lesson_status in {
        LessonStatus.SAVED,
        LessonStatus.UNFULFILLED,
        LessonStatus.FULLFILLED,
        }

def is_valid_lessonDuration(Lesson):
    return Lesson.duration in {
        LessonDuration.THIRTY,
        LessonDuration.FOURTY_FIVE,
        LessonDuration.HOUR,
        }

def is_valid_lessonType(Lesson):
    return Lesson.type in {
        LessonType.INSTRUMENT,
        LessonType.THEORY,
        LessonType.PRACTICE,
        LessonType.PERFORMANCE,
        }

def is_valid_Invoice_status(Invoice):
    return Invoice.invoice_status in {
        InvoiceStatus.PAID,
        InvoiceStatus.UNPAID,
        InvoiceStatus.PARTIALLY_PAID,
        InvoiceStatus.DELETED,
    }
