# ─── Imports ───────────────────────────────────────────────────────────────────
from flask import Flask, render_template, request, jsonify, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from werkzeug.utils import secure_filename

allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# ─── Flask App Setup ──────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ─── Database Setup ────────────────────────────────────────────────────────────
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ─── Models ────────────────────────────────────────────────────────────────────
class FeaturedProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project', backref='featured_entries')

class ProjectStatistic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    title = db.Column(db.String(100))
    value = db.Column(db.String(100))
    unit = db.Column(db.String(20))
    order = db.Column(db.Integer)

class ProjectSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    layout_type = db.Column(db.String(20))  # 'full-text', 'text-image', 'image-text', 'stats', etc.
    order = db.Column(db.Integer)
    image_url = db.Column(db.String(255)) 



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
    feature = db.Column(db.Boolean, default=False)
    featured_description = db.Column(db.Text)
    cover_image_url = db.Column(db.String(255))  # For card thumbnails
    sections = db.relationship('ProjectSection', backref='project', cascade="all, delete-orphan")
    statistics = db.relationship('ProjectStatistic', backref='project', cascade="all, delete-orphan")
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
       # Get featured projects
    featured_projects = Project.query.filter_by(feature=True).all()


    
    return render_template("index.html", projects=featured_projects)


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/markets")
def markets():
    return render_template("markets.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/certification")
def certification():
    return render_template("certification.html")

@app.route("/projects")

def show_projects():
        # Order by date descending (newest first)
    all_projects = Project.query.order_by(Project.date.desc()).all()
    return render_template("projects.html", projects=all_projects)

@app.route("/projects/<int:project_id>")
def project_details(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template("projects-sub.html", project=project)

@app.route("/admin/featured")
def featured_projects():
    featured = FeaturedProject.query.join(Project).order_by(Project.date.desc()).all()
    return render_template("admin_featured.html", featured_projects=featured)

# ─── Admin Routes ──────────────────────────────────────────────────────────────
@app.route("/admin/home")
def admin_home():
    return render_template("admin_home.html")
@app.route("/admin/projects/<int:id>/feature", methods=["POST"])
def feature_project(id):
    try:
        project = Project.query.get_or_404(id)
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        action = data.get('action')  # 'feature' or 'unfeature'
        
        if action == 'feature':
            project.feature = True
            if not FeaturedProject.query.filter_by(project_id=id).first():
                db.session.add(FeaturedProject(project_id=id))
        elif action == 'unfeature':
            project.feature = False
            FeaturedProject.query.filter_by(project_id=id).delete()
        else:
            return jsonify({"status": "error", "message": "Invalid action"}), 400
        
        db.session.commit()
        return jsonify({
            "status": "success",
            "featured": project.feature,
            "project_id": project.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/admin/featured/<int:id>/remove", methods=["POST"])
def remove_featured(id):
    featured = FeaturedProject.query.get_or_404(id)
    project = featured.project
    project.feature = False
    db.session.delete(featured)
    db.session.commit()
    return redirect(url_for('featured_projects'))

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
            cover_image_url=image_url,
                
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
        feature = bool(request.form.get('feature'))

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
            if not allowed_file(cover_file.filename):
                flash('Invalid file type - only images allowed')
                return redirect(request.url)
            
            filename = secure_filename(f"cover_{datetime.now().timestamp()}_{cover_file.filename}")            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_file.save(filepath)
            cover_path = f"/static/uploads/{filename}"
        # Create project
        project = Project(
            **form_data,
            date=date,
            completion_date=completion_date,
            cover_image_url=cover_path,
            feature=feature
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
    cover_file = request.files.get("cover_image")
    if cover_file and cover_file.filename:
        if not allowed_file(cover_file.filename):
            flash('Invalid file type - only images allowed')
            return redirect(request.url)
            
        filename = secure_filename(f"cover_{datetime.now().timestamp()}_{cover_file.filename}")            
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cover_file.save(filepath)
        project.cover_image_url = f"/static/uploads/{filename}"

    # Handle feature status 
    feature_status = request.form.get('feature') == 'true'
    project.feature = feature_status

    # Update other fields
    fields = ["title", "subtitle", "description", "service", "market", 
             "location", "client", "collaboration", "featured_description"]
    
    for field in fields:
        value = request.form.get(field)
        setattr(project, field, value if value else None)

    # Handle statistics
    existing_stat_ids = [s.id for s in project.statistics]
    new_stats = []
    
    stat_titles = request.form.getlist('stat_title[]')
    stat_values = request.form.getlist('stat_value[]')
    stat_units = request.form.getlist('stat_unit[]')
    stat_orders = request.form.getlist('stat_order[]')
    
    for i in range(len(stat_titles)):
        if stat_titles[i]:  # Only add if there's a title
            new_stats.append(ProjectStatistic(
                title=stat_titles[i],
                value=stat_values[i],
                unit=stat_units[i],
                order=int(stat_orders[i]) if stat_orders[i] else 0,
                project_id=project.id
            ))
    
    # Replace all statistics
    ProjectStatistic.query.filter_by(project_id=project.id).delete()
    db.session.add_all(new_stats)

    # Handle sections - FIRST create all new sections
    existing_section_ids = [s.id for s in project.sections]
    new_sections = []
    
    section_layouts = request.form.getlist('section_layout[]')
    section_titles = request.form.getlist('section_title[]')
    section_descriptions = request.form.getlist('section_description[]')
    section_orders = request.form.getlist('section_order[]')
    
    for i in range(len(section_titles)):
        if section_titles[i] or section_descriptions[i]:  # Only add if there's content
            new_section = ProjectSection(
                layout_type=section_layouts[i],
                title=section_titles[i],
                description=section_descriptions[i],
                order=int(section_orders[i]) if section_orders[i] else 0,
                project_id=project.id
            )
            new_sections.append(new_section)
    
    # Replace all sections
    ProjectSection.query.filter_by(project_id=project.id).delete()
    db.session.add_all(new_sections)
    db.session.flush()  # This ensures the new sections get IDs
    
    # NOW handle section images for existing sections
    for section in project.sections:
        if section.layout_type in ['text-image', 'image-text']:
            file_key = f'section_image_{section.id}'
            if file_key in request.files:
                img_file = request.files[file_key]
                if img_file and img_file.filename:
                    if not allowed_file(img_file.filename):
                        flash('Invalid file type for section image - only images allowed')
                        continue
                    
                    # Delete old image if exists
                    if section.image_url:
                        try:
                            old_path = os.path.join('static', section.image_url.lstrip('/static/'))
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        except Exception as e:
                            app.logger.error(f"Error deleting old section image: {e}")
                    
                    # Save new image
                    filename = secure_filename(f"section_{section.id}_{datetime.now().timestamp()}_{img_file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    img_file.save(filepath)
                    section.image_url = f"/static/uploads/{filename}"

    # Handle new sections with images
    section_images = [f for f in request.files if f.startswith('new_section_image_')]
    for file_key in section_images:
        img_file = request.files[file_key]
        if img_file and img_file.filename:
            if not allowed_file(img_file.filename):
                flash('Invalid file type for new section image - only images allowed')
                continue
            
            # Get the section index from the file key
            try:
                section_idx = int(file_key.split('_')[-1])
                if section_idx < len(new_sections):
                    filename = secure_filename(f"section_new_{section_idx}_{datetime.now().timestamp()}_{img_file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    img_file.save(filepath)
                    new_sections[section_idx].image_url = f"/static/uploads/{filename}"
            except (IndexError, ValueError):
                app.logger.error(f"Invalid section image key: {file_key}")
    
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