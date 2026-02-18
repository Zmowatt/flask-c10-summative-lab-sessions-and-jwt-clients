from faker import Faker
from app import app
from models import db, User, Note

fake = Faker()

def seed():
    with app.app_context():
        Note.query.delete()
        User.query.delete()

        u1 = User(username="zach")
        u1.set_password("password")

        u2 = User(username="destiny")
        u2.set_password("password")

        db.session.add_all([u1, u2])
        db.session.commit()

        notes = []
        for _ in range(8):
            notes.append(Note(
                title=fake.sentence(nb_words=4),
                content=fake.paragraph(nb_sentences=3),
                user_id=u1.id
            ))
        for _ in range(5):
            notes.append(Note(
                title=fake.sentence(nb_words=4),
                content=fake.paragraph(nb_sentences=3),
                user_id=u2.id
            ))

        db.session.add_all(notes)
        db.session.commit()

        print("✅ Seed complete: 2 users + notes created")

if __name__ == "__main__":
    seed()
