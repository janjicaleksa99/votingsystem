from flask import Flask, request, Response;
from configuration import Configuration;
from flask_jwt_extended import JWTManager, jwt_required, get_jwt, verify_jwt_in_request;
from models import database, Glas, Izbori, UcesnikIzbori, Poruke;
import csv;
import io;
import json;
from datetime import datetime;
from sqlalchemy import and_;
from redis import Redis;
from functools import wraps
from pytz import timezone;

application = Flask(__name__);
application.config.from_object(Configuration);
jwt = JWTManager(application);

def roleCheck ( role ):
    def innerRole ( function ):
        @wraps ( function )
        def decorator ( *arguments, **keywordArguments ):
            verify_jwt_in_request ( );
            claims = get_jwt ( );
            if ( ( "roles" in claims ) and ( role in claims["roles"] ) ):
                return function ( *arguments, **keywordArguments );
            else:
                ret = {
                    "msg": "Missing Authorization Header"
                }
                return Response(json.dumps(ret), status=401);

        return decorator;

    return innerRole;

brojUlaska = 1;

@application.route("/vote", methods=["POST"])
@roleCheck(role = "zvanicnik")
@jwt_required()
def vote():
    #global brojUlaska;
    #poruka = Poruke(poruka="Ulaz u vote broj " + str(brojUlaska));
    #database.session.add(poruka);
    #database.session.commit();
    #brojUlaska += 1;

    error = {
        "message" : ""
    };
    try:
        content = request.files["file"].stream.read().decode("utf-8");
    except Exception:
        #poruka = Poruke(poruka="Field file is missing.");
        #database.session.add(poruka);
        #database.session.commit();
        error["message"] = "Field file is missing.";
        return Response(json.dumps(error), status=400);

    stream = io.StringIO(content);
    reader = csv.reader(stream);


    addiotionalClaims = get_jwt();
    jmbg = addiotionalClaims["jmbg"];
    rowNum = 0;
    for row in reader:

        #poruka = Poruke(poruka=str(row));
        #database.session.add(poruka);
        #database.session.commit();

        if (len(row) != 2):
            #poruka = Poruke(poruka="Incorrect number of values on line " + str(rowNum) + ".");
            #database.session.add(poruka);
            #database.session.commit();
            error["message"] = "Incorrect number of values on line " + str(rowNum) + ".";
            return Response(json.dumps(error), status=400);

        guid = row[0];
        try:
            redniBroj = int(row[1]);
        except ValueError:
            #poruka = Poruke(poruka="Incorrect poll number on line " + str(rowNum) + ".");
            #database.session.add(poruka);
            #database.session.commit();
            error["message"] = "Incorrect poll number on line " + str(rowNum) + ".";
            return Response(json.dumps(error), status=400);

        if (redniBroj <= 0):
            #poruka = Poruke(poruka="Incorrect poll number on line " + str(rowNum) + ".");
            #database.session.add(poruka);
            #database.session.commit();
            error["message"] = "Incorrect poll number on line " + str(rowNum) + ".";
            return Response(json.dumps(error), status=400);

        #glas = Glas(guid=guid, jmbg=jmbg, izboriId=trIzbori.id , pollNumber=redniBroj);

        #Ubacivanje glasa u redis servis
        with Redis(host=Configuration.REDIS_HOST) as redis:
            poruka = str(guid) + "," + str(jmbg) + "," + str(redniBroj);
            redis.rpush(Configuration.REDIS_VOTE_LIST, poruka);
        rowNum+= 1;

    #poruka = Poruke(poruka="Kraj vote sa statusom 200");
    #database.session.add(poruka);
    #database.session.commit();
    return Response(status=200);

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5002);