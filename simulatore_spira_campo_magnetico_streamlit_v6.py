import time
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch


st.set_page_config(
    page_title="Spira in campo magnetico",
    page_icon="🧲",
    layout="wide",
)

st.title("Spira quadrata in moto in un campo magnetico")
st.caption("La spira attraversa il bordo di una regione con campo magnetico uniforme.")

# ============================================================
# PARAMETRI
# ============================================================
st.sidebar.header("Parametri")

L = st.sidebar.number_input(
    "Lato della spira L (m)",
    min_value=0.10, max_value=10.0,
    value=1.0, step=0.10
)

B_abs = st.sidebar.number_input(
    "Modulo del campo B (T)",
    min_value=0.0, max_value=20.0,
    value=1.0, step=0.10
)

B_direction = st.sidebar.selectbox(
    "Verso del campo",
    ["Uscente dal piano", "Entrante nel piano"]
)

motion = st.sidebar.radio(
    "Legge del moto",
    ["Moto uniforme", "Moto uniformemente accelerato"]
)

if motion == "Moto uniforme":
    v0 = st.sidebar.number_input(
        "Velocità v (m/s)",
        min_value=0.01, max_value=20.0,
        value=0.50, step=0.05
    )
    a = 0.0
else:
    v0 = st.sidebar.number_input(
        "Velocità iniziale v₀ (m/s)",
        min_value=0.0, max_value=20.0,
        value=0.20, step=0.05
    )
    a = st.sidebar.number_input(
        "Accelerazione a (m/s²)",
        min_value=-10.0, max_value=10.0,
        value=0.20, step=0.05
    )

start_gap = st.sidebar.slider(
    "Distanza iniziale dal campo (in multipli di L)",
    min_value=0.10,
    max_value=1.50,
    value=0.50,
    step=0.10
)

after_time = st.sidebar.slider(
    "Secondi mostrati dopo l'ingresso completo",
    0.5, 4.0, 1.5, 0.1
)

fps = st.sidebar.slider(
    "Fluidità animazione",
    5, 30, 15, 1
)

speed_factor = st.sidebar.slider(
    "Velocità di riproduzione",
    0.25, 3.0, 1.0, 0.25
)

# ============================================================
# MOTO
# ============================================================
# q(t) = spostamento del lato destro rispetto alla posizione iniziale.
# La spira parte con il lato destro a x = -gap, quindi interamente fuori.
gap = start_gap * L

def displacement(t):
    t = np.asarray(t, dtype=float)
    if motion == "Moto uniforme":
        return v0 * t
    return v0 * t + 0.5 * a * t**2

def velocity(t):
    t = np.asarray(t, dtype=float)
    if motion == "Moto uniforme":
        return np.full_like(t, v0, dtype=float)
    return v0 + a * t

def right_edge(t):
    return -gap + displacement(t)

# Trova contatto iniziale x_right = 0 e ingresso completo x_right = L.
search_times = np.linspace(0.0, 120.0, 24001)
search_x = right_edge(search_times)

contact_idx = np.where(search_x >= 0.0)[0]
full_idx = np.where(search_x >= L)[0]

if len(contact_idx) == 0 or len(full_idx) == 0:
    st.error(
        "Con questi parametri la spira non riesce a entrare completamente "
        "nella regione magnetica. Modifica velocità o accelerazione."
    )
    st.stop()

t_contact = float(search_times[contact_idx[0]])
t_full = float(search_times[full_idx[0]])
t_end = t_full + after_time

n_steps = max(30, int(np.ceil(t_end * fps)))
times = np.linspace(0.0, t_end, n_steps + 1)
x_right = right_edge(times)
velocities = velocity(times)

# ============================================================
# FLUSSO
# ============================================================
# Regione magnetica: x >= 0
# Spira: [x_right-L, x_right]
immersed_width = np.clip(x_right, 0.0, L)
immersed_area = L * immersed_width

Bz = B_abs if B_direction == "Uscente dal piano" else -B_abs
flux = Bz * immersed_area

# ============================================================
# FEM: VALORE ASSOLUTO
# ============================================================
# Per una spira quadrata che entra attraverso un bordo rettilineo:
#
#   0 < x_right < L:
#       A_imm = L*x_right
#       |E| = |B| L |v|
#
# Fuori o completamente dentro:
#       |E| = 0
#
# Questo evita artefatti grafici dovuti a intervalli temporali che
# attraversano esattamente il bordo x=0 o x=L.
emf_abs = np.zeros_like(times)

entering = (x_right > 0.0) & (x_right < L)
emf_abs[entering] = B_abs * L * np.abs(velocities[entering])

