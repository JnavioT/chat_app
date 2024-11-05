import os
import logging
from dotenv import load_dotenv
from openai import AzureOpenAI
from config.parameters import Parameters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureOpenAIClient:
    """Class to interact with Azure OpenAI service."""

    def __init__(self):
        try:
            # Set parameters
            parameters = Parameters().parameters
            self.temperature = parameters.get("temperature", 0.7)
            self.max_tokens = parameters.get("max_tokens", 500)
            logger.info("Parameters loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading parameters: {e}")
            raise
    
    @staticmethod
    def load_env_var():
        """Loads necessary environment variables for Azure OpenAI."""
        try:
            load_dotenv()
            required_vars = [
                    "AZURE_OPENAI_ENDPOINT",
                    "AZURE_OPENAI_API_KEY",
                    "AZURE_OPENAI_API_VERSION",
                    "AZURE_OPENAI_DEPLOYMENT_NAME"
            ]
            env_vars = {var: os.getenv(var) for var in required_vars}
            missing_vars = [var for var, value in env_vars.items() if not value]
            if missing_vars:
                logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
                raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.info("Azure OpenAI environment variables loaded successfully.")
            return env_vars
        except Exception as e:
            logger.error(f"Error loading environment variables: {e}")
            raise
    
    @staticmethod
    def create_openai_client(env_vars):
        """Creates and returns an Azure OpenAI client instance."""
        try:
            client = AzureOpenAI(
                azure_endpoint=env_vars["AZURE_OPENAI_ENDPOINT"],
                api_key=env_vars["AZURE_OPENAI_API_KEY"],
                api_version=env_vars["AZURE_OPENAI_API_VERSION"]
            )
            logger.info("Azure OpenAI client created successfully.")
            return client
        except Exception as e:
            logger.error(f"Error creating Azure OpenAI client: {e}")
            raise

    def openai_response(self, client, deployment_name, messages):
        """Gets a response from Azure OpenAI."""
        try:
            print(messages)
            completion = client.chat.completions.create(
                model=deployment_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=messages,
            )
            logger.info("Response received from Azure OpenAI.")
            #response = completion.choices[0].message.content
            response = [completion.choices[0].message.content, completion.usage.total_tokens]
            
            return response

        except Exception as e:
            logger.error(f"Error getting response from Azure OpenAI: {e}")
            raise

        
    def run(self, system_prompt, messages_history, message=None):
        """Executes the OpenAI chat completion process."""
        try:
            # Cargar las variables de entorno necesarias
            env_vars = self.load_env_var()
            client = self.create_openai_client(env_vars)

            # Construcción de los mensajes para la solicitud
            messages = [{"role": "system", "content": system_prompt}]
            if messages_history:
                messages.extend(messages_history)  # Agrega el historial si existe
            if message:
                # Asegurarse de que message es un diccionario y no una lista
                if isinstance(message, dict):
                    messages.append(message)  # Usar append en lugar de extend
                elif isinstance(message, list):
                    messages.extend(message)  # Si es una lista, usar extend

            #print("MENSAJES que entrar a OPENAI:", messages)

            # Llamar a la API de OpenAI
            response = self.openai_response(client, env_vars["AZURE_OPENAI_DEPLOYMENT_NAME"], messages)
            #logger.info(f"RESPUESTA CRUDA DEL ASISTENTE en run : {response}")
            return response

        except Exception as e:
            logger.error(f"Error running Azure OpenAI process: {e}")
            return {"error": str(e)}
        
    def run_eval(self, system_prompt, user_prompt=None):
        """Executes the OpenAI chat completion process."""
        try:
            env_vars = self.load_env_var()
            client = self.create_openai_client(env_vars)

            messages = [{"role": "system", "content": system_prompt}]
            if user_prompt:  # Solo agregar el mensaje del usuario si se proporciona
                if isinstance(user_prompt, str):  # Verificar que user_prompt sea una cadena
                    messages.append({"role": "user", "content": user_prompt})
                else:
                    logger.error("El user_prompt no es una cadena. Se ignorará el mensaje del usuario.")

            response = self.openai_response(client, env_vars["AZURE_OPENAI_DEPLOYMENT_NAME"], messages)
            return response

        except Exception as e:
            logger.error(f"Error running Azure OpenAI process: {e}")
            return {"error": str(e)}
