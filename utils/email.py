from datetime import datetime

import resend
import streamlit as st


def enviar_email_vencimentos(
    destinatario: str,
    ativos_vencendo: list,
    ativos_vencidos: list,
) -> dict:
    try:
        resend.api_key = st.secrets["RESEND_API_KEY"]
        remetente = st.secrets["RESEND_FROM"]

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h1 style="color: #00A878;">Carteira B3</h1>
          <h2>Resumo de Vencimentos de Renda Fixa</h2>
          <p style="color: #666;">Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        """

        if ativos_vencidos:
            html += """
          <h3 style="color: #ff4444;">⚠️ Ativos Vencidos</h3>
          <table style="width:100%; border-collapse: collapse;">
            <tr style="background: #ff4444; color: white;">
              <th style="padding: 8px; text-align: left;">Ativo</th>
              <th style="padding: 8px; text-align: left;">Valor Investido</th>
              <th style="padding: 8px; text-align: left;">Vencimento</th>
            </tr>
            """
            for ativo in ativos_vencidos:
                html += f"""
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 8px;">{ativo['ticker']}</td>
              <td style="padding: 8px;">R$ {ativo['preco_medio']:,.2f}</td>
              <td style="padding: 8px;">{ativo.get('vencimento', 'N/A')}</td>
            </tr>
                """
            html += "</table><br>"

        if ativos_vencendo:
            html += """
          <h3 style="color: #ff8c00;">📅 Vencendo em breve</h3>
          <table style="width:100%; border-collapse: collapse;">
            <tr style="background: #ff8c00; color: white;">
              <th style="padding: 8px; text-align: left;">Ativo</th>
              <th style="padding: 8px; text-align: left;">Valor Investido</th>
              <th style="padding: 8px; text-align: left;">Vencimento</th>
              <th style="padding: 8px; text-align: left;">Dias restantes</th>
            </tr>
            """
            for ativo in ativos_vencendo:
                html += f"""
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 8px;">{ativo['ticker']}</td>
              <td style="padding: 8px;">R$ {ativo['preco_medio']:,.2f}</td>
              <td style="padding: 8px;">{ativo.get('vencimento', 'N/A')}</td>
              <td style="padding: 8px;">{ativo.get('dias_para_vencer', 'N/A')} dias</td>
            </tr>
                """
            html += "</table><br>"

        html += """
          <hr>
          <p style="color: #999; font-size: 12px;">
            Este email foi enviado pelo Carteira B3.<br>
            Não é recomendação de investimento.
          </p>
        </body>
        </html>
        """

        result = resend.Emails.send({
            "from": remetente,
            "to": [destinatario],
            "subject": "Carteira B3: Resumo de Vencimentos",
            "html": html,
        })
        return {"success": True, "id": result.get("id")}

    except Exception as e:
        return {"success": False, "error": str(e)}
