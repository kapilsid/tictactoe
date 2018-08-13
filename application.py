from flask import Flask, render_template, request, session, flash, redirect, jsonify, json
from dynamodb.ConnectionManager import ConnectionManager
from dynamodb.gameController    import GameController 
from uuid                       import uuid4
 





application = Flask(__name__)
application.debug = True
application.secret_key = str(uuid4())



@application.route('/')
@application.route('/index', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return redirect('index') 
    
    inviteGames = controller.getGameInvites(session["username"])
