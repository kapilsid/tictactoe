from boto.exception import JSONResponseError
from boto.dynamodb2.exceptions import ConditionalCheckFailedException, ItemNotFound, ValidationException
from boto.dynamodb2.items import Item
from boto.dynamodb2.table import Table
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


class GameController:
    
    def __init__(self,connectionManager):
        self.cm = connectionManager
        self.ResourceNotFound = 'com.amazonaws.dynamodb.v20120810#ResourceNotFoundException'


    def createGame(self, gameId, creator, invitee):
        now = str(datetime.now())
        statusDate = "PENDING_" + now
        item = Item(self.cm.getGameTable(), data = {
                           "GameId" : gameId,
                           "HostId" : creator,
                           "StatusDate" : statusDate,
                           "OUser" : creator,
                           "Turn"  : invitee,
                           "Opponent" : invitee          
                        })
        return item.save() 
    
      
    def checkIfTableIsActive(self) :
        description = self.cm.db.describe_table('Games')
        status = description['Table']['TableStatus']

        return status == 'ACTIVE' 
  

    def gameGame(self,gameId):
        try:
           item = self.cm.getGamesTable().get_item(GameId=gameId)
        except ItemNotFound  as inf:
           return None
        except JSONResponseError as e:
           return None 

        return item


    def acceptGameInvite(self,gameId):
        
        key = { "GameId": {"S" : game["GameId"]}  }
        date = str(datetime.now())
        statusDate = "PROGRESS_" + date
        attributeUpdates =  {"StatusDate" : {
                                "ACTION":"PUT", 
                                "VALUE": {"S":statusDate}
                                }
                            } 
        expectations = {"StatusDate" : {
                             "AtrributeValueList" : [{"S" : "PENDOMG_"}],
                             "ComparisonOperator" : "BEGIN_WITH"
                          }                      
                       }  
                         
        try:
           self.cm.db.update_item("Games",key=key,
                                  attribute_updates=attributeUpdates,
                                  expected=expectations)
              

        except ConditionalCheckFailedException as ccfe:
           return False

        return True
    
    def getGameInvites(self,user):
        invites = []
        if user == None:
            return invites

        gameInvitesIndex = self.cm.getGamesTable().query(
            OpponentId__eq = user,
            StatusDate__beginswith="PENDING_",
            index = "OpponentId-StatusDate-index",
            limit=10 
        )    
        
        for i in range(10):
            try:
                gameInvite = next(gameInvitesIndex)
            except StopIteration as si:
                break
            except ValidationException as ve:
                break
            except JSONResponseError as jre:
                if jre.body.get(u'__type', None) == self.ResourceNotFound:
                    return None
                else:
                    raise jre
            invites.append(gameInvite)

        return invites

    def getGamesWithStatus(self,user,status):

        if user == None:
            return []

        hostGamesInProgress = self.cm.getGamesTable().query(HostId__eq=user,
                                            StatusDate__beginswith=status,
                                            index="HostId-StatusDate-index",
                                            limit=10)

        oppGamesInProgress = self.cm.getGamesTable().query(OpponentId__eq=user,
                                            StatusDate__beginswith=status,
                                            index="OpponentId-StatusDate-index",
                                            limit=10)

        games = self.mergeQueries(hostGamesInProgress,
                                oppGamesInProgress)
        return games
    
    def createNewGame(self,gameId,creator,invitee):
        now = str(datetime.now())
        statusDate = "PENDING_" + now
        try :
            item = Item(self.cm.getGamesTable(), data = {
                "GameId" : gameId,
                "HostId" : creator,
                "OpponentId" : invitee,
                "StatusDate" : statusDate,
                "OUser" : creator,
                "Turn" : invitee
                })
        except Exception as ex:
            logger.debug( ex.msg)
            return None
        return item.save()


    def mergeQueries(self,host,opp,limit=10):
        games = []
        game_one = None
        game_two = None

        while len(games) <= limit:
            if game_one == None:
                try:
                    game_one = next(host)
                except StopIteration as si:
                    if game_two != None:
                        games.append(next(opp))
                    
                    for rest in opp:
                        if len(games) == limit:
                            break
                        else:
                            games.append(rest)
                    return games

            if game_two == None:
                try:
                    game_two = next(opp)
                except StopIteration as si:
                    if game_one != None:
                        games.append(game_one)

                    for rest in host:
                        if len(games) == limit:
                            break
                        else:
                            games.append(rest)
                    return games

            if game_one > game_two:
                games.append(game_one)
                game_one = None
            else:
                games.append(game_two)
                game_two = None

        return games

    

    def getGame(self,gameId):
        try:
            item = self.cm.getGamesTable().get_item(GameId=gameId)
        except ItemNotFound as inf:
            return None
        except JSONResponseError as jre:
                return None

        return item

    def getBoardState(self,item):
        squares = ["TopLeft", "TopMiddle", "TopRight", "MiddleLeft", "MiddleMiddle", "MiddleRight", \
                        "BottomLeft", "BottomMiddle", "BottomRight"]

        state = []

        for square in squares:
            value = item[square]
            if value == None:
                state.append(" ")
            else:
                state.append(value)
        
        return state

    def checkForGameResult(self,board,item,current_player):
        yourMarker = "X"
        theirMarker = "O"

        if current_player == item["OUser"]:
            yourMarker = "O"
            theirMarker = "X"
        
        winConditions = [[0,1,2],[3,4,5],[6,7,8],
                        [0,3,6],[1,4,7],[2,5,8],
                        [0,4,8],[2,4,6]]

        for winCondition in winConditions:
            b_zero = board[winCondition[0]]
            b_one  = board[winCondition[1]]
            b_two  = board[winCondition[2]]
            if b_zero == b_one and \
                b_one == b_two and \
                b_two == yourMarker:
                    return "Win"

            if b_zero == b_one and \
                    b_one == b_two and \
                    b_two == theirMarker:
                        return "Lose"

        if self.checkForTie(board):
            return "Tie"

        return  None

    def checkForTie(self, board):
            for cell in board:
                if cell == " ":
                    return False
            return True


    def changeGameToFinishedState(self, item, result, current_user):
            
            #Happens if you're visiting a game that already has a winner
            if item["Result"] != None:
                return True

            date = str(datetime.now())
            status = "FINISHED"
            item["StatusDate"] = status + "_" + date
            item["Turn"] = "N/A"

            if result == "Tie":
                item["Result"] = result
            elif result == "Win":
                item["Result"] = current_user
            else:
                if item["HostId"] == current_user:
                    item["Result"] = item["OpponentId"]
                else:
                    item["Result"] = item["HostId"]

            return item.save()





               
