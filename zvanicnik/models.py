from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy();

class UcesnikIzbori(database.Model):
    __tablename__ = "ucesnikizbori";

    id = database.Column(database.Integer, primary_key=True);

    ucesnikId = database.Column(database.Integer, database.ForeignKey("ucesnik.id"), nullable=False);
    izboriId = database.Column(database.Integer, database.ForeignKey("izbori.id"), nullable=False);
    pollNumber = database.Column(database.Integer, nullable=False);

class Ucesnik(database.Model):
    __tablename__ = "ucesnik";

    id = database.Column(database.Integer, primary_key=True);

    name = database.Column(database.String(256), nullable=False);
    type = database.Column(database.String(256), nullable=False);

    izbori = database.relationship("Izbori", secondary = UcesnikIzbori.__tablename__, back_populates = "ucesnici");

class Izbori(database.Model):
    __tablename__ = "izbori";

    id = database.Column(database.Integer, primary_key=True);

    start = database.Column(database.DATETIME, nullable=False);
    end = database.Column(database.DATETIME, nullable=False);
    type = database.Column(database.String(256), nullable=False);

    ucesnici = database.relationship("Ucesnik", secondary=UcesnikIzbori.__tablename__, back_populates="izbori");

class Glas(database.Model):
    __tablename__ = "glas";

    id = database.Column(database.Integer, primary_key=True);
    guid = database.Column(database.String(256), nullable=False);
    jmbg = database.Column(database.String(13), nullable=False);
    invalidVoteInfo = database.Column(database.String(256), nullable=False);
    pollNumber = database.Column(database.Integer, nullable=False);

    izboriId = database.Column(database.Integer, database.ForeignKey("izbori.id"), nullable=False);

class Poruke(database.Model):
    __tablename__ = "poruke";
    id = database.Column(database.Integer, primary_key=True);
    poruka = database.Column(database.String(256), nullable=False);