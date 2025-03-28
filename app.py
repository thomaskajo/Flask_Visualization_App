import json
import os
import io
import pandas as pd
import numpy as np
from scipy import stats
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Data, Chart, Collection, CollectionFile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return redirect(url_for("login"))

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

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("login"))

        hashed_pw = generate_password_hash(password, method="pbkdf2:sha256")
        user = User(first_name=first_name, last_name=last_name, company=company, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/index")
@login_required
def index():
    return render_template("index.html", current_link="index", js_files=['static/assets/js/index.js'], css_files=[])

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title='Dashboard', current_link='dashboard',
                           js_files=['static/assets/js/echarts.min.js', 'static/assets/js/dashboard.js'],
                           css_files=['static/assets/css/dashboard.css'])

@app.route("/database", methods=["GET", "POST"])
@login_required
def database():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("No file selected.", "danger")
            return redirect(request.url)

        if file.filename.endswith(".csv"):
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            df = pd.read_csv(path)
            db_entry = Data(filename=file.filename, data=df.to_json())
            db.session.add(db_entry)
            db.session.commit()
            flash("File uploaded successfully.", "success")
            return redirect(url_for("browse_data"))

    return render_template("database.html", title='Upload Data', current_link='database', js_files=[], css_files=[])

@app.route("/browse-data")
@login_required
def browse_data():
    files = Data.query.all()
    return render_template("browse-data.html", files=files, title='Browse Data', current_link='browse_data', js_files=[], css_files=[])

@app.route("/view-data/<int:file_id>")
@login_required
def view_data(file_id):
    file = Data.query.get_or_404(file_id)
    df = pd.read_json(io.StringIO(file.data))
    return render_template("view-data.html", file=file, table=df.to_html(classes='table table-bordered'),
                           title='View Data', current_link='browse_data', js_files=[], css_files=[])

@app.route("/clean-data/<int:file_id>", methods=["GET", "POST"])
@login_required
def clean_data(file_id):
    file = Data.query.get_or_404(file_id)
    df = pd.read_json(file.data)
    if request.method == "POST":
        if 'remove_duplicates' in request.form:
            df = df.drop_duplicates()

        missing_action = request.form.get("missing_values")
        if missing_action == "drop":
            df = df.dropna()
        elif missing_action == "fill_mean":
            df = df.fillna(df.mean(numeric_only=True))
        elif missing_action == "fill_median":
            df = df.fillna(df.median(numeric_only=True))
        elif missing_action == "fill_mode":
            df = df.fillna(df.mode().iloc[0])

        if 'remove_outliers' in request.form:
            z = np.abs(stats.zscore(df.select_dtypes(include=['number'])))
            df = df[(z < 3).all(axis=1)]

        selected_cols = request.form.getlist("columns_to_remove")
        df = df.drop(columns=selected_cols, errors='ignore')

        date_col = request.form.get("date_column")
        if 'handle_dates' in request.form and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        if 'sort_dates' in request.form and date_col in df.columns:
            df = df.sort_values(by=[date_col])

        cleaned_file = Data(filename="cleaned_" + file.filename, data=df.to_json())
        db.session.add(cleaned_file)
        db.session.commit()
        flash("Data cleaned and saved.", "success")
        return redirect(url_for('view_data', file_id=cleaned_file.id))

    return render_template("clean-data.html", file=file, df=df, columns=df.columns, expected_df=df)

@app.route("/delete-file/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    file = Data.query.get_or_404(file_id)
    db.session.delete(file)
    db.session.commit()
    flash("File deleted successfully.", "success")
    return redirect(url_for("browse_data"))

@app.route("/analytics")
@login_required
def analytics():
    file_id = request.args.get('file_id')
    headers = []
    if file_id:
        file = Data.query.get_or_404(file_id)
        df = pd.read_json(io.StringIO(file.data))
        headers = df.columns.tolist()
    return render_template("analytics.html", title="Analysis Reports", current_link="analytics",
                           fileId=file_id, headers=headers,
                           js_files=['static/assets/js/echarts.min.js', 'static/assets/js/analytics.js'],
                           css_files=[])

@app.route("/saveAnalyticsData", methods=["POST"])
@login_required
def saveAnalyticsData():
    data = request.json
    chart = Chart(name=data['name'], x_axis=json.dumps(data['xAxis']), y_axis=json.dumps(data['yAxis']),
                  type=data['type'], content=data['content'])
    db.session.add(chart)
    db.session.commit()
    return jsonify({"status": 1})

@app.route("/getAnalyticsData", methods=["POST"])
@login_required
def getAnalyticsData():
    data = request.json
    file = Data.query.get_or_404(data['fileId'])
    df = pd.read_json(io.StringIO(file.data))
    x, y = data['xAxisSelect'], data['yAxisSelect']
    response = []

    if x:
        if y:
            grouped = df.groupby(x)[y].sum().reset_index()
            response = grouped.to_dict(orient='records')
        else:
            counts = df.groupby(x).size().reset_index(name='count')
            response = counts.to_dict(orient='records')

    return jsonify({"status": 1, "reqData": data, "respData": response})

@app.route("/personal-collection")
@login_required
def personal_collection():
    charts = Chart.query.all()
    return render_template("personal-collection.html", charts=charts, title="Personal Collection",
                           current_link="collection", js_files=['static/assets/js/collection.js'],
                           css_files=['static/assets/css/collection.css'])

@app.route("/deletePersonCollection", methods=["POST"])
@login_required
def deletePersonCollection():
    name = request.json['name']
    chart = Chart.query.get(name)
    if chart:
        db.session.delete(chart)
        db.session.commit()
    return jsonify({"status": 1})

@app.route("/manage-collections")
@login_required
def manage_collections():
    return render_template("manage-collections.html")

from collection_manager import collection_bp
app.register_blueprint(collection_bp)

if __name__ == "__main__":
    os.makedirs("uploads/collections", exist_ok=True)
    os.makedirs("instance", exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=9999)
