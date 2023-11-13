import unittest
import json
import requests
from azure.cosmos import cosmos_client

class TestPlayerRegisterFunction(unittest.TestCase):
    TEST_URL='http://localhost:7071/api/player/register'
    PUBLIC_URL=''
    #{"username": "pisell1", "password": "abracadabra01"}
    # Setup CosmosDB client for verification
    
    @classmethod
    #setup necessary proxies using local settings information
    def setUpClass(cls):
        with open('local.settings.json') as settings_file:
            settings = json.load(settings_file)
        MyCosmos = cosmos_client.CosmosClient.from_connection_string(settings['Values']['AzureCosmosDBConnectionString'])
        TreeHuggersDBProxy = MyCosmos.get_database_client(settings['Values']['DatabaseName'])
        PlayerContainerProxy = TreeHuggersDBProxy.get_container_client(settings['Values']['PlayerContainerName'])
        
        cls.client = MyCosmos
        cls.container = PlayerContainerProxy

    def test_insert_player_empty_db(self):
        # Clear the database before testing
        for item in self.container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True):
            self.container.delete_item(item, partition_key=item['id'])

        payload = {"username": "testuser1", "password": "password12345"}
        response = requests.post(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})

        # Verify that the player is in the database
        query = f"SELECT * FROM c WHERE c.username = '{payload['username']}'"
        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
        self.assertEqual(len(items), 1)

    def test_insert_player_non_empty_db(self):
        payload = {"username": "testuser2", "password": "password12345"}
        response = requests.post(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})

    def test_username_length(self):
        # Test with username less than 4 characters
        payload = {"username": "abc", "password": "password12345"}
        response = requests.post(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username less than 4 characters or more than 14 characters"})

        # Test with username more than 14 characters
        payload = {"username": "a" * 15, "password": "password12345"}
        response = requests.post(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username less than 4 characters or more than 14 characters"})

    def test_password_length(self):
        # Test with password less than 10 characters
        payload = {"username": "testuser", "password": "pass"}
        response = requests.post(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Password less than 10 characters or more than 20 characters"})

        # Test with password more than 20 characters
        payload = {"username": "testuser", "password": "p" * 21}
        response = requests.post(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Password less than 10 characters or more than 20 characters"})

    def test_duplicate_username(self):
        payload = {"username": "uniqueuser", "password": "password12345"}
        # Insert the user first
        requests.post(self.TEST_URL, json=payload)

        # Try inserting the same user again
        response = requests.post(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username already exists"})
    
    def test_login_existing_user_correct_password(self):
        # Ensure the user exists in the database
        payload = {"username": "testuser", "password": "correctpassword"}
        requests.post(self.TEST_URL, json=payload)

        # Test GET method
        response = requests.get(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"result": True, "msg": "OK"})
        
    # If user doesn't exist their password can't be incorrect or correct ;)
    def test_login_nonexistent_user(self):
        payload = {"username": "nonexistent", "password": "wrongpassword"}
        response = requests.get(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username or password incorrect"})

    def test_login_existing_user_wrong_password(self):
        # Ensure the user exists in the database
        payload = {"username": "testuser", "password": "correctpassword"}
        requests.post(self.TEST_URL, json=payload)

        # Test GET method with wrong password
        payload = {"username": "testuser", "password": "wrongpassword"}
        response = requests.get(self.TEST_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"result": False, "msg": "Username or password incorrect"})
        
    @classmethod
    def tearDownClass(cls):
        # Clean up test data from CosmosDB after tests
        for item in cls.container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True):
            cls.container.delete_item(item, partition_key=item['id'])

if __name__ == '__main__':
    unittest.main()