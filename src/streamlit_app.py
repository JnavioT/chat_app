import streamlit as st
import requests

# Título del chatbot
st.markdown("<h1 style='text-align: center;'>Asistente Virtual - Interbank</h1>", unsafe_allow_html=True)

# Inicializamos el estado de la sesión si no existe
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # Guardar los mensajes del chat

# Usamos un `sessionID` fijo para identificar la sesión de chat
sessionID = "100000000017"

# Mostrar los mensajes previos en la interfaz
for msg in st.session_state["messages"]:
    style = "text-align: right; color: blue;" if msg["role"] == "user" else "text-align: left; color: black;"
    st.markdown(f"<p style='{style}'>{msg['content']}</p>", unsafe_allow_html=True)

# Definir función para enviar el mensaje al backend Flask
def send_message():
    user_message = st.session_state["user_input"]  # Captura el mensaje ingresado
    if user_message:
        # Guardar el mensaje del usuario en el estado de la sesión
        st.session_state["messages"].append({"role": "user", "content": user_message})

        # Enviar la solicitud al backend Flask
        try:
            response = requests.post(
                "http://localhost:8080/chat",  # Cambia esto si usas otra URL
                json={"sessionID": sessionID, "query": user_message}  # Enviar `sessionID` y la consulta
            )

            # Verificar si la respuesta es válida
            if response.ok:
                try:
                    # Procesar la respuesta como JSON
                    data = response.json()
                    print("ESTA ES LA DATA", data)

                    # Extraer la respuesta del chatbot
                    chat_response = data.get("chat_response", "Respuesta no encontrada.")

                    # Mostrar solo la respuesta del asistente en la conversación
                    st.session_state["messages"].append({"role": "assistant", "content": chat_response})

                    # Mostrar información adicional (formulario, score, oferta, etc.)
                    if "internal_data" in data:
                        with st.expander("Detalles del formulario y oferta"):
                            st.json(data["internal_data"])

                except ValueError as e:
                    # Manejar errores en la decodificación de JSON
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": f"Error al procesar JSON: {str(e)}"}
                    )

            else:
                st.session_state["messages"].append(
                    {"role": "assistant", "content": f"Error del servidor: {response.status_code} - {response.text}"}
                )

        except Exception as e:
            # Mostrar errores en la conversación si falla la solicitud
            st.session_state["messages"].append({"role": "assistant", "content": f"Error: {str(e)}"})

        # Limpiar la entrada de texto después de enviar el mensaje
        st.session_state["user_input"] = ""  

# Crear campo de entrada de texto para el usuario
st.text_input(
    "Escribe tu mensaje...",
    key="user_input",  # Guardamos el input en el estado de la sesión
    on_change=send_message  # Llama a `send_message` al cambiar el texto (cuando se presiona Enter)
)
