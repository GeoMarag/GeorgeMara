from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import *
from flask_gravatar import Gravatar
from functools import wraps
from flask import abort, Markup
import hashlib
import os
from dotenv import *
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('app_config_587')
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

##CONNECT TO DB
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

## login manager
login_manager = LoginManager()
login_manager.init_app(app)

##CONFIGURE TABLES
user_usertype = db.Table('UserID_UserTypeID',
                         db.Column('UserID', db.Integer, db.ForeignKey('users.id'), unique=True, primary_key=True),
                         db.Column('UserTypeID', db.Integer, db.ForeignKey('user_type.user_type_id'), primary_key=True)
                         )


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    Blogpost_user_relationship = relationship("User", back_populates="user_Blogpost_relationship")
    comments = relationship("Comment", back_populates="post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    user_types = relationship(
        "User_types",
        secondary=user_usertype,
        back_populates="users")
    user_Blogpost_relationship = relationship("BlogPost", back_populates="Blogpost_user_relationship")
    comments = relationship("Comment", back_populates="user")


class User_types(db.Model):
    __tablename__ = "user_type"
    user_type_id = db.Column(db.Integer, primary_key=True)
    user_type_name = db.Column(db.String(250), nullable=False)
    user_type_info = db.Column(db.String(250))
    users = relationship(
        "User",
        secondary=user_usertype,
        back_populates="user_types")


class Comment(db.Model):
    __tablename__ = "comments"
    comment_ID = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blogpost_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    user = relationship("User", back_populates="comments")
    post = relationship("BlogPost", back_populates="comments")


db.create_all()


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            # If id is not 1 then return abort with 403 error
            if current_user.id != 1:
                return abort(403)
            # Otherwise continue with the route function
            return f(*args, **kwargs)
        else:
            return abort(403)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()

    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data
        password = request.form["password"]
        password_encrypted = generate_password_hash(password=password, method='pbkdf2:sha256', salt_length=8)
        name = request.form["name"]
        # print(email)
        # Search if this email already exist:
        if User.query.filter_by(email=email).first() == None:

            new_user = User(email=email,
                            password=password_encrypted,
                            name=name)
            db.session.add(new_user)
            db.session.commit()
            user_added = User.query.filter_by(email=email).first()
            # add usertype to 3 (user) for the new user
            add_user_usertype = user_usertype.insert().values(UserID=user_added.id, UserTypeID=3)
            db.session.execute(add_user_usertype)
            db.session.commit()
            # print(user_id)
            ### LOGIN USER
            status_login_user = login_user(user_added)
            # print(status_login_user)
            # print(current_user.is_authenticated)
            flash(f'Hallo {name}. You are successfully logged in.')
            return redirect(url_for("get_all_posts"))
        else:  # Στης περίπτωση που υπάρχει ο χρήστης πρέπει να τον οδηγήσουμε στο login ώστε να μπορεί να κάνει login
            flash('You have already registered with this email. Please log on instead')
            return redirect(url_for("login"))
    else:

        return render_template("register.html", form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LogonForm()
    if request.method == "POST":
        email = request.form["email"]
        password = form.password.data
        user_to_login = User.query.filter_by(email=email).first()
        if user_to_login != None and check_password_hash(user_to_login.password, password):
            login_user(user_to_login)
            flash(f'Hallo {user_to_login.name}. You are successfully logged in.')
            return redirect(url_for("get_all_posts"))
        else:
            flash("Your email or Password is wrong. Please try again.")
            return render_template("login.html", form=form)
        # return f"<p>{email},{password}</p>"

    else:
        return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()

    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["POST", 'GET'])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    # find all commends to this post
    comments_for_this_post = Comment.query.filter_by(blogpost_id=post_id).all()
    if form.validate_on_submit():
        comment = form.comment.data
        if current_user.is_authenticated:
            comment_to_add = Comment(text=comment,
                                     user_id=current_user.id,
                                     blogpost_id=post_id)
            db.session.add(comment_to_add)
            db.session.commit()
            flash("Your comment is added successfully")
            return redirect(url_for('show_post', post_id=post_id))


        else:
            flash(Markup(
                f"You have to login before you write a comment. If you are not registered, please click here <a href={url_for('register')} class='alert-link'>here</a>. "))
            return redirect(url_for("login"))


    return render_template("post.html", post=requested_post, form=form, comments=comments_for_this_post)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["POST", "GET"])
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    if current_user.id == 1:
        post = BlogPost.query.get(post_id)
        edit_form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            body=post.body
        )
        if edit_form.validate_on_submit():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            post.author = edit_form.author.data
            post.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))

        return render_template("make-post.html", form=edit_form)
    else:
        redirect(url_for("login"))


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    # protection for the users that know the link for deleting
    if current_user.id == 1:
        post_to_delete = BlogPost.query.get(post_id)
        db.session.delete(post_to_delete)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    else:
        return redirect(url_for('get_all_posts'))


