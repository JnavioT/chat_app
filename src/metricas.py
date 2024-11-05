import pandas as pd
import json

# Cargar los resultados desde un CSV
results_df = pd.read_csv("output_results_2.csv")

# Función para calcular la precisión
def calculate_accuracy(row):
    try:
        expected = json.loads(row['Expected Result'])
        llm = json.loads(row['LLM_result'])
        
        # Comparar claves y valores
        return expected == llm
    except json.JSONDecodeError as e:
        # Registrar el error si el JSON no se puede decodificar
        print(f"Error decoding JSON for row {row.name}: {e}")
        return False  # Considerar que hay una falta de coincidencia

# Aplicar la función de precisión
results_df['Accuracy'] = results_df.apply(calculate_accuracy, axis=1)

# Calcular la tasa de precisión total
accuracy_rate = results_df['Accuracy'].mean()
print(f"Tasa de precisión total: {accuracy_rate * 100:.2f}%")
