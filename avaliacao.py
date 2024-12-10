import streamlit as st
import psycopg2
from psycopg2 import sql, errors
from dotenv import load_dotenv
import os
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# Configuração da página
st.set_page_config(page_title="AFM 2024", layout="wide")

# Carrega as variáveis de ambiente
load_dotenv()
DB_URL = os.getenv("DB_URL")

# Função para conectar ao banco de dados
def get_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        st.error(f"Erro na conexão com o banco de dados: {e}")
        return None

# Função para autenticar jurado (case-insensitive)
def autenticar_jurado(login, senha):
    try:
        conn = get_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        query = '''
            SELECT id_jurado, nome, senha 
            FROM tbl_jurados 
            WHERE LOWER(login) = LOWER(%s);
        '''
        cursor.execute(query, (login,))
        result = cursor.fetchone()
        if result:
            id_jurado, nome, senha_stored = result
            # Comparar diretamente as senhas
            if senha == senha_stored:
                return (id_jurado, nome)
            else:
                return None
        else:
            return None
    except Exception as e:
        st.error(f"Erro durante autenticação: {e}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# Função para carregar equipes com status 'votando' para o jurado atual
def carregar_equipes_votando(id_jurado):
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()
        cursor = conn.cursor()
        query = '''
            SELECT DISTINCT e.id_equipe, e.nome, e.grau, e.ficha_tecnica, m.id_modalidade AS modalidade_id, m.nome AS modalidade
            FROM tbl_equipes e
            JOIN tbl_modalidades m ON e.id_modalidade = m.id_modalidade
            JOIN tbl_notas n ON e.id_equipe = n.id_equipe
            WHERE e.status_votacao = 'votando'
              AND n.id_jurado = %s
              AND n.status IN ('votando', 'liberado')
            ORDER BY e.nome;
        '''
        cursor.execute(query, (id_jurado,))
        rows = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=colunas)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar equipes em votação: {e}")
        return pd.DataFrame()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# Função para carregar critérios de uma modalidade
