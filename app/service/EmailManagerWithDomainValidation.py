from flask_user import EmailManager


class EmailManagerWithDomainValidation(EmailManager):

    def __init__(self, app, domains=["sberbank.ru"]):
        super().__init__(app)
        self.domains = domains

    def send_confirm_email_email(self, user, user_email):
        success = False
        for domain in self.domains:
            success = success or user_email.endswith(domain)
        if success:
            super().send_confirm_email_email(user, user_email)
