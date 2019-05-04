import os
from flask_user import EmailManager, UserManager, forms
import logging

from app.service.validators import CertainDomains


class EmailManagerWithDomainValidation(EmailManager):

    def __init__(self, app, domains=["sberbank.ru"]):
        super().__init__(app)
        self.domains = domains
        self.app = app
        logging.info("EmailManagerWithDomainValidation INIT")

    def __repr__(self):
        return 'EmailManagerWithDomainValidation'

    def _render_and_send_email(self, email, user, template_filename, **kwargs):
        if self.validate(user.email):
            super()._render_and_send_email(email, user, template_filename, **kwargs)

    def send_confirm_email_email(self, user, user_email):
        if self.validate(user_email.email):
            super().send_confirm_email_email(self, user, user_email)

    def validate(self, email):
        success = False
        for domain in self.domains:
            success = success or email.endswith(domain)
        if not success:
            raise Exception("Corporate email required.")
        else:
            return success


class CustomUserProfileForm(forms.EditUserProfileForm):
    pass


class CustomRegisterForm(forms.RegisterForm):

    def validate(self):
        self.email.validators.append(CertainDomains(os.environ.get('CORPORATE_DOMAINS', '').split()))
        return super().validate()


class CustomUserManager(UserManager):

    def customize(self, app):
        logging.info("CustomUserManager INIT")
        self.RegisterFormClass = CustomRegisterForm
        self.UserProfileFormClass = CustomUserProfileForm
