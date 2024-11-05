import os
import pandas as pd
import openai
from dotenv import load_dotenv
from services.azopenai import AzureOpenAIClient

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configurar las credenciales de OpenAI
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Leer el archivo TSV
df = pd.read_csv("corrected_properties_data.tsv", sep="\t")

# Lista para almacenar resultados
results = []

# Instancia del cliente AzureOpenAI
openai_client = AzureOpenAIClient()

# Procesar cada fila
for index, row in df.iterrows():
    system_prompt = row['System Prompt']
    user_prompt = row['User Prompt']
    expected_result = row['Expected Result']

    # Ejecutar la solicitud al modelo de OpenAI usando la clase AzureOpenAIClient
    result = openai_client.run_eval(system_prompt, user_prompt)

    # Guardar el resultado junto con la entrada
    results.append({
        "System Prompt": system_prompt,
        "User Prompt": user_prompt,
        "Expected Result": expected_result,
        "LLM_result": result
    })

# Convertir los resultados a un DataFrame
results_df = pd.DataFrame(results)

# Guardar los resultados en un archivo CSV para evaluación futura
results_df.to_csv("output_results.csv", index=False)

print("Los resultados han sido guardados en 'output_results.csv'.")