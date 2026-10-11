import os
import sqlite3
from datetime import datetime

import flet as ft
import flet_charts as fc

VERSAO_APP = "1.4"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "assistencia.db")


# ------------------------------------------------------------------
# BANCO DE DADOS (SQLite) — os dados ficam salvos em assistencia.db,
# na mesma pasta do main.py, e continuam lá mesmo depois de fechar o programa.
# ------------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            endereco TEXT,
            apelido TEXT
        );

        CREATE TABLE IF NOT EXISTS aparelhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            marca TEXT,
            modelo TEXT,
            senha TEXT,
            acessorios TEXT,
            defeitos TEXT,
            autorizado INTEGER DEFAULT 0,
            valor TEXT,
            orcamento INTEGER DEFAULT 0,
            relatorio TEXT,
            observacoes TEXT,
            status TEXT DEFAULT 'em_manutencao',
            data_entrada TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        );

        CREATE TABLE IF NOT EXISTS pecas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade INTEGER DEFAULT 0,
            preco REAL DEFAULT 0
        );
        """
    )
    conn.commit()
    conn.close()


def salvar_nota(dados):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO clientes (nome, telefone, endereco, apelido) VALUES (?, ?, ?, ?)",
        (dados["nome"], dados["telefone"], dados["endereco"], dados["apelido"]),
    )
    cliente_id = cur.lastrowid
    cur.execute(
        """INSERT INTO aparelhos
           (cliente_id, marca, modelo, senha, acessorios, defeitos, autorizado, valor,
            orcamento, relatorio, observacoes, status, data_entrada)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            cliente_id,
            dados["marca"],
            dados["modelo"],
            dados["senha"],
            dados["acessorios"],
            dados["defeitos"],
            1 if dados["autorizado"] else 0,
            dados["valor"],
            1 if dados["orcamento"] else 0,
            dados["relatorio"],
            dados["observacoes"],
            "em_manutencao",
            datetime.now().strftime("%d/%m/%Y %H:%M"),
        ),
    )
    conn.commit()
    conn.close()


def listar_clientes():
    conn = get_conn()
    rows = conn.execute(
        """SELECT c.*, COUNT(a.id) as total_aparelhos
           FROM clientes c
           LEFT JOIN aparelhos a ON a.cliente_id = c.id
           GROUP BY c.id
           ORDER BY c.id DESC"""
    ).fetchall()
    conn.close()
    return rows


def listar_aparelhos():
    conn = get_conn()
    rows = conn.execute(
        """SELECT a.*, c.nome as cliente_nome, c.telefone as cliente_telefone
           FROM aparelhos a
           LEFT JOIN clientes c ON c.id = a.cliente_id
           ORDER BY a.id DESC"""
    ).fetchall()
    conn.close()
    return rows


def marcar_aparelho_concluido(aparelho_id):
    conn = get_conn()
    conn.execute("UPDATE aparelhos SET status = 'concluido' WHERE id = ?", (aparelho_id,))
    conn.commit()
    conn.close()


def listar_pecas():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM pecas ORDER BY nome ASC").fetchall()
    conn.close()
    return rows


def adicionar_peca(nome, quantidade, preco):
    conn = get_conn()
    conn.execute(
        "INSERT INTO pecas (nome, quantidade, preco) VALUES (?, ?, ?)",
        (nome, quantidade, preco),
    )
    conn.commit()
    conn.close()


def excluir_peca(peca_id):
    conn = get_conn()
    conn.execute("DELETE FROM pecas WHERE id = ?", (peca_id,))
    conn.commit()
    conn.close()


def obter_estatisticas():
    conn = get_conn()
    recebidos = conn.execute("SELECT COUNT(*) FROM aparelhos").fetchone()[0]
    em_manutencao = conn.execute(
        "SELECT COUNT(*) FROM aparelhos WHERE status = 'em_manutencao'"
    ).fetchone()[0]
    concluidos = conn.execute(
        "SELECT COUNT(*) FROM aparelhos WHERE status = 'concluido'"
    ).fetchone()[0]
    clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    conn.close()
    return {
        "recebidos": recebidos,
        "em_manutencao": em_manutencao,
        "concluidos": concluidos,
        "clientes": clientes,
    }


