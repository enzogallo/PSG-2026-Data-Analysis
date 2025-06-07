import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import base64
import os
from streamlit_card import card
 
# Configuration de la page
st.set_page_config(
    page_title="PSG Data Center 2024-2025",
    page_icon="⚽",
    layout="wide"
)

# Chargement du CSS
try:
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.error("Le fichier styles.css est introuvable. Assurez-vous qu'il est dans le même répertoire que app.py.")

# ----------------------------
# FONCTIONS FBREF
# ----------------------------
def get_player_position(pos):
    """Détermine la position principale d'un joueur"""
    if pd.isna(pos):
        return 'Unknown'
    
    pos = str(pos).strip()
    
    # Gardiens
    if 'GK' in pos:
        return 'GK'
    
    # Défenseurs
    if 'DF' in pos or 'CB' in pos or 'LB' in pos or 'RB' in pos or 'WB' in pos:
        return 'DF'
    
    # Milieux
    if 'MF' in pos or 'DM' in pos or 'CM' in pos or 'AM' in pos:
        return 'MF'
    
    # Attaquants
    if 'FW' in pos or 'ST' in pos or 'LW' in pos or 'RW' in pos or 'CF' in pos:
        return 'FW'
    
    return 'Unknown'

def get_detailed_position(pos):
    """Détermine la position détaillée d'un joueur"""
    if pd.isna(pos):
        return 'Unknown'
    
    pos = str(pos).strip()
    
    # Gardiens
    if 'GK' in pos:
        return 'Gardien'
    
    # Défenseurs
    if 'CB' in pos:
        return 'Défenseur Central'
    if 'LB' in pos:
        return 'Latéral Gauche'
    if 'RB' in pos:
        return 'Latéral Droit'
    if 'WB' in pos:
        return 'Arrière Latéral'
    if 'DF' in pos:
        return 'Défenseur'
    
    # Milieux
    if 'DM' in pos:
        return 'Milieu Défensif'
    if 'CM' in pos:
        return 'Milieu Central'
    if 'AM' in pos:
        return 'Milieu Offensif'
    if 'MF' in pos:
        return 'Milieu'
    
    # Attaquants
    if 'ST' in pos:
        return 'Attaquant'
    if 'LW' in pos:
        return 'Ailier Gauche'
    if 'RW' in pos:
        return 'Ailier Droit'
    if 'CF' in pos:
        return 'Attaquant de Pointe'
    if 'FW' in pos:
        return 'Attaquant'
    
    return 'Unknown'

@st.cache_data
def load_fbref_data():
    """Charge les données FBref du PSG pour la saison 2024-2025"""
    standard_stats = pd.read_csv('data/PSG Standard Stats.csv')
    shooting_stats = pd.read_csv('data/PSG Shooting.csv')
    passing_stats = pd.read_csv('data/PSG Passing.csv')
    possession_stats = pd.read_csv('data/PSG Possession.csv')
    playing_time = pd.read_csv('data/PSG Playing Time.csv')
    goalkeeping_stats = pd.read_csv('data/PSG Goalkeeping.csv')
    
    # Nettoyage des données
    for df in [standard_stats, shooting_stats, passing_stats, possession_stats, playing_time, goalkeeping_stats]:
        df['Player'] = df['Player'].str.strip()
        if 'Pos' in df.columns:
            df['Pos'] = df['Pos'].str.strip()
            # Ajout des colonnes de position
            df['Position'] = df['Pos'].apply(get_player_position)
            df['Position_Detail'] = df['Pos'].apply(get_detailed_position)
    
    return {
        'standard': standard_stats,
        'shooting': shooting_stats,
        'passing': passing_stats,
        'possession': possession_stats,
        'playing_time': playing_time,
        'goalkeeping': goalkeeping_stats,
        'field_players_standard': standard_stats[standard_stats['Position'] != 'GK'].copy(),
        'field_players_shooting': shooting_stats[shooting_stats['Pos'].str.contains('GK') == False].copy(),
        'field_players_passing': passing_stats[passing_stats['Pos'].str.contains('GK') == False].copy(),
        'field_players_possession': possession_stats[possession_stats['Pos'].str.contains('GK') == False].copy()
    }

def create_scatter_plot(data, x_col, y_col, color_col, size_col, title, hover_data=None):
    """Crée un graphique de dispersion personnalisé"""
    fig = go.Figure()
    
    for _, row in data.iterrows():
        if pd.notna(row[size_col]):
            fig.add_trace(go.Scatter(
                x=[row[x_col]],
                y=[row[y_col]],
                mode='markers+text',
                name=row['Player'],
                text=[row['Player']],
                textposition="top center",
                marker=dict(
                    size=float(row[size_col])/100,
                    color=float(row[color_col]),
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title=color_col)
                ),
                hovertemplate=(
                    f"Joueur: {row['Player']}<br>"
                    + "<br>".join([f"{col}: {row[col]}" for col in hover_data])
                )
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        showlegend=False
    )
    
    return fig

def display_player_metrics(player_data, player_passing, player_shooting):
    """Affiche les métriques d'un joueur"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Matches joués", player_data['MP'])
        st.metric("Minutes jouées", player_data['Min'])
        st.metric("Buts", player_data['Gls'])
        st.metric("Passes décisives", player_data['Ast'])
    
    with col2:
        st.metric("xG", round(player_data['xG'], 2))
        st.metric("xAG", round(player_data['xAG'], 2))
        st.metric("Tirs", player_shooting['Sh'])
        st.metric("Tirs cadrés", player_shooting['SoT'])
    
    with col3:
        st.metric("Précision des passes", f"{player_passing['Cmp%']}%")
        st.metric("Passes progressives", player_passing['PrgP'])
        st.metric("Passes clés", player_passing['KP'])
        st.metric("Centres", player_passing['CrsPA'])

def display_position_metrics(position_players):
    """Affiche les métriques moyennes par position"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Buts moyens", round(position_players['Gls'].mean(), 2))
        st.metric("Passes décisives moyennes", round(position_players['Ast'].mean(), 2))
    
    with col2:
        st.metric("xG moyen", round(position_players['xG'].mean(), 2))
        st.metric("xAG moyen", round(position_players['xAG'].mean(), 2))
    
    with col3:
        st.metric("Minutes jouées moyennes", round(position_players['Min'].mean(), 2))
        st.metric("Matches joués moyens", round(position_players['MP'].mean(), 2))

def render_overview():
    """Affiche la vue d'ensemble des performances de l'équipe"""
    data = load_fbref_data()
    
    # Utiliser les données des joueurs de champ
    field_player_data = data['field_players_standard'].copy()
    
    # Conversion des colonnes numériques
    numeric_columns = ['Gls', 'Ast', 'xG', 'xAG', 'Min', 'MP']
    for col in numeric_columns:
        if col in field_player_data.columns:
            field_player_data[col] = pd.to_numeric(field_player_data[col], errors='coerce')
    
    # Calcul des statistiques par 90 minutes
    field_player_data['Gls/90'] = (field_player_data['Gls'] * 90) / field_player_data['Min'].replace(0, np.nan)
    field_player_data['Ast/90'] = (field_player_data['Ast'] * 90) / field_player_data['Min'].replace(0, np.nan)
    
    # Statistiques globales 
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_goals = field_player_data['Gls'].sum()
        total_assists = field_player_data['Ast'].sum()
        st.metric("Buts marqués ", int(total_goals))
        st.metric("Passes décisives ", int(total_assists))
    
    with col2:
        avg_xg = field_player_data['xG'].mean()
        avg_xag = field_player_data['xAG'].mean()
        st.metric("xG moyen par joueur ", round(avg_xg, 2))
        st.metric("xAG moyen par joueur ", round(avg_xag, 2))
    
    with col3:
        total_minutes = field_player_data['Min'].sum()
        total_matches = field_player_data['MP'].sum()
        st.metric("Minutes jouées ", int(total_minutes))
        st.metric("Matches joués ", int(total_matches))
    
    # Top 5 buteurs 
    st.markdown("""<h2 style='color: white; font-size: 1.8rem; font-weight: 700; font-family: \"Poppins\", sans-serif;'>Top 5 Buteurs </h2>""", unsafe_allow_html=True)
    top_scorers = field_player_data.nlargest(5, 'Gls')[['Player', 'Gls', 'xG', 'Gls/90']]
    fig_scorers = px.bar(top_scorers, x='Player', y='Gls',
                        title='',
                        color='Gls',
                        color_continuous_scale='Blues')
    st.plotly_chart(fig_scorers, use_container_width=True)
    
    # Top 5 passeurs 
    st.markdown("""<h2 style='color: white; font-size: 1.8rem; font-weight: 700; font-family: \"Poppins\", sans-serif;'>Top 5 Passeurs </h2>""", unsafe_allow_html=True)
    top_assists = field_player_data.nlargest(5, 'Ast')[['Player', 'Ast', 'xAG', 'Ast/90']]
    fig_assists = px.bar(top_assists, x='Player', y='Ast',
                        title='',
                        color='Ast',
                        color_continuous_scale='Greens')
    st.plotly_chart(fig_assists, use_container_width=True)

