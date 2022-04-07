from flask import Flask, request, Response;
from configuration import Configuration;
from flask_jwt_extended import jwt_required, JWTManager, verify_jwt_in_request, get_jwt;
from models import Ucesnik, database, Izbori, UcesnikIzbori, Glas;
import json;
from datetime import datetime;
from functools import wraps;
from sqlalchemy import and_;
import re;
import isodate.isodatetime;

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


@application.route("/createParticipant", methods=["POST"])
@roleCheck(role = "admin")
@jwt_required()
def createParticipant():
    name = request.json.get("name", "");
    individual = str(request.json.get("individual", ""));

    error = {
        "message" : ""
    };

    if (name == None or len(name) == 0):
        error["message"] = "Field name is missing.";
        return Response(json.dumps(error), status=400);

    if (individual == None or len(individual) == 0):
        error["message"] = "Field individual is missing.";
        return Response(json.dumps(error), status=400);

    tip = "";
    if (individual == "True"):
        tip = "pojedinac";
    else:
        tip = "politicka stranka";

    ucesnik = Ucesnik(name=name, type=tip);

    database.session.add(ucesnik);
    database.session.commit();

    msg = {
      "id" : ucesnik.id
    };
    return Response(json.dumps(msg), status=200);

@application.route("/getParticipants", methods=["GET"])
@roleCheck(role = "admin")
@jwt_required()
def getParticipants():
    ucesnici = Ucesnik.query.filter().all();

    result = {
        "participants" : []
    }

    for ucesnik in ucesnici:
        elem = {
            "id": "",
            "name": "",
            "individual": ""
        }
        elem["id"] = ucesnik.id;
        elem["name"] = ucesnik.name;
        if (ucesnik.type == "pojedinac"):
            elem["individual"] = True
        elif (ucesnik.type == "politicka stranka"):
            elem["individual"] = False;
        result["participants"].append(elem);

    return Response(json.dumps(result), status=200);

@application.route("/createElection", methods=["POST"])
@roleCheck(role = "admin")
@jwt_required()
def createElection():
    start = request.json.get("start", "");
    end = request.json.get("end", "");
    individual = str(request.json.get("individual", ""));
    participants = request.json.get("participants", "");

    error = {
        "message": ""
    };

    if (start == None or len(start) == 0):
        error["message"] = "Field start is missing.";
        return Response(json.dumps(error), status=400);
    if (end == None or len(end) == 0):
        error["message"] = "Field end is missing.";
        return Response(json.dumps(error), status=400);
    if (individual == None or len(individual) == 0):
        error["message"] = "Field individual is missing.";
        return Response(json.dumps(error), status=400);
    if (participants == ""):
        error["message"] = "Field participants is missing.";
        return Response(json.dumps(error), status=400);

    regex = "^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):?[0-5][0-9])?$";
    if (not (re.search(regex, start)) or not (re.search(regex, end))):
        error["message"] = "Invalid date and time.";
        return Response(json.dumps(error), status=400);


    startDateTime = isodate.parse_datetime(start);
    endDateTime = isodate.parse_datetime(end);

    if (startDateTime >= endDateTime):
        error["message"] = "Invalid date and time.";
        return Response(json.dumps(error), status=400);

    izbori = Izbori.query.filter().all();
    for item in izbori:
        if ((startDateTime >= item.start and startDateTime < item.end) or (endDateTime >= item.start and endDateTime < item.end)):
            error["message"] = "Invalid date and time.";
            return Response(json.dumps(error), status=400);


    if (len(participants) < 2):
        error["message"] = "Invalid participants.";
        return Response(json.dumps(error), status=400);

    if (individual == "True"):
        type = "predsednicki";
    elif (individual == "False"):
        type = "parlamentarni";

    for participant in participants:
        id = int(participant);
        ucesnik = Ucesnik.query.filter(Ucesnik.id == id).first();

        if (ucesnik == None):
            error["message"] = "Invalid participants.";
            return Response(json.dumps(error), status=400);

        if ((ucesnik.type == "pojedinac" and type == "parlamentarni") or (ucesnik.type == "politicka stranka" and type == "predsednicki")):
            error["message"] = "Invalid participants.";
            return Response(json.dumps(error), status=400);

    izbori = Izbori(start=startDateTime, end=endDateTime, type=type);

    database.session.add(izbori);
    database.session.commit();

    pollNumber = 1;
    for participant in participants:
        id = int(participant);
        ucesnik = Ucesnik.query.filter(Ucesnik.id == id).first();
        ucesnikIzbori = UcesnikIzbori(ucesnikId=ucesnik.id, izboriId=izbori.id, pollNumber=pollNumber);
        database.session.add(ucesnikIzbori);
        database.session.commit();
        pollNumber+= 1;

    message = {
        "pollNumbers" : []
    };
    i = 1;
    for participant in participants:
        message["pollNumbers"].append(i);
        i += 1;

    return Response(json.dumps(message), status=200);

@application.route("/getElections", methods=["GET"])
@roleCheck(role = "admin")
@jwt_required()
def getElections():
    result = {
      "elections" : []
    };
    izbori = Izbori.query.filter().all();
    for item in izbori:
        type = "";
        if (item.type == "predsednicki"):
            type = True;
        elif (item.type == "parlamentarni"):
            type = False;
        election = {
            "id": item.id,
            "start": str(item.start),
            "end": str(item.end),
            "individual": type,
            "participants": []
        };
        ucesnikIzbori = UcesnikIzbori.query.filter(UcesnikIzbori.izboriId==item.id).all();
        for elem in ucesnikIzbori:
            ucesnik = Ucesnik.query.filter(Ucesnik.id ==elem.ucesnikId).first();
            participant = {
                "id" : ucesnik.id,
                "name" : ucesnik.name
            };
            election["participants"].append(participant);
        result["elections"].append(election);

    return Response(json.dumps(result), status=200);

