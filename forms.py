from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField
import email_validator
from wtforms.fields.html5 import EmailField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators = [DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register")

class LogonForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators = [DataRequired()])
    submit = SubmitField("Login")

class UserTypesForm(FlaskForm):
    user_type_name = StringField("User type", validators=[DataRequired()])
    user_type_info = StringField("Extra info for this user type")
    submit = SubmitField("Add new user type")

class CommentForm(FlaskForm):
    comment = CKEditorField("Type your Comment", validators=[DataRequired()], default="", render_kw={'placeholder': 'please input title'})
    submit = SubmitField("Add new comment")