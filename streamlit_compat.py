"""
Module de compatibilité pour différentes versions de Streamlit
"""
import streamlit as st
from packaging import version
import streamlit as st_module

def get_streamlit_version():
    """Retourne la version de Streamlit"""
    try:
        return st_module.__version__
    except:
        return "1.29.0"  # Version par défaut

def rerun():
    """Fonction de rechargement compatible toutes versions"""
    st_version = get_streamlit_version()
    
    try:
        # Streamlit >= 1.27
        if hasattr(st, 'rerun'):
            st.rerun()
        # Streamlit < 1.27
        elif hasattr(st, 'experimental_rerun'):
            st.experimental_rerun()
        else:
            # Fallback - recharge la page avec JavaScript
            st.markdown("""
            <script>
                window.parent.location.reload();
            </script>
            """, unsafe_allow_html=True)
    except Exception as e:
        print(f"Erreur rerun: {e}")
        # Fallback
        st.markdown("""
        <script>
            window.parent.location.reload();
        </script>
        """, unsafe_allow_html=True)

def clear_cache():
    """Nettoie le cache de manière compatible"""
    try:
        # Nouvelles versions
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        # Anciennes versions
        if hasattr(st, 'legacy_caching'):
            st.legacy_caching.clear_cache()
        if hasattr(st, 'caching'):
            st.caching.clear_cache()
        # Très anciennes versions
        if hasattr(st, 'cache'):
            if hasattr(st.cache, 'clear'):
                st.cache.clear()
    except Exception as e:
        print(f"Erreur clear cache: {e}")

def show_html(html_content, height=2000, scrolling=True):
    """Affiche du HTML de manière compatible"""
    try:
        # Essayer avec les paramètres standards
        st.components.v1.html(html_content, height=height, scrolling=scrolling)
    except TypeError:
        # Si erreur, essayer sans scrolling
        try:
            st.components.v1.html(html_content, height=height)
        except:
            # Dernier recours - iframe manuel
            import base64
            html_bytes = html_content.encode('utf-8')
            html_b64 = base64.b64encode(html_bytes).decode()
            iframe = f'''
            <iframe 
                src="data:text/html;base64,{html_b64}" 
                width="100%" 
                height="{height}"
                frameborder="0"
                style="border: none; width: 100%; height: {height}px;">
            </iframe>
            '''
            st.markdown(iframe, unsafe_allow_html=True)

def get_query_params():
    """Récupère les paramètres de requête de manière compatible"""
    try:
        # Nouvelles versions (>= 1.30)
        if hasattr(st, 'query_params'):
            params = st.query_params
            # Convertir en dict si nécessaire
            if hasattr(params, 'get_all'):
                result = {}
                for key in params:
                    result[key] = params.get_all(key)
                return result
            else:
                return dict(params)
        # Versions moyennes
        elif hasattr(st, 'experimental_get_query_params'):
            return st.experimental_get_query_params()
        # Anciennes versions
        else:
            return {}
    except:
        return {}

def set_query_params(**params):
    """Définit les paramètres de requête de manière compatible"""
    try:
        # Nouvelles versions (>= 1.30)
        if hasattr(st, 'query_params'):
            st.query_params.update(params)
        # Versions moyennes
        elif hasattr(st, 'experimental_set_query_params'):
            st.experimental_set_query_params(**params)
    except Exception as e:
        print(f"Erreur set query params: {e}")

# Test de compatibilité au chargement
if __name__ == "__main__":
    print(f"Streamlit version: {get_streamlit_version()}")
    print(f"Rerun disponible: {hasattr(st, 'rerun')}")
    print(f"Experimental rerun disponible: {hasattr(st, 'experimental_rerun')}")
    print(f"Cache_data disponible: {hasattr(st, 'cache_data')}")
    print(f"Query_params disponible: {hasattr(st, 'query_params')}")