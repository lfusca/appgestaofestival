import streamlit as st
from . import main
from paginas import login

# Inicializa a página caso não esteja definida
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = 'login'

# Redireciona para a página de acordo com o estado
if st.session_state['pagina'] == 'login':
    login.show()
elif st.session_state['pagina'] == 'menu':
    main.show()
