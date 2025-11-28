from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from datetime import datetime
import os


app = Flask(__name__)
app.secret_key = 'secretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(300))
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/')
def splash():
    return render_template('splash.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('⚠️ Username already exists!')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('✅ Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('❌ Invalid credentials!')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    completed = sum(1 for t in tasks if t.completed)
    progress = int((completed / len(tasks)) * 100) if tasks else 0
    return render_template('dashboard.html', tasks=tasks, progress=progress)



@app.route('/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    description = request.form.get('description', '')

  
    date_str = request.form.get('due_date_date')
    time_str = request.form.get('due_date_time')

    due_date = None
    if date_str:
        try:
            if time_str:
                due_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            else:
                due_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            flash("⚠️ Invalid date or time format!")

    new_task = Task(
        title=title,
        description=description,
        due_date=due_date,
        user_id=current_user.id
    )
    db.session.add(new_task)
    db.session.commit()
    flash('✅ Task added successfully!')
    return redirect(url_for('dashboard'))



@app.route('/update/<int:task_id>')
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('⚠️ Unauthorized action!')
        return redirect(url_for('dashboard'))

    task.completed = not task.completed
    db.session.commit()
    flash('🔄 Task status updated!')
    return redirect(url_for('dashboard'))


@app.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('⚠️ Unauthorized action!')
        return redirect(url_for('dashboard'))

    db.session.delete(task)
    db.session.commit()
    flash('🗑️ Task deleted successfully!')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    if not os.path.exists('todo.db'):
        with app.app_context():
            db.create_all()
            print("✅ Database created successfully!")

    app.run(debug=True)