## Database User Section
@app.route('/UserType', methods=["POST", "GET"])
@admin_only
def user_type():
    form = UserTypesForm()
    all_user_types = db.session.query(User_types).all()

    if request.method == "POST":
        user_type_name = form.user_type_name.data
        user_type_info = form.user_type_info.data
        user_to_login_search_for_same = User_types.query.filter_by(user_type_name=user_type_name).first()
        if user_to_login_search_for_same is None:
            user_type_add = User_types(user_type_name=user_type_name,
                                       user_type_info=user_type_info)
            db.session.add(user_type_add)
            db.session.commit()
            flash(f'User added successfully')
            return redirect(url_for("user_type"))
        else:
            flash("This user type already exist")
            return redirect(url_for("user_type"))
        # return f"<p>{email},{password}</p>"

    else:
        return render_template("user_type.html", form=form, user_types=all_user_types)


@app.route('/allUsers', methods=["POST", "GET"])
def all_users():
    users = db.session.query(User).all()
    # print(type(users))
    # print(users[0].id)
    user_types = db.session.query(User_types).all()

    # αυτή η συνάρτηση διαβάζει απο το database την τιμή που έχει το userType και ανάλογα εισάγει το selected στην λιστα επιλογών
    def UsertypeID_selected(in_userID, in_currentUsertypeID):
        if check_if_user_in_table(in_table="user_usertype", in_check_Column="UserID", in_Value=in_userID):
            # take the value of the UsertypeID for the current User
            s = user_usertype.select().where(user_usertype.c.UserID == in_userID)
            # resUserID = db.session.execute(s).fetchone()
            # resUserID, resUsertypeID = db.session.execute(s).fetchone()
            result = db.session.execute(s).fetchone()
            # print(f"user_id = {in_userID} usertypeID = {in_currentUsertypeID}" )
            # print(result)
            # resUsertypeID=1

            if in_currentUsertypeID == result[1]:
                return "selected"
            else:
                return ""

        else:
            if in_currentUsertypeID == 5:
                return "selected"
            else:
                return ""
        table_info = db.session.query(user_usertype).all()
        print(table_info)
        return "george"

    # return render_template("all_users.html", users = users, hello=hello, user_types = user_types)
    return render_template("all_users.html", users=users, UsertypeID_selected=UsertypeID_selected,
                           user_types=user_types)


@app.route('/updateUserType/<userID>', methods=["POST", "GET"])
@admin_only
def updateUserType(userID):
    ### See how to add a value to a many to many relationship in sqlalchemy
    # todone δες αμα με αυτή την εντολή κάθε φορά προσθέτει τιμές, διαφορετικά πρέπει αρχικά να ελεγξεις αμα υπάρχει η τιμή και μετά να κάνεις update
    usertype = request.args.get('userType')
    user_to_change_usertype = User.query.filter_by(id=userID).first()
    #### προσθήκη user στο table ή update value
    if not check_if_user_in_table(in_table="user_usertype", in_check_Column="UserID", in_Value=userID):
        # Insert command
        add_user = user_usertype.insert().values(UserID=userID, UserTypeID=usertype)
        db.session.execute(add_user)
        db.session.commit()

    else:
        ##update command
        update_user = user_usertype.update().where(user_usertype.c.UserID == userID).values(UserTypeID=usertype)
        db.session.execute(update_user)
        db.session.commit()
    # flash message to mark the change in user
    flash(f'You have changed the User type of the user {user_to_change_usertype.name}')
    return redirect(url_for("all_users"))


