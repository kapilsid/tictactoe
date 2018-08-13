from boto.exception import JSONResponseError
from boto.dynamodb2.exceptions import ConditionalCheckFailedException, ItemNotFound, ValidationException
from boto.dynamodb2.items import Item
from boto.dynamodb2.table import Table
from datetime import datetime


class GameController:
    
     def __init__(self,connectionManager):
        self.cm = conectionManager
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
                                "VALUE": {"S":StatusDate}
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

     


      
               