def get_player_photo(player_name):
    """Récupère le chemin de la photo d'un joueur"""
    import os
    
    # Mapping des noms de joueurs vers les noms de fichiers
    player_photo_mapping = {
        'Arnau Tenas': 'profile_23-24_0000_tenas.png',
        'Gianluigi Donnarumma': 'profile_24-25_donnarumma.png',
        'Matvei Safonov': 'profile_24-25_safonov.png',
        'Achraf Hakimi': 'profile_23-24_0017_hakimi.png',
        'Presnel Kimpembe': 'profile_23-24_0016_kimpembe.png',
        'Marquinhos': 'profile_23-24_0004_marquinhos.png',
        'Lucas Hernández': 'profile_23-24_lucashernandez2.png',
        'Nuno Mendes': 'profile_23-24_0003_nuno.png',
        'Lucas Beraldo': 'profile_23-24_0020_beraldo.png',
        'Yoram Zague': 'profile_24-25_zague.png',
        'Naoufel El Hannach': 'profile_24-25-elhannach-25.png',
        'Warren Zaïre-Emery': 'profile_23-24_0005_zaire.png',
        'Vitinha': 'profile_23-24_0006_vitinha.png',
        'Fabián Ruiz Peña': 'profile_23-24_0010_ruiz.png',
        'Gonçalo Ramos': 'profile_23-24_0011_ramos.png',
        'Ousmane Dembélé': 'profile_23-24_0018_dembele.png',
        'Lee Kang-in': 'profile_23-24_0014_lee.png',
        'João Neves': 'profile_23-24_neves.png',
        'Ibrahim Mbaye': 'profile_24-25_mbaye.png',
        'Bradley Barcola': 'profile_24-25_barcolav2.png',
        'Désiré Doué': 'profile_24-25_doue.png',
        'Khvicha Kvaratskhelia': 'khvicha-2425-profile.png',
        'Willian Pacho': 'profile_23-24_wpacho.png',
        'Senny Mayulu': 'profile_23-24_mayuluv2.png'
    }
    
    photo_name = player_photo_mapping.get(player_name)
    if photo_name:
        # Utilisation d'un chemin absolu
        base_path = os.path.dirname(os.path.abspath(__file__))
        photo_path = os.path.join(base_path, 'assets', 'player_photos', photo_name)
        
        # Vérification de l'existence du fichier
        if os.path.exists(photo_path):
            return photo_path
        else:
            st.warning(f"Photo non trouvée pour {player_name} à {photo_path}")
            return None
    return None

def render_player_analysis():
    """Affiche l'analyse détaillée par joueur"""
    data = load_fbref_data()

    # Utiliser les données des joueurs de champ
    field_players_standard = data['field_players_standard'].copy()
    field_players_shooting = data['field_players_shooting'].copy()
    field_players_passing = data['field_players_passing'].copy()
    field_players_possession = data['field_players_possession'].copy()

    # Sélection du joueur (parmi les joueurs de champ)
    player_names = field_players_standard['Player'].tolist()
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="player_analysis_select")

    # Affichage de la photo du joueur et des métriques de base
    photo_path = get_player_photo(selected_player)
    if photo_path:
        try:
            col1, col2, col3, col4 = st.columns([2, 0.5, 3, 1])
            with col1:
                st.image(photo_path, width=800, use_container_width=True)
            with col3:
                st.markdown(f'''<h2 style='color: white; font-size: 1.8rem; font-weight: 700; font-family: "Poppins", sans-serif;'>Analyse de {selected_player}</h2>''', unsafe_allow_html=True)
                
                # Informations de base
                player_data = field_players_standard[field_players_standard['Player'] == selected_player]

                if player_data.empty:
                    st.warning(f"Aucune donnée trouvée pour {selected_player} dans les statistiques standard.")
                    return

                # Fusionner avec les données de possession pour avoir toutes les métriques
                player_possession_data = field_players_possession[field_players_possession['Player'] == selected_player]
                if not player_possession_data.empty:
                    player_data = pd.merge(player_data, player_possession_data, on='Player', how='left', suffixes=('_standard', '_possession'))
                else:
                    st.warning(f"Aucune donnée de possession trouvée pour {selected_player}.")

                player_data = player_data.iloc[0] # Récupérer la ligne unique si elle existe

                player_shooting_data = field_players_shooting[field_players_shooting['Player'] == selected_player]
                player_passing_data = field_players_passing[field_players_passing['Player'] == selected_player]

                # Affichage des métriques
                col_metrics1, col_metrics2, col_metrics3 = st.columns(3)

                with col_metrics1:
                    st.metric("Matches joués", player_data['MP'])
                    st.metric("Minutes jouées", player_data['Min'])
                    st.metric("Buts", int(player_data['Gls']))
                    st.metric("Passes décisives", int(player_data['Ast']))

                with col_metrics2:
                    st.metric("xG", round(player_data['xG'], 2))
                    st.metric("xAG", round(player_data['xAG'], 2))
                    if not player_shooting_data.empty:
                        st.metric("Tirs", player_shooting_data.iloc[0]['Sh'])
                        st.metric("Tirs cadrés", player_shooting_data.iloc[0]['SoT'])
                    else:
                        st.text("Tirs : N/A")
                        st.text("Tirs cadrés : N/A")

                with col_metrics3:
                    if not player_passing_data.empty:
                        st.metric("Précision des passes", f"{player_passing_data.iloc[0]['Cmp%']}% ")
                        st.metric("Passes progressives", player_passing_data.iloc[0]['PrgP'])
                        st.metric("Passes clés", player_passing_data.iloc[0]['KP'])
                        st.metric("Centres", player_passing_data.iloc[0]['CrsPA'])
                    else:
                        st.text("Précision des passes : N/A")
                        st.text("Passes progressives : N/A")
                        st.text("Passes clés : N/A")
                        st.text("Centres : N/A")

                
        except Exception as e:
            st.error(f"Erreur lors de l'affichage de la photo : {str(e)}")
            st.subheader(f"Analyse de {selected_player}")
    else:
        st.subheader(f"Analyse de {selected_player}")

    # Graphiques de performance
    st.markdown('''<h2 style='color: white; font-size: 1.8rem; font-weight: 700; font-family: "Poppins", sans-serif;'>Performance offensive</h2>''', unsafe_allow_html=True)
    fig_offensive = go.Figure()

    fig_offensive.add_trace(go.Bar(
        name='Réalisé',
        x=['Buts', 'Passes décisives'],
        y=[player_data['Gls'], player_data['Ast']],
        marker_color=['#1f77b4', '#ff7f0e']
    ))

    fig_offensive.add_trace(go.Bar(
        name='Attendu',
        x=['xG', 'xAG'],
        y=[player_data['xG'], player_data['xAG']],
        marker_color=['#2ca02c', '#d62728']
    ))

    fig_offensive.update_layout(
        title='Performance offensive',
        barmode='group',
        showlegend=True
    )
    

    st.plotly_chart(fig_offensive, use_container_width=True)

    # Graphique radar des performances défensives
    st.markdown('''<h2 style='color: white; font-size: 1.8rem; font-weight: 700; font-family: "Poppins", sans-serif;'>Performance défensive</h2>''', unsafe_allow_html=True)
    
    # Création du graphique radar
    defensive_metrics = {
        'Touches défensives': float(player_data['Def 3rd']) if 'Def 3rd' in player_data else 0,
        'Dribbles subis': float(player_data['Tkld']) if 'Tkld' in player_data else 0,
        'Dribbles réussis': float(player_data['Succ']) if 'Succ' in player_data else 0,
        'Cartons jaunes': float(player_data['CrdY']) if 'CrdY' in player_data else 0,
        'Cartons rouges': float(player_data['CrdR']) if 'CrdR' in player_data else 0,
        'Touches totales': float(player_data['Touches']) if 'Touches' in player_data else 0
    }

    # Normalisation des valeurs pour le radar chart
    max_values = {
        'Touches défensives': 2000,
        'Dribbles subis': 100,
        'Dribbles réussis': 100,
        'Cartons jaunes': 10,
        'Cartons rouges': 2,
        'Touches totales': 4000
    }

    normalized_values = {
        metric: (value / max_values[metric]) * 100 
        for metric, value in defensive_metrics.items()
    }

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=list(normalized_values.values()),
        theta=list(normalized_values.keys()),
        fill='toself',
        name=selected_player,
        line_color='#8B0000'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=True,
                tickfont=dict(color='white')
            )
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Légende des performances
    st.markdown("""
    **Légende des performances défensives :**
    - Touches défensives : Nombre de touches dans le tiers défensif
    - Dribbles subis : Nombre de dribbles subis
    - Dribbles réussis : Nombre de dribbles réussis
    - Cartons jaunes : Nombre de cartons jaunes reçus
    - Cartons rouges : Nombre de cartons rouges reçus
    - Touches totales : Nombre total de touches du ballon
    """)

def render_position_analysis():
    """Affiche l'analyse par position"""
    data = load_fbref_data()
    
    # Conversion des colonnes numériques
    numeric_columns = ['Gls', 'Ast', 'xG', 'xAG', 'Min', 'MP']
    for col in numeric_columns:
        if col in data['standard'].columns:
            data['standard'][col] = pd.to_numeric(data['standard'][col], errors='coerce')
    
    # Sélection de la position
    positions = ['FW', 'MF', 'DF', 'GK']
    position_names = {
        'FW': 'Attaquants',
        'MF': 'Milieux',
        'DF': 'Défenseurs',
        'GK': 'Gardiens'
    }
    selected_position = st.selectbox("Sélectionnez une position", positions, key="position_analysis_select", format_func=lambda x: position_names[x])
    
    # Filtrage des joueurs par position
    position_players = data['standard'][data['standard']['Position'] == selected_position]

    if position_players.empty:
        st.info(f"Aucune donnée trouvée pour la position {position_names[selected_position]}.")
        return
    
    # Statistiques moyennes par position
    st.markdown(f'''<h2 style='color: white; font-size: 1.8rem; font-weight: 700; font-family: "Poppins", sans-serif;'>Statistiques moyennes - {position_names[selected_position]}</h2>''', unsafe_allow_html=True)
    display_position_metrics(position_players)
    
    # Graphique de dispersion
    fig = create_scatter_plot(
        position_players,
        'Gls', 'Ast', 'Gls', 'Min',
        f'Buts vs Passes décisives - {position_names[selected_position]}',
        ['Gls', 'Ast', 'xG', 'xAG', 'Min']
        )

    st.plotly_chart(fig, use_container_width=True)