# Agli istanti esatti di contatto e ingresso completo mostriamo 0:
# la curva avrà quindi transizioni nette senza valori "medi" spurii.
emf_abs[np.isclose(x_right, 0.0, atol=1e-10)] = 0.0
emf_abs[np.isclose(x_right, L, atol=1e-10)] = 0.0

# Per la tabella manteniamo anche il calcolo a differenze finite del flusso,
# utile didatticamente.
dt = np.diff(times)
dflux = np.diff(flux)
emf_fd_abs = np.abs(-dflux / dt)

# ============================================================
# SIMBOLI B DISEGNATI
# ============================================================
def field_symbol(
    ax, x, y, direction, radius,
    alpha=0.65, linewidth=1.5,
    color="black"
):
    """Cerchio+punto o cerchio+croce, tutto nello stesso colore."""
    ax.add_patch(
        Circle(
            (x, y),
            radius,
            fill=False,
            linewidth=linewidth,
            alpha=alpha,
            edgecolor=color
        )
    )

    if direction == "out":
        ax.add_patch(
            Circle(
                (x, y),
                radius * 0.20,
                facecolor=color,
                edgecolor=color,
                alpha=alpha
            )
        )
    else:
        d = radius * 0.60
        ax.plot(
            [x-d, x+d], [y-d, y+d],
            linewidth=linewidth,
            alpha=alpha,
            color=color
        )
        ax.plot(
            [x-d, x+d], [y+d, y-d],
            linewidth=linewidth,
            alpha=alpha,
            color=color
        )

def current_arrows(ax, left, bottom, side, direction):
    pad = 0.07 * side

    if direction == "antioraria":
        segs = [
            ((left + pad, bottom + pad), (left + side - pad, bottom + pad)),
            ((left + side - pad, bottom + pad), (left + side - pad, bottom + side - pad)),
            ((left + side - pad, bottom + side - pad), (left + pad, bottom + side - pad)),
            ((left + pad, bottom + side - pad), (left + pad, bottom + pad)),
        ]
    else:
        segs = [
            ((left + side - pad, bottom + pad), (left + pad, bottom + pad)),
            ((left + side - pad, bottom + side - pad), (left + side - pad, bottom + pad)),
            ((left + pad, bottom + side - pad), (left + side - pad, bottom + side - pad)),
            ((left + pad, bottom + pad), (left + pad, bottom + side - pad)),
        ]

    for p0, p1 in segs:
        ax.add_patch(
            FancyArrowPatch(
                p0, p1,
                arrowstyle="-|>",
                mutation_scale=13,
                linewidth=2.1
            )
        )

# ============================================================
# VERSO CORRENTE (serve solo per l'animazione)
# ============================================================
def current_state(i):
    # Nessuna corrente fuori dalla fase di ingresso.
    if not (0.0 < x_right[i] < L):
        return "nessuna", "none"

    # Durante l'ingresso il flusso esterno aumenta in modulo.
    # Se B esterno è uscente, B_ind deve essere entrante -> corrente oraria.
    # Se B esterno è entrante, B_ind deve essere uscente -> corrente antioraria.
    if Bz > 0:
        return "oraria", "in"
    elif Bz < 0:
        return "antioraria", "out"
    else:
        return "nessuna", "none"

