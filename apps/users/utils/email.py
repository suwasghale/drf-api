from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_verification_email(to_email, username, verification_url):
    subject = "Verify your email"
    text_content = f"Hi {username}, click here to verify your email: {verification_url}"
    html_content = f"""
    <html>
      <body>
        <p>Hi {username},</p>
        <p>Click the button below to verify your email:</p>
        <a href="{verification_url}" style="padding:10px 15px; background-color: #4CAF50; color:white; text-decoration:none;">Verify Email</a>
      </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