def render_comparisons():
    """Affiche les comparaisons entre joueurs"""
    data = load_fbref_data()
    
    st.header("Comparaison de joueurs")
    
    # Utiliser les données des joueurs de champ pour la sélection
    field_players_standard = data['field_players_standard'].copy()
    
    # Sélection des joueurs à comparer (parmi les joueurs de champ)
    player_names = field_players_standard['Player'].tolist()
    selected_players = st.multiselect("Sélectionnez les joueurs à comparer", player_names, max_selections=3, key="comparison_select")
    
    if len(selected_players) > 0:
        # Filtrage des données pour les joueurs sélectionnés (utilisant les données complètes pour les métriques)
        comparison_data = data['standard'][data['standard']['Player'].isin(selected_players)].copy()
        
        if comparison_data.empty:
             st.info("Aucune donnée trouvée pour les joueurs sélectionnés.")
             return
        
        # Affichage des photos et des noms
        cols = st.columns(len(selected_players))
        for i, player in enumerate(selected_players):
            with cols[i]:
                photo_path = get_player_photo(player)
                if photo_path:
                    try:
                        st.image(photo_path, width=300, use_container_width='auto')
                    except Exception as e:
                        st.error(f"Erreur lors de l'affichage de la photo de {player}: {str(e)}")
                st.subheader(player)
        
        # Création du graphique de comparaison
        metrics = ['Gls', 'Ast', 'xG', 'xAG', 'PrgC', 'PrgP']
        metric_names = ['Buts', 'Passes décisives', 'xG', 'xAG', 'Progrès porté', 'Passes progressives']
        
        # Récupérer les données des joueurs sélectionnés avec les métriques nécessaires
        # Assurez-vous que toutes les métriques existent pour éviter les erreurs
        comparison_metrics_data = comparison_data[['Player'] + [m for m in metrics if m in comparison_data.columns]]

        # Gérer les valeurs NaN pour le graphique
        for col in comparison_metrics_data.columns:
            if col != 'Player':
                 comparison_metrics_data[col] = pd.to_numeric(comparison_metrics_data[col], errors='coerce').fillna(0)

        fig_comparison = go.Figure()
        
        for i, player in enumerate(selected_players):
            player_metrics_row = comparison_metrics_data[comparison_metrics_data['Player'] == player]
            if not player_metrics_row.empty:
                player_metrics = player_metrics_row.iloc[0]
                # S'assurer que les métriques existent avant de les utiliser pour y et text
                y_values = [player_metrics[metric] if metric in player_metrics else 0 for metric in metrics if metric in comparison_metrics_data.columns]
                text_values = [round(player_metrics[metric], 2) if metric in player_metrics else "N/A" for metric in metrics if metric in comparison_metrics_data.columns]

                fig_comparison.add_trace(go.Bar(
                    name=player,
                    x=[metric_names[metrics.index(m)] for m in metrics if m in comparison_metrics_data.columns], # Utiliser les noms d'affichage corrects
                    y=y_values,
                    text=text_values,
                    textposition='auto',
                ))
        
        fig_comparison.update_layout(
            title='Comparaison des performances',
            barmode='group',
            showlegend=True
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
    else:
        st.info("Sélectionnez des joueurs pour afficher la comparaison.")

def analyze_tactical_performance():
    """Analyse des performances tactiques de l'équipe"""
    data = load_fbref_data()
    
    st.header("Analyse Tactique")
    
    # Analyse des phases de jeu
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Possession et Progression")
        possession_metrics = {
            "Passes progressives": f"{data['passing']['PrgP'].mean():.1f}",
            "Passes complétées": f"{data['passing']['Cmp'].mean():.1f}",
            "Précision des passes": f"{data['passing']['Cmp%'].mean():.1f}%",
            "Distance totale des passes": f"{data['passing']['TotDist'].mean():.1f}"
        }
        for metric, value in possession_metrics.items():
            st.metric(metric, value)
    
    with col2:
        st.subheader("Efficacité offensive")
        offensive_metrics = {
            "xG par match": f"{data['standard']['xG'].mean():.2f}",
            "Précision des tirs": f"{data['shooting']['SoT%'].mean():.1f}%",
            "Passes clés": f"{data['passing']['KP'].mean():.1f}",
            "Centres réussis": f"{data['passing']['CrsPA'].mean():.1f}"
        }
        for metric, value in offensive_metrics.items():
            st.metric(metric, value)
    
    # Analyse des profils de joueurs
    st.subheader("Profils de Joueurs")
    
    # Création d'un radar chart pour les profils
    positions = ['FW', 'MF', 'DF']
    selected_pos = st.selectbox("Sélectionnez une position pour l'analyse des profils", positions)
    
    position_players = data['standard'][data['standard']['Pos'].str.contains(selected_pos, na=False)]
    
    # Calcul des métriques normalisées pour chaque joueur
    metrics = ['Gls', 'Ast', 'xG', 'xAG', 'PrgP', 'PrgC']
    metric_names = ['Buts', 'Passes', 'xG', 'xAG', 'Progression', 'Création']
    
    for _, player in position_players.iterrows():
        values = []
        for metric in metrics:
            if metric in player:
                # Normalisation par rapport à la moyenne de la position
                normalized_value = (player[metric] - position_players[metric].mean()) / position_players[metric].std()
                values.append(max(0, normalized_value + 2))  # Ajustement pour avoir des valeurs positives
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metric_names,
            fill='toself',
            name=player['Player']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 4]
                )
            ),
            title=f"Profil de {player['Player']}",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

def analyze_team_strengths():
    """Analyse des forces et faiblesses de l'équipe"""
    data = load_fbref_data()
    
    st.header("Analyse des Forces et Faiblesses")
    
    # Analyse des forces
    st.subheader("Forces de l'Équipe")
    
    # Création d'un graphique en barres pour les statistiques clés
    key_stats = {
        'Buts': data['standard']['Gls'].sum(),
        'xG': data['standard']['xG'].sum(),
        'Passes décisives': data['standard']['Ast'].sum(),
        'xAG': data['standard']['xAG'].sum(),
        'Passes progressives': data['passing']['PrgP'].sum(),
        'Dribbles réussis': data['possession']['Succ'].sum()
    }
    
    fig_strengths = go.Figure(data=[
        go.Bar(
            x=list(key_stats.keys()),
            y=list(key_stats.values()),
            marker_color='#1f77b4'
        )
    ])
    
    fig_strengths.update_layout(
        title="Statistiques Offensives",
        xaxis_title="Métriques",
        yaxis_title="Valeur Totale"
    )
    
    st.plotly_chart(fig_strengths, use_container_width=True)
    
    # Analyse des faiblesses
    st.subheader("Faiblesses de l'Équipe")
    
    # Création d'un graphique en barres pour les statistiques clés de faiblesse
    # Récupération des données nécessaires
    shooting_data = data['shooting']
    passing_data = data['passing']
    possession_data = data['possession']
    standard_data = data['standard']
    
    # Calcul des métriques de faiblesse (moyennes ou sommes selon la métrique)
    weakness_stats = {
        '% Tirs cadrés (moyen)': shooting_data['SoT%'].mean() if 'SoT%' in shooting_data.columns else 0,
        '% Passes réussies (moyen)': passing_data['Cmp%'].mean() if 'Cmp%' in passing_data.columns else 0,
        'Ballons perdus (total)': possession_data['Dis'].sum() if 'Dis' in possession_data.columns else 0,
        'Cartons jaunes (total)': standard_data['CrdY'].sum() if 'CrdY' in standard_data.columns else 0,
        'Cartons rouges (total)': standard_data['CrdR'].sum() if 'CrdR' in standard_data.columns else 0
    }
    
    # Convertir les pourcentages en valeurs pour une meilleure visualisation si nécessaire, ou adapter le graphique
    # Pour le graphique à barres, afficher les valeurs brutes est acceptable avec des étiquettes claires
    
    fig_weaknesses = go.Figure(data=[
        go.Bar(
            x=list(weakness_stats.keys()),
            y=list(weakness_stats.values()),
            marker_color=['#d62728', '#ff7f0e', '#1f77b4', '#9467bd', '#8c564b'] # Couleurs pour les faiblesses
        )
    ])
    
    fig_weaknesses.update_layout(
        title="Statistiques des Faiblesses",
        xaxis_title="Métriques",
        yaxis_title="Quantité (Total ou Moyenne)"
    )
    
    st.plotly_chart(fig_weaknesses, use_container_width=True)
    
    # Analyse des profils de position
    st.subheader("Analyse par Position")
    
    positions = ['FW', 'MF', 'DF']
    for pos in positions:
        pos_players = data['standard'][data['standard']['Pos'].str.contains(pos, na=False)]
        
        st.write(f"### {pos}")
        
        # Calcul des moyennes par position
        pos_metrics = {
            'Buts': pos_players['Gls'].mean(),
            'Passes décisives': pos_players['Ast'].mean(),
            'xG': pos_players['xG'].mean(),
            'xAG': pos_players['xAG'].mean()
        }
        
        col1, col2, col3, col4 = st.columns(4)
        for (metric, value), col in zip(pos_metrics.items(), [col1, col2, col3, col4]):
            with col:
                st.metric(metric, f"{value:.2f}")

