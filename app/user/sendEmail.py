from django.core.mail import send_mail, get_connection, EmailMultiAlternatives


def sendEmail(receiver, code):
    FROM = "swe573fall2022@gmail.com"
    TO = [
        receiver,
    ]
    SUBJECT = "Reset Password for MeetAll"
    MESSAGE = "The code to reset your password is: " + str(code)
    messages = []
    fail_silently = False
    user = None
    password = None
    connection = None
    try:
        connection = connection or get_connection(
            username=user, password=password, fail_silently=fail_silently
        )
        message = EmailMultiAlternatives(SUBJECT, MESSAGE, FROM, TO)
        messages.append(message)
        connection.send_messages(messages)
        return 1

    except Exception as e:
        print(e)
        return 0
