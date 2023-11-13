import unittest
import json
import requests
from azure.cosmos import cosmos_client

class TestPlayerUpdateFunction(unittest.TestCase):
    TEST_REGISTER_URL='http://localhost:7071/api/player/register'
    TEST_UPDATE_URL='http://localhost:7071/api/player/update'
    TEST_LOGIN_URL='http://localhost:7071/api/player/login'
    PUBLIC_URL=''
    
    @classmethod
    #setup necessary proxies using local settings information
    def setUpClass(cls):
        with open('local.settings.json') as settings_file:
            settings = json.load(settings_file)
        MyCosmos = cosmos_client.CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
        QuiplashDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
        PlayerContainerProxy = QuiplashDBProxy.get_container_client(settings['Values']['PlayerContainerName'])

        cls.client = MyCosmos
        cls.container = PlayerContainerProxy
    
    def test_player_updated_correctly(self):
        #Adding a player
        payload = {"username":"correctusername", "password":"veryvalidpassword"}
        requests.post(self.TEST_REGISTER_URL, json=payload)
        
        #Updating the player
        payload = {"username":"correctusername", "add_to_games_played": 2, "add_to_score":200}
        response = requests.put(self.TEST_UPDATE_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})
    
    def test_player_object_actually_updated(self):
        # Add a player
        payload = {"username": "updatecheck", "password": "password12345"}
        requests.post(self.TEST_REGISTER_URL, json=payload)

        # Update the player
        payload = {"username": "updatecheck", "add_to_games_played": 3, "add_to_score": 300}
        requests.put(self.TEST_UPDATE_URL, json=payload)

        # Query CosmosDB to check the update
        query = "SELECT * FROM c WHERE c.username = 'updatecheck'"
        player = list(self.container.query_items(query=query, enable_cross_partition_query=True))[0]
        self.assertEqual(player['games_played'], 3)
        self.assertEqual(player['total_score'], 300)
    
    def test_nonexistent_username(self):
        # Update using a nonexistent username
        payload = {"username": "nonexistentuser", "add_to_games_played": 2, "add_to_score": 200}
        response = requests.put(self.TEST_UPDATE_URL, json=payload)
        #self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"result": False, "msg": "Player does not exist"})

if __name__ == '__main__':
    unittest.main()