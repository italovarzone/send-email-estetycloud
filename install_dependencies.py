import subprocess
import sys

def install_dependencies():
    try:
        # Instalar as dependências do arquivo requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Todas as dependências foram instaladas com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")
    except FileNotFoundError:
        print("Arquivo requirements.txt não encontrado.")

if __name__ == "__main__":
    install_dependencies()