def carregar_criterios(id_modalidade):
    try:
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        query = '''
            SELECT id_criterio, nome 
            FROM tbl_criterios 
            WHERE id_modalidade = %s
            ORDER BY nome;
        '''
        cursor.execute(query, (int(id_modalidade),))  # Converter para int
        rows = cursor.fetchall()
        criterios = rows  # (id_criterio, nome)
        return criterios
    except Exception as e:
        st.error(f"Erro ao carregar critérios: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# Função para carregar participantes de uma equipe
def carregar_participantes(id_equipe):
    try:
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor()
        query = '''
            SELECT nome 
            FROM tbl_participantes 
            WHERE id_equipe = %s
            ORDER BY nome;
        '''
        cursor.execute(query, (int(id_equipe),))  # Converter para int
        rows = cursor.fetchall()
        participantes = [row[0] for row in rows]
        return participantes
    except Exception as e:
        st.error(f"Erro ao carregar participantes: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# Função para carregar notas do jurado para uma equipe
def carregar_notas_jurado(id_equipe, id_jurado):
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()
        cursor = conn.cursor()
        query = '''
            SELECT 
                n.id_nota,
                c.id_criterio,
                c.nome AS criterio,
                n.nota,
                n.status
            FROM tbl_notas n
            JOIN tbl_criterios c ON n.id_criterio = c.id_criterio
            WHERE n.id_equipe = %s AND n.id_jurado = %s
              AND n.status IN ('votando', 'liberado')
            ORDER BY c.nome;
        '''
        cursor.execute(query, (int(id_equipe), int(id_jurado)))  # Converter para int
        rows = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=colunas)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar notas: {e}")
        return pd.DataFrame()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# Função para salvar notas
def salvar_notas(id_nota, nota):
    try:
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        query = '''
            UPDATE tbl_notas 
            SET nota = %s, status = 'ok'
            WHERE id_nota = %s;
        '''
        cursor.execute(query, (nota, int(id_nota)))  # Converter id_nota para int
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar notas: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()
        st_autorefresh(interval=2000, limit=1, key="logout_refresh")
# Função para exibir formulário de voto
def exibir_formulario_voto(id_equipe, id_jurado, criterios, participantes, modalidade):
    st.markdown("---")
    st.write(f"### Votação para a Equipe: **{participantes[0] if participantes else 'Sem Participantes'}**")
    st.write(f"**Modalidade:** {modalidade}")
    st.write(f"**Participantes:** " + ", ".join(participantes))
    
    # Carregar notas existentes
    df_notas = carregar_notas_jurado(id_equipe, id_jurado)
    
    if df_notas.empty:
        st.write("Todas as notas já foram salvas para esta equipe.")
        return
    
    with st.form(f"form_notas_{id_equipe}"):
        notas_dict = {}
        
        for index, row in df_notas.iterrows():
            id_nota = row['id_nota']
            criterio = row['criterio']
            nota_atual = row['nota']
            status_nota = row['status']
            
            if status_nota == 'ok':
                st.write(f"**{criterio}:** {nota_atual} (já salva)")
            else:
                nota_selecionada = st.selectbox(
                    f"{criterio}",
                    options=[6,7,8,9,10],
                    index=0 if nota_atual is None else nota_atual - 6,
                    key=f"nota_{id_equipe}_{id_nota}"
                )
                notas_dict[id_nota] = nota_selecionada
        
        submit_notas = st.form_submit_button("Salvar Notas")
        
        if submit_notas:
            # Verificar se todas as notas foram preenchidas
            notas_faltantes = df_notas[df_notas['status'] != 'ok']['id_nota'].tolist()
            notas_preenchidas = notas_dict.keys()
            if not all(id_nota in notas_preenchidas for id_nota in notas_faltantes):
                st.warning("Por favor, preencha todas as notas antes de salvar.")
            else:
                # Salvar as notas no banco de dados
                sucesso = True
                for id_nota, nota in notas_dict.items():
                    if nota is not None:
                        resultado_salvar = salvar_notas(id_nota, nota)
                        if not resultado_salvar:
                            sucesso = False
                if sucesso:
                    st.success("Notas salvas com sucesso!")
                    st_autorefresh(interval=2000, limit=1, key=f"refresh_{id_equipe}")  # Recarrega após 2 segundos
                else:
                    st.error("Ocorreu um erro ao salvar as notas.")

# Função para registrar jurado (apenas para fins de teste, deve ser removida ou protegida na produção)
def registrar_jurado(nome, login, senha):
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = '''
            INSERT INTO tbl_jurados (nome, login, senha)
            VALUES (%s, %s, %s)
            RETURNING id_jurado;
        '''
        cursor.execute(query, (nome, login, senha))
        id_jurado = cursor.fetchone()[0]
        conn.commit()
        st.success(f"Jurado '{nome}' registrado com sucesso! ID: {id_jurado}")
    except errors.UniqueViolation:
        st.error(f"Erro: O jurado com login '{login}' já existe.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao registrar o jurado: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn:
            conn.close()

# Função para registrar jurado via interface (somente para teste)
def registrar_jurado_interface():
    st.write("### Registrar Novo Jurado (Somente para Teste)")
    with st.form("form_registrar_jurado"):
        nome = st.text_input("Nome:")
        login = st.text_input("Login:")
        senha = st.text_input("Senha:", type="password")
        confirmar_senha = st.text_input("Confirmar Senha:", type="password")
        submit = st.form_submit_button("Registrar Jurado")
        
        if submit:
            if not nome or not login or not senha or not confirmar_senha:
                st.warning("Por favor, preencha todos os campos.")
            elif senha != confirmar_senha:
                st.warning("As senhas não coincidem.")
            else:
                registrar_jurado(nome, login, senha)

# Verifica se o usuário já está logado
if 'jurado_id' not in st.session_state:
    st.session_state['jurado_id'] = None
    st.session_state['jurado_nome'] = None

if st.session_state['jurado_id'] is None:
    # Tela de Login
    st.write("### Login de Jurado")
    with st.form("login_form"):
        login = st.text_input("Login:")
        senha = st.text_input("Senha:", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if login.strip() == "" or senha.strip() == "":
                st.warning("Por favor, preencha ambos os campos de login e senha.")
            else:
                resultado = autenticar_jurado(login.strip(), senha.strip())
                if resultado:
                    st.session_state['jurado_id'], st.session_state['jurado_nome'] = resultado
                    st.success(f"Bem-vindo, {st.session_state['jurado_nome']}!")
                    st_autorefresh(interval=2000, limit=1, key="login_refresh")  # Recarrega após 2 segundos
                else:
                    st.error("Credenciais inválidas. Por favor, tente novamente.")
    # Apenas para fins de teste, descomente a linha abaixo para acessar a interface de registro de jurados
    # registrar_jurado_interface()
else:
    # Usuário está logado
    st.sidebar.write(f"### Jurado: {st.session_state['jurado_nome']}")
    if st.sidebar.button("Logout"):
        st.session_state['jurado_id'] = None
        st.session_state['jurado_nome'] = None
        st_autorefresh(interval=2000, limit=1, key="logout_refresh")  # Recarrega após 2 segundos

    st.write(f"Bem-vindo, **{st.session_state['jurado_nome']}**! Aguardando equipes para votar.")

    # Carrega equipes em votação para o jurado atual
    df_equipes = carregar_equipes_votando(st.session_state['jurado_id'])

    if df_equipes.empty:
        st.info("Não há votações em andamento no momento. Aguardando atualização...")
        # Adiciona o autorefresh para verificar novamente em 5 segundos
        st_autorefresh(interval=5000, limit=100, key="voting_refresh")  # Recarrega a cada 5 segundos
    else:
        # Iterar sobre todas as equipes disponíveis para votação
        for index, equipe in df_equipes.iterrows():
            id_equipe_selecionada = equipe['id_equipe']
            nome_equipe = equipe['nome']
            grau_equipe = equipe['grau']
            ficha_tecnica = equipe['ficha_tecnica']
            modalidade = equipe['modalidade']
            id_modalidade = equipe['modalidade_id']  # Obtém o id_modalidade
            
            st.markdown("---")
            st.write(f"### Votação para a Equipe: **{nome_equipe}**")
            st.write(f"**Modalidade:** {modalidade}")
            st.write(f"**Grau:** {grau_equipe}")
            st.write(f"**Ficha Técnica:** {ficha_tecnica}")
            
            # Carregar participantes da equipe
            participantes = carregar_participantes(id_equipe_selecionada)
            if participantes:
                st.write("**Participantes:** " + ", ".join(participantes))
            else:
                st.write("**Participantes:** Sem participantes registrados.")
            
            # Carregar critérios da modalidade
            criterios = carregar_criterios(id_modalidade)  # Passa o id_modalidade correto
            if not criterios:
                st.warning("Não há critérios cadastrados para esta modalidade.")
            else:
                # Exibir formulário de voto para a equipe atual
                exibir_formulario_voto(id_equipe_selecionada, st.session_state['jurado_id'], criterios, participantes, modalidade)