# ============================================================
# SCENA
# ============================================================
def make_scene(i):
    xr = float(x_right[i])
    xl = xr - L
    bottom = -L / 2
    cx = xl + L / 2

    current_dir, bind_dir = current_state(i)

    fig, ax = plt.subplots(figsize=(9.2, 5.8))

    # Limiti fissi che comprendono anche la posizione iniziale.
    x_min = -(1.15 + start_gap) * L
    x_max = 2.25 * L
    y_min = -0.95 * L
    y_max = 0.95 * L

    ax.axvspan(0, x_max, alpha=0.10)
    ax.axvline(0, linewidth=2)
    ax.text(0.06 * L, 0.82 * L, "B uniforme", fontsize=11, va="top")

    external_dir = "out" if Bz >= 0 else "in"
    xs = np.linspace(0.25 * L, 2.0 * L, 5)
    ys = np.linspace(-0.60 * L, 0.60 * L, 4)

    for xx in xs:
        for yy in ys:
            field_symbol(
                ax, xx, yy,
                external_dir,
                radius=0.055 * L
            )

    direction_text = "uscente" if Bz >= 0 else "entrante"
    ax.text(
        1.12 * L, -0.83 * L,
        f"B = {B_abs:.2f} T — {direction_text}",
        ha="center", fontsize=10
    )

    ax.add_patch(
        Rectangle(
            (xl, bottom),
            L, L,
            fill=False,
            linewidth=3
        )
    )

    # Normale positiva: perpendicolare al piano della spira.
    # Convenzione: n uscente dallo schermo, rappresentata da cerchio + punto.
    normal_y = 0.30 * L
    field_symbol(
        ax, cx, normal_y,
        "out",
        radius=0.075 * L,
        alpha=1.0,
        linewidth=1.8
    )
    ax.text(
        cx + 0.11 * L,
        normal_y,
        "n (uscente)",
        va="center",
        fontsize=10
    )

    if current_dir != "nessuna":
        current_arrows(ax, xl, bottom, L, current_dir)

        field_symbol(
            ax, cx, -0.08 * L,
            bind_dir,
            radius=0.095 * L,
            alpha=1.0,
            linewidth=1.8,
            color="tab:blue"
        )

        bind_text = "uscente" if bind_dir == "out" else "entrante"
        ax.text(
            cx, -0.27 * L,
            rf"$B_{{ind}}$ {bind_text}",
            ha="center", fontsize=10
        )
        ax.text(
            cx, bottom - 0.13 * L,
            f"I: {current_dir}",
            ha="center", fontsize=10
        )
    else:
        ax.text(
            cx, bottom - 0.13 * L,
            "I = 0",
            ha="center", fontsize=10
        )

    # --------------------------------------------------------
    # Forza magnetica sul lato anteriore percorso dalla corrente indotta:
    #
    #       F = I L x B
    #
    # Non è la forza q v x B sulle singole cariche.
    #
    # Durante l'ingresso, per la legge di Lenz, la forza risultante sul
    # lato anteriore immerso nel campo si oppone al moto della spira.
    # La mostriamo quindi solo mentre 0 < x_right < L, cioè quando
    # esistono f.e.m. e corrente indotte.
    # --------------------------------------------------------
    if (
        0.0 < xr < L
        and abs(float(velocities[i])) > 1e-12
        and B_abs > 0
    ):
        front_x = xr

        # La forza magnetica resistente è opposta alla velocità.
        sign_v = np.sign(float(velocities[i]))
        force_len = 0.32 * L

        x0_force = front_x
        x1_force = front_x - sign_v * force_len
        y_force = 0.0

        ax.add_patch(
            FancyArrowPatch(
                (x0_force, y_force),
                (x1_force, y_force),
                arrowstyle="-|>",
                mutation_scale=17,
                linewidth=2.6,
                color="tab:red",
                zorder=8
            )
        )

        ax.text(
            (x0_force + x1_force) / 2,
            y_force + 0.09 * L,
            r"$F_L$",
            color="tab:red",
            fontsize=12,
            fontweight="bold",
            ha="center",
            va="bottom"
        )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal", adjustable="box")
    ax.set_yticks([])
    ax.set_xlabel("x")
    ax.set_title(f"t = {times[i]:.2f} s")
    ax.grid(axis="x", alpha=0.15)

    fig.tight_layout()
    return fig

# ============================================================
# GRAFICO |FEM| PROGRESSIVO
# ============================================================
def make_emf_graph(i):
    fig, ax = plt.subplots(figsize=(7.4, 4.7))

    max_e = max(float(np.max(emf_abs)), 1e-6)

    ax.set_xlim(0, t_end)
    ax.set_ylim(0, 1.18 * max_e)

    # La curva viene costruita solo fino all'istante raggiunto.
    ax.plot(
        times[:i+1],
        emf_abs[:i+1],
        linewidth=2.4
    )

    ax.scatter(
        [times[i]],
        [emf_abs[i]],
        s=65,
        zorder=5
    )

    # Linee verticali leggere per evidenziare i due eventi fisici.
    ax.axvline(t_contact, linestyle="--", alpha=0.30)
    ax.axvline(t_full, linestyle="--", alpha=0.30)

    ax.text(
        t_contact,
        1.08 * max_e,
        "inizio ingresso",
        rotation=90,
        va="top",
        ha="right",
        fontsize=8,
        alpha=0.7
    )
    ax.text(
        t_full,
        1.08 * max_e,
        "ingresso completo",
        rotation=90,
        va="top",
        ha="right",
        fontsize=8,
        alpha=0.7
    )

    ax.set_xlabel("t (s)")
    ax.set_ylabel("modulo f.e.m. (V)")
    ax.set_title("Modulo della f.e.m. indotta")
    ax.grid(alpha=0.22)

    fig.tight_layout()
    return fig

# ============================================================
# SESSION STATE
# ============================================================
if "frame_spira_v3" not in st.session_state:
    st.session_state.frame_spira_v3 = 0

if "playing_spira_v3" not in st.session_state:
    st.session_state.playing_spira_v3 = False

def start_animation():
    if st.session_state.frame_spira_v3 >= n_steps:
        st.session_state.frame_spira_v3 = 0
    st.session_state.playing_spira_v3 = True

def stop_animation():
    st.session_state.playing_spira_v3 = False

