from flask import Flask, render_template, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# ─── Database Setup ─────────────────────────────────────────────
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ─── Models ─────────────────────────────────────────────────────
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(200))
    service = db.Column(db.String(100))
    market = db.Column(db.String(100))
    location = db.Column(db.String(100))
    client = db.Column(db.String(100))
    collaboration = db.Column(db.String(100))
    date = db.Column(db.Date) 
    completion_date = db.Column(db.String(100))
    description = db.Column(db.Text)
    cover_image_url = db.Column(db.String(255))

# ─── Routes ─────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index2.html")
@app.route("/admin/projects/new", methods=["GET", "POST"])
def add_project():
    if request.method == "POST":
        title = request.form.get("title")
        subtitle = request.form.get("subtitle")
        description = request.form.get("description")
        service = request.form.get("service")
        market = request.form.get("market")
        location = request.form.get("location")
        client = request.form.get("client")
        collaboration = request.form.get("collaboration")

        date_str = request.form.get("date")
        completion_str = request.form.get("completion_date")
        date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        completion_date = datetime.strptime(completion_str, "%Y-%m-%d").date() if completion_str else None

        cover_file = request.files.get("cover_image")
        cover_path = None
        if cover_file and cover_file.filename:
            filename = f"cover_{datetime.now().timestamp()}_{cover_file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_file.save(filepath)
            cover_path = f"/{filepath}"

        project = Project(
            title=title,
            subtitle=subtitle,
            description=description,
            service=service,
            market=market,
            location=location,
            client=client,
            collaboration=collaboration,
            date=date,
            completion_date=completion_date,
            cover_image_url=cover_path
        )
        db.session.add(project)
        db.session.commit()

        # You can save gallery images here later too

        return redirect("/admin/projects")

    return render_template("add_project.html")


@app.route("/admin/projects", methods=["GET", "POST"])
def admin_projects():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        market = request.form.get("market")
        service = request.form.get("service")
        date_str = request.form["date"]  # e.g., "06 June 2025"
        date_str = request.form["date"]  # e.g., "06 June 2025"
        date = datetime.strptime(date_str, "%d %B %Y").date()
        image_url = request.form.get("image_url")

        new_project = Project(
            title=title,
            subtitle=request.form.get("subtitle"),
            description=description,
            market=market,
            service=service,
            date=date,
            location=request.form.get("location"),
            client=request.form.get("client"),
            collaboration=request.form.get("collaboration"),
            completion_date=request.form.get("completion_date"),
            cover_image_url=image_url
        )
        db.session.add(new_project)
        db.session.commit()
        return "✅ Project added successfully!"

    projects = Project.query.all()
    return render_template("admin_projects.html", projects=projects)

@app.route("/admin/projects/<int:id>/edit", methods=["POST"])
def edit_project_full(id):
    project = Project.query.get_or_404(id)

    fields = ["title", "subtitle", "description", "service", "market","date", "location", "client", "collaboration", "completion_date"]
    for field in fields:
        value = request.form.get(field)
        setattr(project, field, value if value else None)
    if field == "date":
        value = datetime.strptime(value, "%d %B %Y").date() 
    db.session.commit()
    return redirect(f"/admin/projects/{project.id}")

@app.route("/admin/projects/<int:id>/delete", methods=["POST"])
def delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"status": "deleted"})

@app.route("/projects")
def show_projects():
    all_projects = Project.query.all()
    return render_template("projects.html", projects=all_projects)

@app.route("/admin/projects/<int:id>")
def edit_project_page(id):
    project = Project.query.get_or_404(id)
    panel_fields = {
        "service": project.service,
        "market": project.market,
        "location": project.location,
        "client": project.client,
        "collaboration": project.collaboration,
        "completion_date": project.completion_date
    }
    return render_template("edit_project.html", project=project, panel_fields=panel_fields)

# ─── Run ────────────────────────────────────────────────────────
if __name__ == "__main__":  
    app.run(debug=True)