@application.route("/getResults", methods=["GET"])
@roleCheck(role = "admin")
@jwt_required()
def getResults():
    electionId = request.args.get("id");

    error = {
        "message" : ""
    };

    if (electionId == None):
        error["message"] = "Field id is missing.";
        return Response(json.dumps(error), status=400);

    izbori = Izbori.query.filter(Izbori.id == electionId).first();

    if (izbori == None):
        error["message"] = "Election does not exist.";
        return Response(json.dumps(error), status=400);

    now = datetime.now();
    currentDT = now.strftime("%Y-%m-%dT%H:%M:%S");
    if (currentDT >= str(izbori.start) and currentDT <= str(izbori.end)):
        error["message"] = "Election is ongoing.";
        return Response(json.dumps(error), status=400);

    rezultati = {
        "participants" : [],
        "invalidVotes" : []
    };

    ucesniciNaIzborima = UcesnikIzbori.query.filter(UcesnikIzbori.izboriId == izbori.id).all();

    if (izbori.type == "parlamentarni"):
        ispodCenzusa = [];
        ukupanBrojGlasova = len(Glas.query.filter(and_(Glas.izboriId == izbori.id, Glas.invalidVoteInfo == "")).all());
        for item in ucesniciNaIzborima:
            brojGlasova = len(Glas.query.filter(and_(Glas.izboriId == item.izboriId,
                                            Glas.pollNumber == item.pollNumber, Glas.invalidVoteInfo == "")).all());
            if (brojGlasova / ukupanBrojGlasova < 0.05):
                ispodCenzusa.append(item);

        for item in ispodCenzusa:
            ucesniciNaIzborima.remove(item);

        quotient = [0 for item in ucesniciNaIzborima];
        seatNum = [0 for item in ucesniciNaIzborima];

        numberOfVotes = [len(
                    Glas.query.filter(and_(Glas.izboriId == item.izboriId,
                                      Glas.pollNumber == item.pollNumber, Glas.invalidVoteInfo == "")).all()) for item in ucesniciNaIzborima];

        i = 0;
        while (i < 250):
            j = 0;
            for item in ucesniciNaIzborima:
                quotient[j] = numberOfVotes[j] / (seatNum[j] + 1);
                j += 1;

            max = 0;
            maxIndex = 0;
            for k in range(j):
                if (quotient[k] > max):
                    max = quotient[k];
                    maxIndex = k;

            seatNum[maxIndex] += 1;
            i += 1;

        #i = 0;
        #results = [];
        #sortedSeatNum = [item for item in seatNum];
        #sortedSeatNum.sort(reverse=True);
        #while (i < len(ucesniciNaIzborima)):
        #   seatNumber = sortedSeatNum[i];
            #for item in seatNum:
             #   if (item == seatNumber):
            #        results[i] = ucesniciNaIzborima[i].pollnumber;
           #         break;
          #  i += 1;

        for item in ispodCenzusa:
            ucesnik = Ucesnik.query.filter(Ucesnik.id == item.ucesnikId).first();
            participant = {
                "pollNumber": 1,
                "name": "",
                "result": 0
            };
            participant["pollNumber"] = item.pollNumber;
            participant["name"] = ucesnik.name;
            participant["result"] = 0;
            rezultati["participants"].append(participant);

        for item, seats in zip(ucesniciNaIzborima, seatNum):
            ucesnik = Ucesnik.query.filter(Ucesnik.id == item.ucesnikId).first();
            participant = {
                "pollNumber": 1,
                "name": "",
                "result": 0
            };
            participant["pollNumber"] = item.pollNumber;
            participant["name"] = ucesnik.name;
            participant["result"] = seats;
            rezultati["participants"].append(participant);

    elif (izbori.type == "predsednicki"):
        ukupanBrojGlasova = len(Glas.query.filter(and_(Glas.izboriId == izbori.id, Glas.invalidVoteInfo == "")).all());

        for item in ucesniciNaIzborima:
            brojGlasovaUcesnika = len(Glas.query.filter(and_(Glas.izboriId == item.izboriId,
                                                        Glas.pollNumber == item.pollNumber, Glas.invalidVoteInfo == "")).all());
            procenat = brojGlasovaUcesnika / ukupanBrojGlasova;
            ucesnik = Ucesnik.query.filter(Ucesnik.id == item.ucesnikId).first();
            participant = {
                "pollNumber": 1,
                "name": "",
                "result": 0
            };
            participant["pollNumber"] = item.pollNumber;
            participant["name"] = ucesnik.name;
            participant["result"] = round(procenat, 2);
            rezultati["participants"].append(participant);

    invalidVotes = Glas.query.filter(and_(Glas.izboriId == izbori.id, Glas.invalidVoteInfo != "")).all();
    for vote in invalidVotes:
        invalidVote = {
            "electionOfficialJmbg": "",
            "ballotGuid": "",
            "pollNumber": 1,
            "reason": ""
        };
        invalidVote["electionOfficialJmbg"] = vote.jmbg;
        invalidVote["ballotGuid"] = vote.guid;
        invalidVote["pollNumber"] = vote.pollNumber;
        invalidVote["reason"] = vote.invalidVoteInfo;
        rezultati["invalidVotes"].append(invalidVote);

    return Response(json.dumps(rezultati), status=200);

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5001);