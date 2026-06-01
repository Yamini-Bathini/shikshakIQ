from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from models import StudentUser, Student, Result, ConceptMastery, Quiz, QuizQuestion, RemediationQuiz, Intervention, User, TeacherAssignment, Class, Subject
from extensions import db

student_portal_bp = Blueprint('student_portal', __name__)


@student_portal_bp.route('/api/student/login', methods=['POST'])
def student_login():
    """Student login to access their own progress"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip().lower()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        student_user = StudentUser.query.filter_by(username=username).first()
        if not student_user or not check_password_hash(student_user.password, password):
            return jsonify({'error': 'Invalid username or password'}), 401

        if not student_user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403

        student = Student.query.get(student_user.student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        student_user.last_login = datetime.utcnow()
        db.session.commit()

        # Get class and subject info
        class_obj = Class.query.get(student.class_id)
        assignments = TeacherAssignment.query.filter_by(class_id=student.class_id).all()

        subjects = []
        for a in assignments:
            subj = Subject.query.get(a.subject_id)
            if subj:
                subjects.append({
                    'assignment_id': a.id,
                    'subject_id': subj.id,
                    'subject_name': subj.name,
                    'teacher_name': User.query.get(a.teacher_id).name if User.query.get(a.teacher_id) else '',
                })

        # Calculate progress stats
        results = Result.query.filter_by(student_id=student.id).all()
        total_quizzes = len(results)
        avg_score = sum(r.percentage for r in results) / total_quizzes if total_quizzes > 0 else 0
        masteries = ConceptMastery.query.filter_by(student_id=student.id).all()
        avg_mastery = sum(m.mastery_level for m in masteries) / len(masteries) if masteries else 0

        access_token = create_access_token(
            identity=f'student_{student.id}',
            additional_claims={
                'student_id': student.id,
                'name': student.name,
                'role': 'student',
                'class_name': student.class_name
            }
        )

        return jsonify({
            'token': access_token,
            'student': {
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'class_name': student.class_name,
                'section': student.section,
                'parent_name': student.parent_name,
                'total_quizzes': total_quizzes,
                'average_score': round(avg_score, 2),
                'average_mastery': round(avg_mastery, 2),
                'subjects': subjects,
                'last_login': student_user.last_login.isoformat() if student_user.last_login else None,
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_portal_bp.route('/api/student/me', methods=['GET'])
@jwt_required()
def get_student_profile():
    """Get student's own profile and progress summary"""
    try:
        identity = get_jwt_identity()
        student_id = int(identity.replace('student_', ''))
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        results = Result.query.filter_by(student_id=student.id).order_by(Result.submitted_at.desc()).all()
        masteries = ConceptMastery.query.filter_by(student_id=student.id).all()

        # Recent results
        recent_results = []
        for r in results[:5]:
            recent_results.append({
                'id': r.id,
                'quiz_title': r.quiz.title if r.quiz else '',
                'subject': r.quiz.subject if r.quiz else '',
                'score': r.score,
                'total_marks': r.total_marks,
                'percentage': r.percentage,
                'submitted_at': r.submitted_at.isoformat() if r.submitted_at else '',
                'strengths': r.strengths,
                'weaknesses': r.weaknesses,
            })

        # Concept performance
        concept_performance = [{
            'concept': m.concept_name,
            'mastery_level': m.mastery_level,
            'attempts': m.attempts,
            'correct_attempts': m.correct_attempts,
            'last_updated': m.last_updated.isoformat() if m.last_updated else '',
        } for m in masteries]

        # Overall stats
        total_quizzes = len(results)
        avg_score = sum(r.percentage for r in results) / total_quizzes if total_quizzes > 0 else 0
        avg_mastery = sum(m.mastery_level for m in masteries) / len(masteries) if masteries else 0
        weak_concepts = [m.concept_name for m in masteries if m.mastery_level < 0.4]

        return jsonify({
            'student': student.to_dict(),
            'stats': {
                'total_quizzes': total_quizzes,
                'average_score': round(avg_score, 2),
                'average_mastery': round(avg_mastery, 2),
                'weak_concepts_count': len(weak_concepts),
                'strong_concepts_count': sum(1 for m in masteries if m.mastery_level >= 0.7),
            },
            'recent_results': recent_results,
            'concept_performance': sorted(concept_performance, key=lambda x: x['mastery_level']),
            'weak_concepts': weak_concepts[:10],
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_portal_bp.route('/api/student/progress', methods=['GET'])
@jwt_required()
def get_student_progress():
    """Detailed progress timeline and growth data"""
    try:
        identity = get_jwt_identity()
        student_id = int(identity.replace('student_', ''))
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        results = Result.query.filter_by(student_id=student.id).order_by(Result.submitted_at).all()
        masteries = ConceptMastery.query.filter_by(student_id=student.id).all()

        # Score timeline
        timeline = [{
            'date': r.submitted_at.strftime('%Y-%m-%d') if r.submitted_at else '',
            'score': r.score,
            'total_marks': r.total_marks,
            'percentage': r.percentage,
            'quiz_title': r.quiz.title if r.quiz else '',
            'subject': r.quiz.subject if r.quiz else '',
        } for r in results]

        # Mastery growth per concept
        concept_growth = {}
        for m in masteries:
            if m.concept_name not in concept_growth:
                concept_growth[m.concept_name] = []
            concept_growth[m.concept_name].append({
                'mastery': m.mastery_level,
                'date': m.last_updated.strftime('%Y-%m-%d') if m.last_updated else '',
            })

        # Subject-wise breakdown
        subject_performance = {}
        for r in results:
            subject = r.quiz.subject if r.quiz else 'General'
            if subject not in subject_performance:
                subject_performance[subject] = {'total': 0, 'count': 0, 'highest': 0, 'lowest': 100}
            subject_performance[subject]['total'] += r.percentage
            subject_performance[subject]['count'] += 1
            subject_performance[subject]['highest'] = max(subject_performance[subject]['highest'], r.percentage)
            subject_performance[subject]['lowest'] = min(subject_performance[subject]['lowest'], r.percentage)

        subject_breakdown = [{
            'subject': subj,
            'average': round(data['total'] / data['count'], 2),
            'quizzes': data['count'],
            'highest': data['highest'],
            'lowest': data['lowest'],
        } for subj, data in subject_performance.items()]

        # Improvement metrics
        improvement_rate = 0
        if len(timeline) >= 2:
            first_score = timeline[0]['percentage']
            last_score = timeline[-1]['percentage']
            improvement_rate = round((last_score - first_score) / len(timeline), 2)

        return jsonify({
            'timeline': timeline,
            'concept_growth': concept_growth,
            'subject_breakdown': subject_breakdown,
            'improvement_rate': improvement_rate,
            'total_quizzes': len(timeline),
            'current_average': round(sum(r.percentage for r in results) / len(results), 2) if results else 0,
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_portal_bp.route('/api/student/remediation-quizzes', methods=['GET'])
@jwt_required()
def get_student_remediation():
    """Get remediation quizzes assigned to the student"""
    try:
        identity = get_jwt_identity()
        student_id = int(identity.replace('student_', ''))
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        remediation_quizzes = RemediationQuiz.query.filter_by(student_id=student.id).order_by(RemediationQuiz.assigned_at.desc()).all()

        # Return remediation quizzes with their questions
        result_data = []
        for rq in remediation_quizzes:
            rq_data = rq.to_dict()
            # Fetch quiz questions if quiz exists
            quiz = Quiz.query.get(rq.quiz_id)
            if quiz:
                questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order_index).all()
                rq_data['questions'] = [q.to_dict() for q in questions]
                rq_data['quiz'] = quiz.to_dict()
            else:
                rq_data['questions'] = []
                rq_data['quiz'] = None
            result_data.append(rq_data)

        return jsonify({
            'remediation_quizzes': result_data,
            'pending_count': sum(1 for rq in remediation_quizzes if not rq.is_completed),
            'completed_count': sum(1 for rq in remediation_quizzes if rq.is_completed),
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@student_portal_bp.route('/api/student/remediation-quizzes/<int:rem_id>/complete', methods=['POST'])
@jwt_required()
def complete_remediation_quiz(rem_id):
    """Mark a remediation quiz as completed with score"""
    try:
        identity = get_jwt_identity()
        student_id = int(identity.replace('student_', ''))

        remediation_quiz = RemediationQuiz.query.filter_by(id=rem_id, student_id=student_id).first()
        if not remediation_quiz:
            return jsonify({'error': 'Remediation quiz not found'}), 404

        data = request.get_json() or {}
        score = data.get('score', 0)

        remediation_quiz.is_completed = True
        remediation_quiz.score = score
        remediation_quiz.completed_at = datetime.utcnow()

        # Update the associated intervention
        if remediation_quiz.intervention_id:
            intervention = Intervention.query.get(remediation_quiz.intervention_id)
            if intervention:
                intervention.status = 'completed'
                intervention.outcome_score_after = score
                intervention.completion_date = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': 'Remediation quiz completed',
            'remediation_quiz': remediation_quiz.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
