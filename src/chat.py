import json
import logging
from flask import request, jsonify
from services.azopenai import AzureOpenAIClient
from services.azureaisearch import AzureAISearchClient
from services.cosmosdb import AzureCosmosDBClient
from services.mock_ml_model import MockCreditScoringModel  # Importamos el mockup
from config.parameters import Parameters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure SDK logging level
azure_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
azure_logger.setLevel(logging.WARNING)

class Chat:
    """Clase que maneja la interacción con el asistente virtual."""

    def __init__(self):
        try:
            parameters = Parameters().parameters
            self.prompts_path = parameters.get("prompts_path")
            logger.info("Parameters loaded successfully.")
            self.scoring_model = MockCreditScoringModel()  # Inicializamos el mockup del modelo
            self.azurezopenai = AzureOpenAIClient()
            self.azurecosmos = AzureCosmosDBClient()
            self.system_prompt = self.read_file("./src/prompts/system_prompt_v7.prompt")
            
        except Exception as e:
            logger.error(f"Error loading parameters: {e}")
            raise

    def run(self, sessionID, query):
        try:
            logger.info("Empezando proceso de respuesta del chat...")

            # Obtener historial de CosmosDB y asegurar que es una lista
            data = self.azurecosmos.run(sessionID, 'S')
            chat_history = data.get("chat_history", [])
            chat_history = chat_history if isinstance(chat_history, list) else []

            # Obtener o inicializar el formulario
            formulario = data.get("formulario", {
                "question01": "¿Cuántas propiedades tienes registradas en SUNARP?",
                "answer01": "",
                "question02": "¿Cuál es el nivel educativo más alto que has alcanzado?",
                "answer02": "",
                "question03": "¿Cuántos títulos profesionales has obtenido hasta la fecha?",
                "answer03": "",
                "question04": "¿Cuál es tu edad actual?",
                "answer04": "",
                "question05": "¿Cuál es tu situación laboral?",
                "answer05": "",
                "question06": "¿Dónde resides actualmente?",
                "answer06": "",
                "question07": "¿Cuántos vehículos tienes registrados a tu nombre?",
                "answer07": "",
                "question08": "¿Cuántos años han pasado desde tu primera graduación?",
                "answer08": "",
                "question09": "¿Cuál ha sido tu ingreso neto promedio de los últimos tres meses?",
                "answer09": ""
            })

            # Agregar el mensaje del usuario al historial
            message_user = {"role": "user", "content": query}
            chat_history.append(message_user)

            # Obtener la respuesta del asistente
            data_response = self.azurezopenai.run(self.system_prompt, chat_history, message_user)
            response = data_response[0]  # Contenido de la respuesta en JSON
            tokens = data_response[1]
            logger.info(f"TOKENS utilizados: {tokens}")
            
            # Dado que el esquema está definido por tools, podemos asumir que response ya es JSON
            response_data = response
            
            # Extraer la respuesta conversacional y agregar al historial
            chat_response = response_data.get("chat_response", "")
            message_assistant = {"role": "assistant", "content": chat_response}
            chat_history.append(message_assistant)

            # Actualizar el formulario con la respuesta
            formulario = self.update_formulario_dinamico(formulario, response_data)

            # Verificar si todas las preguntas han sido respondidas
            flag_output = response_data.get("flag_output", False)
            score, loan = None, None

            if flag_output:
                score = self.calculate_score(formulario)
                loan = self.generate_loan_offer(score)
                chat_response += f" Basado en tus respuestas, tu puntaje de crédito es {score} y tu oferta {loan}."
                logger.info(f"Score: {score}, Loan Offer: {loan}")

            # Guardar el historial actualizado en CosmosDB
            self.azurecosmos.run(sessionID, 'I', chat_history, formulario, score=score, loan=loan)

            # Devolver la respuesta al frontend
            return {
                "chat_response": chat_response,
                "formulario": formulario,
                "score": score,
                "loan": loan
            }, 200

        except Exception as e:
            logger.error(f"Error generating model response: {e}")
            return {"error": str(e)}, 500



    @staticmethod
    def read_file(file_path, as_json=False):
        """Lee el contenido de un archivo."""
        try:
            with open(file_path, 'r') as file:
                logger.info(f"File '{file_path}' successfully loaded.")
                return json.load(file) if as_json else file.read()
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON file: {file_path}")
            return ""
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return ""
    
    def calculate_score(self, formulario):
        """Calcula un puntaje usando el mock del modelo."""
        try:
            # Extraer las respuestas del formulario
            answers = [
                formulario.get("answer01", ""),
                formulario.get("answer02", ""),
                formulario.get("answer03", ""),
                formulario.get("answer04", ""),
                formulario.get("answer05", ""),
                formulario.get("answer06", ""),
                formulario.get("answer07", ""),
                formulario.get("answer08", ""),
                formulario.get("answer09", "")
            ]

            # Simular un cálculo de score simple: sumar 100 por cada respuesta válida
            score = sum(100 for answer in answers if answer)
            logger.info(f"Score calculado: {score}")
            return score
        except Exception as e:
            logger.error(f"Error al calcular el score: {e}")
            return None
        
    def generate_loan_offer(self, score):
        """Genera una oferta de préstamo basada en el puntaje."""
        if score >= 750:
            return {"amount": 10000, "rate": 5.5, "term": 12}
        elif score >= 600:
            return {"amount": 5000, "rate": 8.0, "term": 24}
        else:
            return {"amount": 1000, "rate": 12.0, "term": 36}

    def update_formulario_dinamico(self, formulario, response_data):
        """Actualiza el formulario con base en la respuesta JSON del asistente."""
        formulario_actualizado = response_data.get("formulario", {})
        
        # Actualizamos solo las respuestas proporcionadas en la conversación
        for key, value in formulario_actualizado.items():
            if value:  # Si hay una respuesta, actualizamos el formulario
                formulario[key] = value

        return formulario