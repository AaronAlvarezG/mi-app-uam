import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
INPUT_FILE = "zeroshot_predictions_uam.parquet"
SHEET_NAME = "etiquetas_uam"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Taxonomía principal de la app (10 categorías del proyecto)
CATEGORIES = {
    "cs.AI": "Artificial Intelligence",
    "cs.CL": "Computation and Language",
    "cs.CR": "Cryptography and Security",
    "cs.CV": "Computer Vision and Pattern Recognition",
    "cs.DS": "Data Structures and Algorithms",
    "cs.IT": "Information Theory",
    "cs.LG": "Machine Learning",
    "cs.NA": "Numerical Analysis",
    "cs.RO": "Robotics",
    "cs.SY": "Systems and Control",
}

def fmt(code):
    name = ARXIV_ALL.get(code, {}).get("name") or CATEGORIES.get(code, "Categoría definida por usuario")
    return f"{code} — {name}"

# ── Catálogo completo arXiv (arxiv.org/category_taxonomy) ──────────────────
# Formato: { "código": {"name": "...", "desc": "..."} }
ARXIV_ALL = {
    # Computer Science
    "cs.AI":  {"name": "Artificial Intelligence",                    "desc": "Covers all areas of AI except Vision, Robotics, Machine Learning, Multiagent Systems, and Computation and Language. Includes Expert Systems, Theorem Proving, Knowledge Representation, Planning, and Uncertainty in AI."},
    "cs.AR":  {"name": "Hardware Architecture",                      "desc": "Covers systems organization and hardware architecture."},
    "cs.CC":  {"name": "Computational Complexity",                   "desc": "Covers models of computation, complexity classes, structural complexity, complexity tradeoffs, upper and lower bounds."},
    "cs.CE":  {"name": "Computational Engineering, Finance, Science","desc": "Covers applications of computer science to the mathematical modeling of complex systems in science, engineering, and finance."},
    "cs.CG":  {"name": "Computational Geometry",                     "desc": "Roughly includes material in ACM Subject Classes I.3.5 and F.2.2."},
    "cs.CL":  {"name": "Computation and Language",                   "desc": "Covers natural language processing. Includes parsing, generation, machine translation, dialogue, and information extraction."},
    "cs.CR":  {"name": "Cryptography and Security",                  "desc": "Covers all areas of cryptography and security including authentication, public key cryptosystems, proof-carrying code, etc."},
    "cs.CV":  {"name": "Computer Vision and Pattern Recognition",    "desc": "Covers image processing, computer vision, pattern recognition, and scene understanding."},
    "cs.CY":  {"name": "Computers and Society",                      "desc": "Covers impact of computers on society, computer ethics, information technology and public policy, legal aspects of computing."},
    "cs.DB":  {"name": "Databases",                                  "desc": "Covers database management, data mining, and data processing."},
    "cs.DC":  {"name": "Distributed, Parallel, and Cluster Computing","desc": "Covers fault-tolerance, distributed algorithms, stability, parallel computation, and cluster computing."},
    "cs.DL":  {"name": "Digital Libraries",                          "desc": "Covers all aspects of digital library design and document and text creation."},
    "cs.DM":  {"name": "Discrete Mathematics",                       "desc": "Covers combinatorics, graph theory, applications of probability."},
    "cs.DS":  {"name": "Data Structures and Algorithms",             "desc": "Covers data structures and analysis of algorithms."},
    "cs.ET":  {"name": "Emerging Technologies",                      "desc": "Covers approaches to information processing based on alternatives to silicon CMOS: nanoscale, photonic, spin-based, superconducting, quantum technologies."},
    "cs.FL":  {"name": "Formal Languages and Automata Theory",       "desc": "Covers automata theory, formal language theory, grammars, and combinatorics on words."},
    "cs.GL":  {"name": "General Literature",                         "desc": "Covers introductory material, survey material, predictions of future trends, biographies, and miscellaneous CS material."},
    "cs.GR":  {"name": "Graphics",                                   "desc": "Covers all aspects of computer graphics."},
    "cs.GT":  {"name": "Computer Science and Game Theory",           "desc": "Covers all theoretical and applied aspects at the intersection of computer science and game theory."},
    "cs.HC":  {"name": "Human-Computer Interaction",                 "desc": "Covers human factors, user interfaces, and collaborative computing."},
    "cs.IR":  {"name": "Information Retrieval",                      "desc": "Covers indexing, dictionaries, retrieval, content and analysis."},
    "cs.IT":  {"name": "Information Theory",                         "desc": "Covers theoretical and experimental aspects of information theory and coding."},
    "cs.LG":  {"name": "Machine Learning",                           "desc": "Papers on all aspects of machine learning research: supervised, unsupervised, reinforcement learning, bandit problems, robustness, explanation, fairness, and methodology."},
    "cs.LO":  {"name": "Logic in Computer Science",                  "desc": "Covers all aspects of logic in computer science, including finite model theory, logics of programs, modal logic, and program verification."},
    "cs.MA":  {"name": "Multiagent Systems",                         "desc": "Covers multiagent systems, distributed artificial intelligence, intelligent agents, coordinated interactions."},
    "cs.MM":  {"name": "Multimedia",                                 "desc": "Roughly includes material in ACM Subject Class H.5.1."},
    "cs.MS":  {"name": "Mathematical Software",                      "desc": "Roughly includes material in ACM Subject Class G.4."},
    "cs.NA":  {"name": "Numerical Analysis",                         "desc": "Alias for math.NA. Covers numerical algorithms for problems in analysis and algebra, scientific computation."},
    "cs.NE":  {"name": "Neural and Evolutionary Computing",          "desc": "Covers neural networks, connectionism, genetic algorithms, artificial life, adaptive behavior."},
    "cs.NI":  {"name": "Networking and Internet Architecture",       "desc": "Covers all aspects of computer communication networks, including network architecture, protocols, and internetwork standards."},
    "cs.OH":  {"name": "Other Computer Science",                     "desc": "For documents that do not fit anywhere else in cs."},
    "cs.OS":  {"name": "Operating Systems",                          "desc": "Roughly includes material in ACM Subject Classes D.4.x."},
    "cs.PF":  {"name": "Performance",                                "desc": "Covers performance measurement and evaluation, queueing, and simulation."},
    "cs.PL":  {"name": "Programming Languages",                      "desc": "Covers programming language semantics, language features, and programming approaches such as OOP and functional programming."},
    "cs.RO":  {"name": "Robotics",                                   "desc": "Covers robotics: manipulation, locomotion, sensors, perception, planning, control, and human-robot interaction."},
    "cs.SC":  {"name": "Symbolic Computation",                       "desc": "Roughly includes material in ACM Subject Class I.1."},
    "cs.SD":  {"name": "Sound",                                      "desc": "Covers all aspects of computing with sound, including analysis, synthesis, audio interfaces, and music."},
    "cs.SE":  {"name": "Software Engineering",                       "desc": "Covers design tools, software metrics, testing and debugging, programming environments."},
    "cs.SI":  {"name": "Social and Information Networks",            "desc": "Covers design, analysis, and modeling of social and information networks."},
    "cs.SY":  {"name": "Systems and Control",                        "desc": "Alias for eess.SY. Covers automatic control systems, modeling, simulation and optimization, nonlinear, distributed, adaptive, stochastic and robust control."},
    # Economics
    "econ.EM": {"name": "Econometrics",         "desc": "Econometric Theory, Micro/Macro-Econometrics, Empirical Content of Economic Relations."},
    "econ.GN": {"name": "General Economics",    "desc": "General methodological, applied, and empirical contributions to economics."},
    "econ.TH": {"name": "Theoretical Economics","desc": "Includes Contract Theory, Decision Theory, Game Theory, General Equilibrium, Market and Mechanism Design."},
    # Electrical Engineering and Systems Science
    "eess.AS": {"name": "Audio and Speech Processing", "desc": "Theory and methods for processing signals representing audio, speech, and language."},
    "eess.IV": {"name": "Image and Video Processing",  "desc": "Theory, algorithms, and architectures for image, video, and multidimensional signal processing."},
    "eess.SP": {"name": "Signal Processing",           "desc": "Theory, algorithms, performance analysis and applications of signal and data analysis."},
    "eess.SY": {"name": "Systems and Control",         "desc": "Theoretical and experimental research covering all facets of automatic control systems."},
    # Mathematics
    "math.AC": {"name": "Commutative Algebra",       "desc": "Commutative rings, modules, ideals, homological algebra, computational aspects, invariant theory."},
    "math.AG": {"name": "Algebraic Geometry",        "desc": "Algebraic varieties, stacks, sheaves, schemes, moduli spaces, complex geometry."},
    "math.AP": {"name": "Analysis of PDEs",          "desc": "Existence and uniqueness, boundary conditions, linear and non-linear operators, stability, integrable PDEs."},
    "math.AT": {"name": "Algebraic Topology",        "desc": "Homotopy theory, homological algebra, algebraic treatments of manifolds."},
    "math.CA": {"name": "Classical Analysis and ODEs","desc": "Special functions, orthogonal polynomials, harmonic analysis, ODEs, calculus of variations."},
    "math.CO": {"name": "Combinatorics",             "desc": "Discrete mathematics, graph theory, enumeration, combinatorial optimization, Ramsey theory."},
    "math.CT": {"name": "Category Theory",           "desc": "Enriched categories, topoi, abelian categories, monoidal categories, homological algebra."},
    "math.CV": {"name": "Complex Variables",         "desc": "Holomorphic functions, automorphic group actions, pseudoconvexity, complex geometry."},
    "math.DG": {"name": "Differential Geometry",     "desc": "Complex, contact, Riemannian, pseudo-Riemannian and Finsler geometry, relativity, gauge theory."},
    "math.DS": {"name": "Dynamical Systems",         "desc": "Dynamics of differential equations and flows, mechanics, iterations, complex dynamics."},
    "math.FA": {"name": "Functional Analysis",       "desc": "Banach spaces, function spaces, real functions, integral transforms, theory of distributions, measure theory."},
    "math.GM": {"name": "General Mathematics",       "desc": "Mathematical material of general interest, topics not covered elsewhere."},
    "math.GN": {"name": "General Topology",          "desc": "Continuum theory, point-set topology, spaces with algebraic structure, foundations."},
    "math.GR": {"name": "Group Theory",              "desc": "Finite groups, topological groups, representation theory, cohomology, classification and structure."},
    "math.GT": {"name": "Geometric Topology",        "desc": "Manifolds, orbifolds, polyhedra, cell complexes, foliations, geometric structures."},
    "math.HO": {"name": "History and Overview",      "desc": "Biographies, philosophy of mathematics, mathematics education, recreational mathematics."},
    "math.IT": {"name": "Information Theory",        "desc": "Alias for cs.IT. Covers theoretical and experimental aspects of information theory and coding."},
    "math.KT": {"name": "K-Theory and Homology",     "desc": "Algebraic and topological K-theory, relations with topology, commutative algebra, and operator algebras."},
    "math.LO": {"name": "Logic",                     "desc": "Logic, set theory, point-set topology, formal mathematics."},
    "math.MG": {"name": "Metric Geometry",           "desc": "Euclidean, hyperbolic, discrete, convex, coarse geometry, comparisons in Riemannian geometry."},
    "math.MP": {"name": "Mathematical Physics",      "desc": "Alias for math-ph. Application of mathematics to problems in physics."},
    "math.NA": {"name": "Numerical Analysis",        "desc": "Numerical algorithms for problems in analysis and algebra, scientific computation."},
    "math.NT": {"name": "Number Theory",             "desc": "Prime numbers, diophantine equations, analytic and algebraic number theory, arithmetic geometry."},
    "math.OA": {"name": "Operator Algebras",         "desc": "Algebras of operators on Hilbert space, C*-algebras, von Neumann algebras."},
    "math.OC": {"name": "Optimization and Control",  "desc": "Operations research, linear programming, control theory, systems theory, optimal control, game theory."},
    "math.PR": {"name": "Probability",               "desc": "Theory and applications of probability and stochastic processes."},
    "math.QA": {"name": "Quantum Algebra",           "desc": "Quantum groups, skein theories, operadic and diagrammatic algebra, quantum field theory."},
    "math.RA": {"name": "Rings and Algebras",        "desc": "Non-commutative rings and algebras, universal algebra, lattice theory, linear algebra."},
    "math.RT": {"name": "Representation Theory",     "desc": "Linear representations of algebras and groups, Lie theory, associative algebras."},
    "math.SG": {"name": "Symplectic Geometry",       "desc": "Hamiltonian systems, symplectic flows, classical integrable systems."},
    "math.SP": {"name": "Spectral Theory",           "desc": "Schrödinger operators, operators on manifolds, general differential operators."},
    "math.ST": {"name": "Statistics Theory",         "desc": "Applied, computational and theoretical statistics: inference, regression, time series, multivariate analysis."},
    # Physics
    "astro-ph.CO": {"name": "Cosmology and Nongalactic Astrophysics","desc": "Phenomenology of early universe, CMB, cosmological parameters, large-scale structure."},
    "astro-ph.EP": {"name": "Earth and Planetary Astrophysics",      "desc": "Planetary physics, extrasolar planets, comets, asteroids, solar system formation."},
    "astro-ph.GA": {"name": "Astrophysics of Galaxies",              "desc": "Phenomena pertaining to galaxies or the Milky Way: star clusters, ISM, galactic structure, AGN."},
    "astro-ph.HE": {"name": "High Energy Astrophysical Phenomena",   "desc": "Cosmic ray production, gamma ray astronomy, X-rays, supernovae, neutron stars, pulsars."},
    "astro-ph.IM": {"name": "Instrumentation and Methods for Astrophysics","desc": "Detector and telescope design, laboratory astrophysics, data analysis methods."},
    "astro-ph.SR": {"name": "Solar and Stellar Astrophysics",        "desc": "White dwarfs, star formation, stellar evolution, helioseismology, solar neutrinos."},
    "cond-mat.dis-nn":  {"name": "Disordered Systems and Neural Networks","desc": "Glasses, spin glasses, random systems, neural networks."},
    "cond-mat.mes-hall":{"name": "Mesoscale and Nanoscale Physics",  "desc": "Quantum dots, wires, wells, spintronics, 2D electron gases, nanotubes, graphene."},
    "cond-mat.mtrl-sci":{"name": "Materials Science",                "desc": "Synthesis, characterization, structural phase transitions, mechanical properties."},
    "cond-mat.other":   {"name": "Other Condensed Matter",           "desc": "Work in condensed matter that does not fit other cond-mat classifications."},
    "cond-mat.quant-gas":{"name": "Quantum Gases",                   "desc": "Ultracold atomic and molecular gases, Bose-Einstein condensation, optical lattices."},
    "cond-mat.soft":    {"name": "Soft Condensed Matter",            "desc": "Membranes, polymers, liquid crystals, glasses, colloids, granular matter."},
    "cond-mat.stat-mech":{"name": "Statistical Mechanics",           "desc": "Phase transitions, thermodynamics, field theory, non-equilibrium phenomena, renormalization group."},
    "cond-mat.str-el":  {"name": "Strongly Correlated Electrons",    "desc": "Quantum magnetism, non-Fermi liquids, spin liquids, quantum criticality."},
    "cond-mat.supr-con":{"name": "Superconductivity",                "desc": "Superconductivity: theory, models, experiment. Superflow in helium."},
    "gr-qc":   {"name": "General Relativity and Quantum Cosmology",  "desc": "Gravitational physics, gravitational waves, experimental tests, relativistic astrophysics."},
    "hep-ex":  {"name": "High Energy Physics - Experiment",          "desc": "Results from high-energy/particle physics experiments."},
    "hep-lat": {"name": "High Energy Physics - Lattice",             "desc": "Lattice field theory, phenomenology, algorithms and hardware."},
    "hep-ph":  {"name": "High Energy Physics - Phenomenology",       "desc": "Theoretical particle physics and its interrelation with experiment."},
    "hep-th":  {"name": "High Energy Physics - Theory",              "desc": "Formal aspects of quantum field theory, string theory, supersymmetry and supergravity."},
    "math-ph": {"name": "Mathematical Physics",                      "desc": "Application of mathematics to problems in physics; mathematically rigorous formulations of physical theories."},
    "nlin.AO": {"name": "Adaptation and Self-Organizing Systems",    "desc": "Self-organizing systems, statistical physics, stochastic processes, machine learning."},
    "nlin.CD": {"name": "Chaotic Dynamics",                          "desc": "Dynamical systems, chaos, quantum chaos, turbulence."},
    "nlin.CG": {"name": "Cellular Automata and Lattice Gases",       "desc": "Computational methods, time series analysis, signal processing, wavelets."},
    "nlin.PS": {"name": "Pattern Formation and Solitons",            "desc": "Pattern formation, coherent structures, solitons."},
    "nlin.SI": {"name": "Exactly Solvable and Integrable Systems",   "desc": "Exactly solvable systems, integrable PDEs, Painlevé analysis."},
    "nucl-ex": {"name": "Nuclear Experiment",                        "desc": "Results from experimental nuclear physics."},
    "nucl-th": {"name": "Nuclear Theory",                            "desc": "Theory of nuclear structure from hadron structure to neutron stars."},
    "physics.acc-ph":  {"name": "Accelerator Physics",        "desc": "Accelerator theory, simulation, technology, beam physics, radiation sources."},
    "physics.ao-ph":   {"name": "Atmospheric and Oceanic Physics","desc": "Atmospheric and oceanic physics, biogeophysics, climate science."},
    "physics.app-ph":  {"name": "Applied Physics",            "desc": "Applications of physics to new technology: electronics, optics, photonics, metamaterials, nanotechnology."},
    "physics.atm-clus":{"name": "Atomic and Molecular Clusters","desc": "Atomic and molecular clusters, nanoparticles: electronic, optical, chemical, magnetic properties."},
    "physics.atom-ph": {"name": "Atomic Physics",             "desc": "Atomic and molecular structure, spectra, collisions. Cold atoms and molecules."},
    "physics.bio-ph":  {"name": "Biological Physics",         "desc": "Molecular, cellular, neurological biophysics, single-molecule biophysics, bioinformatics."},
    "physics.chem-ph": {"name": "Chemical Physics",           "desc": "Experimental, computational, and theoretical physics of atoms, molecules, and clusters."},
    "physics.class-ph":{"name": "Classical Physics",          "desc": "Newtonian and relativistic dynamics, Maxwell's equations, classical waves, thermodynamics."},
    "physics.comp-ph": {"name": "Computational Physics",      "desc": "All aspects of computational science applied to physics."},
    "physics.data-an": {"name": "Data Analysis, Statistics and Probability","desc": "Methods and software for physics data analysis, statistical and mathematical aspects."},
    "physics.ed-ph":   {"name": "Physics Education",          "desc": "Research on teaching and learning in physics, misconceptions, classroom practices."},
    "physics.flu-dyn": {"name": "Fluid Dynamics",             "desc": "Turbulence, instabilities, compressible/incompressible flows, biological fluid dynamics."},
    "physics.gen-ph":  {"name": "General Physics",            "desc": "General physics topics."},
    "physics.geo-ph":  {"name": "Geophysics",                 "desc": "Atmospheric physics, computational geophysics, solid earth geophysics, space plasma physics."},
    "physics.hist-ph": {"name": "History and Philosophy of Physics","desc": "History and philosophy of all branches of physics, astrophysics, and cosmology."},
    "physics.ins-det": {"name": "Instrumentation and Detectors","desc": "Instrumentation and detectors for research in natural science."},
    "physics.med-ph":  {"name": "Medical Physics",            "desc": "Radiation therapy, dosimetry, biomedical imaging, new modalities."},
    "physics.optics":  {"name": "Optics",                     "desc": "Adaptive, astronomical, biomedical optics; lasers, holography, quantum optics, fiber optics."},
    "physics.plasm-ph":{"name": "Plasma Physics",             "desc": "Fundamental plasma physics, magnetically confined plasmas, high energy density plasmas."},
    "physics.pop-ph":  {"name": "Popular Physics",            "desc": "Popular physics topics."},
    "physics.soc-ph":  {"name": "Physics and Society",        "desc": "Structure, dynamics and collective behavior of societies and groups. Complex networks."},
    "physics.space-ph":{"name": "Space Physics",              "desc": "Space plasma physics, heliophysics, space weather, planetary magnetospheres."},
    "quant-ph": {"name": "Quantum Physics",                   "desc": "Quantum mechanics, quantum information, quantum computing, quantum optics."},
    # Quantitative Biology
    "q-bio.BM": {"name": "Biomolecules",              "desc": "DNA, RNA, proteins, lipids; molecular structures, folding kinetics, molecular interactions."},
    "q-bio.CB": {"name": "Cell Behavior",             "desc": "Cell-cell signaling, morphogenesis, apoptosis, viral-host interaction, immunology."},
    "q-bio.GN": {"name": "Genomics",                  "desc": "DNA sequencing, gene finding, RNA editing, genomic structure and processes."},
    "q-bio.MN": {"name": "Molecular Networks",        "desc": "Gene regulation, signal transduction, proteomics, metabolomics, enzymatic networks."},
    "q-bio.NC": {"name": "Neurons and Cognition",     "desc": "Synapse, cortex, neuronal dynamics, neural network, sensorimotor control, behavior."},
    "q-bio.OT": {"name": "Other Quantitative Biology","desc": "Work in quantitative biology that does not fit other q-bio classifications."},
    "q-bio.PE": {"name": "Populations and Evolution", "desc": "Population dynamics, epidemiological models, co-evolution, biodiversity, molecular evolution."},
    "q-bio.QM": {"name": "Quantitative Methods",      "desc": "Experimental, numerical, statistical and mathematical contributions of value to biology."},
    "q-bio.SC": {"name": "Subcellular Processes",     "desc": "Assembly and control of subcellular structures, molecular motors, mitosis and meiosis."},
    "q-bio.TO": {"name": "Tissues and Organs",        "desc": "Blood flow, biomechanics of bones, electrical waves, endocrine system, tumor growth."},
    # Quantitative Finance
    "q-fin.CP": {"name": "Computational Finance",     "desc": "Monte Carlo, PDE, lattice and other numerical methods with applications to financial modeling."},
    "q-fin.EC": {"name": "Economics",                 "desc": "Alias for econ.GN. Micro and macro economics, international economics, labor economics."},
    "q-fin.GN": {"name": "General Finance",           "desc": "Development of general quantitative methodologies with applications in finance."},
    "q-fin.MF": {"name": "Mathematical Finance",      "desc": "Mathematical and analytical methods of finance, including stochastic and probabilistic analysis."},
    "q-fin.PM": {"name": "Portfolio Management",      "desc": "Security selection, capital allocation, investment strategies and performance measurement."},
    "q-fin.PR": {"name": "Pricing of Securities",     "desc": "Valuation and hedging of financial securities, derivatives, and structured products."},
    "q-fin.RM": {"name": "Risk Management",           "desc": "Measurement and management of financial risks in trading, banking, and insurance."},
    "q-fin.ST": {"name": "Statistical Finance",       "desc": "Statistical, econometric and econophysics analyses with applications to financial markets."},
    "q-fin.TR": {"name": "Trading and Market Microstructure","desc": "Market microstructure, liquidity, exchange design, automated trading, agent-based modeling."},
    # Statistics
    "stat.AP": {"name": "Statistics - Applications", "desc": "Biology, Education, Epidemiology, Engineering, Environmental Sciences, Medical, Social Sciences."},
    "stat.CO": {"name": "Statistics - Computation",  "desc": "Algorithms, Simulation, Visualization."},
    "stat.ME": {"name": "Statistics - Methodology",  "desc": "Design, Surveys, Model Selection, Multiple Testing, Multivariate Methods, Time Series."},
    "stat.ML": {"name": "Statistics - Machine Learning","desc": "Machine learning papers with a statistical or theoretical grounding: supervised, unsupervised, RL, high-dimensional inference."},
    "stat.OT": {"name": "Other Statistics",          "desc": "Work in statistics that does not fit other stat classifications."},
    "stat.TH": {"name": "Statistics Theory",         "desc": "Alias for math.ST. Asymptotics, Bayesian Inference, Decision Theory, Estimation, Testing."},
}