@app.route('/demo/<userID>', methods=["POST", "GET"])  # to delete
def demo(userID):
    ### See how to add a value to a many to many relationship in sqlalchemy
    # t#odo δες αμα με αυτή την εντολή κάθε φορά προσθέτει τιμές, διαφορετικά πρέπει αρχικά να ελεγξεις αμα υπάρχει η τιμή και μετά να κάνεις update
    usertype = request.args.get('userType')
    return f"<p>userID={userID} usertype={usertype}</p>"

    # This function checks if the user is on the table and outputs True or False


def check_if_user_in_table(in_table, in_check_Column, in_Value):
    command_string = f"{in_table}.select().where({in_table}.c.{in_check_Column}=={in_Value})"
    # print (command_string)
    s = eval(command_string)
    # print(type(s))
    resUserID = db.session.execute(s)
    # print(resUserID)
    # print(type(resUserID))
    # print(resUserID.fetchone())
    if resUserID.fetchone() == None:
        return False
    else:
        return True


# def author_name(in_user_id):
#     return User.query.filter_by(id=in_user_id).first().name
'''
# check_if_user_in_table(in_table="user_usertype", in_check_Column="UserID", in_Value=1)


# s = user_usertype.select().where(user_usertype.c.UserID==1)
s = user_usertype.select().where(user_usertype.c.UserTypeID==2)
# resUserID = db.session.execute(s).fetchone()
resUserID = db.session.execute(s)
# print(resUserID)
print(resUserID)
print(type(resUserID))
print(resUserID.fetchone())
for row in resUserID:
    id = row.UserID
    print(id)
    print(type(id))
# a = user_usertype.select().where(user_usertype.c.UserTypeID==1)
# resUserIDa = db.session.execute(a).fetchone()
# print(resUserIDa)
'''

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)

# todone φτιάξε μια σελίδα που θα μπορείς να δεις όλους τους χρήστες σαν table.
# todone Στο τέλος κάθε χρήστη θα πρέπει να υπάρχει ένα κουμπί που θα σε παραπέμπει στον συγκεκριμένο χρήστη ώστε να μπορείς να αντικαταστήσεις το είδος του χρήστη
# todone extra Θα ήταν ωραίο να μην χρειάζεται να πας σε άλλη σελίδα για να αντικαταστήσεις την ιδιότητα του χρήστη, αλλά αυτό να γίνεται με το που πατάς το κουμπί
# todone καλό θα ήταν να μπορούσες να περιορίσεις ότι ο κάθε χρήστης θα μπορεί να έχει μόνο ένα user type. δες το unique constraints https://docs.sqlalchemy.org/en/14/core/constraints.html#unique-constraint
# todone φτιάξε ένα καινούρια class στο οποίο θα διαλέγεις τον χρήστη και το είδος του χρήστη. Ολα θα πρέπει να είναι με select.
# todone πρέπει στο select να είναι επιλεγμένο κάθε φορά η τιμή που αντιστοιχεί στο usertype
# t#odo όρισε να μπορείς να διαγράψεις χρήστες
# todone στον πίνακα θα πρέπει να προσδιορίζεται το usertype σε περίπτωση που έχει καταχωρηθεί στο UserUsertype διαφορετικά θα πρέπει να βγαζει None
# todone Θα μπορούσες και κατά την δημιουργία ενώς καινούριου χρήστη κατευθείαν να προσθέσεις και μια νέα σύνδεση στο UserUsertype με user
# t#odo πρέπει να διορθώσεις το adminonly ώστε να ελέγχει αν ο χρήστης με αυτο το Id σε ποιά κατηγορία ανήκει
# t#odo popup κατά την διαγραφή ώστε ο χρήστης να πρέπει να επιβεβαιώσει την διαγραφή
# t#odo ο χρήστης μπορεί να τροποποιήσει μόνο τα blogs που έχει δημιουργήσει ο ίδιος
# todone user comments και μπορεί να δημιουργήσει ένα καινούριο θέμα, θα πρέπει αυτόματα να μπαίνει σαν author
#
