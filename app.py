import os
from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email
import google.oauth2.credentials
import google_auth_oauthlib.flow
import re
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)



app.config['SECRET_KEY'] = os.urandom(24)
oauth = OAuth(app)
app.config['GOOGLE_CLIENT_ID'] = ""
app.config['GOOGLE_CLIENT_SECRET'] = ""
# Set up the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simplifiedskill.db'  # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=7)
app.config['COURSE_IMAGE_UPLOAD_FOLDER'] = 'static/courseimg'  # Folder where images will be saved


db = SQLAlchemy(app)
# db.init_app(app)

class Admin(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    useremail = db.Column(db.String(130), unique=True, nullable=False)
    userrole = db.Column(db.Integer, unique=False, nullable=False)

    def __init__(self, useremail, userrole):
        self.useremail = useremail
        self.userrole = userrole



class Category(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    categoryname = db.Column(db.String(130), unique=True, nullable=False)



class Subcategory(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    subcategoryname = db.Column(db.String(130), unique=True, nullable=False)

    # Define a relationship to Category
    category = db.relationship('Category', backref=db.backref('subcategories', lazy=True))






class Course(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'), nullable=False)
    course_title = db.Column(db.String(130), unique=True, nullable=False)
    course_overview = db.Column(db.String(700), nullable=False)
    course_keytopic = db.Column(db.String(400), nullable=False)
    course_slug = db.Column(db.String(313), unique=True, nullable=False)
    course_old_slug = db.Column(db.String(313), nullable=True)
    course_price = db.Column(db.Integer, nullable=False)
    course_discount = db.Column(db.Integer, nullable=False, default=0)
    course_discount_percentage = db.Column(db.Integer, nullable=False, default=0)
    course_class_type = db.Column(db.Integer, nullable=False, default=1)
    course_duration = db.Column(db.Integer, nullable=False)
    course_avail_seat = db.Column(db.Integer, nullable=False, default=0)
    course_image = db.Column(db.String(230), nullable=False)
    # course_total_seat = db.Column(db.Integer, nullable=False, default=0)

    # Define a relationship to Subcategory
    subcategory = db.relationship('Subcategory', backref=db.backref('courses', lazy=True))


class CourseContent(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    course_content_title = db.Column(db.String(130), unique=False, nullable=False)
    course_content_description = db.Column(db.String(700), nullable=False)
    # course_content_file = db.Column(db.String(230), nullable=False)
    # course_content_type = db.Column(db.Integer, nullable=False, default=1)

    # Define a relationship to Course
    course = db.relationship('Course', backref=db.backref('course_contents', lazy=True))



class CourseBatch(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    batch_num = db.Column(db.Integer, unique=False, nullable=False)
    batch_avail_seat = db.Column(db.Integer, nullable=False, default=0)
    batch_status = db.Column(db.Integer, nullable=False, default=0)

    # Define a relationship to Course
    course = db.relationship('Course', backref=db.backref('course_batches', lazy=True))
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('course_id', 'batch_num', name='_course_batch_uc'),)


# Google OAuth 2.0 client configuration

google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri = "https://www.googleapis.com/oauth2/v3/certs"
)



@app.route('/')
@app.route('/home')
def home():
    # return 'Hello from Flask! <h1>Hello</h1>'
    return render_template('userend/index.html')


@app.route('/simplifiedskill/admin')
def admin():
    if 'userrole' in session and session['userrole'] == 1:
        flash(f'Welcome, Admin!')
        return render_template('adminend/index.html', useremail=session['useremail'])
    else:
        # session.pop('useremail', None)
        # session.pop('userrole', None)
        flash('You are not authorized to access this page.')
        return redirect(url_for('admin_login'))



@app.route('/category', methods=["GET", "POST"])
def category():
    if 'userrole' in session and session['userrole'] == 1:
        if request.method == "POST":
            categoryname = request.form['category']
            if request.form['category'] != '' and request.form['category'] != None and request.form['category'] != ' ':
                category = Category(categoryname=categoryname)
                db.session.add(category)
                db.session.commit()
                flash('Category added successfully!')
                return redirect(url_for('category'))
            else:
                flash('Please enter a valid category name.')
                return redirect(url_for('category'))
        else:
            return render_template('adminend/category.html')
    else:
        # session.pop('useremail', None)
        # session.pop('userrole', None)
        flash('You are not authorized to access this page.')
        return redirect(url_for('admin_login'))
    


@app.route('/edit_category/<int:id>', methods=["GET", "POST"])
def category_edit(id):
    if 'userrole' in session and session['userrole'] == 1:
        category = Category.query.get_or_404(id)
        if request.method == "POST":
            new_categoryname = request.form['category']
            if new_categoryname and new_categoryname.strip():
                category.categoryname = new_categoryname
                db.session.commit()
                flash('Category updated successfully!')
                return redirect(url_for('category'))
            else:
                flash('Please enter a valid category name.')
                return redirect(url_for('category_edit', id=id))
        else:
            return render_template('adminend/edit_category.html', category=category)
    else:
        flash('You are not authorized to access this page.')
        return redirect(url_for('admin_login'))
    
@app.route('/delete_category/<int:id>')
def category_delete(id):
    if 'userrole' in session and session['userrole'] == 1:
        category = Category.query.get_or_404(id)
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!')
        return redirect(url_for('category'))
    else:
        flash("You are not authorized to access this page.")
        return redirect(url_for('admin_login'))

@app.route('/category-data')
def category_data():
    if 'userrole' in session and session['userrole'] == 1:
        categories = Category.query.all()
        return render_template('adminend/categorydata.html', categories=categories)
    else:
        flash('You are not authorized to access this page.')
        return redirect(url_for('admin_login'))


@app.route('/subcategory', methods=["GET", "POST"])
def subcategory():
    if 'userrole' in session and session['userrole'] == 1:
        # if request.method == "POST":
            category = Category.query.all()
            if request.method == "POST":
                category = request.form['category']
                if request.form['subcategory'] != '' and request.form['subcategory'] != None and request.form['subcategory'] != ' ':
                    subcategory = Subcategory(category_id=category, subcategoryname=request.form['subcategory'])
                    db.session.add(subcategory)
                    db.session.commit()
                    flash('Subcategory added successfully!')
                    return redirect(url_for('subcategory'))
                else:
                    flash('Please enter a valid subcategory name.')
                    return redirect(url_for('subcategory'))
            
            return render_template('adminend/subcategory.html', categories=category)  
    else:
        flash('You are not authorized to access this page.')
        return redirect(url_for('admin_login'))
    


@app.route('/edit_subcategory/<int:id>', methods=["GET", "POST"])
def subcategory_edit(id):
    if 'userrole' in session and session['userrole'] == 1:
        subcategory = Subcategory.query.get_or_404(id)
        categories = Category.query.all()  # Fetch all categories for the select dropdown

        if request.method == "POST":
            category_id = request.form['category']
            subcategory_name = request.form['subcategory']

            if subcategory_name and subcategory_name.strip():
                subcategory.category_id = category_id
                subcategory.subcategoryname = subcategory_name
                db.session.commit()
                flash('Subcategory updated successfully!')
                return redirect(url_for('subcategory'))
            else:
                flash('Please enter a valid subcategory name.')
                return redirect(url_for('subcategory_edit', id=id))
        
        return render_template('adminend/edit_subcategory.html', subcategory=subcategory, categories=categories)
    else:
        flash('You are not authorized to access this page.')

        return redirect(url_for('admin_login'))


@app.route('/delete_subcategory/<int:id>')
def subcategory_delete(id):
    if 'userrole' in session and session['userrole'] == 1:
        subcategory = Subcategory.query.get_or_404(id)
        db.session.delete(subcategory)
        db.session.commit()
        flash("Subcategory deleted successfully!")
        return redirect(url_for('subcategory'))
    else:
        flash("You are not authorized to access this page.")
        return redirect(url_for('admin_login'))


@app.route('/subcategory-data')
def subcategory_data():
    if 'userrole' in session and session['userrole'] == 1:
        subcategories = db.session.query(Subcategory, Category).join(Category).all()
        return render_template('adminend/subcategorydata.html', subcategories=subcategories)
    else:
        flash('You are not authorized to access this page.')
        return redirect(url_for('admin_login'))



# Function to slugify the course title
def slugify(title):
    title = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', title)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    return slug

@app.route('/course-create', methods=['GET', 'POST'])
def course_create():
    if 'userrole' in session and session['userrole'] == 1:
        if request.method == 'POST':
            
            subcategory_id = request.form.get('subcategory')
            course_title = request.form.get('coursetitle')
            course_overview = request.form.get('courseoverview')
            course_keytopic = request.form.get('coursekeytopic')
            course_slug = slugify(course_title)
            course_price = request.form.get('courseprice')
            course_discount = request.form.get('coursediscount')
            course_discount_percentage = request.form.get('coursediscountpercentage')
            course_class_type = request.form.get('courseclasstype')
            course_duration = request.form.get('courseduration')
            course_avail_seat = request.form.get('courseavailseat')
            course_image_file = request.files.get('courseimage')

            # # Validate data
            if not course_title or not subcategory_id:
                flash('Please fill out all required fields.', 'error')
                return redirect(url_for('course_create'))

            # # Check for unique course title
            existing_course = Course.query.filter_by(course_title=course_title).first()
            if existing_course:
                flash('Course title already exists.', 'error')
                return redirect(url_for('course_create'))

            # # Save course image
            if course_image_file:
                filename = secure_filename(course_image_file.filename)
                course_image_path = os.path.join(app.config['COURSE_IMAGE_UPLOAD_FOLDER'], filename)
                course_image_file.save(course_image_path)
            else:
                flash('Please upload a course image.', 'error')
                return redirect(url_for('course_create'))

            # # Create new course
            new_course = Course(
                subcategory_id=subcategory_id,
                course_title=course_title,
                course_overview=course_overview,
                course_keytopic=course_keytopic,
                course_slug=course_slug,
                course_price=course_price,
                course_discount=course_discount,
                course_discount_percentage=course_discount_percentage,
                course_class_type=course_class_type,
                course_duration=course_duration,
                course_avail_seat=course_avail_seat,
                course_image=filename  # Store the filename in the database
            )

            # # Add to database
            db.session.add(new_course)
            db.session.commit()

            flash('Course created successfully!', 'success')
            return redirect(url_for('course_create'))

        else:# If GET request, render the form
            subcategories = Subcategory.query.all()
            return render_template('adminend/course.html', subcategories=subcategories)
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login'))





@app.route('/course-edit-update/<int:id>', methods=['GET', 'POST'])
def course_edit_update(id):
    if 'userrole' in session and session['userrole'] == 1:

        course = Course.query.get_or_404(id)
        if request.method == 'POST':
            course.subcategory_id = request.form.get('subcategory')
            course.course_title = request.form.get('coursetitle')
            course.course_overview = request.form.get('courseoverview')
            course.course_keytopic = request.form.get('coursekeytopic')
            if course.course_old_slug != '' and course.course_old_slug != None:
                course_old_slug_list = course.course_old_slug.split('#')
                if course.course_slug not in course_old_slug_list:
                    course.course_old_slug = course.course_old_slug + course.course_slug + '#'
                # else:
                #     flash('Nice!!!!!!!')
                #     return redirect(url_for('course_create'))
            else:
                course.course_old_slug = course.course_slug + '#'
            course.course_slug = slugify(course.course_title)
            course.course_price = request.form.get('courseprice')
            course.course_discount = request.form.get('coursediscount')
            course.course_discount_percentage = request.form.get('coursediscountpercentage')
            course.course_class_type = request.form.get('courseclasstype')
            course.course_duration = request.form.get('courseduration')
            course.course_avail_seat = request.form.get('courseavailseat')
            course_image_file = request.files.get('courseimage')

            # Validate data
            if not course.course_title or not course.subcategory_id:
                flash('Please fill out all required fields.', 'error')
                return redirect(url_for('course_edit_update', id=id))

            # Check if a new image is uploaded
            if course_image_file:
                filename = secure_filename(course_image_file.filename)
                course_image_path = os.path.join(app.config['COURSE_IMAGE_UPLOAD_FOLDER'], filename)
                course_image_file.save(course_image_path)
                course.course_image = filename  # Update the image filename in the database

            db.session.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('course_create'))
        else:    
            subcategories = Subcategory.query.all()
            return render_template('adminend/edit_course.html', course=course, subcategories=subcategories)
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login'))


@app.route('/course-delete/<int:id>')
def course_delete(id):
    if 'userrole' in session and session['userrole'] == 1:
        course = Course.query.get_or_404(id)
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully!', 'error')
        return redirect(url_for('course_data'))
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login')) 


@app.route('/course-content-create', methods=['GET', 'POST'])
def course_content_create():
    if 'userrole' in session and session['userrole'] == 1:
        if request.method == 'POST':
            course_id = request.form.get('course')
            course_content_title = request.form.get('courseContentTitle')
            course_content_description = request.form.get('courseContentDetail')
            # course_content_file = request.files.get('courseContentFile')
            # course_content_type = request.form.get('courseContentType')

            # # Validate data
            if not course_content_title or not course_id:
                flash('Please fill out all required fields.', 'error')
                return redirect(url_for('course_content_create'))

            # # Save course content file
            # if course_content_file:
            #     filename = secure_filename(course_content_file.filename)
            #     course_content_file_path = os.path.join(app.config['COURSE_CONTENT_UPLOAD_FOLDER'], filename)
            #     course_content_file.save(course_content_file_path)
            # else:
            #     flash('Please upload a course content file.', 'error')
            #     return redirect(url_for('course_content_create'))

            # # Create new course content
            new_course_content = CourseContent(
                course_id=course_id,
                course_content_title=course_content_title,
                course_content_description=course_content_description,
                # course_content_file=filename,  # Store the filename in the database
                # course_content_type=course_content_type
            )
            # # Add to database
            db.session.add(new_course_content)
            db.session.commit()

            flash('Course content created successfully!', 'success')
            return redirect(url_for('course_content_create'))
        else:
            courses = Course.query.all()
            return render_template('adminend/course_content.html', courses=courses)
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login'))


@app.route('/course-content-edit/<int:id>', methods=['GET', 'POST'])
def course_content_edit_update(id):
    if 'userrole' in session and session['userrole'] == 1:
        course_content = CourseContent.query.get_or_404(id)
        courses = Course.query.all()
        if request.method == 'POST':
            course_content.course_id = request.form.get('course')
            course_content.course_content_title = request.form.get('courseContentTitle')
            course_content.course_content_description = request.form.get('courseContentDetail')
            # course_content.course_content_file = request.files.get('courseContentFile')
            # course_content.course_content_type = request.form.get('courseContentType')

            # # Validate data
            if not course_content.course_content_title or not course_content.course_id:
                flash('Please fill out all required fields.', 'error')
                return redirect(url_for('course_content_edit_update', id=id))

            # # Save course content file
            # if course_content.course_content_file:
            #     filename = secure_filename(course_content.course_content_file.filename)
            #     course_content_file_path = os.path.join(app.config['COURSE_CONTENT_UPLOAD_FOLDER'], filename)
            #     course_content.course_content_file.save(course_content_file_path)
            # else:
            #     flash('Please upload a course content file.', 'error')
            #     return redirect(url_for('course_content_edit', id=id))

            # # Update course content
            db.session.commit()

            flash('Course content updated successfully!', 'success')
            return redirect(url_for('course_content_data'))
        else:
            return render_template('adminend/edit_course_content.html', course_content=course_content, courses=courses)
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login'))



@app.route('/course-content-delete/<int:id>')
def course_content_delete(id):
    if 'userrole' in session and session['userrole'] == 1:
        course_content = CourseContent.query.get_or_404(id)
        db.session.delete(course_content)
        db.session.commit()
        flash('Course content deleted successfully!', 'error')
        return redirect(url_for('course_content_data'))
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login'))



@app.route('/course-content-data')
def course_content_data():
    if 'userrole' in session and session['userrole'] == 1:
        course_contents = db.session.query(CourseContent, Course).join(Course).all()
        return render_template('adminend/course_contentdata.html', course_contents=course_contents)
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login'))
    

@app.route('/course-batch-create', methods=['GET', 'POST'])
def course_batch_create():
    if 'userrole' in session and session['userrole'] == 1:
        if request.method == 'POST':
            course_id = request.form.get('course')
            batch_num = request.form.get('courseBatchNum')
            # batch_start_date = request.form.get('batchstartdate')
            # batch_end_date = request.form.get('batchenddate')
            batch_avail_seat = request.form.get('batchAvailSeat')
            # batch_status = request.form.get('batchstatus')

            # # Validate data
            if not course_id or not batch_num:
                flash('Please fill out all required fields.', 'error')
                return redirect(url_for('course_batch_create'))

            existing_batch = CourseBatch.query.filter_by(course_id=course_id, batch_num=batch_num).first()
            if existing_batch:
                flash('Course batch already exists!')
                return redirect(url_for('course_batch_create'))
            # # Create new course batch
            new_course_batch = CourseBatch(
                course_id=course_id,
                batch_num=batch_num,
                # batch_start_date=batch_start_date,
                # batch_end_date=batch_end_date,
                batch_avail_seat=batch_avail_seat,
                # batch_status=batch_status
            )
            # # Add to database
            db.session.add(new_course_batch)
            db.session.commit()

            flash('Course batch created successfully!', 'success')
            return redirect(url_for('course_batch_create'))
        else:
            courses = Course.query.all()
            return render_template('adminend/course_batch.html', courses=courses)
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login'))


# @app.route('/course-batch-edit/<int:id>', methods=['GET', 'POST'])
# def course_batch_edit_update(id):
#     if 'userrole' in session and session['userrole'] == 1:
#         course_batch = CourseBatch.query.get_or_404(id)
#         courses = Course.query.all()
#         if request.method == 'POST':
#             course_batch.course_id = request.form.get('course')
#             course_batch.batch_num = request.form.get('batchnum')
#             course_batch.batch_start_date = request.form.get('batchstartdate')
#             course_batch.batch_end_date = request.form.get('batchenddate')
#             course_batch.batch_avail_seat = request.form.get('batchavailseat')
#             # course_batch.batch_status = request.form.get('batchstatus') 
            #


@app.route('/course/<course_url>')
def course_detail(course_url):
    # Try to find the course with the given slug
    course = Course.query.filter_by(course_slug=course_url).first()

    if course is None:
        # If the course is not found, check in the old slugs
        courses = Course.query.with_entities(Course.course_title, Course.course_old_slug).filter(Course.course_old_slug.isnot(None)).all()
        
        for course_title, course_old_slug in courses:
            # Split the old slug field into a list
            course_old_slug_list = course_old_slug.split('#')
            
            # Check if the provided course_url exists in the old slug list
            if course_url in course_old_slug_list:
                # If a match is found, get the course with the corresponding title
                course = Course.query.filter_by(course_title=course_title).first_or_404()
                return render_template('userend/course_details.html', course=course)

        # If no course is found, flash a message and redirect
        flash('Course not found.')
        return redirect(url_for('course_data'))
    
    # If the course is found with the current slug, render the page
    return render_template('userend/course_details.html', course=course)


@app.route('/course-data')
def course_data():
    if 'userrole' in session and session['userrole'] == 1:
        courses = db.session.query(Course, Subcategory).join(Subcategory).all()
        return render_template('adminend/coursedata.html', courses=courses)
    else:
        flash('You are not authorized to access this page.', 'error')
        return redirect(url_for('admin_login'))




@app.route('/simplifiedskill/login/google')
def google_login_signin():
    google = oauth.create_client('google')
    redirect_url = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_url)


# Google authorize route
@app.route('/simplifiedskill/login/google/callback')
def google_authorize():
    google = oauth.create_client('google')  # Reuse the OAuth client
    token = google.authorize_access_token()  # Retrieve the access token
    resp = google.get('userinfo').json()  # Use the token to fetch the user info
    # print(resp.keys())
    # Assuming 'sub' is the unique identifier for the user in Google's response
    data = Admin.query.filter_by(useremail = resp['email']).first()
    
    if not data:
        # If the user doesn't exist, create a new one
        count = db.session.query(Admin).count()
        if count == 0:
            admin = Admin(
                useremail = resp['email'],
                userrole = 1
            # Other fields...
            )
        # else:
        #     admin = Admin(
        #         useremail = resp['email'],
        #         userrole = 0
        #     # Other fields...
        #     )
            db.session.add(admin)
            db.session.commit()
            session['useremail'] = resp['email']
            session['userrole'] = 1
    else:
        session['useremail'] = data.useremail
        session['userrole'] = data.userrole
    # print('Check: ' ,user.username, '\n')   
    # login_user(user)
    

    return redirect(url_for('admin'))



class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    useremail = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Signup')


@app.route('/simplifiedskill/signup', methods=["GET", "POST"])
def admin_signup():
    if "useremail" in session and session['useremail'] == 'mdfarhansadiq01@gmail.com':
        flash('You are already logged in!')
        return redirect(url_for('admin'))
    
    form = SignupForm()

    if request.method == "POST":
        if form.validate_on_submit():
            # Extract data directly from the form object
            username = form.username.data
            useremail = form.useremail.data
            
            # Save data to the session
            session.permanent = True
            session['useremail'] = useremail
            
            # Redirect to the admin page
            
            return redirect(url_for("admin"))
        else:
            flash('Form validation failed. Please try again.')
    
    # Render the signup template with the form
    return render_template('adminend/signup.html', form=form)




class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    useremail = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Login')


@app.route('/simplifiedskill/login', methods=["GET", "POST"])
def admin_login():
    if "useremail" in session and session['useremail'] == 'mdfarhansadiq01@gmail.com':
        flash('You are already logged in!')
        return redirect(url_for('admin'))
    form = LoginForm()

    if request.method == "POST":
        if form.validate_on_submit():
            # Extract data directly from the form object
            username = form.username.data
            useremail = form.useremail.data
            
            # Save data to the session
            session.permanent = True
            session['useremail'] = useremail
            
            # Redirect to the admin page
            
            return redirect(url_for("admin"))
    return render_template('adminend/login.html', form=form)



@app.route('/admin_logout_signout')
def admin_logout_signout():
    session.pop('useremail', None)
    session.pop('userrole', None)
    return redirect(url_for('admin_login'))

# @app.route('/<uemail>')
# def user(uemail):
#     return f'Hello {uemail}!'


# @app.route('/admin')
# def admin():
#     return redirect(url_for('user', name='Admin!'))

# def drop_course_table():
#     with app.app_context():
#         # Create a MetaData object
#         meta = db.MetaData()
#         # Reflect the existing database into MetaData
#         meta.reflect(bind=db.engine)
#         # Access the 'course' table
#         course_table = meta.tables.get('course')
#         if course_table is not None:
#             # Drop the table if it exists
#             course_table.drop(bind=db.engine)
#             print("Course table dropped.")
#         else:
#             print("Course table does not exist.")


# def drop_course_batch_table():
#     with app.app_context():
#         # Create a MetaData object
#         meta = db.MetaData()
#         # Reflect the existing database into MetaData
#         meta.reflect(bind=db.engine)
#         # Access the 'course_batch' table
#         course_batch_table = meta.tables.get('course_batch')
#         if course_batch_table is not None:
#             # Drop the table if it exists
#             course_batch_table.drop(bind=db.engine)
#             print("CourseBatch table dropped.")
#         else:
#             print("CourseBatch table does not exist.")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # drop_course_batch_table()
    app.run(host='0.0.0.0', port=5000, debug=True)
