import os
import pandas as pd
import numpy as np
from scipy import stats
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import login_required
from models import db, Collection, CollectionFile, Data

collection_bp = Blueprint("collection", __name__)
UPLOAD_FOLDER = "uploads/collections"

@collection_bp.route("/collections/create", methods=["POST"])
@login_required
def create_collection():
    name = request.form.get("name")
    description = request.form.get("description", "")
    if Collection.query.filter_by(name=name).first():
        return jsonify({"error": "Collection already exists"}), 400

    collection = Collection(name=name, description=description)
    db.session.add(collection)
    db.session.commit()
    os.makedirs(os.path.join(UPLOAD_FOLDER, name), exist_ok=True)
    return jsonify({"message": "Collection created", "id": collection.id})

@collection_bp.route("/collections/list", methods=["GET"])
@login_required
def list_collections():
    collections = Collection.query.all()
    return jsonify([{"id": c.id, "name": c.name} for c in collections])

@collection_bp.route("/collections/<collection_name>/upload", methods=["POST"])
@login_required
def upload_files(collection_name):
    collection = Collection.query.filter_by(name=collection_name).first_or_404()
    files = request.files.getlist("files[]")
    saved_files = []

    for file in files:
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, collection_name, filename)
        file.save(save_path)

        db_file = CollectionFile(collection_id=collection.id, filename=filename, filepath=save_path)
        db.session.add(db_file)
        saved_files.append(filename)

    db.session.commit()
    return jsonify({"message": "Files uploaded", "files": saved_files})

@collection_bp.route("/collections/<collection_name>/view", methods=["GET"])
@login_required
def view_collection_data_html(collection_name):
    collection = Collection.query.filter_by(name=collection_name).first_or_404()
    files = CollectionFile.query.filter_by(collection_id=collection.id).all()
    dfs = [pd.read_csv(f.filepath) for f in files]
    if not dfs:
        return render_template("view-data.html", file=None, table="<p>No files in this collection.</p>")

    merged = pd.concat(dfs, ignore_index=True)
    temp_data = Data(filename=f"collection_{collection.name}_view", data=merged.to_json())
    db.session.add(temp_data)
    db.session.commit()

    return render_template("view-data.html", file=temp_data, table=merged.to_html(classes='table table-bordered'))

@collection_bp.route("/collections/<collection_name>/analytics", methods=["GET"])
@login_required
def collection_analytics_html(collection_name):
    collection = Collection.query.filter_by(name=collection_name).first_or_404()
    files = CollectionFile.query.filter_by(collection_id=collection.id).all()
    dfs = [pd.read_csv(f.filepath) for f in files]
    if not dfs:
        return render_template("analytics.html", fileId=None, headers=[], title="Collection Analytics", current_link="analytics")

    merged = pd.concat(dfs, ignore_index=True)
    headers = merged.columns.tolist()

    temp_data = Data(filename=f"collection_{collection.name}_analytics", data=merged.to_json())
    db.session.add(temp_data)
    db.session.commit()

    return render_template("analytics.html", fileId=temp_data.id, headers=headers, title="Collection Analytics", current_link="analytics")

@collection_bp.route("/collections/<collection_name>/clean", methods=["GET", "POST"])
@login_required
def clean_collection_html(collection_name):
    collection = Collection.query.filter_by(name=collection_name).first_or_404()
    files = CollectionFile.query.filter_by(collection_id=collection.id).all()
    dfs = [pd.read_csv(f.filepath) for f in files]
    if not dfs:
        flash("No files to clean.", "danger")
        return redirect(url_for('manage_collections'))

    df = pd.concat(dfs, ignore_index=True)

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

        cleaned_data = Data(filename=f"cleaned_collection_{collection.name}", data=df.to_json())
        db.session.add(cleaned_data)
        db.session.commit()

        flash("✅ Cleaned collection saved as new dataset.", "success")
        return redirect(url_for('view_data', file_id=cleaned_data.id))

    # When GET: render clean-data.html
    temp_data = Data(filename=f"temp_clean_{collection.name}", data=df.to_json())
    db.session.add(temp_data)
    db.session.commit()

    return render_template("clean-data.html", file=temp_data, df=df, columns=df.columns, expected_df=df)

@collection_bp.route("/collections/<collection_name>/delete", methods=["DELETE"])
@login_required
def delete_collection(collection_name):
    collection = Collection.query.filter_by(name=collection_name).first_or_404()
    files = CollectionFile.query.filter_by(collection_id=collection.id).all()

    for file in files:
        if os.path.exists(file.filepath):
            os.remove(file.filepath)
        db.session.delete(file)

    folder_path = os.path.join(UPLOAD_FOLDER, collection_name)
    if os.path.exists(folder_path):
        os.rmdir(folder_path)

    db.session.delete(collection)
    db.session.commit()
    return jsonify({"message": f"Collection '{collection_name}' and its files have been deleted."})
