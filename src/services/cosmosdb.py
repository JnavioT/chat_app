import os
import json
import logging
from azure.cosmos import CosmosClient, exceptions, PartitionKey
from dotenv import load_dotenv
from config.parameters import Parameters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureCosmosDBClient:
    """Class to interact with Azure Cosmos DB."""
    
    def __init__(self) -> None:
        try:
            # Set parameters
            parameters = Parameters().parameters
            self.database_name = parameters.get("database_name")
            self.container_name = parameters.get("container_name")            
            logger.info("CosmosDBClient initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing CosmosDBClient: {e}")
            raise
    
    @staticmethod
    def load_env_var():
        """Loads necessary environment variables for CosmosDB."""
        try:
            load_dotenv()
            required_vars = [
                    "COSMOSDB_ENDPOINT",
                    "COSMOSDB_PRIMARY_KEY"
                ]
            env_vars = {var: os.getenv(var) for var in required_vars}
            missing_vars = [var for var, value in env_vars.items() if not value]
            if missing_vars:
                logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
                raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.info("Azure CosmosDB environment variables loaded successfully.")
            return env_vars
        except Exception as e:
            logger.error(f"Error loading environment variables: {e}")
            raise
    
    @staticmethod
    def create_cosmos_client(env_vars):
        """Creates and returns a CosmosClient instance."""
        try:
            client = CosmosClient(
                url=env_vars["COSMOSDB_ENDPOINT"],
                credential=env_vars["COSMOSDB_PRIMARY_KEY"],
            )
            return client
        except Exception as e:
            logger.error(f"Error creating Cosmos Client: {e}")
            raise

    def get_container(self, client):
        """Gets the specified container, creating it if it doesn't exist."""
        try:
            database = client.create_database_if_not_exists(id=self.database_name)
            container = database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path='/id')
            )
            logger.info(f"Container '{self.container_name}' created or already exists.")
            return container
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create container '{self.container_name}': {e}")
            raise
        
    def upsert_chat(self, container, session_id, new_messages, formulario, score=None, loan=None):
        """Upserts chat history into Cosmos DB with only relevant messages."""
        try:
            try:
                # Intentar leer el historial existente
                item = container.read_item(item=session_id, partition_key=session_id)
                chat_history = item.get("chat_history", [])
                formulario_actual = item.get("formulario", {})
            except exceptions.CosmosResourceNotFoundError:
                # Si no existe historial, inicializamos uno nuevo
                chat_history = []
                formulario_actual = formulario or {}  # Usamos el formulario inicial
                item = {"id": session_id, "chat_history": chat_history, "formulario": formulario_actual}

            # Filtrar mensajes nuevos para evitar duplicados
            existing_contents = {message["content"] for message in chat_history}
            filtered_messages = [msg for msg in new_messages if msg["content"] not in existing_contents]

            # Actualizar el historial solo con mensajes nuevos
            chat_history.extend(filtered_messages)
            if formulario:
                formulario_actual.update(formulario)

            # Actualizar el elemento con los nuevos datos
            item["chat_history"] = chat_history
            item["formulario"] = formulario_actual

            # Guardar score y loan si están disponibles
            if score is not None:
                item["score"] = score
            if loan is not None:
                item["loan"] = loan

            # Remover cualquier metadato innecesario
            item = self.remove_metadata(item)

            # Realizar la operación de upsert en CosmosDB
            container.upsert_item(item)
            logger.info(f"Chat history for session_id '{session_id}' updated successfully.")

        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to upsert chat history for sessionID '{session_id}': {e}")
            raise


    
    def get_chat_history(self, container, session_id):
        """Retrieves chat history from Cosmos DB."""
        try:
            item = container.read_item(item=session_id, partition_key=session_id)
            return item.get("chat_history", [])
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"No chat history found for session_id '{session_id}'.")
            return {}

    def remove_metadata(self, item):
        """Removes metadata from the item."""
        keys_to_remove = ["_rid", "_self", "_etag", "_attachments", "_ts"]
        for key in keys_to_remove:
            item.pop(key, None)
        return item
    
    def run(self, session_id, operation, message=None, formulario=None, score=None, loan=None):
        """
        Main method to interact with the Cosmos DB client.
        Use operation 'I' to insert/update data, 'S' to select/retrieve data.
        """
        try:
            env_vars = self.load_env_var()
            client = self.create_cosmos_client(env_vars)
            container = self.get_container(client)
            
            if operation == 'I':
                # Llamamos a upsert_chat con los parámetros necesarios
                self.upsert_chat(container, session_id, message, formulario, score, loan)
                return {"status": "success", "message": f"Data inserted for session ID '{session_id}'."}
            elif operation == 'S':
                chat_history = self.get_chat_history(container, session_id)
                return {"status": "success", "chat_history": chat_history}
            else:
                raise ValueError(f"Invalid operation '{operation}' provided. Use 'I' for insert and 'S' for select.")
        except Exception as e:
            logger.error(f"Error during CosmosDB operation: {e}")
            raise


# cosmos = AzureCosmosDBClient()
# session_id = "1111"
# operation = "I"
# role = "user"
# content = "quiero generar un envio masivo"
# response_i_cosmos = cosmos.run(session_id, operation, role, content)
# print(f"Insert: {response_i_cosmos}")

# operation = "S"
# response_s_cosmos = cosmos.run(session_id, operation)
# chat_history = response_s_cosmos['chat_history']
# print(f"chat_history: {chat_history}")
