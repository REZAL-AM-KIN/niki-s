from django.core.exceptions import ValidationError

def strictlyPositiveValidator(value):
    if value <= 0:
        raise ValidationError(
            "Ensure this value is strictly positive",
            code="positive_value",
            params={'value':value},
        )
