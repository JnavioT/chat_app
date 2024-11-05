import random
import json

class MockCreditScoringModel:
    """Clase para simular un modelo de scoring crediticio."""

    def __init__(self):
        # Puedes agregar inicialización de parámetros si es necesario
        pass

    def preprocess_data(self, answers):
        """Preprocesa las respuestas a un formato numérico."""
        # Aquí puedes implementar la lógica de preprocesamiento
        processed_data = {
            "num_properties": int(answers.get("question01", 0)),
            "education_level": self.encode_education(answers.get("question02", "")),
            "num_degrees": int(answers.get("question03", 0)),
            "age": int(answers.get("question04", 0)),
            "employment_status": self.encode_employment(answers.get("question05", "")),
            "location": answers.get("question06", ""),
            "num_vehicles": int(answers.get("question07", 0)),
            "years_since_graduation": int(answers.get("question08", 0)),
            "average_income": float(answers.get("question09", 0))
        }
        return processed_data

    def encode_education(self, level):
        """Codifica el nivel educativo a un número."""
        levels = {"secundaria": 1, "técnico": 2, "universitario": 3}
        return levels.get(level.lower(), 0)

    def encode_employment(self, status):
        """Codifica el estado laboral a un número."""
        statuses = {"dependiente": 1, "independiente": 2, "informal": 3, "mixto": 4}
        return statuses.get(status.lower(), 0)

    def calculate_credit_score(self, processed_data):
        """Simula el cálculo del score crediticio basado en datos procesados."""
        # Simulamos un score aleatorio para fines de demostración
        score = random.randint(300, 850)
        return score

    def make_loan_offer(self, score):
        """Genera una oferta de préstamo basada en el score crediticio."""
        if score >= 700:
            return {"amount": 50000, "rate": 0.08}
        elif score >= 600:
            return {"amount": 30000, "rate": 0.10}
        else:
            return {"amount": 10000, "rate": 0.15}

    def run(self, answers):
        """Método principal para ejecutar la simulación del modelo."""
        processed_data = self.preprocess_data(answers)
        score = self.calculate_credit_score(processed_data)
        loan_offer = self.make_loan_offer(score)
        
        result = {
            "score": score,
            "loan_offer": loan_offer
        }
        
        return json.dumps(result, indent=2)

# Ejemplo de uso
if __name__ == "__main__":
    model = MockCreditScoringModel()
    
    # Simulación de respuestas
    user_answers = {
        "question01": "2",
        "question02": "Universitario",
        "question03": "1",
        "question04": "35",
        "question05": "Dependiente",
        "question06": "Lima",
        "question07": "1",
        "question08": "10",
        "question09": "5000"
    }
    
    output = model.run(user_answers)
    print(output)
