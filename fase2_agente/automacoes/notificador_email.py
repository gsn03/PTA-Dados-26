import os
import requests
import resend
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Inicializa o Resend com a chave do .env
resend.api_key = os.getenv("RESEND_API_KEY")

# Carrega a URL da API do .env (com fallback para localhost caso falte)
API_URL = os.getenv("API_KEY")

def enviar_email_alerta(email_destinatario: str, nome_cliente: str, numero_processo: str, data_prazo: str) -> bool:
    """
    Envia o alerta de prazo utilizando a API do Resend.
    """
    conteudo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #d9534f;">Aviso de Prazo Iminente ⚠️</h2>
            <p>Olá,</p>
            <p>O prazo para o processo <strong>{numero_processo}</strong> do cliente <strong>{nome_cliente}</strong> 
            encerra em exatos 5 dias (<strong>{data_prazo}</strong>).</p>
            <p>Por favor, verifique as providências necessárias no sistema.</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p style="font-size: 12px; color: #777;">Esta é uma mensagem automática do sistema.</p>
        </body>
    </html>
    """

    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [email_destinatario],
            "subject": f"URGENTE: Prazo vencendo em 5 dias - Processo {numero_processo}",
            "html": conteudo_html
        }

        resend.Emails.send(params)
        return True
        
    except Exception as e:
        print(f"Erro ao disparar e-mail via Resend: {str(e)}")
        return False

def verificar_e_notificar_prazos_5_dias():
    hoje = datetime.now().date()
    data_limite = hoje + timedelta(days=5)
    
    try:
        # Pede os próximos 5 dias para a API
        resposta = requests.get(f"{API_URL}/ia/prazos_urgentes", params={"dias": 5})
        
        if resposta.status_code == 200:
            dados = resposta.json()
            processos = dados.get("processos_urgentes", [])
            
            if not processos:
                print("Nenhum processo urgente retornado pela API.")
                return
                
            emails_enviados = 0
            
            for p in processos:
                try:
                    prazo_processo = datetime.strptime(p["prazo"], "%Y-%m-%d").date()
                except ValueError:
                    prazo_processo = datetime.strptime(p["prazo"].split()[0], "%Y-%m-%d").date()

                if hoje <= prazo_processo <= data_limite:
                    chave_alerta = f"{p['numero_processo']}_{p['prazo']}"                 
                    email_teste = "ptaequipegustavo@gmail.com"
                    
                    sucesso = enviar_email_alerta(
                        email_destinatario=email_teste,
                        nome_cliente=p["nome_cliente"],
                        numero_processo=p["numero_processo"],
                        data_prazo=p["prazo"]
                    )
                    
                    if sucesso:
                        emails_enviados += 1
                        print(f"E-mail enviado: Cliente {p['nome_cliente']} | Processo {p['numero_processo']}")
            
            print(f"Varredura concluída. {emails_enviados} novos alertas enviados hoje.")
        else:
            print(f"Erro da API ao buscar prazos. Status Code: {resposta.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Erro crítico. A API do escritório está desligada ou inacessível no momento.")

# Bloco para execução direta do script no agendador de tarefas
if __name__ == "__main__":
    print(f"[{datetime.now()}] Iniciando rotina de notificações...")
    verificar_e_notificar_prazos_5_dias()