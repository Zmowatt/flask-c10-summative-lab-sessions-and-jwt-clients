from flask import Flask, request, session, jsonify
from flask_migrate import Migrate
from models import db, bcrypt, User, Note

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-change-me"

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    db.init_app(app)
    bcrypt.init_app(app)
    Migrate(app, db)

    def current_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        return db.session.get(User, user_id)

    def require_login():
        user = current_user()
        if not user:
            return None, (jsonify({"error": "Unauthorized"}), 401)
        return user, None

    @app.post("/signup")
    def signup():
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"error": "username and password required"}, 400

        if User.query.filter_by(username=username).first():
            return {"error": "username already taken"}, 409

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        return user.to_dict(), 201

    @app.post("/login")
    def login():
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return {"error": "username and password required"}, 400

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return {"error": "Invalid credentials"}, 401

        session["user_id"] = user.id
        return user.to_dict(), 200

    @app.delete("/logout")
    def logout():
        session.pop("user_id", None)
        return ("", 204)

    @app.get("/check_session")
    def check_session():
        user = current_user()
        if not user:
            return {"error": "Unauthorized"}, 401
        return user.to_dict(), 200

    @app.get("/notes")
    def notes_index():
        user, err = require_login()
        if err:
            return err

        
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=10, type=int)
        per_page = max(1, min(per_page, 50))

        query = Note.query.filter_by(user_id=user.id).order_by(Note.id.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [n.to_dict() for n in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages, 
        }, 200

    @app.post("/notes")
    def notes_create():
        user, err = require_login()
        if err:
            return err

        data = request.get_json() or {}
        title = data.get("title")
        content = data.get("content")

        if not title or not content:
            return {"error": "title and content required"}, 400

        note = Note(title=title, content=content, user_id=user.id)
        db.session.add(note)
        db.session.commit()

        return note.to_dict(), 201

    @app.patch("/notes/<int:note_id>")
    def notes_update(note_id):
        user, err = require_login()
        if err:
            return err

        note = db.session.get(Note, note_id)
        if not note:
            return {"error": "Not found"}, 404

        if note.user_id != user.id:
            return {"error": "Forbidden"}, 403

        data = request.get_json() or {}
        if "title" in data and data["title"]:
            note.title = data["title"]
        if "content" in data and data["content"]:
            note.content = data["content"]

        db.session.commit()
        return note.to_dict(), 200

    @app.delete("/notes/<int:note_id>")
    def notes_delete(note_id):
        user, err = require_login()
        if err:
            return err

        note = db.session.get(Note, note_id)
        if not note:
            return {"error": "Not found"}, 404

        if note.user_id != user.id:
            return {"error": "Forbidden"}, 403

        db.session.delete(note)
        db.session.commit()
        return ("", 204)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)