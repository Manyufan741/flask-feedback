from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, UserForm, FeedbackForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "oneonetwotwo"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username=username, password=password,
                                 email=email, first_name=first_name, last_name=last_name)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = new_user.username
        return redirect(f"/users/{username}")
    else:
        return render_template('register_form.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        u = User.authenticate(username=username, password=password)

        if u:
            session['username'] = u.username
            return redirect(f"/users/{u.username}")
        else:
            form.username.errors = ["Incorrect username/password"]

    return render_template('login_form.html', form=form)


@app.route('/users/<username>')
def user_info(username):
    user = User.query.get_or_404(username)
    feedbacks = Feedback.query.all()
    form = UserForm(obj=user)
    if 'username' in session:
        return render_template('users/info.html', form=form, user=user, feedbacks=feedbacks)
    else:
        flash("You're not authorized!")
        return redirect('/')


@app.route('/users/<username>/delete', methods=["POST"])
def delete(username):
    user = User.query.get_or_404(username)
    if 'username' not in session or username != session['username']:
        flash("You are not authorized!")
        return redirect('/')
    db.session.delete(user)
    db.session.commit()
    session.pop("username")
    return redirect('/')


@app.route('/users/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    if "username" not in session or username != session['username']:
        flash("You are not authorized!")
        return redirect('/')

    user = User.query.get_or_404(username)
    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(
            title=title, content=content, username=user.username)
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f"/users/{user.username}")
    else:
        return render_template('feedbacks/feedback_form.html', form=form)


@app.route('/feedback/<int:id>/update', methods=["GET", "POST"])
def update_feedback(id):
    feedback = Feedback.query.get_or_404(id)
    if "username" not in session or feedback.user.username != session['username']:
        flash("You are not authorized!")
        return redirect('/')

    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        return redirect(f"/users/{feedback.user.username}")
    else:
        return render_template('feedbacks/update_feedback.html', form=form, feedback=feedback)


@app.route('/feedback/<int:id>/delete', methods=["POST"])
def delete_feedback(id):
    feedback = Feedback.query.get_or_404(id)
    if "username" not in session or feedback.user.username != session['username']:
        flash("You are not authorized!")
        return redirect('/')

    db.session.delete(feedback)
    db.session.commit()
    return redirect(f"/users/{feedback.user.username}")


@app.route("/logout")
def logout():
    """Logout route."""

    session.pop("username")
    return redirect('/')


@app.route('/secret')
def secret():
    if "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/")
    else:
        return "You made it!"
