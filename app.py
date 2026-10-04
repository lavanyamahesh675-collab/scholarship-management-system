import os
import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'scholarship_portal_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scholarship.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    income = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'course': self.course,
            'year': self.year,
            'income': self.income,
            'formatted_income': f"₹{self.income:,.2f}"
        }

class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    provider = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    deadline = db.Column(db.String(50), nullable=False)
    eligibility = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'provider': self.provider,
            'amount': self.amount,
            'formatted_amount': f"₹{self.amount:,.2f}",
            'deadline': self.deadline,
            'eligibility': self.eligibility
        }

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'), nullable=False)
    date_submitted = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Approved, Rejected

    student = db.relationship('Student', backref=db.backref('applications', lazy=True))
    scholarship = db.relationship('Scholarship', backref=db.backref('applications', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else 'Unknown',
            'scholarship_id': self.scholarship_id,
            'scholarship_title': self.scholarship.title if self.scholarship else 'Unknown',
            'date_submitted': self.date_submitted,
            'status': self.status
        }

def init_db():
    with app.app_context():
        db.create_all()
        # Seed initial data if empty
        if Student.query.count() == 0:
            student1 = Student(
                id=1,
                name="Rahul Kumar",
                email="rahul@example.com",
                phone="9876543210",
                course="B.Tech CSE",
                year="Year 2",
                income=180000.00
            )
            student2 = Student(
                id=2,
                name="Ananya Reddy",
                email="ananya@example.com",
                phone="9123456789",
                course="B.Tech ECE",
                year="Year 3",
                income=220000.00
            )
            db.session.add_all([student1, student2])

            sch1 = Scholarship(
                id=1,
                title="Merit Scholarship",
                provider="ABC Foundation",
                amount=25000.00,
                deadline="31 Dec 2026",
                eligibility="Academic Excellence > 8.5 CGPA"
            )
            sch2 = Scholarship(
                id=2,
                title="Need Based Scholarship",
                provider="Global Edu Trust",
                amount=40000.00,
                deadline="15 Nov 2026",
                eligibility="Family Income < ₹2,50,000/year"
            )
            db.session.add_all([sch1, sch2])
            db.session.commit()

            app1 = Application(
                id=1,
                student_id=1,
                scholarship_id=1,
                date_submitted="2 Oct 2026",
                status="Pending"
            )
            app2 = Application(
                id=2,
                student_id=2,
                scholarship_id=2,
                date_submitted="2 Oct 2026",
                status="Approved"
            )
            db.session.add_all([app1, app2])
            db.session.commit()

# Serve static files including campus_bg.jpg
@app.route('/campus_bg.jpg')
def serve_campus_bg():
    return send_from_directory('.', 'campus_bg.jpg')

# Page Routes
@app.route('/')
def index():
    return render_template('index.html')

# API Endpoints
@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_students = Student.query.count()
    total_scholarships = Scholarship.query.count()
    total_applications = Application.query.count()
    pending = Application.query.filter_by(status='Pending').count()
    approved = Application.query.filter_by(status='Approved').count()
    rejected = Application.query.filter_by(status='Rejected').count()

    return jsonify({
        'total_students': total_students,
        'total_scholarships': total_scholarships,
        'total_applications': total_applications,
        'pending': pending,
        'approved': approved,
        'rejected': rejected
    })

# Students API
@app.route('/api/students', methods=['GET', 'POST'])
def api_students():
    if request.method == 'GET':
        students = Student.query.order_by(Student.id.desc()).all()
        return jsonify([s.to_dict() for s in students])
    elif request.method == 'POST':
        data = request.json
        new_student = Student(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            course=data['course'],
            year=data['year'],
            income=float(data['income'])
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify(new_student.to_dict()), 201

@app.route('/api/students/<int:student_id>', methods=['PUT', 'DELETE'])
def api_student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'PUT':
        data = request.json
        student.name = data.get('name', student.name)
        student.email = data.get('email', student.email)
        student.phone = data.get('phone', student.phone)
        student.course = data.get('course', student.course)
        student.year = data.get('year', student.year)
        student.income = float(data.get('income', student.income))
        db.session.commit()
        return jsonify(student.to_dict())
    elif request.method == 'DELETE':
        # Remove related applications first
        Application.query.filter_by(student_id=student_id).delete()
        db.session.delete(student)
        db.session.commit()
        return jsonify({'message': 'Student deleted successfully'})

# Scholarships API
@app.route('/api/scholarships', methods=['GET', 'POST'])
def api_scholarships():
    if request.method == 'GET':
        scholarships = Scholarship.query.all()
        return jsonify([s.to_dict() for s in scholarships])
    elif request.method == 'POST':
        data = request.json
        new_sch = Scholarship(
            title=data['title'],
            provider=data['provider'],
            amount=float(data['amount']),
            deadline=data['deadline'],
            eligibility=data.get('eligibility', 'Open to all')
        )
        db.session.add(new_sch)
        db.session.commit()
        return jsonify(new_sch.to_dict()), 201

@app.route('/api/scholarships/<int:sch_id>', methods=['PUT', 'DELETE'])
def api_scholarship_detail(sch_id):
    sch = Scholarship.query.get_or_404(sch_id)
    if request.method == 'PUT':
        data = request.json
        sch.title = data.get('title', sch.title)
        sch.provider = data.get('provider', sch.provider)
        sch.amount = float(data.get('amount', sch.amount))
        sch.deadline = data.get('deadline', sch.deadline)
        sch.eligibility = data.get('eligibility', sch.eligibility)
        db.session.commit()
        return jsonify(sch.to_dict())
    elif request.method == 'DELETE':
        Application.query.filter_by(scholarship_id=sch_id).delete()
        db.session.delete(sch)
        db.session.commit()
        return jsonify({'message': 'Scholarship deleted successfully'})

# Applications API
@app.route('/api/applications', methods=['GET', 'POST'])
def api_applications():
    if request.method == 'GET':
        apps = Application.query.order_by(Application.id.asc()).all()
        return jsonify([a.to_dict() for a in apps])
    elif request.method == 'POST':
        data = request.json
        today_str = datetime.datetime.now().strftime("%d %b %Y")
        new_app = Application(
            student_id=int(data['student_id']),
            scholarship_id=int(data['scholarship_id']),
            date_submitted=data.get('date_submitted', today_str),
            status=data.get('status', 'Pending')
        )
        db.session.add(new_app)
        db.session.commit()
        return jsonify(new_app.to_dict()), 201

@app.route('/api/applications/<int:app_id>', methods=['PUT', 'DELETE'])
def api_application_detail(app_id):
    app_obj = Application.query.get_or_404(app_id)
    if request.method == 'PUT':
        data = request.json
        if 'status' in data:
            app_obj.status = data['status']
        db.session.commit()
        return jsonify(app_obj.to_dict())
    elif request.method == 'DELETE':
        db.session.delete(app_obj)
        db.session.commit()
        return jsonify({'message': 'Application deleted successfully'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
