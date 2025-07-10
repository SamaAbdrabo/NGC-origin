from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    service = db.Column(db.String(100))
    market = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    image_url = db.Column(db.String(255))

# ─── Routes ─────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index2.html")

@app.route("/admin/projects", methods=["GET", "POST"])
def admin_projects():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        market = request.form.get("market")
        service = request.form.get("service")
        date_str = request.form["date"]  # e.g., "06 June 2025"
        date = datetime.strptime(date_str, "%d %B %Y").date()
        image_url = request.form.get("image_url")

        new_project = Project(
            title=title,
            date=date,
            description=description,
            market=market,
            service=service,
            image_url=image_url
        )
        db.session.add(new_project)
        db.session.commit()
        return "✅ Project added successfully!"
    
    projects = Project.query.all()
    return render_template("admin_projects.html", projects=projects)

@app.route("/admin/projects/<int:id>/edit", methods=["POST"])
def edit_project(id):
    project = Project.query.get_or_404(id)
    data = request.get_json()
    field = data.get("field")
    value = data.get("value")

    if field == "date":
        value = datetime.strptime(value, "%d %B %Y").date()

    setattr(project, field, value)
    db.session.commit()
    return jsonify({"status": "updated"})

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
    return render_template("edit_project.html", project=project)


# ─── Run ────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
