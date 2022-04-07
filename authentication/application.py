from flask import Flask, request, Response, jsonify;
from configuration import Configuration;
from models import database, User, UserRole;
from flask_jwt_extended import jwt_required, JWTManager, create_access_token, create_refresh_token, verify_jwt_in_request, get_jwt_identity, get_jwt;
from functools import wraps;
import json;
from sqlalchemy import and_;
import re;


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
                    "msg" : "Missing Authorization Header"
                }
                return Response ( json.dumps(ret), status = 401 );

        return decorator;

    return innerRole;


@application.route("/register", methods=["POST"])
def register():
    jmbg = request.json.get("jmbg", "");
    forename = request.json.get("forename", "");
    surname = request.json.get("surname", "");
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    jmbgEmpty = len(jmbg) == 0;
    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;
    forenameEmpty = len(forename) == 0;
    surnameEmpty = len(surname) == 0;

    error = {
        "message" : ""
    };

    if (jmbgEmpty or jmbg == None):
        error["message"] = "Field jmbg is missing.";
        return Response(json.dumps(error), status=400);
    if (forenameEmpty or forename == None):
        error["message"] = "Field forename is missing.";
        return Response(json.dumps(error), status=400);
    if (surnameEmpty or surname == None):
        error["message"] = "Field surname is missing.";
        return Response(json.dumps(error), status=400);
    if (emailEmpty or email == None):
        error["message"] = "Field email is missing.";
        return Response(json.dumps(error), status=400);
    if (passwordEmpty or password == None):
        error["message"] = "Field password is missing.";
        return Response(json.dumps(error), status=400);

    if (len(jmbg) != 13):
        error["message"] = "Invalid jmbg.";
        return Response(json.dumps(error), status=400);

    dd = int(jmbg[0:2]);
    mm = int(jmbg[2:4]);
    yyy = int(jmbg[4:7]);
    rr = int(jmbg[7:9]);
    bbb = int(jmbg[9:12]);
    k = int(jmbg[12]);

    cifre = [int(item)  for item in jmbg];

    m = 11 - ((7 * (cifre[0] + cifre[6]) + 6 * (cifre[1] + cifre[7]) + 5 * (cifre[2] + cifre[8])
               + 4 * (cifre[3] + cifre[9]) + 3 * (cifre[4] + cifre[10]) + 2 * (cifre[5] + cifre[11])) % 11);

    if (m >= 1 or m <= 9):
        kVallue = m;
    elif (m == 10 or m == 11):
        kVallue = 0;


    if (dd < 1 or dd > 31 or mm < 1 or mm > 12 or yyy < 0 or yyy > 999 or rr < 70 or rr > 99 or bbb < 0 or bbb > 999
    or k != kVallue):
        error["message"] = "Invalid jmbg.";
        return Response(json.dumps(error), status=400);

    regex = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$";
    if (not (re.search(regex, email)) or len(email) > 256):
        error["message"] = "Invalid email.";
        return Response(json.dumps(error), status=400);

    brojKaraktera = len(password) >= 8 and len(password) <= 256;

    imaMaloSlovo = False;
    imaVelikoSlovo = False;
    imaCifru = False;
    for char in password:
        if (char.isupper() == True):
            imaVelikoSlovo = True;
        if (char.isupper() == False):
            imaMaloSlovo = True;
        if (char.isnumeric() == True):
            imaCifru = True;

    if (not (imaCifru and imaVelikoSlovo and imaMaloSlovo and brojKaraktera)):
        error["message"] = "Invalid password.";
        return Response(json.dumps(error), status=400);

    result = User.query.filter(User.email == email).all();
    if (len(result) > 0):
        error["message"] = "Email already exists.";
        return Response(json.dumps(error), status = 400);


    user = User(jmbg = jmbg, password=password, email=email, forename=forename, surname=surname);

    database.session.add(user);
    database.session.commit();

    userRole = UserRole(userId=user.id, roleId=2);
    database.session.add(userRole);
    database.session.commit();

    return Response(status=200);

@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    emailEmpty = len(email) == 0;
    passwordEmpty = len(password) == 0;

    error = {
        "message": ""
    };

    if (emailEmpty or email == None):
        error["message"] = "Field email is missing.";
        return Response(json.dumps(error), status=400);
    if (passwordEmpty or password == None):
        error["message"] = "Field password is missing.";
        return Response(json.dumps(error), status=400);

    regex = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$";
    if (not (re.search(regex, email)) or len(email) > 256):
        error["message"] = "Invalid email.";
        return Response(json.dumps(error), status=400);

    user = User.query.filter(and_(User.email == email, User.password == password)).first();
    if (user == None):
        error["message"] = "Invalid credentials.";
        return Response(json.dumps(error), status=400);
    userRole = UserRole.query.filter(UserRole.userId == user.id).first();
    if (not user):
        error["message"] = "Invalid credentials.";
        return Response(json.dumps(error), status=400);

    role = "";
    if (userRole.roleId == 1):
        role = "admin"
    elif (userRole.roleId == 2):
        role = "zvanicnik";

    additionalClaims = {
        "email" : user.email,
        "jmbg" : user.jmbg,
        "forename": user.forename,
        "surname": user.surname,
        "password": user.password,
        "roles" : role
    };

    accessToken = create_access_token(identity=email, additional_claims=additionalClaims);
    refreshToken = create_refresh_token(identity=email, additional_claims=additionalClaims);

    # return Response(accessToken, status = 200);
    return jsonify(accessToken=accessToken, refreshToken=refreshToken);

@application.route("/refresh", methods=["POST"])
def refresh():
    verify_jwt_in_request(refresh=True);

    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "email": refreshClaims["email"],
        "jmbg" : refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "password": refreshClaims["password"],
        "roles": refreshClaims["roles"]
    };

    accessToken = create_access_token(identity = identity, additional_claims= additionalClaims);

    message = {
        "accessToken" : accessToken
    };

    return Response(json.dumps(message), status = 200);

@application.route("/delete", methods=["POST"])
@roleCheck(role = "admin")
@jwt_required()
def delete():
    email = request.json.get("email", "");

    error = {
        "message": ""
    };

    if (email == None or len(email) == 0):
        error["message"] = "Field email is missing.";
        return Response(json.dumps(error), status=400);

    regex = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$";
    if (not (re.search(regex, email)) or len(email) > 256):
        error["message"] = "Invalid email.";
        return Response(json.dumps(error), status=400);

    user = User.query.filter(User.email == email).first();
    if (not user):
        error["message"] = "Unknown user.";
        return Response(json.dumps(error), status=400);

    UserRole.query.filter(UserRole.userId == user.id).delete();
    database.session.commit();

    User.query.filter(User.email == email).delete();
    database.session.commit();
    return Response(status=200);

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5000);