def main(page: ft.Page):
    init_db()

    page.title = "Assistência Técnica - Ordem de Serviço"
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 900
    page.window.min_height = 600
    page.padding = 0
    page.bgcolor = "#F2F3F7"
    page.fonts = {}
    page.theme = ft.Theme(font_family="Arial")

    conteudo = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    sombra_cartao = ft.BoxShadow(
        spread_radius=0,
        blur_radius=10,
        color="#14000000",
        offset=ft.Offset(0, 2),
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def campo(label, expand=1, largura=None, multiline=False, min_lines=1, max_lines=1, password=False):
        return ft.TextField(
            label=label,
            expand=expand if largura is None else False,
            width=largura,
            multiline=multiline,
            min_lines=min_lines,
            max_lines=max_lines,
            password=password,
            can_reveal_password=password,
            border_radius=8,
            filled=True,
            bgcolor="white",
            border_color="#DADCE3",
            focused_border_color="#3B5BFD",
            content_padding=12,
        )

    def titulo_secao(texto):
        return ft.Text(texto, size=15, weight=ft.FontWeight.BOLD, color="#2B2F3A")

    def cartao(*controls, padding=20):
        return ft.Container(
            content=ft.Column(controls, spacing=14),
            bgcolor="white",
            border_radius=12,
            padding=padding,
            border=ft.Border.all(1, "#E3E5EC"),
        )

    # ------------------------------------------------------------------
    # PÁGINA: NOTA DE ENTRADA
    # ------------------------------------------------------------------
    def pagina_nota_entrada():
        # --- Dados do cliente ---
        nome = campo("Nome do cliente")
        telefone = campo("Telefone de contato")
        endereco = campo("Endereço")
        apelido = campo("Apelido")

        bloco_cliente = cartao(
            titulo_secao("Dados do Cliente"),
            ft.Row([nome, telefone], spacing=14),
            ft.Row([endereco, apelido], spacing=14),
        )

        # --- Dados do aparelho ---
        marca = campo("Marca do dispositivo")
        modelo = campo("Modelo do dispositivo")
        senha = campo("Senha", password=True)
        acessorios = campo("Acessórios")

        bloco_aparelho = cartao(
            titulo_secao("Dados do Aparelho"),
            ft.Row([marca, modelo], spacing=14),
            ft.Row([senha, acessorios], spacing=14),
        )

        # --- Defeitos (checkboxes) ---
        lista_defeitos = [
            "Touch",
            "Display",
            "Molhou",
            "Formatação",
            "Software",
            "Bateria",
            "Não liga",
            "Tela trincada",
        ]
        checks_defeitos = [ft.Checkbox(label=d, value=False) for d in lista_defeitos]

        # organiza em grade de 4 colunas
        linhas_defeitos = []
        for i in range(0, len(checks_defeitos), 4):
            linhas_defeitos.append(ft.Row(checks_defeitos[i:i + 4], spacing=20, wrap=True))

        bloco_defeitos = cartao(
            titulo_secao("Defeito Relatado"),
            *linhas_defeitos,
        )

        # --- Serviço autorizado / Orçamento ---
        campo_valor = campo("Valor (R$)", largura=180)

        container_valor = ft.Container(content=campo_valor, visible=False)

        linha_autorizado = ft.Row(
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        def atualizar_linha_autorizado():
            marcado = check_autorizado.value
            container_valor.visible = marcado
            linha_autorizado.controls = [check_autorizado, container_valor]

        def on_change_autorizado(e):
            atualizar_linha_autorizado()
            page.update()

        check_autorizado = ft.Checkbox(
            label="Serviço Autorizado",
            value=False,
            on_change=on_change_autorizado,
        )
        atualizar_linha_autorizado()
        check_orcamento = ft.Checkbox(label="Orçamento", value=False)

        bloco_servico = cartao(
            titulo_secao("Serviço"),
            linha_autorizado,
            check_orcamento,
        )

        # --- Relatório técnico / Observações ---
        relatorio_tecnico = campo("Relatório Técnico", multiline=True, min_lines=5, max_lines=8)
        observacoes = campo("Observações", multiline=True, min_lines=5, max_lines=8)

        bloco_relatorio = cartao(
            ft.Row(
                [
                    ft.Column([titulo_secao("Relatório Técnico"), relatorio_tecnico], expand=1, spacing=8),
                    ft.Column([titulo_secao("Observações"), observacoes], expand=1, spacing=8),
                ],
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )

        # --- Assinaturas ---
        def linha_assinatura(rotulo):
            return ft.Column(
                [
                    ft.Container(height=60, border=ft.Border.only(bottom=ft.BorderSide(1, "#9AA0AC"))),
                    ft.Text(rotulo, size=12, color="#6B7280", text_align=ft.TextAlign.CENTER),
                ],
                spacing=6,
                expand=1,
            )

        bloco_assinaturas = cartao(
            ft.Row(
                [
                    linha_assinatura("Assinatura do Técnico"),
                    linha_assinatura("Assinatura do Cliente"),
                ],
                spacing=40,
            )
        )

        # --- Botões de ação ---
        def salvar_click(e):
            if not nome.value:
                snack_erro = ft.SnackBar(
                    ft.Text("Informe ao menos o nome do cliente."),
                    bgcolor="#E5484D",
                    open=True,
                )
                page.overlay.append(snack_erro)
                page.update()
                return

            defeitos_marcados = [c.label for c in checks_defeitos if c.value]

            salvar_nota({
                "nome": nome.value,
                "telefone": telefone.value,
                "endereco": endereco.value,
                "apelido": apelido.value,
                "marca": marca.value,
                "modelo": modelo.value,
                "senha": senha.value,
                "acessorios": acessorios.value,
                "defeitos": ", ".join(defeitos_marcados),
                "autorizado": check_autorizado.value,
                "valor": campo_valor.value,
                "orcamento": check_orcamento.value,
                "relatorio": relatorio_tecnico.value,
                "observacoes": observacoes.value,
            })

            snack = ft.SnackBar(
                ft.Text("Nota de entrada salva com sucesso!"),
                bgcolor="#22A559",
                open=True,
            )
            page.overlay.append(snack)
            limpar_click(None)
            page.update()

        def limpar_click(e):
            for c in [nome, telefone, endereco, apelido, marca, modelo, senha, acessorios,
                      campo_valor, relatorio_tecnico, observacoes]:
                c.value = ""
            for c in checks_defeitos:
                c.value = False
            check_autorizado.value = False
            check_orcamento.value = False
            atualizar_linha_autorizado()
            if e is not None:
                page.update()

        botoes = ft.Row(
            [
                ft.OutlinedButton("Limpar", on_click=limpar_click),
                ft.ElevatedButton(
                    "Salvar Nota de Entrada",
                    bgcolor="#3B5BFD",
                    color="white",
                    on_click=salvar_click,
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
            spacing=10,
        )

        return ft.Column(
            [
                ft.Text("Nota de Entrada", size=24, weight=ft.FontWeight.BOLD, color="#1F2430"),
                ft.Text("Preencha os dados abaixo para registrar a entrada do aparelho.",
                        size=13, color="#6B7280"),
                ft.Container(height=8),
                bloco_cliente,
                bloco_aparelho,
                bloco_defeitos,
                bloco_servico,
                bloco_relatorio,
                bloco_assinaturas,
                botoes,
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ------------------------------------------------------------------
    # PÁGINA: INÍCIO
    # ------------------------------------------------------------------
    def cartao_inicio(icone, cor, titulo, subtitulo, destino):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icone, size=30, color=cor),
                    ft.Container(height=10),
                    ft.Text(titulo, size=17, weight=ft.FontWeight.BOLD, color="#1F2430"),
                    ft.Text(subtitulo, size=12, color="#6B7280"),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            width=300,
            height=190,
            bgcolor="white",
            border_radius=10,
            padding=24,
            ink=True,
            on_click=lambda e, c=destino: navegar(c),
            shadow=sombra_cartao,
        )

    def pagina_inicio():
        cartoes = ft.Row(
            [
                cartao_inicio(ft.Icons.ASSIGNMENT_ROUNDED, "#2E8BF0", "Nota de Entrada",
                               "Cadastrar um novo aparelho", "nota_entrada"),
                cartao_inicio(ft.Icons.PEOPLE_ROUNDED, "#2E8BF0", "Clientes",
                               "Consultar clientes", "clientes"),
                cartao_inicio(ft.Icons.PHONE_ANDROID_ROUNDED, "#2E8BF0", "Aparelhos",
                               "Consultar aparelhos", "aparelhos"),
                cartao_inicio(ft.Icons.SETTINGS_INPUT_COMPONENT_ROUNDED, "#2E8BF0", "Peças",
                               "Controlar estoque de peças", "pecas"),
                cartao_inicio(ft.Icons.BAR_CHART_ROUNDED, "#2E8BF0", "Desempenho",
                               "Visualizar estatísticas", "desempenho"),
                cartao_inicio(ft.Icons.SETTINGS_ROUNDED, "#2E8BF0", "Configurações",
                               "Configurar o sistema", "config"),
            ],
            wrap=True,
            spacing=20,
            run_spacing=20,
        )

        return ft.Column(
            [
                ft.Text("Bem-vindo!", size=30, weight=ft.FontWeight.BOLD, color="#1F2430"),
                ft.Text("Sistema de gerenciamento da assistência técnica.",
                        size=14, color="#6B7280"),
                ft.Container(height=20),
                cartoes,
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ------------------------------------------------------------------
    # PÁGINA: DESEMPENHO
    # ------------------------------------------------------------------
    def cartao_stat(icone, titulo, valor, com_fundo=False):
        if com_fundo:
            icone_widget = ft.Container(
                content=ft.Icon(icone, size=18, color="white"),
                bgcolor="#2E8BF0",
                border_radius=30,
                padding=6,
            )
        else:
            icone_widget = ft.Icon(icone, size=26, color="#2E8BF0")

        return ft.Container(
            content=ft.Column(
                [
                    icone_widget,
                    ft.Container(height=14),
                    ft.Text(titulo, size=13, color="#3D4250"),
                    ft.Text(str(valor), size=26, weight=ft.FontWeight.BOLD, color="#1F2430"),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            width=280,
            bgcolor="white",
            border_radius=10,
            padding=20,
            shadow=sombra_cartao,
        )

    def pagina_desempenho():
        stats = obter_estatisticas()
        recebidos = stats["recebidos"]
        em_manutencao = stats["em_manutencao"]
        concluidos = stats["concluidos"]
        clientes = stats["clientes"]

        cartoes_stat = ft.Row(
            [
                cartao_stat(ft.Icons.PHONE_ANDROID_ROUNDED, "Aparelhos recebidos", recebidos),
                cartao_stat(ft.Icons.BUILD_ROUNDED, "Em manutenção", em_manutencao),
                cartao_stat(ft.Icons.CHECK_CIRCLE_ROUNDED, "Concluídos", concluidos, com_fundo=True),
                cartao_stat(ft.Icons.PEOPLE_ROUNDED, "Clientes", clientes),
            ],
            wrap=True,
            spacing=20,
            run_spacing=20,
        )

        # --- Gráfico de barras: status dos aparelhos ---
        maior_valor = max(recebidos, em_manutencao, concluidos, 1)

        grafico_barras = fc.BarChart(
            groups=[
                fc.BarChartGroup(
                    x=0,
                    rods=[fc.BarChartRod(to_y=recebidos, width=40, color="#2E8BF0",
                                              border_radius=6, tooltip="Recebidos")],
                ),
                fc.BarChartGroup(
                    x=1,
                    rods=[fc.BarChartRod(to_y=em_manutencao, width=40, color="#F5A623",
                                              border_radius=6, tooltip="Em manutenção")],
                ),
                fc.BarChartGroup(
                    x=2,
                    rods=[fc.BarChartRod(to_y=concluidos, width=40, color="#22A559",
                                              border_radius=6, tooltip="Concluídos")],
                ),
            ],
            border=ft.Border.all(0, "transparent"),
            left_axis=fc.ChartAxis(label_size=32, show_labels=True),
            bottom_axis=fc.ChartAxis(
                label_size=32,
                labels=[
                    fc.ChartAxisLabel(value=0, label=ft.Text("Recebidos", size=11, color="#6B7280")),
                    fc.ChartAxisLabel(value=1, label=ft.Text("Em manut.", size=11, color="#6B7280")),
                    fc.ChartAxisLabel(value=2, label=ft.Text("Concluídos", size=11, color="#6B7280")),
                ],
            ),
            horizontal_grid_lines=fc.ChartGridLines(color="#E3E5EC", width=1),
            max_y=maior_valor + max(1, round(maior_valor * 0.2)),
            interactive=True,
            height=260,
        )

        # --- Gráfico de pizza: distribuição dos status ---
        total_pizza = recebidos + em_manutencao + concluidos
        if total_pizza == 0:
            secoes_pizza = [fc.PieChartSection(value=1, color="#DADCE3", title="")]
        else:
            secoes_pizza = [
                fc.PieChartSection(value=recebidos, color="#2E8BF0", title="Recebidos",
                                    title_style=ft.TextStyle(size=11, color="white", weight=ft.FontWeight.BOLD)),
                fc.PieChartSection(value=em_manutencao, color="#F5A623", title="Em manut.",
                                    title_style=ft.TextStyle(size=11, color="white", weight=ft.FontWeight.BOLD)),
                fc.PieChartSection(value=concluidos, color="#22A559", title="Concluídos",
                                    title_style=ft.TextStyle(size=11, color="white", weight=ft.FontWeight.BOLD)),
            ]

        grafico_pizza = fc.PieChart(
            sections=secoes_pizza,
            sections_space=2,
            center_space_radius=40,
            height=260,
        )

        bloco_graficos = ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [titulo_secao("Status dos aparelhos"), grafico_barras],
                        spacing=14,
                    ),
                    bgcolor="white",
                    border_radius=10,
                    padding=20,
                    shadow=sombra_cartao,
                    expand=1,
                ),
                ft.Container(
                    content=ft.Column(
                        [titulo_secao("Distribuição por status"), grafico_pizza],
                        spacing=14,
                    ),
                    bgcolor="white",
                    border_radius=10,
                    padding=20,
                    shadow=sombra_cartao,
                    expand=1,
                ),
            ],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        return ft.Column(
            [
                ft.Text("Desempenho", size=30, weight=ft.FontWeight.BOLD, color="#1F2430"),
                ft.Text("Indicadores da assistência técnica.", size=14, color="#6B7280"),
                ft.Container(height=20),
                cartoes_stat,
                ft.Container(height=24),
                bloco_graficos,
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ------------------------------------------------------------------
    # PÁGINA: CLIENTES
    # ------------------------------------------------------------------
    def pagina_clientes():
        clientes = listar_clientes()

        if not clientes:
            lista = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE_ROUNDED, size=48, color="#B9BDC9"),
                        ft.Text("Nenhum cliente cadastrado ainda.", color="#9AA0AC"),
                        ft.Text("Cadastre um cliente pela tela de Nota de Entrada.",
                                size=12, color="#B9BDC9"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
                alignment=ft.Alignment.CENTER,
                bgcolor="white",
                border_radius=12,
                border=ft.Border.all(1, "#E3E5EC"),
                padding=60,
            )
        else:
            linhas = []
            for c in clientes:
                linhas.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.Icons.PERSON_ROUNDED, color="white", size=20),
                                    bgcolor="#2E8BF0",
                                    border_radius=30,
                                    padding=10,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(c["nome"], size=15, weight=ft.FontWeight.BOLD, color="#1F2430"),
                                        ft.Text(
                                            f"{c['telefone'] or '-'}  •  {c['apelido'] or 'sem apelido'}",
                                            size=12, color="#6B7280",
                                        ),
                                        ft.Text(c["endereco"] or "-", size=12, color="#9AA0AC"),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        f"{c['total_aparelhos']} aparelho(s)",
                                        size=12, color="#2E8BF0", weight=ft.FontWeight.BOLD,
                                    ),
                                    bgcolor="#E8F1FD",
                                    border_radius=20,
                                    padding=ft.Padding.symmetric(vertical=6, horizontal=12),
                                ),
                            ],
                            spacing=14,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor="white",
                        border_radius=10,
                        padding=16,
                        shadow=sombra_cartao,
                    )
                )
            lista = ft.Column(linhas, spacing=12)

        return ft.Column(
            [
                ft.Text("Clientes", size=30, weight=ft.FontWeight.BOLD, color="#1F2430"),
                ft.Text(f"{len(clientes)} cliente(s) cadastrado(s).", size=14, color="#6B7280"),
                ft.Container(height=20),
                lista,
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ------------------------------------------------------------------
    # PÁGINA: APARELHOS
    # ------------------------------------------------------------------
    def pagina_aparelhos():
        aparelhos = listar_aparelhos()

        cores_status = {
            "em_manutencao": ("#F5A623", "Em manutenção"),
            "concluido": ("#22A559", "Concluído"),
        }

        if not aparelhos:
            lista = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.PHONE_ANDROID_ROUNDED, size=48, color="#B9BDC9"),
                        ft.Text("Nenhum aparelho cadastrado ainda.", color="#9AA0AC"),
                        ft.Text("Cadastre um aparelho pela tela de Nota de Entrada.",
                                size=12, color="#B9BDC9"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
                alignment=ft.Alignment.CENTER,
                bgcolor="white",
                border_radius=12,
                border=ft.Border.all(1, "#E3E5EC"),
                padding=60,
            )
        else:
            def concluir_click(aparelho_id):
                def handler(e):
                    marcar_aparelho_concluido(aparelho_id)
                    navegar("aparelhos")
                return handler

            linhas = []
            for a in aparelhos:
                cor, rotulo = cores_status.get(a["status"], ("#9AA0AC", a["status"]))
                acoes = []
                if a["status"] != "concluido":
                    acoes.append(
                        ft.TextButton(
                            "Marcar como concluído",
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                            on_click=concluir_click(a["id"]),
                        )
                    )
                linhas.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Column(
                                            [
                                                ft.Text(f"{a['marca'] or '-'} {a['modelo'] or ''}".strip(),
                                                        size=15, weight=ft.FontWeight.BOLD, color="#1F2430"),
                                                ft.Text(f"Cliente: {a['cliente_nome'] or '-'}",
                                                        size=12, color="#6B7280"),
                                                ft.Text(f"Defeito: {a['defeitos'] or '-'}",
                                                        size=12, color="#6B7280"),
                                                ft.Text(f"Entrada: {a['data_entrada'] or '-'}",
                                                        size=11, color="#9AA0AC"),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        ft.Container(
                                            content=ft.Text(rotulo, size=12, color="white",
                                                             weight=ft.FontWeight.BOLD),
                                            bgcolor=cor,
                                            border_radius=20,
                                            padding=ft.Padding.symmetric(vertical=6, horizontal=12),
                                        ),
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                ft.Row(acoes, alignment=ft.MainAxisAlignment.END) if acoes else ft.Container(),
                            ],
                            spacing=8,
                        ),
                        bgcolor="white",
                        border_radius=10,
                        padding=16,
                        shadow=sombra_cartao,
                    )
                )
            lista = ft.Column(linhas, spacing=12)

        return ft.Column(
            [
                ft.Text("Aparelhos", size=30, weight=ft.FontWeight.BOLD, color="#1F2430"),
                ft.Text(f"{len(aparelhos)} aparelho(s) registrado(s).", size=14, color="#6B7280"),
                ft.Container(height=20),
                lista,
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ------------------------------------------------------------------
    # PÁGINA: PEÇAS
    # ------------------------------------------------------------------
    def pagina_pecas():
        campo_nome_peca = campo("Nome da peça", expand=2)
        campo_qtd_peca = campo("Quantidade", largura=140)
        campo_preco_peca = campo("Preço (R$)", largura=140)

        def adicionar_click(e):
            if not campo_nome_peca.value:
                snack_erro = ft.SnackBar(
                    ft.Text("Informe o nome da peça."), bgcolor="#E5484D", open=True,
                )
                page.overlay.append(snack_erro)
                page.update()
                return
            try:
                qtd = int(campo_qtd_peca.value) if campo_qtd_peca.value else 0
            except ValueError:
                qtd = 0
            try:
                preco = float((campo_preco_peca.value or "0").replace(",", "."))
            except ValueError:
                preco = 0.0
            adicionar_peca(campo_nome_peca.value, qtd, preco)
            navegar("pecas")

        formulario = cartao(
            titulo_secao("Adicionar peça ao estoque"),
            ft.Row([campo_nome_peca, campo_qtd_peca, campo_preco_peca], spacing=14),
            ft.Row(
                [ft.ElevatedButton("Adicionar", bgcolor="#3B5BFD", color="white",
                                    on_click=adicionar_click)],
                alignment=ft.MainAxisAlignment.END,
            ),
        )

        pecas = listar_pecas()

        def excluir_click(peca_id):
            def handler(e):
                excluir_peca(peca_id)
                navegar("pecas")
            return handler

        if not pecas:
            lista = ft.Container(
                content=ft.Text("Nenhuma peça cadastrada ainda.", color="#9AA0AC"),
                alignment=ft.Alignment.CENTER,
                bgcolor="white",
                border_radius=12,
                border=ft.Border.all(1, "#E3E5EC"),
                padding=40,
            )
        else:
            linhas = []
            for p in pecas:
                linhas.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(p["nome"], size=14, weight=ft.FontWeight.BOLD, color="#1F2430"),
                                        ft.Text(f"Qtd: {p['quantidade']}  •  R$ {p['preco']:.2f}",
                                                size=12, color="#6B7280"),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                    icon_color="#E5484D",
                                    on_click=excluir_click(p["id"]),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor="white",
                        border_radius=10,
                        padding=14,
                        shadow=sombra_cartao,
                    )
                )
            lista = ft.Column(linhas, spacing=10)

        return ft.Column(
            [
                ft.Text("Peças", size=30, weight=ft.FontWeight.BOLD, color="#1F2430"),
                ft.Text(f"{len(pecas)} peça(s) no estoque.", size=14, color="#6B7280"),
                ft.Container(height=16),
                formulario,
                ft.Container(height=16),
                lista,
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # ------------------------------------------------------------------
    # PÁGINAS SIMPLES (placeholders)
    # ------------------------------------------------------------------
    def pagina_generica(titulo, subtitulo):
        return ft.Column(
            [
                ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD, color="#1F2430"),
                ft.Text(subtitulo, size=13, color="#6B7280"),
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.CONSTRUCTION, size=48, color="#B9BDC9"),
                            ft.Text("Em construção", color="#9AA0AC"),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                    bgcolor="white",
                    border_radius=12,
                    border=ft.Border.all(1, "#E3E5EC"),
                    padding=60,
                ),
            ],
            spacing=8,
            expand=True,
        )

    paginas = {
        "inicio": pagina_inicio,
        "nota_entrada": pagina_nota_entrada,
        "clientes": pagina_clientes,
        "aparelhos": pagina_aparelhos,
        "pecas": pagina_pecas,
        "desempenho": pagina_desempenho,
        "config": lambda: pagina_generica("Configurações", "Preferências do sistema."),
    }

    # ------------------------------------------------------------------
    # MENU LATERAL
    # ------------------------------------------------------------------
    itens_menu = [
        ("inicio", ft.Icons.HOME_ROUNDED, "Início"),
        ("nota_entrada", ft.Icons.ASSIGNMENT_ROUNDED, "Nota de Entrada"),
        ("clientes", ft.Icons.PEOPLE_ROUNDED, "Clientes"),
        ("aparelhos", ft.Icons.PHONE_ANDROID_ROUNDED, "Aparelhos"),
        ("pecas", ft.Icons.SETTINGS_INPUT_COMPONENT_ROUNDED, "Peças"),
        ("desempenho", ft.Icons.BAR_CHART_ROUNDED, "Desempenho"),
        ("config", ft.Icons.SETTINGS_ROUNDED, "Configurações"),
    ]

    botoes_menu = {}

    def navegar(chave):
        conteudo.controls.clear()
        conteudo.controls.append(
            ft.Container(content=paginas[chave](), padding=30, expand=True)
        )
        for k, btn in botoes_menu.items():
            ativo = k == chave
            btn.bgcolor = "#3B5BFD" if ativo else None
            btn.content.controls[0].color = "white" if ativo else "#5B6070"
            btn.content.controls[1].color = "white" if ativo else "#2B2F3A"
            btn.content.controls[1].weight = ft.FontWeight.BOLD if ativo else ft.FontWeight.NORMAL
        page.update()

    def criar_item_menu(chave, icone, texto):
        item = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icone, size=20, color="#5B6070"),
                    ft.Text(texto, size=14, color="#2B2F3A"),
                ],
                spacing=12,
            ),
            padding=ft.Padding.symmetric(vertical=12, horizontal=16),
            border_radius=8,
            on_click=lambda e, c=chave: navegar(c),
            ink=True,
        )
        botoes_menu[chave] = item
        return item

    menu_lateral = ft.Container(
        width=250,
        bgcolor="white",
        border=ft.Border.only(right=ft.BorderSide(1, "#E3E5EC")),
        content=ft.Column(
            [
                # Logo
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.PHONE_IPHONE_ROUNDED, color="white", size=22),
                                bgcolor="#3B5BFD",
                                border_radius=10,
                                padding=8,
                            ),
                            ft.Column(
                                [
                                    ft.Text("TechFix", size=17, weight=ft.FontWeight.BOLD, color="#1F2430"),
                                    ft.Text("Assistência Técnica", size=10, color="#9AA0AC"),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                ),
                ft.Divider(height=1, color="#E3E5EC"),
                ft.Container(
                    content=ft.Column(
                        [criar_item_menu(c, i, t) for c, i, t in itens_menu],
                        spacing=4,
                    ),
                    padding=ft.Padding.symmetric(vertical=12, horizontal=12),
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(f"versão {VERSAO_APP}", size=10, color="#B9BDC9"),
                    padding=ft.Padding.symmetric(vertical=10, horizontal=16),
                ),
            ],
            spacing=0,
        ),
    )

    page.add(
        ft.Row(
            [
                menu_lateral,
                ft.Container(content=conteudo, expand=True, bgcolor="#F2F3F7"),
            ],
            spacing=0,
            expand=True,
        )
    )

    navegar("inicio")


if __name__ == "__main__":
    ft.run(main)