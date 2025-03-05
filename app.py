from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
from scipy import stats
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Data Model for Uploaded CSVs
class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    data = db.Column(db.Text, nullable=False)  # Storing CSV as JSON format

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return redirect(url_for("login"))

# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        company = request.form.get("company")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("login"))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = User(first_name=first_name, last_name=last_name, company=company, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

# Index Route (Protected)
@app.route("/index")
@login_required
def index():
    return render_template("index.html")

# Database Upload Route (Protected)
@app.route("/database", methods=["GET", "POST"])
@login_required
def database():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file", "danger")
            return redirect(request.url)

        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            df = pd.read_csv(filepath)
            data_json = df.to_json()

            new_data = Data(filename=file.filename, data=data_json)
            db.session.add(new_data)
            db.session.commit()

            flash("File uploaded successfully!", "success")
            return redirect(url_for("browse_data"))

    return render_template("database.html")

# Browse Uploaded Data (Protected)
@app.route("/browse-data")
@login_required
def browse_data():
    files = Data.query.all()
    return render_template("browse-data.html", files=files)

# View Uploaded Data (Protected)
@app.route("/view-data/<int:file_id>")
@login_required
def view_data(file_id):
    file = Data.query.get_or_404(file_id)
    df = pd.read_json(file.data)
    return render_template("view-data.html", file=file, table=df.to_html(classes='table table-bordered'))

# Clean Data Route (Protected)
@app.route("/clean-data/<int:file_id>", methods=["GET", "POST"])
@login_required
def clean_data(file_id):
    file = Data.query.get_or_404(file_id)
    df = pd.read_json(file.data)
    
    if request.method == "POST":
        # Perform cleaning operations based on user input
        if 'remove_duplicates' in request.form:
            df = df.drop_duplicates()
        
        if 'handle_dates' in request.form:
            date_column = request.form.get('date_column')
            date_format = request.form.get('date_format')
            if date_column in df.columns:
                df[date_column] = pd.to_datetime(df[date_column], format=date_format, errors='coerce')
        
        if 'normalize_units' in request.form:
            column = request.form.get('normalize_column')
            from_unit = request.form.get('from_unit')
            to_unit = request.form.get('to_unit')
            if column in df.columns:
                if from_unit == 'kg' and to_unit == 'tons':
                    df[column] = df[column] / 1000
                elif from_unit == 'tons' and to_unit == 'kg':
                    df[column] = df[column] * 1000
        
        if 'remove_outliers' in request.form:
            method = request.form.get('outlier_method')
            column = request.form.get('outlier_column')
            if column in df.columns:
                if method == 'iqr':
                    Q1 = df[column].quantile(0.25)
                    Q3 = df[column].quantile(0.75)
                    IQR = Q3 - Q1
                    df = df[(df[column] >= Q1 - 1.5*IQR) & (df[column] <= Q3 + 1.5*IQR)]
                elif method == 'zscore':
                    z_scores = np.abs(stats.zscore(df[column]))
                    df = df[z_scores < 3]
        
        if 'handle_missing' in request.form:
            method = request.form.get('missing_method')
            column = request.form.get('missing_column')
            if column in df.columns:
                if method == 'drop':
                    df = df.dropna(subset=[column])
                elif method == 'mean':
                    df[column] = df[column].fillna(df[column].mean())
                elif method == 'median':
                    df[column] = df[column].fillna(df[column].median())
                elif method == 'interpolate':
                    df[column] = df[column].interpolate()
        
        # Save the cleaned data as a new file
        cleaned_filename = f"cleaned_{file.filename}"
        cleaned_file = Data(filename=cleaned_filename, data=df.to_json())
        db.session.add(cleaned_file)
        db.session.commit()
        
        flash("Data cleaned successfully! New cleaned file created.", "success")
        return redirect(url_for('view_data', file_id=cleaned_file.id))
    
    return render_template("clean-data.html", file=file, df=df, columns=df.columns)

# Delete File Route (Protected)
@app.route("/delete-file/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    file = Data.query.get_or_404(file_id)
    db.session.delete(file)
    db.session.commit()
    flash("File deleted successfully!", "success")
    return redirect(url_for('browse_data'))

# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/personal-collection")
@login_required
def personal_collection():
    return render_template("personal-collection.html")

@app.route("/analysis-detail")
@login_required
def analysis_detail():
    return render_template("analysis-detail.html")

@app.route("/environmental")
@login_required
def environmental():
    return redirect(url_for("analysis_detail") + "#environmental")

@app.route("/performance-metrics")
@login_required
def performance_metrics():
    return redirect(url_for("analysis_detail") + "#performance-metrics")

@app.route("/reports")
@login_required
def reports():
    return redirect(url_for("analysis_detail") + "#reports")


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)