def reset_animation():
    st.session_state.playing_spira_v3 = False
    st.session_state.frame_spira_v3 = 0

# ============================================================
# CONTROLLI
# ============================================================
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

with c1:
    st.button(
        "▶ Avvia / riprendi",
        on_click=start_animation,
        use_container_width=True,
        type="primary"
    )

with c2:
    st.button(
        "⏸ Ferma",
        on_click=stop_animation,
        use_container_width=True
    )

with c3:
    st.button(
        "↺ Ricomincia",
        on_click=reset_animation,
        use_container_width=True
    )

with c4:
    st.caption(
        f"Contatto: {t_contact:.2f} s · "
        f"ingresso completo: {t_full:.2f} s · "
        f"fine: {t_end:.2f} s"
    )

# ============================================================
# VISUALIZZAZIONE
# ============================================================
i = int(np.clip(st.session_state.frame_spira_v3, 0, n_steps))

left_col, right_col = st.columns([3, 2])

with left_col:
    scene_fig = make_scene(i)
    st.pyplot(scene_fig, use_container_width=True)
    plt.close(scene_fig)
    st.caption(
        "Blu: campo magnetico indotto · Rosso: forza magnetica "
        "sul lato della spira percorso dalla corrente indotta."
    )

with right_col:
    graph_fig = make_emf_graph(i)
    st.pyplot(graph_fig, use_container_width=True)
    plt.close(graph_fig)

current_now, _ = current_state(i)

m1, m2, m3, m4 = st.columns(4)
m1.metric("t", f"{times[i]:.2f} s")
m2.metric("Flusso", f"{flux[i]:.4g} Wb")
m3.metric("Modulo f.e.m.", f"{emf_abs[i]:.4g} V")
m4.metric("Corrente", current_now)

# ============================================================
# AVANZAMENTO
# ============================================================
if st.session_state.playing_spira_v3:
    if i < n_steps:
        frame_delay = (times[1] - times[0]) / max(speed_factor, 1e-6)
        frame_delay = min(frame_delay, 0.25)

        time.sleep(frame_delay)
        st.session_state.frame_spira_v3 += 1
        st.rerun()
    else:
        st.session_state.playing_spira_v3 = False
        st.success(
            "Simulazione terminata: la spira è completamente immersa "
            "nel campo e |f.e.m.| = 0."
        )

# ============================================================
# SPIEGAZIONE
# ============================================================
st.markdown("---")
st.subheader("Spiegazione")

st.write(
    "All'inizio la spira è completamente fuori dalla regione magnetica: "
    "il flusso è nullo e quindi anche la f.e.m. è nulla."
)

st.write("Quando il lato anteriore supera il bordo del campo, l'area immersa cresce:")
st.latex(r"A_{\mathrm{imm}} = Lx")

st.write(
    "Durante questa fase il flusso varia. Per il moto uniforme "
    "il modulo della f.e.m. è costante:"
)
st.latex(r"|\mathcal{E}| = |B|Lv")

st.write(
    "Nel moto uniformemente accelerato la velocità cambia nel tempo "
    "e cambia anche il modulo della f.e.m.:"
)
st.latex(r"|\mathcal{E}| = |B|L|v(t)|")

st.write(
    "Quando anche il lato posteriore supera il bordo, la spira è completamente "
    "immersa. L'area attraversata dal campo non cambia più:"
)
st.latex(r"A_{\mathrm{imm}} = L^2")
st.latex(r"\Phi = BL^2 = \mathrm{costante}")

st.write("Di conseguenza il flusso non varia e:")
st.latex(r"|\mathcal{E}| = 0")

st.write(
    "La freccia rossa rappresenta la forza magnetica esercitata dal campo "
    "esterno sul lato della spira percorso dalla corrente indotta:"
)
st.latex(r"\vec F_L = I\,\vec L \times \vec B")
st.write(
    "Durante l'ingresso questa forza è opposta al moto della spira, "
    "come conseguenza della legge di Lenz. Quando la spira è completamente "
    "immersa nel campo uniforme, la f.e.m. e la corrente indotta diventano "
    "nulle e quindi scompare anche questa forza."
)

st.write(
    "Le linee tratteggiate del grafico indicano l'inizio dell'ingresso "
    "e l'istante in cui l'ingresso è completo."
)

with st.expander("Mostra i calcoli numerici"):
    table = pd.DataFrame({
        "t (s)": times,
        "x lato destro (m)": x_right,
        "v (m/s)": velocities,
        "Area immersa (m²)": immersed_area,
        "Flusso (Wb)": flux,
        "Modulo f.e.m. (V)": emf_abs,
    })
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.caption(
        "Il grafico mostra il modulo della f.e.m. durante l'ingresso. "
        "Prima del contatto e dopo l'ingresso completo il valore è zero."
    )
