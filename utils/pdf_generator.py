import io
from datetime import datetime, timedelta, timezone

_FUSO_BRASILIA = timezone(timedelta(hours=-3))


def _agora() -> datetime:
    return datetime.now(_FUSO_BRASILIA)

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

COR_PRINCIPAL    = HexColor('#00A878')
COR_FUNDO_ESCURO = HexColor('#1A1F2E')
COR_TEXTO        = HexColor('#333333')
COR_CINZA        = HexColor('#666666')
COR_LINHA        = HexColor('#EEEEEE')


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf_carteira(
    ativos: list,
    alocacao_atual: dict,
    alocacao_alvo: dict,
    perfil: str,
    historico: list,
    user_email: str,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'Titulo', parent=styles['Title'],
        fontSize=24, textColor=COR_PRINCIPAL, spaceAfter=6,
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo', parent=styles['Normal'],
        fontSize=12, textColor=COR_CINZA, spaceAfter=20,
    )
    estilo_secao = ParagraphStyle(
        'Secao', parent=styles['Heading2'],
        fontSize=14, textColor=COR_PRINCIPAL,
        spaceBefore=20, spaceAfter=10,
    )
    estilo_subsecao = ParagraphStyle(
        'SubSecao', parent=styles['Normal'],
        fontSize=11, textColor=COR_TEXTO,
        fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=6,
    )
    estilo_rodape = ParagraphStyle(
        'Rodape', parent=styles['Normal'],
        fontSize=8, textColor=COR_CINZA, alignment=TA_CENTER,
    )

    elementos = []

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    elementos.append(Paragraph("Carteira B3", estilo_titulo))
    elementos.append(Paragraph(
        f"Relatório gerado em {_agora().strftime('%d/%m/%Y às %H:%M')} | {user_email}",
        estilo_subtitulo,
    ))
    elementos.append(HRFlowable(width="100%", thickness=2, color=COR_PRINCIPAL, spaceAfter=20))

    # ── Resumo Patrimonial ────────────────────────────────────────────────────
    elementos.append(Paragraph("Resumo Patrimonial", estilo_secao))

    valor_total = sum(a.get("valor_atual", 0) for a in ativos)

    tabela_resumo = Table([
        ["Patrimônio Total",    _fmt_brl(valor_total)],
        ["Perfil do Investidor", perfil.capitalize()],
        ["Total de Ativos",     str(len(ativos))],
        ["Data do Relatório",   _agora().strftime("%d/%m/%Y")],
    ], colWidths=[8 * cm, 8 * cm])
    tabela_resumo.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (0, -1), HexColor('#F5F5F5')),
        ('TEXTCOLOR',   (0, 0), (-1, -1), COR_TEXTO),
        ('FONTSIZE',    (0, 0), (-1, -1), 10),
        ('PADDING',     (0, 0), (-1, -1), 8),
        ('GRID',        (0, 0), (-1, -1), 0.5, COR_LINHA),
        ('FONTNAME',    (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    elementos.append(tabela_resumo)

    # ── Alocação ──────────────────────────────────────────────────────────────
    elementos.append(Paragraph("Alocação da Carteira", estilo_secao))

    _CHAVE = {"Ações": "acoes", "FIIs": "fiis", "Renda Fixa": "renda_fixa", "Alternativo": "alternativos"}
    dados_aloc = [["Classe", "Atual (%)", "Alvo (%)", "Diferença (%)"]]
    for classe in ["Ações", "FIIs", "Renda Fixa", "Alternativo"]:
        atual = alocacao_atual.get(classe, 0)
        alvo  = alocacao_alvo.get(_CHAVE[classe], 0)
        dados_aloc.append([classe, f"{atual:.1f}%", f"{alvo:.1f}%", f"{atual - alvo:+.1f}%"])

    tabela_aloc = Table(dados_aloc, colWidths=[5 * cm, 3 * cm, 3 * cm, 3 * cm])
    tabela_aloc.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), COR_PRINCIPAL),
        ('TEXTCOLOR',     (0, 0), (-1, 0), white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('PADDING',       (0, 0), (-1, -1), 8),
        ('GRID',          (0, 0), (-1, -1), 0.5, COR_LINHA),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
        ('TEXTCOLOR',     (0, 1), (-1, -1), COR_TEXTO),
    ]))
    elementos.append(tabela_aloc)

    # ── Ativos por Classe ─────────────────────────────────────────────────────
    elementos.append(Paragraph("Ativos da Carteira", estilo_secao))

    estilo_celula = ParagraphStyle(
        'Celula', parent=styles['Normal'], fontSize=9, wordWrap='LTR',
    )

    classes = sorted(set(a.get("classe", "Outros") for a in ativos))
    for classe in classes:
        ativos_classe = [a for a in ativos if a.get("classe") == classe]
        if not ativos_classe:
            continue

        elementos.append(Paragraph(classe, estilo_subsecao))

        dados_tab = [["Ticker", "Qtd.", "Preço Médio", "Preço Atual", "Valor Total", "Variação"]]
        for a in ativos_classe:
            pm         = a.get("preco_medio", 0)
            pa         = a.get("preco_atual") or pm
            qt         = a.get("quantidade", 0)
            vt         = a.get("valor_atual", pm * qt)
            var        = ((pa - pm) / pm * 100) if pm > 0 else 0
            ticker_val = a.get("ticker", "")

            if "BTC" in ticker_val or "ETH" in ticker_val:
                if qt >= 1:
                    qt_str = f"{qt:.4f}".rstrip('0').rstrip('.')
                elif qt >= 0.001:
                    qt_str = f"{qt:.6f}".rstrip('0').rstrip('.')
                elif qt >= 0.000001:
                    qt_str = f"{qt:.8f}".rstrip('0').rstrip('.')
                else:
                    qt_str = f"{qt:.2e}"
            elif isinstance(qt, float) and qt != int(qt):
                qt_str = f"{qt:.4f}".rstrip('0').rstrip('.')
            else:
                qt_str = str(int(qt))

            ticker_display = Paragraph(ticker_val, estilo_celula)
            qtd_display    = Paragraph(qt_str, estilo_celula)
            dados_tab.append([ticker_display, qtd_display, _fmt_brl(pm), _fmt_brl(pa), _fmt_brl(vt), f"{var:+.1f}%"])

        tabela = Table(dados_tab, colWidths=[3.5 * cm, 1.5 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm, 2.1 * cm])
        tabela.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), COR_FUNDO_ESCURO),
            ('TEXTCOLOR',     (0, 0), (-1, 0), white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('PADDING',       (0, 0), (-1, -1), 6),
            ('GRID',          (0, 0), (-1, -1), 0.5, COR_LINHA),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
            ('TEXTCOLOR',     (0, 1), (-1, -1), COR_TEXTO),
        ]))
        elementos.append(tabela)

    # ── Histórico de Patrimônio ───────────────────────────────────────────────
    if historico and len(historico) >= 2:
        elementos.append(Paragraph("Histórico de Patrimônio", estilo_secao))

        dados_hist = [["Data", "Patrimônio"]]
        for reg in historico[-10:]:
            dados_hist.append([reg.get("data", ""), _fmt_brl(reg.get("valor", 0))])

        tabela_hist = Table(dados_hist, colWidths=[8 * cm, 8 * cm])
        tabela_hist.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), COR_PRINCIPAL),
            ('TEXTCOLOR',     (0, 0), (-1, 0), white),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 10),
            ('PADDING',       (0, 0), (-1, -1), 8),
            ('GRID',          (0, 0), (-1, -1), 0.5, COR_LINHA),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
            ('TEXTCOLOR',     (0, 1), (-1, -1), COR_TEXTO),
        ]))
        elementos.append(tabela_hist)

    # ── Rodapé ────────────────────────────────────────────────────────────────
    elementos.append(Spacer(1, 20))
    elementos.append(HRFlowable(width="100%", thickness=1, color=COR_LINHA, spaceAfter=10))
    elementos.append(Paragraph(
        "Carteira B3 | Não é recomendação de investimento. "
        "Dados baseados nas informações cadastradas pelo usuário.",
        estilo_rodape,
    ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()
