# ─── Imports ───────────────────────────────────────────────────────────────────
from flask import Flask, render_template, request, jsonify, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os


# ─── Flask App Setup ──────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max


# ─── Database Setup ────────────────────────────────────────────────────────────
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ─── Models ────────────────────────────────────────────────────────────────────
class ProjectImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    is_cover = db.Column(db.Boolean, default=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    is_primary = db.Column(db.Boolean, default=False)
    layout_type = db.Column(db.String(20))  # 'full-width', 'half-left', 'half-right', 'gallery'
    caption = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(100))
    service = db.Column(db.String(100))
    market = db.Column(db.String(100))
    location = db.Column(db.String(100))
    client = db.Column(db.String(100))
    collaboration = db.Column(db.String(100))
    date = db.Column(db.Date) 
    completion_date = db.Column(db.Date)
    description = db.Column(db.Text)
    cover_image_url = db.Column(db.String(255))  # For card thumbnails
    images = db.relationship('ProjectImage', backref='project', cascade="all, delete-orphan")
    
    @property
    def formatted_date(self):
        if self.date:
            return self.date.strftime("%d-%m-%Y")  # DD-MM-YYYY
        return None
    
    @property
    def formatted_completion_date(self):
        if self.completion_date:
            return self.completion_date.strftime("%d-%m-%Y")  # DD-MM-YYYY
        return None
# ─── Helper Functions ──────────────────────────────────────────────────────────
def handle_date_input(date_str):
    """Helper function to parse date strings safely"""
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


# ─── Routes ───────────────────────────────────────────────────────────────────

# ─── Main Pages ────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index2.html")


@app.route("/projects")
def show_projects():
        # Order by date descending (newest first)
    all_projects = Project.query.order_by(Project.date.desc()).all()
    return render_template("projects.html", projects=all_projects)

@app.route("/projects/<int:project_id>")
def project_details(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template("projects-sub.html", project=project)
# ─── Admin Routes ──────────────────────────────────────────────────────────────
@app.route("/admin/projects", methods=["GET", "POST"])
def admin_projects():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        market = request.form.get("market")
        service = request.form.get("service")
        image_url = request.form.get("image_url")

        new_project = Project(
            title=title,
            subtitle=request.form.get("subtitle"),
            description=description,
            market=market,
            service=service,
            date=request.form.get("date"),
            location=request.form.get("location"),
            client=request.form.get("client"),
            collaboration=request.form.get("collaboration"),
            completion_date=request.form.get("completion_date"),
            cover_image_url=image_url
        )

        db.session.add(new_project)
        db.session.commit()
        return "✅ Project added successfully!"

       # Order by date descending (newest first)
    projects = Project.query.order_by(Project.date.desc()).all()
    return render_template("admin_projects.html", projects=projects)


@app.route("/admin/projects/new", methods=["GET", "POST"])
def add_project():
    if request.method == "POST":
        # Get form data
        form_data = {
            "title": request.form.get("title"),
            "subtitle": request.form.get("subtitle"),
            "description": request.form.get("description"),
            "service": request.form.get("service"),
            "market": request.form.get("market"),
            "location": request.form.get("location"),
            "client": request.form.get("client"),
            "collaboration": request.form.get("collaboration")
        }

        # Handle dates
        date = handle_date_input(request.form.get("date"))
        completion_date = handle_date_input(request.form.get("completion_date"))
        
        if request.form.get("date") and not date:
            flash("Invalid date format", "error")
            return redirect("/admin/projects/new")
            
        if request.form.get("completion_date") and not completion_date:
            flash("Invalid completion date format", "error")
            return redirect("/admin/projects/new")

        # Handle file upload
        cover_file = request.files.get("cover_image")
        cover_path = None
        if cover_file and cover_file.filename:
            filename = f"cover_{datetime.now().timestamp()}_{cover_file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_file.save(filepath)
            cover_path = f"/{filepath}"

        # Create project
        project = Project(
            **form_data,
            date=date,
            completion_date=completion_date,
            cover_image_url=cover_path
        )
        
        db.session.add(project)
        db.session.commit()
        return redirect("/admin/projects")

    return render_template("add_project.html")


@app.route("/admin/projects/<int:id>")
def edit_project_page(id):
    project = Project.query.get_or_404(id)

    panel_fields = {
        "service": project.service,
        "market": project.market,
        "location": project.location,
        "client": project.client,
        "collaboration": project.collaboration,
        "completion_date": project.completion_date,
        "date": project.date,
    }
    
    return render_template("edit_project.html", 
                         project=project, 
                         date=project.date, 
                         panel_fields=panel_fields)


@app.route("/admin/projects/<int:id>/edit", methods=["POST"])
def edit_project_full(id):
    project = Project.query.get_or_404(id)
    
    # Handle date fields
    date = handle_date_input(request.form.get("date"))
    completion_date = handle_date_input(request.form.get("completion_date"))
    
    if request.form.get("date") and not date:
        flash("Invalid date format (use YYYY-MM-DD)", "error")
        return redirect(f"/admin/projects/{project.id}")

    if request.form.get("completion_date") and not completion_date:
        flash("Invalid completion date format (use YYYY-MM-DD)", "error")
        return redirect(f"/admin/projects/{project.id}")

    project.date = date
    project.completion_date = completion_date

    # Handle cover image
    if 'cover_image' in request.files:
        cover_file = request.files['cover_image']
        if cover_file.filename != '':
            filename = secure_filename(f"cover_{project.id}_{cover_file.filename}")
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_file.save(cover_path)
            project.cover_image_url = f"/static/uploads/{filename}"
    
    # Handle project images
    if 'project_images' in request.files:
        for img_file in request.files.getlist('project_images'):
            if img_file.filename != '':
                filename = secure_filename(f"project_{project.id}_{datetime.now().timestamp()}_{img_file.filename}")
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                img_file.save(img_path)
                
                # Get corresponding layout from form data
                layout = request.form.get('default_layout', 'full-width')
                
                new_image = ProjectImage(
                    url=f"/static/uploads/{filename}",
                    project_id=project.id,
                    layout_type=layout,
                    display_order=len(project.images) + 1
                )
                db.session.add(new_image)
    
    # Handle deleted images
    deleted_ids = request.form.getlist('deleted_images[]')
    for img_id in deleted_ids:
        img = ProjectImage.query.get(img_id)
        if img:
            # Optional: Delete the actual file
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img.url.split('/')[-1]))
            except:
                pass
            db.session.delete(img)
    

    # Update other fields
    fields = ["title", "subtitle", "description", "service", "market", 
             "location", "client", "collaboration"]
    
    for field in fields:
        value = request.form.get(field)
        setattr(project, field, value if value else None)

    db.session.commit()
    return redirect(f"/admin/projects/{project.id}")


@app.route("/admin/projects/<int:id>/delete", methods=["POST"])
def delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"status": "deleted"})


# ─── Main Execution ────────────────────────────────────────────────────────────
if __name__ == "__main__":  
    app.run(debug=True)