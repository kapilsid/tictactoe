from .setupDynamoDB import getDynamoDBConnection,createGamesTable
from boto.dynamodb.table import Table
from uuid import uuid4

class ConnectionManager:
    
    def __init__(self,mode=None,config=None,endpoint=None,use_instance_meta_data=False):
       self.db = None
       self.gamesTable = None
       
       self.db = getDynamoDBConnection(config=config,endpoint=endpoint,use_instance_metadata=use_intance_metadata)
       

       self.setupGamesTable()
    
    def setupGamesTable():
       try:
          self.gamesTable = Table("Games",connection=self.db)
       except Exception as e:
          raise e("There was an issue trying to retrieve the Games table.")
    

    def getGamesTable(self):
        if self.gamesTable == None:
            self.setupGamesTable()
        return self.gamesTable 
       
    def createGamesTable(self):
        self.gamesTable = createGamesTable(self.db)   


