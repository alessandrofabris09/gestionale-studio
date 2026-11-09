from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def validate_form_password(form, cleaned_data, field):
    """Applica i validatori Django anche ai moduli che non usano UserCreationForm."""
    password = cleaned_data.get(field)
    if not password:
        return
    candidate = User(
        username=cleaned_data.get('username', ''),
        email=cleaned_data.get('email', ''),
        first_name=cleaned_data.get('first_name', cleaned_data.get('nome_studio', '')),
        last_name=cleaned_data.get('last_name', ''),
    )
    try:
        validate_password(password, user=candidate)
    except ValidationError as error:
        form.add_error(field, error)
