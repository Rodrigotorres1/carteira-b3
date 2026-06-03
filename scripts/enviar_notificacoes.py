import os
import resend
from supabase import create_client
from datetime import datetime, date


def calcular_dias_para_vencer(vencimento_str):
    if not vencimento_str:
        return None
    try:
        vencimento = datetime.strptime(vencimento_str, "%d/%m/%Y").date()
        return (vencimento - date.today()).days
    except Exception:
        return None


def formatar_status(dias):
    if dias is None:
        return None
    if dias <= 0:
        return "Vencido"
    if dias <= 30:
        return f"Vence em {dias} dias"
    if dias <= 90:
        return f"Vence em {dias} dias"
    if dias <= 365:
        return f"Vence em {dias // 30} meses"
    return None  # Longo prazo não notifica


def montar_html_email(ativos_alertas, user_email):
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h1 style="color: #00A878;">Carteira B3</h1>
      <h2>Alerta de Vencimentos</h2>
      <p style="color: #666;">Gerado em {date.today().strftime('%d/%m/%Y')}</p>
      <p>Olá! Você tem ativos de renda fixa com vencimento próximo:</p>
      <table style="width:100%; border-collapse: collapse;">
        <tr style="background: #00A878; color: white;">
          <th style="padding: 10px; text-align: left;">Ativo</th>
          <th style="padding: 10px; text-align: left;">Valor</th>
          <th style="padding: 10px; text-align: left;">Vencimento</th>
          <th style="padding: 10px; text-align: left;">Status</th>
        </tr>
    """

    for ativo in ativos_alertas:
        cor_status = "#ff4444" if "Vencido" in ativo["status"] else "#ff8c00"
        html += f"""
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 10px;">{ativo['ticker']}</td>
          <td style="padding: 10px;">R$ {ativo['valor']:,.2f}</td>
          <td style="padding: 10px;">{ativo['vencimento']}</td>
          <td style="padding: 10px; color: {cor_status};"><b>{ativo['status']}</b></td>
        </tr>
        """

    html += """
      </table>
      <br>
      <p>Acesse o app para mais detalhes:</p>
      <a href="https://carteira-b3.streamlit.app"
        style="background: #00A878; color: white; padding: 10px 20px;
               text-decoration: none; border-radius: 5px;">
        Abrir Carteira B3
      </a>
      <br><br>
      <hr>
      <p style="color: #999; font-size: 12px;">
        Carteira B3 - Não é recomendação de investimento.
      </p>
    </body>
    </html>
    """
    return html


def main():
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SERVICE_KEY"]
    resend_key   = os.environ["RESEND_API_KEY"]

    supabase = create_client(supabase_url, supabase_key)
    resend.api_key = resend_key

    result = supabase.table("carteiras").select("user_id, dados").execute()

    if not result.data:
        print("Nenhuma carteira encontrada.")
        return

    emails_enviados = 0

    for carteira in result.data:
        user_id = carteira["user_id"]
        dados   = carteira["dados"]

        try:
            user_result = supabase.auth.admin.get_user_by_id(user_id)
            user_email  = user_result.user.email
        except Exception as e:
            print(f"Erro ao buscar email do usuário {user_id}: {e}")
            continue

        ativos     = dados.get("ativos", [])
        renda_fixa = [a for a in ativos if a.get("classe") == "Renda Fixa"]

        if not renda_fixa:
            continue

        ativos_alertas = []
        for ativo in renda_fixa:
            vencimento = ativo.get("vencimento")
            dias       = calcular_dias_para_vencer(vencimento)
            status     = formatar_status(dias)

            if status:
                ativos_alertas.append({
                    "ticker":    ativo.get("ticker", "N/A"),
                    "valor":     ativo.get("preco_medio", 0),
                    "vencimento": vencimento or "N/A",
                    "status":    status,
                    "dias":      dias,
                })

        if not ativos_alertas:
            continue

        try:
            html = montar_html_email(ativos_alertas, user_email)
            resend.Emails.send({
                "from": "Carteira B3 <onboarding@resend.dev>",
                "to":   [user_email],
                "subject": "Carteira B3: Alerta de Vencimentos",
                "html": html,
            })
            emails_enviados += 1
            print(f"Email enviado para {user_email}: {len(ativos_alertas)} ativo(s) com alerta")
        except Exception as e:
            print(f"Erro ao enviar email para {user_email}: {e}")

    print(f"Total: {emails_enviados} email(s) enviado(s)")


if __name__ == "__main__":
    main()
