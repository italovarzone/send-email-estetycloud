from flask import Flask, jsonify
import requests
import datetime
import schedule
import time
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from dotenv import load_dotenv
import os
import threading

# Carregar as variáveis do arquivo .env
load_dotenv()

# Configurações iniciais
API_KEY_SENDINBLUE = os.getenv("API_SENDINBLUE_KEY")  # Chave da API da Brevo
API_BASE_URL = os.getenv("API_BASE_URL")  # URL da API externa
API_USERNAME = os.getenv("API_USERNAME")  # Nome de usuário para autenticação
API_PASSWORD = os.getenv("API_PASSWORD")  # Senha para autenticação
EMAIL_TO_NOTIFY = os.getenv("EMAIL_TO_NOTIFY")  # Email de destino
EMAIL_SENDER = {"name": "Estety Cloud", "email": "lashappapi@gmail.com"}  # Configuração do remetente

# Inicializar o Flask
app = Flask(__name__)

# Endpoint fake
@app.route('/fake-endpoint', methods=['GET'])
def fake_endpoint():
    return jsonify({"message": "O endpoint foi acessado com sucesso!", "timestamp": datetime.datetime.now().isoformat()}), 200

# Autenticação na API externa
def authenticate():
    try:
        response = requests.post(
            f"{API_BASE_URL}/login",
            json={"username": API_USERNAME, "password": API_PASSWORD}
        )
        response.raise_for_status()
        return response.json()["token"]
    except requests.RequestException as e:
        print(f"Erro na autenticação: {e}")
        raise

# Busca tarefas e agendamentos
def get_daily_tasks_and_appointments(token):
    today = datetime.date.today().isoformat()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        appointments = requests.get(
            f"{API_BASE_URL}/api/appointments/calendario",
            headers=headers,
            params={"date": today}
        ).json().get("appointments", [])

        tasks = requests.get(
            f"{API_BASE_URL}/api/tasks",
            headers=headers,
            params={"date": today}
        ).json().get("tasks", [])

        return {"appointments": appointments, "tasks": tasks}
    except requests.RequestException as e:
        print(f"Erro ao buscar tarefas e agendamentos: {e}")
        raise

# Envia email usando Sendinblue
def send_notification_email(email, name, message):
    configuration = Configuration()
    configuration.api_key["api-key"] = API_KEY_SENDINBLUE

    # Instancia o ApiClient diretamente
    api_client = ApiClient(configuration)
    api_instance = TransactionalEmailsApi(api_client)

    appointments_list = "\n".join(
        [f"<li>{a['procedure']} às {a['time']} com {a['client']['name']}</li>" for a in message["appointments"]]
    ) or "<p>Sem agendamentos hoje.</p>"

    tasks_list = "\n".join(
        [f"<li>{t['name']} às {t['time']}</li>" for t in message["tasks"]]
    ) or "<p>Sem tarefas hoje.</p>"

    email_content = f"""
    <html>
    <body>
        <h2>Bom dia, {name}!</h2>
        <p>Resumo do dia:</p>
        <h3>Agendamentos</h3>
        <ul>{appointments_list}</ul>
        <h3>Tarefas</h3>
        <ul>{tasks_list}</ul>
    </body>
    </html>
    """

    send_smtp_email = SendSmtpEmail(
        to=[{"email": email}],
        sender=EMAIL_SENDER,
        subject="Notificação Diária de Tarefas e Agendamentos",
        html_content=email_content
    )

    try:
        api_instance.send_transac_email(send_smtp_email)
        print(f"Email enviado para {email}")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

# Tarefa periódica
def periodic_notification():
    if datetime.date.today().weekday() == 6:
        print("Hoje é domingo. Nenhum e-mail será enviado.")
        return

    try:
        token = authenticate()
        data = get_daily_tasks_and_appointments(token)
        send_notification_email(EMAIL_TO_NOTIFY, "Livia", data)
    except Exception as e:
        print(f"Erro na notificação periódica: {e}")

# Agendar o acesso periódico ao endpoint fake
def schedule_fake_endpoint_access():
    def access_endpoint():
        try:
            response = requests.get("https://send-email-estetycloud.onrender.com/fake-endpoint")
            if response.status_code == 200:
                print(f"Endpoint fake acessado: {response.json()}")
            else:
                print(f"Falha ao acessar o endpoint fake: {response.status_code}")
        except Exception as e:
            print(f"Erro ao acessar o endpoint fake: {e}")

    schedule.every(5).minutes.do(access_endpoint)

    while True:
        schedule.run_pending()
        time.sleep(1)

# Iniciar o servidor Flask e o agendamento
if __name__ == "__main__":
    # Executar o agendamento em uma thread separada
    threading.Thread(target=schedule_fake_endpoint_access, daemon=True).start()

    # Iniciar o servidor Flask
    app.run(port=5000, debug=True)
