from django.core.exceptions import ValidationError

def strictly_positive_validator(value):
    if value <= 0:
        raise ValidationError(
            "Ensure this value is strictly positive",
            code="positive_value",
            params={'value':value},
        )
