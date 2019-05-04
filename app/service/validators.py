from wtforms.validators import ValidationError


class CertainDomains(object):
    """

    :param message:
        Error message to raise in case of a validation error.
    """
    field_flags = ('required', )

    def __init__(self, domains=["sberbank.ru", "omega.ru"], message=None):
        self.message = message
        self.domains = domains

    def __call__(self, form, field):
        success = not self.domains
        for domain in self.domains:
            success = success or field.data.endswith(domain)
        if not success:
            if self.message is None:
                message = field.gettext('Corporate email is required.')
            else:
                message = self.message

            field.errors[:] = []
            raise ValidationError(message)
