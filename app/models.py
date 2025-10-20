from . import db

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100))
    owner = db.Column(db.String(100))

    def __repr__(self):
        return f'<Pet {self.name}>'
