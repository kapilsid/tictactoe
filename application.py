from flask import Flask, render_template, request, session, flash, redirect, jsonify, json
from dynamodb.ConnectionManager import ConnectionManager
from dynamodb.gameController    import GameController 
from uuid                       import uuid4
from models.game                    import Game
import os, time, sys, argparse 
import logging
logger = logging.getLogger(__name__)

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

@application.route('/play', methods=["POST"])
def play():
    form= request.form 
    logger.info(session["username"])
    logger.info(form["invitee"])
    
    if form:
        creator = session["username"]
        gameId = str(uuid4())
        invitee = form["invitee"].strip()

    if not invitee or creator == invitee:
        flash("Use valid a name (not empty or your name)")
        return redirect("/create")
    try:
        if controller.createNewGame(gameId, creator, invitee):
            return redirect("/game="+gameId)
    except Exception as ex:
        flash("could not create new game .. or redirect")

    flash("Something went wrong creating the game.")
    return redirect("/create")

@application.route('/game=<gameId>')
def game(gameId):
    if session.get("username", None) == None:
        flash("Need to login")
        return redirect("/index")

    item = controller.getGame(gameId)
    if item == None:
        flash("That game does not exist.")
        return redirect("/index")    

    boardState = controller.getBoardState(item)
    result = controller.checkForGameResult(boardState,item,session["username"])

    if result != None:
        if controller.changeGameToFinishedState(item,result,session["username"]) == False:
            flash("Some error occured while trying to finish game.")

    game = Game(item)
    status = game.status
    turn = game.turn

    if game.getResult(session["username"]) == None:
        if turn == game.o:
            turn += " (O)"
        else:
            turn += " (X)"
    
    gameData = {'gameId': gameId, 'status': game.status, 'turn': game.turn, 'board': boardState}
    gameJson = json.dumps(gameData)

    return render_template("play.html",
                            gameId=gameId,
                            gameJson=gameJson,
                            user=session["username"],
                            status=status,
                            turn=turn,
                            opponent=game.getOpposingPlayer(session["username"]),
                            result=result,
                            TopLeft=boardState[0],
                            TopMiddle=boardState[1],
                            TopRight=boardState[2],
                            MiddleLeft=boardState[3],
                            MiddleMiddle=boardState[4],
                            MiddleRight=boardState[5],
                            BottomLeft=boardState[6],
                            BottomMiddle=boardState[7],
                            BottomRight=boardState[8])


@application.route('/accept=<invite>', methods=["POST"])
def accept(invite):
    gameId = request.form["response"]
    game = controller.getGame(gameId)

    if game == None:
        flash("That game does not exist anymore.")
        redirect("/index")

    if not controller.acceptGameInvite(game):
        flash("Error validating the game...")
        redirect("/index")

    return redirect("/game="+game["GameId"])

@application.route('/reject=<invite>', methods=["POST"])
def reject(invite):
    """
    Method associated with the route '/reject=<invite>' where invite
    is the game that you have chosen to reject.
    Deletes the item associated with the invite from the Games table.
    """
    gameId = request.form["response"]
    game = controller.getGame(gameId)

    if game == None:
        flash("That game doesn't exist anymore.")
        redirect("/index")

    if not controller.rejectGameInvite(game):
        flash("Something went wrong when deleting invite.")
        redirect("/index")

    return redirect("/index")

@application.route('/select=<gameId>', methods=["POST"])
def selectSquare(gameId):
    value = request.form["cell"]

    item = controller.getGame(gameId)

    if item == None:
        flash("This is not a valid game.")
        return redirect("/index")

    if controller.