def analyze_player_roles():
    """Analyse des rôles et profils des joueurs"""
    data = load_fbref_data()

    st.header("Analyse des Rôles et Profils")

    # Utiliser les données des joueurs de champ
    field_players_standard = data['field_players_standard'].copy()
    field_players_shooting = data['field_players_shooting'].copy()
    field_players_passing = data['field_players_passing'].copy()

    # Sélection du joueur (parmi les joueurs de champ)
    player_names = field_players_standard['Player'].tolist()
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="player_roles_select")

    # Récupération des données du joueur
    player_data = field_players_standard[field_players_standard['Player'] == selected_player]

    if player_data.empty:
        st.warning(f"Aucune donnée standard trouvée pour {selected_player}.")
        return

    player_data = player_data.iloc[0]
    player_passing_data = field_players_passing[field_players_passing['Player'] == selected_player]
    player_shooting_data = field_players_shooting[field_players_shooting['Player'] == selected_player]

    # --- Affichage de la photo et du graphique radar côte à côte ---
    col_photo, space, col_radar = st.columns([1, 1, 2]) # Ajuster les proportions si nécessaire

    with col_photo:
        # Affichage de la photo du joueur
        photo_path = get_player_photo(selected_player)
        if photo_path:
            try:
                st.image(photo_path, width=200, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur lors de l'affichage de la photo : {str(e)}")
        st.subheader(selected_player)

    with col_radar:
        st.subheader("Profil de performance")

        # Profil du joueur (métriques pour le radar chart)
        metrics = {
            'Buts': player_data['Gls'],
            'Passes décisives': player_data['Ast'],
            'xG': player_data['xG'],
            'xAG': player_data['xAG'],
        }

        if not player_passing_data.empty and 'KP' in player_passing_data.iloc[0]:
             metrics['Passes clés'] = player_passing_data.iloc[0]['KP']

        if not player_shooting_data.empty and 'SoT' in player_shooting_data.iloc[0]:
             metrics['Tirs cadrés'] = player_shooting_data.iloc[0]['SoT']

        metrics_to_plot = {k: v for k, v in metrics.items() if pd.notna(v)}

        if not metrics_to_plot:
             st.info("Pas assez de données pour afficher le profil du joueur.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=list(metrics_to_plot.values()),
                theta=list(metrics_to_plot.keys()),
                fill='toself',
                name=selected_player
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(metrics_to_plot.values()) * 1.2 if metrics_to_plot else 100]
                    )
                ),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

    # --- Affichage des métriques détaillées en dessous ---
    st.markdown('''<h3 style='color: white; font-size: 1.4rem; font-weight: 700; font-family: "Poppins", sans-serif;'>Métriques détaillées</h3>''', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Matches joués", player_data['MP'])
        st.metric("Minutes jouées", player_data['Min'])
        st.metric("Buts", player_data['Gls'])
        st.metric("Passes décisives", player_data['Ast'])

    with col2:
        if not player_data.empty and 'xG' in player_data:
             st.metric("xG", round(player_data['xG'], 2))
        else:
             st.text("xG : N/A")

        if not player_data.empty and 'xAG' in player_data:
             st.metric("xAG", round(player_data['xAG'], 2))
        else:
             st.text("xAG : N/A")

        if not player_shooting_data.empty and 'Sh' in player_shooting_data.iloc[0]:
             st.metric("Tirs", player_shooting_data.iloc[0]['Sh'])
        else:
             st.text("Tirs : N/A")

        if not player_shooting_data.empty and 'SoT' in player_shooting_data.iloc[0]:
             st.metric("Tirs cadrés", player_shooting_data.iloc[0]['SoT'])
        else:
             st.text("Tirs cadrés : N/A")

    with col3:
        if not player_passing_data.empty and 'Cmp%' in player_passing_data.iloc[0]:
             st.metric("Précision des passes", f"{player_passing_data.iloc[0]['Cmp%']}% ")
        else:
             st.text("Précision des passes : N/A")

        if not player_passing_data.empty and 'PrgP' in player_passing_data.iloc[0]:
             st.metric("Passes progressives", player_passing_data.iloc[0]['PrgP'])
        else:
             st.text("Passes progressives : N/A")

        if not player_passing_data.empty and 'KP' in player_passing_data.iloc[0]:
              st.metric("Passes clés", player_passing_data.iloc[0]['KP'])
        else:
              st.text("Passes clés : N/A")

        if not player_passing_data.empty and 'CrsPA' in player_passing_data.iloc[0]:
             st.metric("Centres", player_passing_data.iloc[0]['CrsPA'])
        else:
             st.text("Centres : N/A")

def analyze_team_dynamics():
    """Analyse des dynamiques d'équipe"""
    data = load_fbref_data()
    
    st.header("Dynamiques d'Équipe")
    
    # Conversion des colonnes numériques
    numeric_columns = ['Gls', 'Ast', 'xG', 'xAG', 'Min', 'MP']
    for col in numeric_columns:
        if col in data['standard'].columns:
            data['standard'][col] = pd.to_numeric(data['standard'][col], errors='coerce')
    
    # Analyse des duos
    st.subheader("Duos les Plus Efficaces")
    
    # Création d'un graphique en barres pour les meilleurs buteurs
    top_scorers = data['standard'].nlargest(5, 'Gls')[['Player', 'Gls', 'Ast']]
    fig_scorers = px.bar(top_scorers, 
                        x='Player', 
                        y=['Gls', 'Ast'],
                        title='Top 5 buteurs et leurs passes décisives',
                        barmode='group',
                        color_discrete_sequence=['#1f77b4', '#ff7f0e'])
    
    st.plotly_chart(fig_scorers, use_container_width=True)
    
    # Analyse des profils de position
    st.subheader("Profils par Position")
    
    positions = ['FW', 'MF', 'DF']
    selected_position = st.selectbox("Sélectionnez une position", positions, key="position_dynamics_select")
    
    pos_players = data['standard'][data['standard']['Pos'].str.contains(selected_position, na=False)]
    
    st.write(f"### {selected_position}")
    display_position_metrics(pos_players)
    
    # Graphique de dispersion
    fig = create_scatter_plot(
        pos_players,
        'Gls', 'Ast', 'xG', 'Min',
        f'Buts vs Passes décisives - {selected_position}',
        ['Gls', 'Ast', 'xG', 'xAG', 'Min']
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analyze_tactical_patterns():
    """Analyse des patterns tactiques de l'équipe"""
    data = load_fbref_data()

    st.header("Analyse Tactique Avancée")

    # Analyse des phases de jeu
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Phases de Jeu")
        # Calcul des métriques de pressing avec les colonnes disponibles
        # Arrondissement des valeurs
        pressing_metrics = {
            "Passes complétées": round(data['passing']['Cmp'].mean(), 2),
            "Précision des passes": f"{data['passing']['Cmp%'].mean():.1f}%",
            "Passes progressives": round(data['passing']['PrgP'].mean(), 2),
            "Passes clés": round(data['passing']['KP'].mean(), 2)
        }

        for metric, value in pressing_metrics.items():
            st.metric(metric, value)

    with col2:
        st.subheader("Progression du Jeu")
        # Arrondissement des valeurs
        progression_metrics = {
            "Passes progressives": round(data['passing']['PrgP'].mean(), 2),
            "Progression portée": round(data['standard']['PrgC'].mean(), 2),
            "Progression reçue": round(data['standard']['PrgR'].mean(), 2),
            "Distance totale des passes": f"{data['passing']['TotDist'].mean():.1f}"
        }

        for metric, value in progression_metrics.items():
            st.metric(metric, value)

    # Analyse de la Progression par Position
    st.subheader("Progression par Position")

    positions = ['FW', 'MF', 'DF']
    progression_data = data['standard'][data['standard']['Pos'].str.contains('|'.join(positions), na=False)].copy()

    # Assurez-vous que les colonnes de progression sont numériques
    progression_cols = ['PrgC', 'PrgP', 'PrgR']
    for col in progression_cols:
        if col in progression_data.columns:
            progression_data[col] = pd.to_numeric(progression_data[col], errors='coerce').fillna(0)

    # Calculer les moyennes par position
    avg_progression_by_pos = progression_data.groupby('Pos')[progression_cols].mean().reset_index()

    # Renommer les colonnes pour le graphique
    avg_progression_by_pos = avg_progression_by_pos.rename(columns={
        'PrgC': 'Progression portée',
        'PrgP': 'Passes progressives',
        'PrgR': 'Progression reçue'
    })

    # Créer un graphique en barres groupées
    fig_progression = px.bar(avg_progression_by_pos,
                             x='Pos',
                             y=['Progression portée', 'Passes progressives', 'Progression reçue'],
                             title='Progression Moyenne par Position',
                             barmode='group')

    st.plotly_chart(fig_progression, use_container_width=True)

def analyze_defensive_metrics():
    """Analyse des performances défensives"""
    data = load_fbref_data()
    
    st.header("Analyse Défensive")
    
    # Métriques défensives
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Progression")
        defensive_metrics = {
            "Progression portée": data['standard']['PrgC'].mean(),
            "Progression reçue": data['standard']['PrgR'].mean(),
            "Passes progressives": data['passing']['PrgP'].mean()
        }
        for metric, value in defensive_metrics.items():
            st.metric(metric, f"{value:.1f}")
    
    with col2:
        st.subheader("Possession")
        possession_metrics = {
            "Passes complétées": data['passing']['Cmp'].mean(),
            "Passes progressives": data['passing']['PrgP'].mean(),
            "Progression portée": data['standard']['PrgC'].mean()
        }
        for metric, value in possession_metrics.items():
            st.metric(metric, f"{value:.1f}")
    
    with col3:
        st.subheader("Distribution")
        distribution_metrics = {
            "Passes complétées": data['passing']['Cmp'].mean(),
            "Passes progressives": data['passing']['PrgP'].mean(),
            "Progression reçue": data['standard']['PrgR'].mean()
        }
        for metric, value in distribution_metrics.items():
            st.metric(metric, f"{value:.1f}")
    
    # Graphique des performances par position
    st.subheader("Performances par Position")
    
    positions = ['DF', 'MF']
    defensive_data = data['standard'][data['standard']['Pos'].str.contains('|'.join(positions), na=False)]
    
    fig = go.Figure()
    
    for pos in positions:
        pos_players = defensive_data[defensive_data['Pos'].str.contains(pos, na=False)]
        fig.add_trace(go.Bar(
            name=pos,
            x=['Progression', 'Passes', 'Réception'],
            y=[
                pos_players['PrgC'].mean(),
                pos_players['PrgP'].mean(),
                pos_players['PrgR'].mean()
            ]
        ))
    
    fig.update_layout(
        title='Métriques par position',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analyze_goalkeeping_performance():
    """Analyse des performances des gardiens"""
    data = load_fbref_data()
    
    st.header("Analyse des Gardiens")
    
    goalkeepers = data['goalkeeping'].copy()
    
    if goalkeepers.empty:
        st.info("Aucune donnée de gardien disponible.")
        return
    
    # Conversion des colonnes numériques
    numeric_gk_columns = [
        'GA', 'GA90', 'SoTA', 'Saves', 'Save%', 'W', 'D', 'L', 'CS', 'CS%', 
        'PKatt', 'PKA', 'PKsv', 'PKm', 'Save%.1'
    ]
    
    for col in numeric_gk_columns:
        if col in goalkeepers.columns:
            goalkeepers[col] = pd.to_numeric(goalkeepers[col], errors='coerce').fillna(0)
    
    # Vue d'ensemble des gardiens
    st.subheader("Vue d'ensemble des gardiens")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_matches = goalkeepers['MP'].sum()
        total_minutes = goalkeepers['Min'].sum()
        st.metric("Matches joués", total_matches)
        st.metric("Minutes jouées", total_minutes)
    
    with col2:
        total_clean_sheets = goalkeepers['CS'].sum()
        avg_clean_sheets = total_clean_sheets / len(goalkeepers)
        st.metric("Clean Sheets totaux", total_clean_sheets)
        st.metric("Clean Sheets moyens par gardien", f"{avg_clean_sheets:.1f}")
    
    with col3:
        total_saves = goalkeepers['Saves'].sum()
        avg_save_percentage = goalkeepers['Save%'].mean()
        st.metric("Arrêts totaux", total_saves)
        st.metric("Pourcentage d'arrêts moyen", f"{avg_save_percentage:.1f}%")
    
    # Graphique de comparaison des gardiens
    st.subheader("Comparaison des gardiens")
    
    # Création d'un graphique radar pour comparer les gardiens
    metrics = ['Save%', 'CS%', 'GA90', 'PKsv']
    metric_names = ['% Arrêts', '% Clean Sheets', 'Buts encaissés p90', 'Arrêts Penalty']
    
    fig_radar = go.Figure()
    
    for _, gk in goalkeepers.iterrows():
        values = []
        for metric in metrics:
            if metric in gk:
                # Normalisation des valeurs
                max_val = goalkeepers[metric].max()
                min_val = goalkeepers[metric].min()
                if max_val != min_val:
                    # Inverser la normalisation pour GA90 (moins c'est mieux)
                    if metric == 'GA90':
                        normalized_value = (max_val - gk[metric]) / (max_val - min_val) * 100
                    else:
                        normalized_value = (gk[metric] - min_val) / (max_val - min_val) * 100
                else:
                    normalized_value = 50
                # Corrected indentation
                values.append(normalized_value)
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=metric_names,
            fill='toself',
            name=gk['Player']
        ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title='Comparaison des profils des gardiens',
        showlegend=True
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Analyse détaillée par gardien
    st.subheader("Analyse détaillée par gardien")
    
    selected_gk = st.selectbox("Sélectionnez un gardien", goalkeepers['Player'].tolist(), key="goalkeeper_select")
    selected_gk_data = goalkeepers[goalkeepers['Player'] == selected_gk].iloc[0]
    
    # Affichage de la photo du gardien et des métriques côte à côte
    col_photo_gk, space, col_metrics_gk, space = st.columns([1.5, 0.5, 3, 0.5]) # Ajuster les proportions si nécessaire

    with col_photo_gk:
        # Affichage de la photo du gardien
        photo_path = get_player_photo(selected_gk)
        if photo_path:
            try:
                st.image(photo_path, width=200, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur lors de l'affichage de la photo : {str(e)}")
        st.subheader(selected_gk)

    with col_metrics_gk:
        # Métriques de performance
        st.write("### Métriques de performance")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Matches joués", selected_gk_data['MP'])
            st.metric("Minutes jouées", selected_gk_data['Min'])
            st.metric("Buts encaissés", selected_gk_data['GA'])
            st.metric("Buts encaissés p90", f"{selected_gk_data['GA90']:.2f}")
        
        with col2:
            st.metric("Arrêts", selected_gk_data['Saves'])
            st.metric("Pourcentage d'arrêts", f"{selected_gk_data['Save%']:.1f}%")
            st.metric("Clean Sheets", selected_gk_data['CS'])
            st.metric("Pourcentage Clean Sheets", f"{selected_gk_data['CS%']:.1f}%")
        
        with col3:
            st.metric("Arrêts penalty", selected_gk_data['PKsv'])
            st.metric("Tentatives penalty subies", selected_gk_data['PKatt'])
            st.metric("Penalty manqués subis", selected_gk_data['PKm'])
            st.metric("Pourcentage d'arrêts penalty", f"{selected_gk_data['Save%.1']:.1f}%")
    
    # Graphique de performance
    st.subheader("Profil de performance")
    
    performance_metrics = {
        'Arrêts': selected_gk_data['Saves'],
        'Clean Sheets': selected_gk_data['CS'],
        'Buts encaissés p90': selected_gk_data['GA90'],
        'Arrêts Penalty': selected_gk_data['PKsv']
    }
    
    fig_performance = go.Figure()
    fig_performance.add_trace(go.Bar(
        x=list(performance_metrics.keys()),
        y=list(performance_metrics.values()),
        marker_color='#1f77b4'
    ))
    
    fig_performance.update_layout(
        title=f'Profil de performance - {selected_gk}',
        xaxis_title='Métriques',
        yaxis_title='Valeur',
        showlegend=False
    )
    
    st.plotly_chart(fig_performance, use_container_width=True)
    
    # Analyse des performances par match
    st.subheader("Performances par match")
    
    # Création d'un graphique de dispersion pour les performances par match
    fig_scatter = go.Figure()
    
    fig_scatter.add_trace(go.Scatter(
        x=goalkeepers['GA90'],
        y=goalkeepers['Save%'],
        mode='markers+text',
        text=goalkeepers['Player'],
        textposition="top center",
        marker=dict(
            size=goalkeepers['MP'],
            color=goalkeepers['CS%'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title='% Clean Sheets')
        ),
        hovertemplate=(
            "Gardien: %{text}<br>"
            "Buts encaissés p90: %{x:.2f}<br>"
            "Pourcentage d'arrêts: %{y:.1f}%<br>"
            "Matches joués: %{marker.size}<extra></extra>"
        )
    ))
    
    fig_scatter.update_layout(
        title='Performances par match',
        xaxis_title='Buts encaissés p90',
        yaxis_title='Pourcentage d\'arrêts',
        showlegend=False
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

def analyze_match_performance():
    """Analyse détaillée des performances par match"""
    data = load_fbref_data()
    
    # Utiliser les données des joueurs de champ
    field_players_standard = data['field_players_standard'].copy()
    field_players_shooting = data['field_players_shooting'].copy()
    field_players_passing = data['field_players_passing'].copy()
    
    # Sélection du joueur
    player_names = field_players_standard['Player'].tolist()
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="match_performance_select")
    
    # Affichage de la photo du joueur et des métriques de base
    photo_path = get_player_photo(selected_player)
    if photo_path:
        try:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(photo_path, width=200, use_container_width=True)
            with col2:
                st.subheader(f"Performance par match de {selected_player}")
                
                # Récupération des données du joueur
                player_data = field_players_standard[field_players_standard['Player'] == selected_player]
                player_shooting = field_players_shooting[field_players_shooting['Player'] == selected_player]
                player_passing = field_players_passing[field_players_passing['Player'] == selected_player]
                
                if player_data.empty:
                    st.warning(f"Aucune donnée trouvée pour {selected_player}")
                    return
                
                # Affichage des métriques
                col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
                
                with col_metrics1:
                    st.metric("Matches joués", player_data['MP'].iloc[0])
                    st.metric("Minutes jouées", player_data['Min'].iloc[0])
                    st.metric("Buts", int(player_data['Gls'].iloc[0]))
                    st.metric("Passes décisives", int(player_data['Ast'].iloc[0]))
                
                with col_metrics2:
                    st.metric("xG", round(player_data['xG'].iloc[0], 2))
                    st.metric("xAG", round(player_data['xAG'].iloc[0], 2))
                    if not player_shooting.empty:
                        st.metric("Tirs", player_shooting['Sh'].iloc[0])
                        st.metric("Tirs cadrés", player_shooting['SoT'].iloc[0])
                    else:
                        st.text("Tirs : N/A")
                        st.text("Tirs cadrés : N/A")
                
                with col_metrics3:
                    if not player_passing.empty:
                        st.metric("Précision des passes", f"{player_passing['Cmp%'].iloc[0]}%")
                        st.metric("Passes progressives", player_passing['PrgP'].iloc[0])
                        st.metric("Passes clés", player_passing['KP'].iloc[0])
                        st.metric("Centres", player_passing['CrsPA'].iloc[0])
                    else:
                        st.text("Précision des passes : N/A")
                        st.text("Passes progressives : N/A")
                        st.text("Passes clés : N/A")
                        st.text("Centres : N/A")
        except Exception as e:
            st.error(f"Erreur lors de l'affichage de la photo : {str(e)}")
            st.subheader(f"Performance par match de {selected_player}")
    else:
        st.subheader(f"Performance par match de {selected_player}")
    

@st.cache_data
def load_ucl_data():
    """Charge les données des matchs de Ligue des Champions"""
    # Définition de l'ordre chronologique des matchs, leurs phases et leurs scores
    match_order = {
        # Phase de Ligue
        'PSG - Girona': {'phase': 'Phase de Ligue', 'ordre': 1, 'score': '1-0'},
        'Arsenal - PSG': {'phase': 'Phase de Ligue', 'ordre': 2, 'score': '2-0'},
        'PSG -PSV': {'phase': 'Phase de Ligue', 'ordre': 3, 'score': '1-1'},
        'PSG - Atletico': {'phase': 'Phase de Ligue', 'ordre': 4, 'score': '1-2'},
        'Bayern - PSG': {'phase': 'Phase de Ligue', 'ordre': 5, 'score': '1-0'},
        'Salzburg - PSG': {'phase': 'Phase de Ligue', 'ordre': 6, 'score': '0-3'},
        'PSG - Manchester City': {'phase': 'Phase de Ligue', 'ordre': 7, 'score': '4-2'},
        'Stuttgart - PSG': {'phase': 'Phase de Ligue', 'ordre': 8, 'score': '1-4'},
        # Barrages
        'Brest - PSG': {'phase': 'Barrages', 'ordre': 9, 'score': '0-3'},
        'PSG - Brest': {'phase': 'Barrages', 'ordre': 10, 'score': '7-0'},
        # 1/8 de finale
        'PSG - Liverpool': {'phase': '1/8 de finale', 'ordre': 11, 'score': '0-1'},
        'Liverpool - PSG': {'phase': '1/8 de finale', 'ordre': 12, 'score': '1-0 (4-1 pen)'},
        # 1/4 de finale
        'PSG - Aston Villa': {'phase': '1/4 de finale', 'ordre': 13, 'score': '3-1'},
        'Aston Villa - PSG': {'phase': '1/4 de finale', 'ordre': 14, 'score': '3-2'},
        # 1/2 finale
        'Arsenal - PSG 2': {'phase': '1/2 finale', 'ordre': 15, 'score': '0-1'},
        'PSG - Arsenal ': {'phase': '1/2 finale', 'ordre': 16, 'score': '2-1'},
        # Finale
        'PSG - Inter': {'phase': 'Finale', 'ordre': 17, 'score': '5-0'}
    }
    
    ucl_data = {}
    
    for file in os.listdir('data/PSG UCL Games'):
        if file.endswith('.csv'):
            match_name = file.replace('PSG UCL Games - ', '').replace('.csv', '')
            if match_name in match_order:
                df = pd.read_csv(f'data/PSG UCL Games/{file}', skiprows=1)
                df = df.rename(columns={
                    'Performance': 'Player',
                    'Gls': 'Gls',
                    'Ast': 'Ast',
                    'Sh': 'Sh',
                    'SoT': 'SoT',
                    'xG': 'xG',
                    'xAG': 'xAG',
                    'SCA': 'SCA',
                    'GCA': 'GCA',
                    'PrgP': 'PrgP',
                    'PrgC': 'PrgC',
                    'Min': 'Min'
                })
                df['Phase'] = match_order[match_name]['phase']
                df['Ordre'] = match_order[match_name]['ordre']
                df['Score'] = match_order[match_name]['score']
                ucl_data[match_name] = df
    
    return ucl_data

def analyze_ucl_progression():
    """Analyse de la progression dans la Ligue des Champions"""
    data = load_ucl_data()
    
    st.subheader("Progression dans la compétition")
    
    # Calcul des statistiques cumulées
    cumulative_stats = {
        'Gls': [],
        'Ast': [],
        'xG': [],
        'xAG': [],
        'Sh': [],
        'SoT': [],
        'SCA': [],
        'GCA': []
    }
    
    match_names = []
    phases = []
    scores = []
    
    for match_name, match_data in sorted(data.items(), key=lambda x: x[1]['Ordre'].iloc[0]):
        match_names.append(match_name)
        phases.append(match_data['Phase'].iloc[0])
        scores.append(match_data['Score'].iloc[0])
        for stat in cumulative_stats.keys():
            cumulative_stats[stat].append(match_data[stat].sum())
    
    # Création d'un DataFrame pour les statistiques cumulées
    progression_df = pd.DataFrame({
        'Match': match_names,
        'Phase': phases,
        'Score': scores,
        **cumulative_stats
    })
    
    # Graphique de progression des buts et xG
    fig_goals = go.Figure()
    fig_goals.add_trace(go.Scatter(
        name='Buts',
        x=progression_df['Match'],
        y=progression_df['Gls'],
        mode='lines+markers',
        marker=dict(color='#1f77b4'),
        text=progression_df['Score'],
        hovertemplate="Match: %{x}<br>Score: %{text}<br>Buts: %{y}<extra></extra>"
    ))
    fig_goals.add_trace(go.Scatter(
        name='xG',
        x=progression_df['Match'],
        y=progression_df['xG'],
        mode='lines+markers',
        marker=dict(color='#ff7f0e'),
        text=progression_df['Score'],
        hovertemplate="Match: %{x}<br>Score: %{text}<br>xG: %{y}<extra></extra>"
    ))
    
    fig_goals.update_layout(
        title='Progression des buts et xG',
        xaxis_title='Match',
        yaxis_title='Valeur',
        showlegend=True,
        xaxis=dict(tickangle=45)
    )
    
    st.plotly_chart(fig_goals, use_container_width=True)
    
    # Graphique de progression des Créations d'actions
    fig_creation = go.Figure()
    fig_creation.add_trace(go.Scatter(
        name='Créations d\'actions',
        x=progression_df['Match'],
        y=progression_df['SCA'],
        mode='lines+markers',
        marker=dict(color='#2ca02c'),
        text=progression_df['Score'],
        hovertemplate="Match: %{x}<br>Score: %{text}<br>SCA: %{y}<extra></extra>"
    ))
    fig_creation.add_trace(go.Scatter(
        name='Créations d\'actions de buts',
        x=progression_df['Match'],
        y=progression_df['GCA'],
        mode='lines+markers',
        marker=dict(color='#d62728'),
        text=progression_df['Score'],
        hovertemplate="Match: %{x}<br>Score: %{text}<br>GCA: %{y}<extra></extra>"
    ))
    
    fig_creation.update_layout(
        title='Progression des Créations d\'actions',
        xaxis_title='Match',
        yaxis_title='Valeur',
                    showlegend=True,
        xaxis=dict(tickangle=45)
    )
    
    st.plotly_chart(fig_creation, use_container_width=True)
    
    # Analyse des performances par phase
    st.subheader("Performances par phase")
    
    phase_stats = progression_df.groupby('Phase').agg({
        'Gls': 'sum',
        'Ast': 'sum',
        'xG': 'sum',
        'Sh': 'sum',
        'SCA': 'sum',
        'GCA': 'sum'
    }).reset_index()
    
    fig_phase = go.Figure()
    fig_phase.add_trace(go.Bar(
        name='Buts',
        x=phase_stats['Phase'],
        y=phase_stats['Gls'],
        marker_color='#1f77b4'
    ))
    fig_phase.add_trace(go.Bar(
        name='Passes décisives',
        x=phase_stats['Phase'],
        y=phase_stats['Ast'],
        marker_color='#ff7f0e'
    ))
    
    fig_phase.update_layout(
        title='Buts et Passes décisives par phase',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_phase, use_container_width=True)
    


def analyze_ucl_key_players():
    """Analyse des performances clés des joueurs en Ligue des Champions"""
    data = load_ucl_data()
    
    st.subheader("Performances clés des joueurs")
    
    # Calcul des statistiques cumulées par joueur
    player_stats = {}
    
    for match_data in data.values():
        for _, player in match_data.iterrows():
            player_name = player['Player']
            if player_name not in player_stats:
                player_stats[player_name] = {
                    'Gls': 0, 'Ast': 0, 'xG': 0, 'xAG': 0,
                    'Sh': 0, 'SoT': 0, 'SCA': 0, 'GCA': 0,
                    'Min': 0, 'Matches': 0
                }
            
            player_stats[player_name]['Gls'] += player['Gls']
            player_stats[player_name]['Ast'] += player['Ast']
            player_stats[player_name]['xG'] += player['xG']
            player_stats[player_name]['xAG'] += player['xAG']
            player_stats[player_name]['Sh'] += player['Sh']
            player_stats[player_name]['SoT'] += player['SoT']
            player_stats[player_name]['SCA'] += player['SCA']
            player_stats[player_name]['GCA'] += player['GCA']
            player_stats[player_name]['Min'] += player['Min']
            player_stats[player_name]['Matches'] += 1
    
    # Conversion en DataFrame
    key_players_df = pd.DataFrame.from_dict(player_stats, orient='index')
    key_players_df = key_players_df.reset_index().rename(columns={'index': 'Player'})
    
    # Calcul des statistiques par 90 minutes
    key_players_df['Gls/90'] = (key_players_df['Gls'] * 90) / key_players_df['Min']
    key_players_df['Ast/90'] = (key_players_df['Ast'] * 90) / key_players_df['Min']
    key_players_df['xG/90'] = (key_players_df['xG'] * 90) / key_players_df['Min']
    key_players_df['xAG/90'] = (key_players_df['xAG'] * 90) / key_players_df['Min']
    key_players_df['SCA/90'] = (key_players_df['SCA'] * 90) / key_players_df['Min']
    key_players_df['GCA/90'] = (key_players_df['GCA'] * 90) / key_players_df['Min']
    
    # Sélection des joueurs avec au moins 90 minutes jouées
    key_players_df = key_players_df[key_players_df['Min'] >= 90]
    
    # Top 5 buteurs
    st.write("### Top 5 Buteurs")
    top_scorers = key_players_df.nlargest(5, 'Gls')[['Player', 'Gls', 'Gls/90', 'xG', 'xG/90']]
    
    fig_scorers = go.Figure()
    fig_scorers.add_trace(go.Bar(
        name='Buts',
        x=top_scorers['Player'],
        y=top_scorers['Gls'],
        marker_color='#1f77b4'
    ))
    fig_scorers.add_trace(go.Bar(
        name='xG',
        x=top_scorers['Player'],
        y=top_scorers['xG'],
        marker_color='#ff7f0e'
    ))
    
    fig_scorers.update_layout(
        title='',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_scorers, use_container_width=True)
    
    # Top 5 passeurs
    st.write("### Top 5 Passeurs")
    top_assists = key_players_df.nlargest(5, 'Ast')[['Player', 'Ast', 'Ast/90', 'xAG', 'xAG/90']]
    
    fig_assists = go.Figure()
    fig_assists.add_trace(go.Bar(
        name='Passes décisives',
        x=top_assists['Player'],
        y=top_assists['Ast'],
        marker_color='#2ca02c'
    ))
    fig_assists.add_trace(go.Bar(
        name='xAG',
        x=top_assists['Player'],
        y=top_assists['xAG'],
        marker_color='#d62728'
    ))
    
    fig_assists.update_layout(
        title='',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_assists, use_container_width=True)
    
    # Top 5 créateurs de chances
    st.write("### Top 5 Créateurs de Chances")
    top_creators = key_players_df.nlargest(5, 'SCA')[['Player', 'SCA', 'GCA', 'SCA/90', 'GCA/90']]
    
    fig_creators = go.Figure()
    fig_creators.add_trace(go.Bar(
        name='Créations d\'actions',
        x=top_creators['Player'],
        y=top_creators['SCA'],
        marker_color='#9467bd'
    ))
    fig_creators.add_trace(go.Bar(
        name='Créations d\'actions de buts',
        x=top_creators['Player'],
        y=top_creators['GCA'],
        marker_color='#8c564b'
    ))
    
    fig_creators.update_layout(
        title='Top 5 Créateurs de Chances',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_creators, use_container_width=True)

def analyze_ucl_player_match():
    """Analyse détaillée des performances par joueur pour chaque match de Ligue des Champions"""
    data = load_ucl_data()
    
    st.subheader("Analyse détaillée par joueur")
    
    # Sélection du match
    match_names = sorted(data.keys(), key=lambda x: data[x]['Ordre'].iloc[0])
    selected_match = st.selectbox("Sélectionnez un match", match_names, key="ucl_player_match_select")
    
    match_data = data[selected_match]
    
    # Affichage du score et de la phase
    col1_info, col2_info = st.columns(2)
    with col1_info:
        st.metric("Score", match_data['Score'].iloc[0])
    with col2_info:
        st.metric("Phase", match_data['Phase'].iloc[0])
    
    # Sélection du joueur
    player_names = match_data['Player'].tolist()
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="ucl_player_select")
    
    # Récupération des données du joueur pour le match sélectionné
    player_data_for_match = match_data[match_data['Player'] == selected_player]
    
    if player_data_for_match.empty:
        st.warning(f"Aucune donnée trouvée pour {selected_player} dans le match {selected_match}.")
        return
        
    player_data = player_data_for_match.iloc[0]
    
    # --- Affichage de la photo et des métriques côte à côte ---
    col_photo_ucl, space, col_metrics_ucl, space = st.columns([2, 0.5, 3, 1]) # Ajuster les proportions si nécessaire

    with col_photo_ucl:
        # Affichage de la photo du joueur
        photo_path = get_player_photo(selected_player)
        if photo_path:
            try:
                st.image(photo_path, width=400, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur lors de l'affichage de la photo : {str(e)}")
        # Optionnel : Afficher le nom du joueur sous la photo
        st.subheader(selected_player)

    with col_metrics_ucl:
        st.markdown('''<h3 style='color: white; font-size: 1.4rem; font-weight: 700; font-family: "Poppins", sans-serif;'>Métriques détaillées</h3>''', unsafe_allow_html=True)
        
        col1_stats, col2_stats, col3_stats = st.columns(3)

        with col1_stats:
            st.metric("Minutes jouées", player_data['Min'])
            st.metric("Buts", int(player_data['Gls']))
            st.metric("xG", f"{player_data['xG']:.2f}")
            st.metric("Tirs", player_data['Sh'])
            st.metric("Tirs cadrés", player_data['SoT'])

        with col2_stats:
            st.metric("Passes décisives", int(player_data['Ast']))
            st.metric("xAG", f"{player_data['xAG']:.2f}")
            st.metric("Passes progressives", player_data['PrgP'])
            st.metric("Créations d'actions", player_data['SCA'])
            st.metric("Créations d'actions de buts", player_data['GCA'])
        
        with col3_stats:
            st.metric("Progression portée", player_data['PrgC'])
            st.metric("Tacles", player_data['Tkl'] if 'Tkl' in player_data else 0)
            st.metric("Interceptions", player_data['Int'] if 'Int' in player_data else 0)
            st.metric("Tirs bloqués", player_data['Blocks'] if 'Blocks' in player_data else 0)
            st.metric("Dégagements", player_data['Clr'] if 'Clr' in player_data else 0)
    
    # Graphique radar des performances (reste en dessous)
    st.write("### Profil de performance")
    
    metrics = {
        'Gls': player_data['Gls'],
        'Ast': player_data['Ast'],
        'xG': player_data['xG'],
        'xAG': player_data['xAG'],
        'SoT': player_data['SoT'],
        'SCA': player_data['SCA'],
        'GCA': player_data['GCA'],
        'PrgP': player_data['PrgP'],
        'Tkl': player_data['Tkl'] if 'Tkl' in player_data else 0,
        'Int': player_data['Int'] if 'Int' in player_data else 0,
        'Blocks': player_data['Blocks'] if 'Blocks' in player_data else 0,
        'Clr': player_data['Clr'] if 'Clr' in player_data else 0,
        'Touches': player_data['Touches'] if 'Touches' in player_data else 0
    }
    
    display_names = {
        'Gls': 'Buts',
        'Ast': 'Passes décisives',
        'xG': 'xG',
        'xAG': 'xAG',
        'SoT': 'Tirs cadrés',
        'SCA': 'Créations d\'actions',
        'GCA': 'Créations d\'actions de buts',
        'PrgP': 'Passes progressives',
        'Tkl': 'Tacles',
        'Int': 'Interceptions',
        'Blocks': 'Tirs bloqués',
        'Clr': 'Dégagements',
        'Touches': 'Touches'
    }
    
    max_values = {
        'Gls': 3,
        'Ast': 2,
        'xG': 2,
        'xAG': 2,
        'SoT': 5,
        'SCA': 8,
        'GCA': 3,
        'PrgP': 15,
        'Tkl': 5,
        'Int': 5,
        'Blocks': 3,
        'Clr': 5,
        'Touches': 100
    }
    
    normalized_metrics = {display_names[k]: (v / max_values[k]) * 100 for k, v in metrics.items()}
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(normalized_metrics.values()),
        theta=list(normalized_metrics.keys()),
        fill='toself',
        name=selected_player
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title=f'Profil de performance - {selected_player} vs {selected_match} ({match_data["Score"].iloc[0]})',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Comparaison avec la moyenne de l'équipe pour ce match
    st.write("### Comparaison avec la moyenne de l'équipe")
    
    # Filtrer les métriques pour n'inclure que celles présentes dans le DataFrame du match
    available_metrics_keys = [k for k in metrics.keys() if k in match_data.columns]
    team_avg = match_data[available_metrics_keys].mean()
    
    comparison_data = pd.DataFrame({
        'Métrique': [display_names[k] for k in available_metrics_keys],
        'Joueur': [metrics[k] for k in available_metrics_keys],
        'Moyenne Équipe': team_avg.values
    })
    
    fig_comparison = go.Figure()
    fig_comparison.add_trace(go.Bar(
        name='Joueur',
        x=comparison_data['Métrique'],
        y=comparison_data['Joueur'],
        marker_color='#1f77b4'
    ))
    
    fig_comparison.add_trace(go.Bar(
        name='Moyenne Équipe',
        x=comparison_data['Métrique'],
        y=comparison_data['Moyenne Équipe'],
        marker_color='#ff7f0e'
    ))
    
    fig_comparison.update_layout(
        title=f'Comparaison avec la moyenne de l\'équipe - {selected_match} ({match_data["Score"].iloc[0]})',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)

def analyze_ucl_performance():
    """Analyse des performances en Ligue des Champions"""
    data = load_ucl_data()
    
    st.header("Analyse Ligue des Champions")
    
    analysis_type = st.radio(
        "Choisissez une analyse :",
        ("Analyse Match par Match", "Analyse détaillée par joueur", "Progression dans la compétition", "Performances clés des joueurs"),
        key="ucl_analysis_radio"
    )
    
    if analysis_type == "Analyse Match par Match":
        # Sélection du match
        match_names = sorted(data.keys(), key=lambda x: data[x]['Ordre'].iloc[0])
        selected_match = st.selectbox("Sélectionnez un match", match_names, key="ucl_match_select")
        
        match_data = data[selected_match]
        
        # Affichage du score et de la phase
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Score", match_data['Score'].iloc[0])
        with col2:
            st.metric("Phase", match_data['Phase'].iloc[0])
        
        # Statistiques du match
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_goals = match_data['Gls'].sum()
            total_xg = match_data['xG'].sum()
            st.metric("Buts marqués", total_goals)
            st.metric("xG total", f"{total_xg:.2f}")
        
        with col2:
            total_assists = match_data['Ast'].sum()
            total_xag = match_data['xAG'].sum()
            st.metric("Passes décisives", total_assists)
            st.metric("xAG total", f"{total_xag:.2f}")
        
        with col3:
            total_shots = match_data['Sh'].sum()
            shots_on_target = match_data['SoT'].sum()
            st.metric("Tirs totaux", total_shots)
            st.metric("Tirs cadrés", shots_on_target)
        
        # Graphique des performances individuelles
        st.subheader("Performances individuelles")
        
        performance_data = match_data[['Player', 'Gls', 'Ast', 'xG', 'xAG', 'Sh', 'SoT']]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Buts',
            x=performance_data['Player'],
            y=performance_data['Gls'],
            marker_color='#1f77b4'
        ))
        fig.add_trace(go.Bar(
            name='Passes décisives',
            x=performance_data['Player'],
            y=performance_data['Ast'],
            marker_color='#ff7f0e'
        ))
        
        fig.update_layout(
            title=f'Buts et Passes décisives par joueur - {selected_match} ({match_data["Score"].iloc[0]})',
            barmode='group',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Analyse des Créations d'actions
        st.subheader("Créations d'actions")
        
        creation_data = match_data[['Player', 'SCA', 'GCA', 'PrgP', 'PrgC']]
        
        fig_creation = go.Figure()
        fig_creation.add_trace(go.Bar(
            name='Créations d\'actions',
            x=creation_data['Player'],
            y=creation_data['SCA'],
            marker_color='#2ca02c'
        ))
        fig_creation.add_trace(go.Bar(
            name='Créations d\'actions de buts',
            x=creation_data['Player'],
            y=creation_data['GCA'],
            marker_color='#d62728'
        ))
        
        fig_creation.update_layout(
            title=f'Créations d\'actions par joueur - {selected_match} ({match_data["Score"].iloc[0]})',
            barmode='group',
            showlegend=True
        )
        
        st.plotly_chart(fig_creation, use_container_width=True)
    
    elif analysis_type == "Progression dans la compétition":
        analyze_ucl_progression()
    
    elif analysis_type == "Performances clés des joueurs":
        analyze_ucl_key_players()
    
    else:  # Analyse détaillée par joueur
        analyze_ucl_player_match()

def render_home():
    # Enveloppement du logo et du titre dans un conteneur centré via HTML/CSS
    centered_header = """
    <div style='text-align: center; background: none; padding: 15px; border-top-left-radius: 20px; border-top-right-radius: 20px; border-bottom-left-radius: 0; border-bottom-right-radius: 0; margin-bottom: 0;'>
        <img src='https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg' width='100' style='display: block; margin: 0 auto;'>
        <h1 style='text-align: center; color: white; font-size: 2.2em; font-family: "Poppins", sans-serif; font-weight: 700;'>PSG Data Center - Saison 2024-2025</h1>
    </div>
    """
    st.markdown(centered_header, unsafe_allow_html=True)

    # Style personnalisé pour les onglets
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            background: linear-gradient(135deg, #0C1A2A 0%, #8B0000 100%);
            border-top-left-radius: 0 !important;
            border-top-right-radius: 0 !important;
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            padding: 10px;
            margin-top: -22px !important; /* Supprimer la marge négative */
        }
        .stTabs [data-baseweb="tab"] {
            color: white;
            font-weight: bold;
        }
        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Onglets principaux regroupés
    tab_overview, tab_individual, tab_collective, tab_ucl, tab_goalkeeping = st.tabs([
        "Vue d'ensemble",
        "Analyse individuelle",
        "Analyse collective",
        "Ligue des Champions",
        "Analyse Gardiens"
    ])

    with tab_overview:
        render_overview()

    with tab_individual:
        st.markdown('''<h2 style='color: white; font-size: 1.8rem; font-weight: 700; font-family: "Poppins", sans-serif;'>Analyse individuelle des joueurs</h2>''', unsafe_allow_html=True)
        analysis_type = st.radio(
            "Choisissez une analyse :",
            ("Analyse par joueur", "Comparaisons", "Rôles et Profils"),
            key="individual_analysis_radio"
        )
        if analysis_type == "Analyse par joueur":
            render_player_analysis()
        elif analysis_type == "Comparaisons":
            render_comparisons()
        elif analysis_type == "Rôles et Profils":
            analyze_player_roles()

    with tab_collective:
        st.markdown('''<h2 style='color: white; font-size: 1.8rem; font-weight: 700; font-family: "Poppins", sans-serif;'>Analyse collective et tactique</h2>''', unsafe_allow_html=True)
        analysis_type = st.radio(
            "Choisissez une analyse :",
            ("Analyse par position", "Analyse Tactique", "Forces et Faiblesses", "Dynamiques d'Équipe", "Patterns Tactiques", "Analyse Défensive"),
            key="collective_analysis_radio"
        )
        if analysis_type == "Analyse par position":
            render_position_analysis()
        elif analysis_type == "Analyse Tactique":
            analyze_tactical_performance()
        elif analysis_type == "Forces et Faiblesses":
            analyze_team_strengths()
        elif analysis_type == "Dynamiques d'Équipe":
            analyze_team_dynamics()
        elif analysis_type == "Patterns Tactiques":
            analyze_tactical_patterns()
        elif analysis_type == "Analyse Défensive":
            analyze_defensive_metrics()

    with tab_ucl:
        analyze_ucl_performance()

    with tab_goalkeeping:
        analyze_goalkeeping_performance()

def analyze_ucl_match_performance():
    """Analyse détaillée des performances par match en Ligue des Champions"""
    ucl_data = load_ucl_data()
    
    # Sélection du joueur
    all_players = set()
    for match_data in ucl_data.values():
        all_players.update(match_data['Player'].unique())
    player_names = sorted(list(all_players))
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="ucl_match_performance_select")
    
    # Affichage de la photo du joueur
    photo_path = get_player_photo(selected_player)
    if photo_path:
        try:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(photo_path, width=200, use_container_width=True)
            with col2:
                st.subheader(f"Performance par match de {selected_player} en Ligue des Champions")
        except Exception as e:
            st.error(f"Erreur lors de l'affichage de la photo : {str(e)}")
            st.subheader(f"Performance par match de {selected_player} en Ligue des Champions")
    else:
        st.subheader(f"Performance par match de {selected_player} en Ligue des Champions")
    
    # Récupérer les données du joueur pour chaque match
    player_matches = []
    for match_name, match_data in sorted(ucl_data.items(), key=lambda x: x[1]['Ordre'].iloc[0]):
        player_match_data = match_data[match_data['Player'] == selected_player]
        if not player_match_data.empty:
            player_matches.append({
                'Match': match_name,
                'Phase': match_data['Phase'].iloc[0],
                'Score': match_data['Score'].iloc[0],
                'Gls': player_match_data['Gls'].iloc[0],
                'Ast': player_match_data['Ast'].iloc[0],
                'Min': player_match_data['Min'].iloc[0],
                'Tkl': player_match_data['Tkl'].iloc[0] if 'Tkl' in player_match_data else 0,
                'Int': player_match_data['Int'].iloc[0] if 'Int' in player_match_data else 0,
                'Blocks': player_match_data['Blocks'].iloc[0] if 'Blocks' in player_match_data else 0,
                'Clr': player_match_data['Clr'].iloc[0] if 'Clr' in player_match_data else 0
            })
    
    if player_matches:
        # Création du graphique offensif
        fig_offensive = go.Figure()
        
        # Ajout des barres pour les buts et passes décisives
        fig_offensive.add_trace(go.Bar(
            name='Buts',
            x=[m['Match'] for m in player_matches],
            y=[m['Gls'] for m in player_matches],
            marker_color='#1f77b4',
            text=[f"{m['Score']}" for m in player_matches],
            hovertemplate="Match: %{x}<br>Score: %{text}<br>Buts: %{y}<extra></extra>"
        ))
        
        fig_offensive.add_trace(go.Bar(
            name='Passes décisives',
            x=[m['Match'] for m in player_matches],
            y=[m['Ast'] for m in player_matches],
            marker_color='#ff7f0e',
            text=[f"{m['Score']}" for m in player_matches],
            hovertemplate="Match: %{x}<br>Score: %{text}<br>Passes décisives: %{y}<extra></extra>"
        ))
        
        # Mise à jour du layout
        fig_offensive.update_layout(
            title='Performance offensive par match',
            barmode='group',
            xaxis_title='Match',
            yaxis_title='Nombre',
            showlegend=True,
            xaxis=dict(tickangle=45)
        )
        
        st.plotly_chart(fig_offensive, use_container_width=True)
        
        # Création du graphique défensif
        fig_defensive = go.Figure()
        
        # Ajout des barres pour les statistiques défensives
        fig_defensive.add_trace(go.Bar(
            name='Tacles',
            x=[m['Match'] for m in player_matches],
            y=[m['Tkl'] for m in player_matches],
            marker_color='#2ca02c',
            text=[f"{m['Score']}" for m in player_matches],
            hovertemplate="Match: %{x}<br>Score: %{text}<br>Tacles: %{y}<extra></extra>"
        ))
        
        fig_defensive.add_trace(go.Bar(
            name='Interceptions',
            x=[m['Match'] for m in player_matches],
            y=[m['Int'] for m in player_matches],
            marker_color='#d62728',
            text=[f"{m['Score']}" for m in player_matches],
            hovertemplate="Match: %{x}<br>Score: %{text}<br>Interceptions: %{y}<extra></extra>"
        ))
        
        fig_defensive.add_trace(go.Bar(
            name='Blocages',
            x=[m['Match'] for m in player_matches],
            y=[m['Blocks'] for m in player_matches],
            marker_color='#9467bd',
            text=[f"{m['Score']}" for m in player_matches],
            hovertemplate="Match: %{x}<br>Score: %{text}<br>Blocages: %{y}<extra></extra>"
        ))
        
        fig_defensive.add_trace(go.Bar(
            name='Dégagements',
            x=[m['Match'] for m in player_matches],
            y=[m['Clr'] for m in player_matches],
            marker_color='#8c564b',
            text=[f"{m['Score']}" for m in player_matches],
            hovertemplate="Match: %{x}<br>Score: %{text}<br>Dégagements: %{y}<extra></extra>"
        ))
        
        # Mise à jour du layout
        fig_defensive.update_layout(
            title='Performance défensive par match',
            barmode='group',
            xaxis_title='Match',
            yaxis_title='Nombre',
                showlegend=True,
            xaxis=dict(tickangle=45)
        )
        
        st.plotly_chart(fig_defensive, use_container_width=True)
    else:
        st.info(f"{selected_player} n'a pas encore joué de match en Ligue des Champions cette saison.")

def analyze_ucl():
    """Analyse des performances en Ligue des Champions"""
    st.title("Analyse des performances en Ligue des Champions")
    
    # Sélection du type d'analyse
    analysis_type = st.radio(
        "Choisissez le type d'analyse",
        ["Analyse match par match", "Progression dans la compétition", "Performances des joueurs clés", "Analyse détaillée par joueur", "Performance par match"]
    )
    
    if analysis_type == "Analyse match par match":
        analyze_ucl_matches()
    elif analysis_type == "Progression dans la compétition":
        analyze_ucl_progression()
    elif analysis_type == "Performances des joueurs clés":
        analyze_ucl_key_players()
    elif analysis_type == "Analyse détaillée par joueur":
        analyze_ucl_player_match()
    elif analysis_type == "Performance par match":
        analyze_ucl_match_performance()

if __name__ == "__main__":
    render_home()