# Helper: descripción para mostrar en la tarjeta
def get_desc(code):
    return ARXIV_ALL.get(code, {}).get("desc", "")

# ─────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────
@st.cache_resource
def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


def load_saved_labels():
    try:
        records = get_sheet().get_all_records()
        return {str(r["paper_id"]): r["etiqueta_experto"] for r in records if r.get("etiqueta_experto")}
    except Exception as e:
        st.warning(f"No se pudieron cargar etiquetas previas: {e}")
        return {}


def save_label(paper_id, autor, titulo, pred, etiqueta):
    try:
        sheet     = get_sheet()
        ids       = sheet.col_values(1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row       = [str(paper_id), autor, titulo, pred, etiqueta, timestamp]
        if str(paper_id) in ids:
            idx = ids.index(str(paper_id)) + 1
            sheet.update(f"A{idx}:F{idx}", [row])
        else:
            sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# ─────────────────────────────────────────
# DATOS
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_parquet(INPUT_FILE)
    if "etiqueta_experto" not in df.columns:
        df["etiqueta_experto"] = None
    return df


def apply_saved_labels(df, saved):
    for pid, label in saved.items():
        try:
            df.loc[int(pid), "etiqueta_experto"] = label
        except Exception:
            pass
    return df

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    #MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
    .block-container { max-width:1080px; padding-top:1rem !important; padding-bottom:1rem !important; }

    .prog-bg   { background:#E5E3DE; border-radius:6px; height:6px; width:100%; margin:4px 0; }
    .prog-fill { background:#1D9E75; border-radius:6px; height:6px; }

    .sec { font-size:.68rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase;
           color:#888780; margin-bottom:4px; margin-top:2px; }

    .pill      { display:inline-block; background:#EAF3DE; color:#27500A; font-size:.76rem;
                 font-weight:500; padding:3px 11px; border-radius:20px;
                 font-family:'IBM Plex Mono',monospace; }
    .pill-warn { background:#FAEEDA; color:#633806; }

    .paper-card { background:#FAFAF9; border:1px solid #E5E3DE; border-radius:10px;
                  padding:.9rem 1.1rem; margin-bottom:.5rem; }

    /* Botones laterales de artículos */
    div[data-testid="stButton"] button {
        text-align:left; white-space:normal; word-break:break-word;
        font-size:.8rem; line-height:1.3; padding:5px 8px;
    }

    /* Botón primario */
    div[data-testid="stButton"] button[kind="primary"] {
        background:#1D1C1A; color:#FAFAF9; border:none; border-radius:7px;
        font-family:'IBM Plex Sans',sans-serif; font-weight:500;
        font-size:.85rem; transition:background .15s;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover { background:#3a3836; }

    /* Radio compacto */
    div[data-testid="stRadio"] label { font-size:.83rem; padding:1px 0; }
    div[data-testid="stRadio"] > div { gap:1px !important; }

    /* Tabla admin */
    .admin-row { display:grid; grid-template-columns:1fr 60px 120px 90px;
                 gap:8px; align-items:center; padding:6px 10px;
                 border-bottom:0.5px solid #E5E3DE; font-size:.83rem; }
    .admin-row.head { font-weight:600; font-size:.68rem; text-transform:uppercase;
                      letter-spacing:.06em; color:#888780; }
    .chip-done    { background:#EAF3DE; color:#27500A; border-radius:20px;
                    padding:2px 10px; font-size:.72rem; font-weight:500; text-align:center; display:inline-block; }
    .chip-partial { background:#FAEEDA; color:#633806; border-radius:20px;
                    padding:2px 10px; font-size:.72rem; font-weight:500; text-align:center; display:inline-block; }
    .chip-none    { background:#F1EFE8; color:#888780; border-radius:20px;
                    padding:2px 10px; font-size:.72rem; font-weight:500; text-align:center; display:inline-block; }

    details summary { font-size:.8rem; color:#888780; cursor:pointer; }

    /* Tooltip nativo: mostrar cursor de ayuda sobre opciones de radio */
    div[data-testid="stRadio"] label { cursor:help; }
    </style>
    """, unsafe_allow_html=True)


def prog_bar(pct):
    return f'<div class="prog-bg"><div class="prog-fill" style="width:{pct}%"></div></div>'

# ─────────────────────────────────────────
# PANTALLA 0 — BIENVENIDA
# ─────────────────────────────────────────
def screen_welcome(df):
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("### Validación de Artículos · UAM-A")
    with h2:
        if st.button("Vista general →", use_container_width=True):
            st.session_state.screen = "admin"
            st.rerun()

    st.markdown("Seleccione su nombre para comenzar.")
    authors = sorted(df["autor"].dropna().unique())
    author  = st.selectbox("", options=["— seleccione —"] + list(authors))

    if author == "— seleccione —":
        st.caption("Elija su nombre en la lista para ver su progreso.")
        return

    author_df = df[df["autor"] == author]
    total     = len(author_df)
    done      = int(author_df["etiqueta_experto"].notna().sum())
    pct       = int(done / total * 100) if total else 100

    st.markdown("---")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.markdown(f'<div style="font-size:2rem;font-weight:300;color:#1D9E75;line-height:1">{pct}%</div>', unsafe_allow_html=True)
        st.caption(f"{done} / {total} revisados")
        st.markdown(prog_bar(pct), unsafe_allow_html=True)
    with c2:
        st.metric("Pendientes", total - done)
        st.metric("Completados", done)
    with c3:
        st.markdown('<div class="sec">Tus artículos</div>', unsafe_allow_html=True)
        for _, row in author_df.iterrows():
            if pd.notna(row["etiqueta_experto"]):
                st.markdown(f'<div style="font-size:.8rem;color:#085041;padding:2px 0">✓ {row["titulo"][:72]}{"…" if len(row["titulo"])>72 else ""}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="font-size:.8rem;color:#888780;padding:2px 0">○ {row["titulo"][:72]}{"…" if len(row["titulo"])>72 else ""}</div>', unsafe_allow_html=True)

    st.markdown("")
    btn_label = "Ver resumen" if done == total else "Comenzar revisión →"
    target    = "done" if done == total else "validate"
    cb, _ = st.columns([1, 3])
    with cb:
        if st.button(btn_label, type="primary", use_container_width=True):
            st.session_state.author    = author
            st.session_state.paper_idx = 0
            st.session_state.edit_idx  = None
            st.session_state.screen    = target
            st.rerun()

# ─────────────────────────────────────────
# PANTALLA 1 — ADMIN
# ─────────────────────────────────────────
def screen_admin(df):
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("### Avance general · UAM-A")
    with h2:
        if st.button("‹ Volver", use_container_width=True):
            st.session_state.screen = "welcome"
            st.rerun()

    total_p  = len(df)
    total_d  = int(df["etiqueta_experto"].notna().sum())
    glob_pct = int(total_d / total_p * 100) if total_p else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total artículos", total_p)
    m2.metric("Validados", total_d)
    m3.metric("Avance global", f"{glob_pct}%")
    st.markdown(prog_bar(glob_pct), unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(
        '<div class="admin-row head">'
        '<span>Investigador</span><span>Arts.</span><span>Progreso</span><span>Estado</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    authors = sorted(df["autor"].dropna().unique())
    for author in authors:
        a_df = df[df["autor"] == author]
        tot  = len(a_df)
        done = int(a_df["etiqueta_experto"].notna().sum())
        pct  = int(done / tot * 100) if tot else 0

        if done == tot:
            chip = '<span class="chip-done">Completo</span>'
        elif done == 0:
            chip = '<span class="chip-none">Sin iniciar</span>'
        else:
            chip = f'<span class="chip-partial">{pct}%</span>'

        bar  = f'<div class="prog-bg" style="margin:0"><div class="prog-fill" style="width:{pct}%"></div></div>'
        st.markdown(
            f'<div class="admin-row"><span>{author}</span>'
            f'<span style="text-align:center">{done}/{tot}</span>'
            f'{bar}{chip}</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────
# PANTALLA 2 — VALIDACIÓN
# ─────────────────────────────────────────
def screen_validate(df):
    author    = st.session_state.author
    author_df = df[df["autor"] == author].copy()
    pending   = author_df[author_df["etiqueta_experto"].isna()]
    done_df   = author_df[author_df["etiqueta_experto"].notna()]
    total_a   = len(author_df)
    done_n    = len(done_df)

    # Sin pendientes: ir a done, SALVO que el usuario haya llegado
    # explícitamente desde el botón "Corregir etiquetas" (flag correction_mode).
    if len(pending) == 0:
        if st.session_state.get("correction_mode") and len(done_df) > 0:
            # Entrar en modo edición sobre el primer artículo clasificado
            if st.session_state.get("edit_idx") is None:
                st.session_state.edit_idx = done_df.index[0]
        else:
            st.session_state.screen          = "done"
            st.session_state.correction_mode = False
            st.rerun()
            return

    edit_idx = st.session_state.get("edit_idx", None)
    if edit_idx is not None:
        paper        = author_df.loc[edit_idx]
        is_edit_mode = True
    else:
        idx = st.session_state.get("paper_idx", 0)
        if idx >= len(pending):
            idx = 0
            st.session_state.paper_idx = 0
        paper        = pending.iloc[idx]
        is_edit_mode = False

    original_idx = paper.name
    pred_code    = paper["pred_zeroshot"]

    # ── Layout 2 columnas ──
    col_list, col_form = st.columns([1, 2.6], gap="medium")

    # ── LISTA LATERAL ──
    with col_list:
        pct = int(done_n / total_a * 100)
        st.markdown(f'<div style="font-size:.82rem;font-weight:500">{author.split(",")[0]}</div>', unsafe_allow_html=True)
        st.markdown(prog_bar(pct), unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:.7rem;color:#888780;margin-bottom:.5rem">{done_n}/{total_a} revisados</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">Pendientes</div>', unsafe_allow_html=True)
        for i, (ridx, row) in enumerate(pending.iterrows()):
            active = (not is_edit_mode) and (i == st.session_state.get("paper_idx", 0))
            label  = ("▶ " if active else "") + row["titulo"][:52] + ("…" if len(row["titulo"]) > 52 else "")
            if st.button(label, key=f"p_{ridx}", use_container_width=True):
                st.session_state.paper_idx = i
                st.session_state.edit_idx  = None
                st.rerun()

        if len(done_df) > 0:
            st.markdown('<div class="sec" style="margin-top:.5rem">Clasificados</div>', unsafe_allow_html=True)
            for ridx, row in done_df.iterrows():
                active = is_edit_mode and (ridx == edit_idx)
                label  = ("✎ " if active else "✓ ") + row["titulo"][:52] + ("…" if len(row["titulo"]) > 52 else "")
                if st.button(label, key=f"d_{ridx}", use_container_width=True):
                    st.session_state.edit_idx = ridx
                    st.rerun()

        st.markdown("")
        if st.button("‹ Salir", use_container_width=True):
            st.session_state.screen   = "welcome"
            st.session_state.edit_idx = None
            st.rerun()

    # ── FORMULARIO ──
    with col_form:
        if is_edit_mode:
            st.markdown(
                '<div style="font-size:.7rem;background:#FAEEDA;color:#633806;'
                'border-radius:5px;padding:3px 10px;display:inline-block;margin-bottom:.4rem">'
                '✎ Modo corrección — editando artículo ya clasificado</div>',
                unsafe_allow_html=True,
            )

        cur_etq = paper.get("etiqueta_experto", "")
        st.markdown(
            f'<div class="paper-card">'
            f'<div class="sec">Título</div>'
            f'<p style="font-size:.93rem;font-weight:500;margin:3px 0 8px;line-height:1.35">{paper["titulo"]}</p>'
            f'<div class="sec">Predicción del modelo</div>'
            f'<span class="pill">{fmt(pred_code)}</span>'
            f'{"<span style=margin-left:8px class=pill pill-warn>Actual: " + str(cur_etq) + "</span>" if is_edit_mode and cur_etq else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Ver abstract"):
            st.write(paper["Resumen"])

        # ── Tarjeta de selección de categoría ──
        # Determinar preselección:
        #   modo edición  → etiqueta ya guardada
        #   modo normal   → pred_zeroshot del modelo
        custom_val = "__custom__"
        cat_codes  = list(CATEGORIES.keys())

        if is_edit_mode and pd.notna(cur_etq) and cur_etq:
            preselect = cur_etq
        else:
            preselect = pred_code

        # Opciones del combo: todos los códigos + opción personalizada
        combo_options = cat_codes + [custom_val]
        combo_labels  = {c: f"{c} — {CATEGORIES[c]}" for c in cat_codes}
        combo_labels[custom_val] = "Otra — ingresar código manualmente"

        # default_idx para el selectbox
        if preselect in cat_codes:
            default_idx = cat_codes.index(preselect)
        else:
            default_idx = len(cat_codes)  # personalizada

        # Clave única por artículo para que el estado se inicialice correctamente
        sel_key = f"sel_{original_idx}"
        if sel_key not in st.session_state:
            st.session_state[sel_key] = combo_options[default_idx]

        # Cabecera de la tarjeta: categoría actualmente seleccionada
        sel_code = st.session_state.get(sel_key, combo_options[default_idx])
        if sel_code == custom_val:
            sel_display = "Categoría personalizada"
            sel_desc    = "Ingrese el código arXiv en el campo de texto."
        else:
            sel_display = combo_labels.get(sel_code, sel_code)
            sel_desc    = get_desc(sel_code)

        st.markdown(
            f'<div style="background:#FAFAF9;border:1.5px solid #1D9E75;border-radius:10px;padding:.9rem 1.1rem;margin-top:.4rem">'
            f'<div class="sec">Categoría seleccionada</div>'
            f'<div style="font-size:1rem;font-weight:500;color:#1D1C1A;margin:4px 0 2px">{sel_display}</div>'
            f'<div style="font-size:.75rem;color:#5F5E5A;line-height:1.5;min-height:1.2rem">{sel_desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Combo de selección
        selection = st.selectbox(
            "Cambiar categoría",
            options=combo_options,
            format_func=lambda v: combo_labels[v],
            index=combo_options.index(sel_code) if sel_code in combo_options else default_idx,
            label_visibility="collapsed",
            key=sel_key,
        )

        # Campo personalizado con searchbox sobre catálogo completo arXiv
        custom_input = ""
        if selection == custom_val:
            from streamlit_searchbox import st_searchbox

            def search_arxiv(query: str):
                """Filtra el catálogo arXiv por código o nombre. Devuelve lista de (label, value)."""
                q = query.strip().lower()
                if not q:
                    return []
                results = []
                for code, info in ARXIV_ALL.items():
                    name = info["name"].lower()
                    if q in code.lower() or q in name:
                        results.append((f"{code} — {info['name']}", code))
                # Primero coincidencias exactas de prefijo de código
                results.sort(key=lambda x: (not x[1].lower().startswith(q), x[1]))
                return results[:12]

            default_custom = str(cur_etq) if (is_edit_mode and cur_etq and cur_etq not in CATEGORIES) else None

            found = st_searchbox(
                search_arxiv,
                key="searchbox_custom",
                placeholder="Buscar por código (cs.DB) o nombre (databases)…",
                default=default_custom,
                clear_on_submit=False,
                label="Buscar categoría arXiv",
            )

            # Mostrar descripción de lo encontrado, o permitir texto libre
            if found and found in ARXIV_ALL:
                info = ARXIV_ALL[found]
                st.markdown(
                    f'<div style="font-size:.75rem;color:#5F5E5A;background:#F1EFE8;border-radius:6px;'
                    f'padding:6px 10px;margin-top:4px;line-height:1.5">'
                    f'<b style="color:#1D1C1A">{info["name"]}</b><br>{info["desc"]}</div>',
                    unsafe_allow_html=True,
                )
                custom_input = found
            elif found:
                # El investigador escribió algo que no está en el catálogo → se acepta igual
                st.caption(f"Categoría personalizada: «{found}» — se guardará tal como está.")
                custom_input = found
            else:
                st.caption("Escriba un código arXiv o nombre para buscar. Si no existe, puede escribir lo que desee.")

        # Botones acción
        ba1, ba2, _ = st.columns([1.3, 1, 2])
        with ba1:
            save_clicked = st.button("Guardar →", type="primary", use_container_width=True)
        with ba2:
            if is_edit_mode:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.edit_idx = None
                    st.rerun()
            elif st.session_state.get("paper_idx", 0) + 1 < len(pending):
                if st.button("Saltar", use_container_width=True):
                    st.session_state.paper_idx += 1
                    st.rerun()

        if save_clicked:
            if selection == custom_val:
                if not custom_input.strip():
                    st.error("Escriba el código de categoría.")
                    return
                final_label = custom_input.strip()
            else:
                final_label = selection  # directamente el código arXiv (ej. "cs.LG")

            ok = save_label(
                paper_id=original_idx,
                autor=author,
                titulo=paper["titulo"],
                pred=pred_code,
                etiqueta=final_label,
            )
            if ok:
                df.loc[original_idx, "etiqueta_experto"] = final_label
                st.session_state.edit_idx = None
                st.rerun()

# ─────────────────────────────────────────
# PANTALLA 3 — COMPLETADO
# ─────────────────────────────────────────
def screen_done(df):
    author    = st.session_state.author
    author_df = df[df["autor"] == author]
    total     = len(author_df)

    st.markdown("### ¡Revisión completada!")
    st.success(f"Ha validado los {total} artículos asignados. Muchas gracias por su participación.")
    st.markdown("---")

    st.markdown('<div class="sec">Resumen de etiquetas asignadas</div>', unsafe_allow_html=True)
    for _, row in author_df.iterrows():
        etq   = row.get("etiqueta_experto", "—")
        match = etq == row["pred_zeroshot"]
        icon  = "✓" if match else "✎"
        color = "#085041" if match else "#633806"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:5px 8px;border-left:3px solid #1D9E75;margin-bottom:4px;font-size:.82rem">'
            f'<span style="color:#1D1C1A">{row["titulo"][:75]}{"…" if len(row["titulo"])>75 else ""}</span>'
            f'<span style="color:{color};font-family:monospace;font-size:.72rem;white-space:nowrap;margin-left:10px">{icon} {etq}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    c1, c2, _ = st.columns([1, 1.4, 2])
    with c1:
        if st.button("‹ Inicio", type="primary", use_container_width=True):
            st.session_state.screen = "welcome"
            st.session_state.author = None
            st.rerun()
    with c2:
        if st.button("Corregir etiquetas", use_container_width=True):
            st.session_state.screen          = "validate"
            st.session_state.edit_idx        = None
            st.session_state.correction_mode = True
            st.rerun()

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Validación UAM-A",
        page_icon="📄",
        layout="wide",
    )
    inject_css()

    if "screen" not in st.session_state:
        st.session_state.screen          = "welcome"
        st.session_state.author          = None
        st.session_state.paper_idx       = 0
        st.session_state.edit_idx        = None
        st.session_state.correction_mode = False

    try:
        df = load_data()
    except FileNotFoundError:
        st.error(f"No se encontró el archivo: {INPUT_FILE}")
        return

    saved = load_saved_labels()
    df    = apply_saved_labels(df, saved)

    screen = st.session_state.screen
    if screen == "welcome":
        screen_welcome(df)
    elif screen == "admin":
        screen_admin(df)
    elif screen == "validate":
        screen_validate(df)
    elif screen == "done":
        screen_done(df)


if __name__ == "__main__":
    main()
