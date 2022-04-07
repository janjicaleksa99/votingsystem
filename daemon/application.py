from flask import Flask;
from configuration import Configuration;
from models import database, Glas, Izbori, UcesnikIzbori, Poruke;
from redis import Redis;
from datetime import datetime;
from sqlalchemy import and_;
from pytz import timezone;

application = Flask ( __name__ );
application.config.from_object ( Configuration );

database.init_app ( application );

with application.app_context ( ) as context:
    while (True):
        with Redis(host=Configuration.REDIS_HOST) as redis:

            bytesList = redis.lrange(Configuration.REDIS_VOTE_LIST, 0, 0);
            if (len(bytesList) == 0):
                continue;

            bytes = redis.lpop(Configuration.REDIS_VOTE_LIST);
            poruka = bytes.decode("utf-8");
            data = poruka.split(",");
            #glas = Glas(guid=data[0], jmbg=data[1], izboriId=int(data[2]) , pollNumber=int(data[3]));
            guid = data[0];
            jmbg = data[1];
            pollNumber = int(data[2]);

            izbori = Izbori.query.filter().all();
            tz = timezone("Europe/Belgrade");
            now = datetime.now(tz);
            aktivniIzbori = False;
            trIzbori = None;
            for elem in izbori:
                if (now.replace(tzinfo=None) >= elem.start and now.replace(tzinfo=None) <= elem.end):
                    aktivniIzbori = True;
                    trIzbori = elem;
                    break;
            if (aktivniIzbori == False):
                poruka = Poruke(poruka=" Glas " + str(guid) + " " + str(pollNumber) + " je odbacen");
                database.session.add(poruka);
                database.session.commit();
                continue;
            else:
                poruka = Poruke(poruka="Na izborima " + str(trIzbori.id) + " glas " + str(guid) + " " + str(pollNumber));
                database.session.add(poruka);
                database.session.commit();

            invalidVote = False;


            result = Glas.query.filter(and_(Glas.izboriId == trIzbori.id, Glas.guid == guid)).all();


            duplicateBallot = False;
            if (len(result) > 0):
                #poruka = Poruke(poruka="Na izborima " + str(trIzbori.id) + " glas " + str(guid) + " je Duplicate ballot");
                #database.session.add(poruka);
                #database.session.commit();
                duplicateBallot = True;

            result = UcesnikIzbori.query.filter(and_(UcesnikIzbori.izboriId == trIzbori.id,
                                                     UcesnikIzbori.pollNumber == pollNumber)).all();

            invalidPollNum = False;
            if (len(result) == 0):
                #poruka = Poruke(poruka="Na izborima " + str(trIzbori.id) + " glas " + str(guid) + " sa poll numberom " + str(pollNumber) + " je Invalid poll number");
                #database.session.add(poruka);
                #database.session.commit();
                invalidPollNum = True;

            invalidVoteInfo = "";
            if (duplicateBallot):
                invalidVoteInfo+= "Duplicate ballot.";
            if (invalidPollNum):
                invalidVoteInfo+= "Invalid poll number.";

            glas = Glas(guid=guid, jmbg=jmbg, izboriId=trIzbori.id, pollNumber=pollNumber);
            glas.invalidVoteInfo = invalidVoteInfo;
            database.session.add(glas);
            database.session.commit();