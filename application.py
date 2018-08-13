from flask import Flask, render_template, request, session, flash, redirect, jsonify, json
from dynamodb.ConnectionManager import ConnectionManager
from dynamodb.gameController    import GameController 
from uuid                       import uuid4
from models.game                    import Game
 


application = Flask(__name__)
application.debug = True
application.secret_key = str(uuid4())

cm = ConnectionManager()
controller = GameController(cm)

@application.route('/logout')
def logout():
    session["username"] = None
    return redirect("/index")

@application.route('/')
@application.route('/index', methods=["GET", "POST"])
def index():
    if session == {} or session.get("username", None) == None:
        form = request.form
        if form:
            formInput = form["username"]
            if formInput and formInput.strip():
                session["username"] = request.form["username"]
            else:
                session["username"] = None
        else:
            session["username"] = None

    if request.method == "POST":
        return redirect('/index') 
    
    inviteGames = controller.getGameInvites(session["username"])
    if inviteGames == None:
        flash("Table has not been created yet, please follow this link to create table.")
        return render_template("table.html",
                                user="")

    # Don't attempt to iterate over inviteGames until AFTER None test
    inviteGames = [Game(inviteGame) for inviteGame in inviteGames]

    inProgressGames = controller.getGamesWithStatus(session["username"], "IN_PROGRESS")
    inProgressGames = [Game(inProgressGame) for inProgressGame in inProgressGames]

    finishedGames   = controller.getGamesWithStatus(session["username"], "FINISHED")
    fs = [Game(finishedGame) for finishedGame in finishedGames]

    return render_template("index.html",
            user=session["username"],
            invites=inviteGames,
            inprogress=inProgressGames,
            finished=fs)
@application.route('/create')
def create():
    if session.get('username',None) == None:
        flash("Need to login to create game")
        return redirect("/index")
    return render_template("create.html",
                            user=session["username"])  

@application.route('/table', methods=["GET", "POST"])
def createTable():
    cm.createGamesTable()

    while controller.checkIfTableIsActive() == False:
        time.sleep(3)

    return redirect('/index')