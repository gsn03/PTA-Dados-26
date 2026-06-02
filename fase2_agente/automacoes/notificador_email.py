import os
import requests
import resend
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
API_URL = os.getenv("API_KEY") 
EMAIL_EQUIPE = "ptaequipegustavo@gmail.com"

def gerar_linhas_tabela(processos, cor_fundo):
    """Gera as linhas HTML dinâmicas baseadas nos dados da API"""
    if not processos:
        return f"<tr><td colspan='4' style='padding: 10px; text-align: center; background-color: #f9f9f9; color: #777;'>Sem prazos para esta categoria hoje.</td></tr>"

    linhas = ""
    for p in processos:
        linhas += f"""
        <tr style="background-color: {cor_fundo}; border-bottom: 1px solid #ddd;">
            <td style="padding: 10px;"><strong>{p['nome_cliente']}</strong></td>
            <td style="padding: 10px;">{p['numero_processo']}</td>
            <td style="padding: 10px;">{p['prazo']}</td>
            <td style="padding: 10px;">{p['fase_atual']}</td>
        </tr>
        """
    return linhas

def executar_relatorio_matinal():
    print(f"[{datetime.now()}] Iniciando geração do Relatório Matinal...")

    # 1. Busca dados de 5 dias (Zona de Perigo)
    try:
        resp_5 = requests.get(f"{API_URL}/ia/alertas_email", params={"dias_exatos": 5}, timeout=10)
        processos_5 = resp_5.json().get("processos", []) if resp_5.status_code == 200 else []
    except Exception as e:
        print(f"Erro ao buscar prazos de 5 dias: {e}")
        processos_5 = []

    # 2. Busca dados de 15 dias (Zona de Atenção)
    try:
        resp_15 = requests.get(f"{API_URL}/ia/alertas_email", params={"dias_exatos": 15}, timeout=10)
        processos_15 = resp_15.json().get("processos", []) if resp_15.status_code == 200 else []
    except Exception as e:
        print(f"Erro ao buscar prazos de 15 dias: {e}")
        processos_15 = []

    linhas_perigo = gerar_linhas_tabela(processos_5, "#ffebee") # Fundo avermelhado
    linhas_atencao = gerar_linhas_tabela(processos_15, "#fff8e1") # Fundo amarelado

    conteudo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 800px; margin: auto;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px;">Resumo Matinal: Prazos e Urgências da Equipe</h2>
            <p>Bom dia, equipe. Segue o panorama de prazos processuais para foco no dia de hoje.</p>

            <h3 style="color: #c0392b;">🔴 ZONA DE PERIGO (Vencimento em exatos 5 dias)</h3>
            <table style="width: 100%; border-collapse: collapse; text-align: left; border: 1px solid #ddd;">
                <thead>
                    <tr style="background-color: #c0392b; color: white;">
                        <th style="padding: 10px;">Cliente</th>
                        <th style="padding: 10px;">Processo</th>
                        <th style="padding: 10px;">Data de Vencimento</th>
                        <th style="padding: 10px;">Fase Atual</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_perigo}
                </tbody>
            </table>

            <h3 style="color: #f39c12; margin-top: 30px;">🟡 ZONA DE ATENÇÃO (Vencimento em exatos 15 dias)</h3>
            <table style="width: 100%; border-collapse: collapse; text-align: left; border: 1px solid #ddd;">
                <thead>
                    <tr style="background-color: #f39c12; color: white;">
                        <th style="padding: 10px;">Cliente</th>
                        <th style="padding: 10px;">Processo</th>
                        <th style="padding: 10px;">Data de Vencimento</th>
                        <th style="padding: 10px;">Fase Atual</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_atencao}
                </tbody>
            </table>

            <p style="margin-top: 30px; font-size: 14px; background-color: #f4f6f7; padding: 10px; border-radius: 5px;">
                <em>💡 <strong>Dica de uso:</strong> Copie o número do processo e o nome do cliente e consulte o nosso Agente de IA para obter o histórico completo e o status atualizado de forma instantânea.</em>
            </p>
            <hr style="border: 0; border-top: 1px solid #eee; margin-top: 20px;">
            <p style="font-size: 11px; color: #777; text-align: center;">Agente Jurídico Automático - Relatório gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}</p>
        </body>
    </html>
    """

    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": [EMAIL_EQUIPE],
            "subject": "Resumo Matinal: Prazos e Urgências da Equipe",
            "html": conteudo_html
        }

        resend.Emails.send(params)
        print("[SUCESSO] Relatório Matinal enviado para a equipe.")
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha ao enviar e-mail via Resend: {str(e)}")

if __name__ == "__main__":
    executar_relatorio_matinal()