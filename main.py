# main.py

import streamlit as st
from streamlit_option_menu import option_menu
from paginas import (
    cadastro_ano,
    controle_votacao,
    cadastro_criterio,
    cadastro_equipe,
    cadastro_especialista,
    cadastro_jurado,
    cadastro_modalidade,
    cadastro_participante,
    alterar_senha
)
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# Carrega as variáveis de ambiente
load_dotenv()

# Adiciona o diretório atual ao path para permitir importações
sys.path.append(str(Path(__file__).parent))

# Configuração da página - Deve ser a primeira função do Streamlit
st.set_page_config(page_title="Festival de Talentos", layout="wide")

def main():
    # Cria o menu lateral
    with st.sidebar:
        escolha = option_menu(
            menu_title="Menu Principal",  # Título do menu
            options=[
                "Página Inicial",
                "Gerenciar Votação",
                "Cadastro Ano",
                "Cadastro Modalidade",
                "Cadastro Critério",
                "Cadastro Equipe",
                "Cadastro Participante",
                "Cadastro Jurado",
                "Cadastro Especialista",
                "Trocar Senha",
                "Sair"
            ],
            icons=[
                "house",             # Página Inicial
                "key",
                "calendar",          # Cadastro Ano
                "clipboard-data",    # Cadastro Modalidade
                "list-task",         # Cadastro Critério
                "people",            # Cadastro Equipe
                "person-plus",       # Cadastro Participante
                "person",            # Cadastro Jurado
                "gear",              # Cadastro Especialista
                "key",               # Trocar Senha
                "box-arrow-right"    # Sair
            ],
            menu_icon="cast",
            default_index=0,         # Índice padrão selecionado
            orientation="vertical"   # Orientação do menu
        )

    # Exibe o conteúdo de acordo com a opção do menu
    if escolha == "Página Inicial":
        st.title("Bem-vindo ao Festival de Talentos")
        st.write("""
            Utilize o menu lateral para navegar entre as diferentes funcionalidades do sistema.
            Aqui você pode adicionar informações, gerenciar cadastros e muito mais.
        """)
        # Adicione aqui mais conteúdo para a Página Inicial, como estatísticas, gráficos, etc.

    elif escolha == "Cadastro Ano":
        cadastro_ano.show()

    elif escolha == "Gerenciar Votação":
        controle_votacao.show()

    elif escolha == "Cadastro Critério":
        cadastro_criterio.show()

    elif escolha == "Cadastro Equipe":
        cadastro_equipe.show()

    elif escolha == "Cadastro Especialista":
        cadastro_especialista.show()

    elif escolha == "Cadastro Jurado":
        cadastro_jurado.show()

    elif escolha == "Cadastro Modalidade":
        cadastro_modalidade.show()

    elif escolha == "Cadastro Participante":
        cadastro_participante.show()

    elif escolha == "Trocar Senha":
        alterar_senha.show()

    elif escolha == "Sair":
        # Implementação da funcionalidade de Sair
        # Dependendo de como você gerencia a sessão de login, ajuste conforme necessário
        if 'pagina' in st.session_state:
            del st.session_state['pagina']
        st.success("Você foi deslogado com sucesso.")
        st.experimental_rerun()  # Reexecuta o script para refletir as mudanças

if __name__ == "__main__":
    main()
