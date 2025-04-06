import uuid
import hashlib
import datetime
import sqlite3
import json
from config import DATABASE_PATH

class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        # Users
        cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, email TEXT UNIQUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP)')
        # Skills
        cursor.execute('CREATE TABLE IF NOT EXISTS skills (skill_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, category TEXT)')
        # Content Pieces
        cursor.execute('CREATE TABLE IF NOT EXISTS content_pieces (content_id TEXT PRIMARY KEY, title TEXT, original_text TEXT, structured_description TEXT, source TEXT, topic TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        # Content-skill mapping
        cursor.execute('''CREATE TABLE IF NOT EXISTS content_skills (content_id TEXT, skill_id INTEGER, relevance REAL, PRIMARY KEY (content_id, skill_id), FOREIGN KEY (content_id) REFERENCES content_pieces(content_id) ON DELETE CASCADE, FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE)''')
        # User Interactions
        cursor.execute('''CREATE TABLE IF NOT EXISTS interactions (interaction_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, content_id TEXT NOT NULL, interaction_type TEXT, feedback_rating REAL, feedback_comment TEXT, score REAL, time_spent INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE, FOREIGN KEY (content_id) REFERENCES content_pieces(content_id) ON DELETE CASCADE)''')
        # User skill proficiency
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_skills (user_id TEXT NOT NULL, skill_id INTEGER NOT NULL, proficiency REAL DEFAULT 0.0, practice_count INTEGER DEFAULT 0, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, skill_id), FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE, FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE)''')
        # User preferences
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_preferences (user_id TEXT PRIMARY KEY, adaptlearn_profile JSON, theme TEXT DEFAULT 'dark', last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE)''')
        # Learning paths
        cursor.execute('''CREATE TABLE IF NOT EXISTS learning_paths (path_id TEXT PRIMARY KEY, user_id TEXT, title TEXT NOT NULL, description TEXT, focus_skills TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE)''')
        # Learning path items
        cursor.execute('''CREATE TABLE IF NOT EXISTS learning_path_items (path_id TEXT NOT NULL, content_id TEXT NOT NULL, position INTEGER NOT NULL, PRIMARY KEY (path_id, content_id), FOREIGN KEY (path_id) REFERENCES learning_paths(path_id) ON DELETE CASCADE, FOREIGN KEY (content_id) REFERENCES content_pieces(content_id) ON DELETE CASCADE)''')
        
        # QUIZ TABLES
        # Quiz metadata table
        cursor.execute('''CREATE TABLE IF NOT EXISTS quizzes (
            quiz_id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT NOT NULL,
            description TEXT,
            topic TEXT,
            difficulty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE)''')
        
        # Quiz questions table
        cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_questions (
            question_id TEXT PRIMARY KEY,
            quiz_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            question_type TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            adaptation_type TEXT,
            skill_id INTEGER,
            position INTEGER NOT NULL,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE SET NULL)''')
        
        # Quiz attempts table
        cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_attempts (
            attempt_id TEXT PRIMARY KEY,
            quiz_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            score REAL,
            max_score REAL,
            completed BOOLEAN DEFAULT 0,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE)''')
        
        # Quiz question responses
        cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_responses (
            response_id TEXT PRIMARY KEY,
            attempt_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            user_answer TEXT,
            is_correct BOOLEAN,
            time_taken INTEGER,
            FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(attempt_id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES quiz_questions(question_id) ON DELETE CASCADE)''')
        
        # Populate initial common skills
        skills=[("Main Idea","comprehension"),("Sequencing","comprehension"),("Cause/Effect","comprehension"),("Compare/Contrast","comprehension"),("Problem Solving","logic"),("Vocabulary","language"),("Sentence Structure","language"),("Paragraph Structure","language"),("Arithmetic","math"),("Fractions","math"),("Percentages","math"),("Algebra","math"),("Geometry","math"),("Sci Method","science"),("Photosynthesis","biology"),("Newton Laws","physics"),("Arrays/Lists","programming"),("Loops","programming"),("Conditionals","programming"),("Functions","programming"),("OOP","programming"),("Data Structures","programming"),("Algorithms","programming"),("String Ops","programming"),("Recursion","programming")]
        for name, cat in skills:
            cursor.execute('INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)', (name, cat))
        self.conn.commit()
        
    def close(self):
        if self.conn:
            self.conn.close()
            
    # --- User Methods ---
    def create_user(self, username, password, email=None):
        uid=str(uuid.uuid4())
        p_hash=hashlib.sha256(password.encode()).hexdigest()
        now=datetime.datetime.now().isoformat()
        cur=self.conn.cursor()
        try:
            cur.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)', (uid, username, p_hash, email, now, now))
            d_prof=json.dumps({"learning_style": "Visual", "disability_type": "None", "preferences": {"font_size": 12, "contrast": "Standard", "chunk_size": 200}})
            cur.execute('INSERT INTO user_preferences (user_id, adaptlearn_profile) VALUES (?, ?)', (uid, d_prof))
            self.conn.commit()
            return uid
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return None
            
    def authenticate_user(self, username, password):
        p_hash=hashlib.sha256(password.encode()).hexdigest()
        cur=self.conn.cursor()
        cur.execute('SELECT user_id FROM users WHERE username=? AND password_hash=?', (username, p_hash))
        user=cur.fetchone()
        if user:
            now=datetime.datetime.now().isoformat()
            cur.execute('UPDATE users SET last_login=? WHERE user_id=?', (now, user[0]))
            self.conn.commit()
            return user[0]
        return None
        
    def get_user_profile(self, user_id):
        cur=self.conn.cursor()
        cur.execute('SELECT adaptlearn_profile FROM user_preferences WHERE user_id = ?', (user_id,))
        res=cur.fetchone()
        d_prof = {"learning_style": "Visual", "disability_type": "None", "preferences": {"font_size": 12, "contrast": "Standard", "chunk_size": 200}}
        if res and res[0]:
            try:
                p=json.loads(res[0])
                p.setdefault("learning_style", d_prof["learning_style"])
                p.setdefault("disability_type", d_prof["disability_type"])
                pr=p.setdefault("preferences", {})
                pr.setdefault("font_size", d_prof["preferences"]["font_size"])
                pr.setdefault("contrast", d_prof["preferences"]["contrast"])
                pr.setdefault("chunk_size", d_prof["preferences"]["chunk_size"])
                return p
            except json.JSONDecodeError:
                return d_prof
        return d_prof
        
    def save_user_profile(self, user_id, profile_dict):
        cur=self.conn.cursor()
        p_json=json.dumps(profile_dict)
        now=datetime.datetime.now().isoformat()
        cur.execute('INSERT OR REPLACE INTO user_preferences (user_id, adaptlearn_profile, last_updated) VALUES (?, ?, ?)', (user_id, p_json, now))
        self.conn.commit()
        
    # --- Content Methods ---
    def store_content_piece(self, title, original_text, structured_description, source='pasted', topic=None):
        cid=str(uuid.uuid4())
        cur=self.conn.cursor()
        cur.execute('INSERT INTO content_pieces VALUES (?, ?, ?, ?, ?, ?, ?)', (cid, title, original_text, structured_description, source, topic, datetime.datetime.now().isoformat()))
        self.conn.commit()
        return cid
        
    def get_content_piece(self, content_id):
        cur=self.conn.cursor()
        cur.execute('SELECT title, original_text, structured_description, source, topic, created_at FROM content_pieces WHERE content_id=?', (content_id,))
        return cur.fetchone()
        
    # --- Skill Methods ---
    def map_content_skills(self, content_id, skill_relevance):
        cur=self.conn.cursor()
        for name, rel in skill_relevance.items():
            cur.execute('SELECT skill_id FROM skills WHERE name = ?', (name,))
            res=cur.fetchone()
            sid=None
            if not res:
                cat = "general"  # Basic category guessing
                if any(kw in name.lower() for kw in ["math", "algebra", "calc", "geom"]):
                    cat = "math"
                elif any(kw in name.lower() for kw in ["program", "code", "data", "algo", "loop", "func"]):
                    cat = "programming"
                elif any(kw in name.lower() for kw in ["comprehen", "read", "idea", "seq", "summar"]):
                    cat = "comprehension"
                try:
                    cur.execute('INSERT INTO skills (name, category) VALUES (?, ?)', (name, cat))
                    sid = cur.lastrowid
                except sqlite3.IntegrityError:
                    cur.execute('SELECT skill_id FROM skills WHERE name = ?', (name,))
                    sid = cur.fetchone()[0]
            else:
                sid = res[0]
            if sid is not None:
                cur.execute('INSERT OR REPLACE INTO content_skills VALUES (?, ?, ?)',(content_id, sid, rel))
        try:
            self.conn.commit()
        except Exception as e:
            print(f"Error committing skills: {e}")
            self.conn.rollback()
            
    def update_user_skills(self, user_id, content_id, score):
        if score is None or not (0.0<=score<=1.0):
            return
        cur=self.conn.cursor()
        cur.execute('SELECT skill_id, relevance FROM content_skills WHERE content_id=?', (content_id,))
        skills=cur.fetchall()
        rate=0.15
        updated=[]
        for sid, rel in skills:
            cur.execute('SELECT proficiency, practice_count FROM user_skills WHERE user_id=? AND skill_id=?', (user_id, sid))
            res=cur.fetchone()
            cur_p, pc = (res[0], res[1]) if res else (0.0, 0)
            upd_f=(score-0.5)*2
            p_chg=upd_f*rel*rate
            new_p=max(0.0, min(1.0, cur_p+p_chg))
            new_pc=pc+1
            now=datetime.datetime.now().isoformat()
            cur.execute('INSERT INTO user_skills VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id, skill_id) DO UPDATE SET proficiency=excluded.proficiency, practice_count=excluded.practice_count, last_updated=excluded.last_updated', (user_id, sid, new_p, new_pc, now))
            updated.append(sid)
        if updated:
            try:
                self.conn.commit()
            except Exception as e:
                print(f"Error committing skill update: {e}")
                self.conn.rollback()
                
    def get_user_skills(self, user_id):
        cur=self.conn.cursor()
        cur.execute('SELECT s.skill_id, s.name, s.category, COALESCE(us.proficiency, 0) p, COALESCE(us.practice_count, 0) pc FROM skills s LEFT JOIN user_skills us ON s.skill_id = us.skill_id AND us.user_id = ? ORDER BY s.category, p DESC', (user_id,))
        return cur.fetchall()
        
    def get_user_weakest_skills(self, user_id, limit=5):
        cur=self.conn.cursor()
        cur.execute('SELECT s.skill_id, s.name, s.category, us.proficiency FROM user_skills us JOIN skills s ON us.skill_id = s.skill_id WHERE us.user_id=? AND us.practice_count > 0 ORDER BY us.proficiency ASC LIMIT ?', (user_id, limit))
        return cur.fetchall()
        
    def get_user_strongest_skills(self, user_id, limit=5):
        cur=self.conn.cursor()
        cur.execute('SELECT s.skill_id, s.name, s.category, us.proficiency FROM user_skills us JOIN skills s ON us.skill_id = s.skill_id WHERE us.user_id=? ORDER BY us.proficiency DESC LIMIT ?', (user_id, limit))
        return cur.fetchall()
        
    # --- Interaction Methods ---
    def store_interaction(self, user_id, content_id, interaction_type, time_spent, feedback_rating=None, feedback_comment=None):
        iid=str(uuid.uuid4())
        score=max(0.0, min(1.0, (feedback_rating-1)/4.0)) if interaction_type=='feedback' and feedback_rating is not None else None
        cur=self.conn.cursor()
        cur.execute('INSERT INTO interactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',(iid, user_id, content_id, interaction_type, feedback_rating, feedback_comment, score, time_spent, datetime.datetime.now().isoformat()))
        self.conn.commit()
        if score is not None:
            self.update_user_skills(user_id, content_id, score)
        return iid
        
    def get_user_recent_interactions(self, user_id, limit=10):
        cur=self.conn.cursor()
        cur.execute('SELECT i.created_at, cp.title, i.interaction_type, i.feedback_rating, i.score FROM interactions i JOIN content_pieces cp ON i.content_id = cp.content_id WHERE i.user_id=? ORDER BY i.created_at DESC LIMIT ?', (user_id, limit))
        return cur.fetchall()
        
    def get_user_progress_stats(self, user_id):
        cur=self.conn.cursor()
        cur.execute('SELECT COUNT(*) t, COUNT(DISTINCT content_id) c, AVG(score) a, SUM(CASE WHEN feedback_rating >= 4 THEN 1 ELSE 0 END) p FROM interactions WHERE user_id=? AND score IS NOT NULL', (user_id,))
        s=cur.fetchone()
        return {'total_interactions': s[0] or 0, 'content_pieces_interacted': s[1] or 0, 'average_score': s[2] if s and s[2] is not None else 0.0, 'positive_feedback_count': s[3] or 0}
        
    # --- Learning Path Methods ---
    def create_learning_path(self, user_id, title, description, focus_skills_str):
        pid=str(uuid.uuid4())
        cur=self.conn.cursor()
        cur.execute('INSERT INTO learning_paths VALUES (?, ?, ?, ?, ?, ?)', (pid, user_id, title, description, focus_skills_str, datetime.datetime.now().isoformat()))
        self.conn.commit()
        return pid
        
    def add_content_to_path(self, path_id, content_id, position):
        cur=self.conn.cursor()
        cur.execute('INSERT OR REPLACE INTO learning_path_items VALUES (?, ?, ?)', (path_id, content_id, position))
        self.conn.commit()
        
    def get_learning_paths_for_user(self, user_id):
        cur=self.conn.cursor()
        cur.execute('SELECT path_id, title, description, focus_skills, created_at FROM learning_paths WHERE user_id=? ORDER BY created_at DESC', (user_id,))
        return cur.fetchall()
        
    def get_learning_path_content(self, path_id):
        cur=self.conn.cursor()
        cur.execute('SELECT cp.content_id, cp.title, cp.original_text, cp.topic FROM learning_path_items lpi JOIN content_pieces cp ON lpi.content_id=cp.content_id WHERE lpi.path_id=? ORDER BY lpi.position ASC', (path_id,))
        return cur.fetchall()
        
    def get_recommended_content(self, user_id, limit=5):
        cur=self.conn.cursor()
        weak=self.get_user_weakest_skills(user_id, 3)
        if not weak:
            return []
        w_ids=[s[0] for s in weak]
        ph=', '.join(['?' for _ in w_ids])
        cur.execute(f'SELECT DISTINCT cp.content_id, cp.title, cp.original_text, cp.topic FROM content_pieces cp JOIN content_skills cs ON cp.content_id=cs.content_id WHERE cs.skill_id IN ({ph}) AND cp.content_id NOT IN (SELECT content_id FROM interactions WHERE user_id=?) ORDER BY RANDOM() LIMIT ?', (*w_ids, user_id, limit))
        return cur.fetchall()
    
    # --- Quiz Methods ---
    def create_quiz(self, user_id, title, description, topic, difficulty="Medium"):
        """Create a new quiz."""
        quiz_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        
        # FIXED: Ensure all parameters are string type to avoid SQLite errors
        user_id = str(user_id)
        title = str(title)
        description = str(description)
        topic = str(topic)
        difficulty = str(difficulty)
        timestamp = datetime.datetime.now().isoformat()
        
        try:
            cur.execute('INSERT INTO quizzes VALUES (?, ?, ?, ?, ?, ?, ?)', 
                        (quiz_id, user_id, title, description, topic, difficulty, timestamp))
            self.conn.commit()
            return quiz_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error in create_quiz: {e}, types: {[type(x) for x in [quiz_id, user_id, title, description, topic, difficulty, timestamp]]}")
            raise
    
    def add_quiz_question(self, quiz_id, question_text, question_type, correct_answer, 
                         options=None, explanation=None, adaptation_type=None, 
                         skill_id=None, position=0):
        """Add a question to a quiz."""
        question_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        
        # Convert options list to JSON if provided
        options_json = json.dumps(options) if options else None
        
        cur.execute('''INSERT INTO quiz_questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (question_id, quiz_id, question_text, question_type, options_json, 
                     correct_answer, explanation, adaptation_type, skill_id, position))
        self.conn.commit()
        return question_id
    
    def get_quiz(self, quiz_id):
        """Get quiz metadata."""
        cur = self.conn.cursor()
        cur.execute('SELECT quiz_id, user_id, title, description, topic, difficulty, created_at FROM quizzes WHERE quiz_id = ?', (quiz_id,))
        return cur.fetchone()
    
    def get_quiz_questions(self, quiz_id):
        """Get all questions for a quiz."""
        cur = self.conn.cursor()
        cur.execute('''SELECT question_id, question_text, question_type, options, 
                    correct_answer, explanation, adaptation_type, skill_id, position
                    FROM quiz_questions 
                    WHERE quiz_id = ? 
                    ORDER BY position''', (quiz_id,))
        
        questions = []
        for row in cur.fetchall():
            question = {
                'question_id': row[0],
                'question_text': row[1],
                'question_type': row[2],
                'options': json.loads(row[3]) if row[3] else None,
                'correct_answer': row[4],
                'explanation': row[5],
                'adaptation_type': row[6],
                'skill_id': row[7],
                'position': row[8]
            }
            questions.append(question)
        
        return questions
    
    def start_quiz_attempt(self, quiz_id, user_id):
        """Start a new quiz attempt."""
        attempt_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # Get number of questions to set max_score
        cur.execute('SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = ?', (quiz_id,))
        max_score = cur.fetchone()[0]
        
        cur.execute('''INSERT INTO quiz_attempts 
                    (attempt_id, quiz_id, user_id, score, max_score, start_time) 
                    VALUES (?, ?, ?, ?, ?, ?)''', 
                    (attempt_id, quiz_id, user_id, 0, max_score, now))
        self.conn.commit()
        return attempt_id
    
    def record_question_response(self, attempt_id, question_id, user_answer, is_correct, time_taken):
        """Record a user's response to a quiz question."""
        response_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        
        # Convert user_answer to string if it's not already
        if not isinstance(user_answer, str):
            user_answer = str(user_answer)
        
        cur.execute('''INSERT INTO quiz_responses 
                    (response_id, attempt_id, question_id, user_answer, is_correct, time_taken) 
                    VALUES (?, ?, ?, ?, ?, ?)''', 
                    (response_id, attempt_id, question_id, user_answer, 
                     1 if is_correct else 0, time_taken))
        
        # Update the attempt score
        cur.execute('''UPDATE quiz_attempts 
                    SET score = (SELECT COUNT(*) FROM quiz_responses 
                                WHERE attempt_id = ? AND is_correct = 1) 
                    WHERE attempt_id = ?''', (attempt_id, attempt_id))
        
        self.conn.commit()
        return response_id
    
    def complete_quiz_attempt(self, attempt_id):
        """Mark a quiz attempt as completed."""
        cur = self.conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        cur.execute('''UPDATE quiz_attempts 
                    SET completed = 1, end_time = ? 
                    WHERE attempt_id = ?''', (now, attempt_id))
        
        # Get final score and quiz_id
        cur.execute('''SELECT quiz_id, user_id, score, max_score 
                    FROM quiz_attempts WHERE attempt_id = ?''', (attempt_id,))
        quiz_id, user_id, score, max_score = cur.fetchone()
        
        # Update user skills based on results
        if max_score > 0:
            success_rate = score / max_score
            
            # Get associated skills for this quiz
            cur.execute('''SELECT DISTINCT qq.skill_id 
                        FROM quiz_questions qq 
                        WHERE qq.quiz_id = ? AND qq.skill_id IS NOT NULL''', (quiz_id,))
            
            skill_ids = [row[0] for row in cur.fetchall()]
            
            # Update each skill
            for skill_id in skill_ids:
                # Get current skill level
                cur.execute('''SELECT proficiency, practice_count 
                            FROM user_skills 
                            WHERE user_id = ? AND skill_id = ?''', (user_id, skill_id))
                
                result = cur.fetchone()
                if result:
                    current_prof, practice_count = result
                else:
                    current_prof, practice_count = 0.0, 0
                
                # Adjust skill based on quiz performance
                # Success rate above 0.5 increases skill, below decreases
                adjustment = (success_rate - 0.5) * 0.2  # 20% maximum adjustment
                new_prof = max(0.0, min(1.0, current_prof + adjustment))
                new_count = practice_count + 1
                
                # Update or insert
                now = datetime.datetime.now().isoformat()
                cur.execute('''INSERT INTO user_skills 
                            VALUES (?, ?, ?, ?, ?) 
                            ON CONFLICT(user_id, skill_id) 
                            DO UPDATE SET proficiency=excluded.proficiency, 
                            practice_count=excluded.practice_count, 
                            last_updated=excluded.last_updated''', 
                            (user_id, skill_id, new_prof, new_count, now))
        
        self.conn.commit()
        return score, max_score
    
    def get_quiz_attempt_results(self, attempt_id):
        """Get detailed results for a quiz attempt."""
        cur = self.conn.cursor()
        
        # Get attempt info
        cur.execute('''SELECT qa.quiz_id, q.title, qa.score, qa.max_score, 
                    qa.start_time, qa.end_time, qa.completed 
                    FROM quiz_attempts qa 
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id 
                    WHERE qa.attempt_id = ?''', (attempt_id,))
        
        attempt = cur.fetchone()
        if not attempt:
            return None
        
        quiz_id, title, score, max_score, start_time, end_time, completed = attempt
        
        # Get question responses
        cur.execute('''SELECT qr.question_id, qq.question_text, qq.question_type, 
                    qq.options, qq.correct_answer, qr.user_answer, qr.is_correct, 
                    qq.explanation, qr.time_taken
                    FROM quiz_responses qr
                    JOIN quiz_questions qq ON qr.question_id = qq.question_id
                    WHERE qr.attempt_id = ?
                    ORDER BY qq.position''', (attempt_id,))
        
        questions = []
        for row in cur.fetchall():
            question = {
                'question_id': row[0],
                'question_text': row[1],
                'question_type': row[2],
                'options': json.loads(row[3]) if row[3] else None,
                'correct_answer': row[4],
                'user_answer': row[5],
                'is_correct': bool(row[6]),
                'explanation': row[7],
                'time_taken': row[8]
            }
            questions.append(question)
        
        # Calculate success rate
        success_rate = score / max_score if max_score > 0 else 0
        
        return {
            'quiz_id': quiz_id,
            'title': title,
            'score': score,
            'max_score': max_score,
            'success_rate': success_rate,
            'start_time': start_time,
            'end_time': end_time,
            'completed': bool(completed),
            'questions': questions
        }
    
    def get_user_quizzes(self, user_id, limit=10):
        """Get quizzes created by a user."""
        cur = self.conn.cursor()
        cur.execute('''SELECT quiz_id, title, description, topic, difficulty, created_at
                    FROM quizzes
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?''', (user_id, limit))
        
        quizzes = []
        for row in cur.fetchall():
            quiz = {
                'quiz_id': row[0],
                'title': row[1],
                'description': row[2],
                'topic': row[3],
                'difficulty': row[4],
                'created_at': row[5]
            }
            quizzes.append(quiz)
        
        return quizzes
    
    def get_user_quiz_attempts(self, user_id, limit=10):
        """Get quiz attempts by a user."""
        cur = self.conn.cursor()
        cur.execute('''SELECT qa.attempt_id, q.quiz_id, q.title, qa.score, 
                    qa.max_score, qa.completed, qa.start_time, qa.end_time
                    FROM quiz_attempts qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    WHERE qa.user_id = ?
                    ORDER BY qa.start_time DESC
                    LIMIT ?''', (user_id, limit))
        
        attempts = []
        for row in cur.fetchall():
            attempt = {
                'attempt_id': row[0],
                'quiz_id': row[1],
                'title': row[2],
                'score': row[3],
                'max_score': row[4],
                'completed': bool(row[5]),
                'success_rate': row[3] / row[4] if row[4] > 0 else 0,
                'start_time': row[6],
                'end_time': row[7]
            }
            attempts.append(attempt)
        
        return attempts
    
    def get_recommended_quizzes(self, user_id, limit=5):
        """Get quizzes recommended for a user based on skill needs."""
        cur = self.conn.cursor()
        
        # Get user's weak skills
        weak_skills = self.get_user_weakest_skills(user_id, 5)
        if not weak_skills:
            # If no weak skills identified yet, return recent quizzes
            cur.execute('''SELECT q.quiz_id, q.title, q.description, q.topic, q.difficulty, q.created_at
                        FROM quizzes q
                        WHERE q.quiz_id NOT IN (
                            SELECT qa.quiz_id FROM quiz_attempts qa 
                            WHERE qa.user_id = ? AND qa.completed = 1
                        )
                        ORDER BY q.created_at DESC
                        LIMIT ?''', (user_id, limit))
        else:
            # Find quizzes with questions targeting weak skills
            skill_ids = [s[0] for s in weak_skills]
            placeholders = ','.join(['?'] * len(skill_ids))
            
            cur.execute(f'''SELECT DISTINCT q.quiz_id, q.title, q.description, q.topic, q.difficulty, q.created_at
                        FROM quizzes q
                        JOIN quiz_questions qq ON q.quiz_id = qq.quiz_id
                        WHERE qq.skill_id IN ({placeholders})
                        AND q.quiz_id NOT IN (
                            SELECT qa.quiz_id FROM quiz_attempts qa 
                            WHERE qa.user_id = ? AND qa.completed = 1
                        )
                        ORDER BY q.created_at DESC
                        LIMIT ?''', (*skill_ids, user_id, limit))
        
        quizzes = []
        for row in cur.fetchall():
            quiz = {
                'quiz_id': row[0],
                'title': row[1],
                'description': row[2],
                'topic': row[3],
                'difficulty': row[4],
                'created_at': row[5]
            }
            quizzes.append(quiz)
        
        return quizzes
    
    def get_quiz_stats(self, user_id):
        """Get quiz statistics for a user."""
        cur = self.conn.cursor()
        
        # Get total attempts and completions
        cur.execute('''SELECT COUNT(*) as attempts, 
                    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completions,
                    AVG(CASE WHEN completed = 1 THEN (score * 1.0 / max_score) ELSE NULL END) as avg_score
                    FROM quiz_attempts
                    WHERE user_id = ?''', (user_id,))
        
        stats_row = cur.fetchone()
        if not stats_row:
            return {
                'total_attempts': 0,
                'completed_quizzes': 0,
                'average_score': 0,
                'total_correct_answers': 0
            }
        
        # Get total correct answers
        cur.execute('''SELECT COUNT(*) 
                    FROM quiz_responses qr
                    JOIN quiz_attempts qa ON qr.attempt_id = qa.attempt_id
                    WHERE qa.user_id = ? AND qr.is_correct = 1''', (user_id,))
        
        correct_answers = cur.fetchone()[0]
        
        return {
            'total_attempts': stats_row[0],
            'completed_quizzes': stats_row[1],
            'average_score': stats_row[2] if stats_row[2] is not None else 0,
            'total_correct_answers': correct_answers
        }