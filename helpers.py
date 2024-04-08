from flask import redirect, render_template, session
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def check_password(password):
  """Checks if the password is valid."""
  special_chars = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
  if len(password) >= 8:
    if any(char.islower() for char in password):
      if any(char.isupper() for char in password):
        if any(char.isdigit() for char in password):
          if any(char in special_chars for char in password):
            return True
  return False
