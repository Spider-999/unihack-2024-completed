from . import db
from flask_login import UserMixin, current_user
from datetime import datetime, timedelta
from random import randint


# Association tables for the many-to-many relationships
user_badge = db.Table('user_badge',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True)
)

user_quest = db.Table('user_quest',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('quest_id', db.Integer, db.ForeignKey('quest.id'), primary_key=True),
    db.Column('completed', db.Boolean, default=False)
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    user_role = db.Column(db.String(10), nullable=False)
    date_joined = db.Column(db.DateTime(), nullable=False, default=datetime.now())
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    streak = db.Column(db.Integer(), default = 0)
    correct_answers = db.Column(db.Integer, default = 0)
    level = db.Column(db.Integer, default = 0)
    experience = db.Column(db.Integer, default = 0)


    # Daily data specifically needed for quests
    daily_correct_answers = db.Column(db.Integer, default = 0)
    daily_lessons = db.Column(db.Integer, default = 0)
    daily_experience = db.Column(db.Integer, default = 0)


    # Set time to yesterday for newly created user for last exercise solved
    last_exercise = db.Column(db.DateTime(), nullable=True, default=datetime.now() - timedelta(1))
    quest_time = db.Column(db.DateTime(), nullable=False, default=datetime.now() - timedelta(1))

    # backref -> use the author to get the user who created the post
    # lazy -> load the data in one go from the db
    posts = db.relationship('Post', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    questions = db.relationship('Question', backref='user')
    badges = db.relationship('Badge', secondary=user_badge, back_populates='users')
    quests = db.relationship('Quest', secondary=user_quest, back_populates='users')


    def update_streak(self):
        today = datetime.now()
        
        # If user has already completed an exercise don't update the streak again
        if self.last_exercise.date() == today.date():
            return
        
        if (today - self.last_exercise).total_seconds() / 3600 < 25:
            self.streak += 1
        else:
            self.streak = 0

        self.last_exercise = today
        db.session.commit()


    def award_badge(self):
        if current_user.correct_answers == 1:
            badge = Badge.query.filter_by(name="Primul Exercitiu").first()
            if badge not in current_user.badges:
                current_user.badges.append(badge)
                db.session.commit()
        if current_user.streak == 1:
            badge = Badge.query.filter_by(name="Prima Zi").first()
            if badge not in current_user.badges:
                current_user.badges.append(badge)
                db.session.commit()


    def set_daily_quests(self):
        if (datetime.now() - current_user.quest_time).total_seconds() / 3600 >= 24:
            quest = Quest.query.all()
            for i in range(0, 3):
                current_user.quests.append(quest[i])
                db.session.commit()
            current_user.daily_correct_answers = 0
            current_user.daily_lessons = 0
            current_user.daily_experience = 0
            current_user.quest_time = datetime.now()
            db.session.commit()

    
    def check_quests(self):
        for quest in self.quests:
            completed = db.session.query(user_quest.c.completed).filter_by(
                user_id=self.id,
                quest_id=quest.id
            ).scalar()

            if completed:
                continue

            if quest.quest_type == 1 and self.daily_experience >= int(quest.quest_requirement):
                self.daily_experience += quest.experience
                self.experience += quest.experience
                db.session.execute(user_quest.update().where(
                    user_quest.c.user_id == self.id,
                    user_quest.c.quest_id == quest.id
                ).values(completed=True))
            elif quest.quest_type == 2 and self.daily_correct_answers >= int(quest.quest_requirement):
                self.experience += quest.experience
                db.session.execute(user_quest.update().where(
                    user_quest.c.user_id == self.id,
                    user_quest.c.quest_id == quest.id
                ).values(completed=True))

        db.session.commit()


    def get_quests(self):
        user_quests = []
        for quest in current_user.quests:
            completed = db.session.query(user_quest.c.completed).filter_by(
                user_id=current_user.id,
                quest_id=quest.id
            ).scalar()

            user_quests.append({
                'id': quest.id,
                'description': quest.description,
                'experience': quest.experience,
                'quest_requirement': quest.quest_requirement,
                'quest_type': quest.quest_type,
                'completed': completed
            })
        return user_quests

    
    def level_up(self):
        if current_user.level == 0 and current_user.experience >= 10:
            current_user.level = 1
            current_user.experience -= 10
            db.session.commit()
        if current_user.level >= 1 and current_user.level <= 5 and current_user.experience >= 30:
            current_user.level += 1
            current_user.experience -= 30
            db.session.commit()
    

    def get_leaderboard_answers(self):
        return User.query.order_by(User.correct_answers.desc()).all()
    
    def get_leaderboard_days(self):
        return User.query.order_by(User.streak.desc()).all()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), nullable=False)
    date_posted = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now())
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(32), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan', lazy='dynamic')


    def get_comments(self):
        return Comment.query.filter_by(post_id=Post.id).order_by(Comment.time_posted)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    time_posted = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now())
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable = False, unique = True)
    lessons = db.relationship('Lesson', backref='grade', lazy=True)


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    grade_id = db.Column(db.Integer, db.ForeignKey('grade.id'), nullable=False)
    questions = db.relationship('Question', backref='lesson', lazy=True)
    themes = db.relationship('Theme', backref='lesson', lazy=True)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(256), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    answer = db.Column(db.String(128), nullable = True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(128), nullable=False)
    image_file = db.Column(db.String(64), nullable=False, default='profile_pics/default.jpg')
    users = db.relationship('User', secondary=user_badge, back_populates='badges')
    

class Quest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    quest_requirement = db.Column(db.String, nullable=False)
    quest_type = db.Column(db.Integer, nullable=False)
    users = db.relationship('User', secondary=user_quest, back_populates='quests')


class Theme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    content = db.Column(db.String(4096), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
