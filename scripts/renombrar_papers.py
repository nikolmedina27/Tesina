"""Renombra los PDFs de papers/ a su título y guarda el mapeo en docs/analisis/papers_mapeo.csv.

Uso: py scripts/renombrar_papers.py        (idempotente: si el archivo ya tiene el título, lo omite)
Los títulos se tomaron de la primera página de cada PDF.
"""
import csv
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / 'papers'
MAX_NOMBRE = 150          # el límite de Windows es 260 caracteres para la ruta completa

# archivo original -> (título completo, autores principales, año, revista)
TITULOS = {
    '1 (2).pdf': ('A Study on the Man-Hour Prediction in Structural Steel Fabrication', 'Wei et al.', 2024, 'Processes'),
    '2.pdf': ('Manufacturing time estimation for offer pricing: A machine learning application in a French metallurgy industry', 'Hajj Chehade et al.', 2024, 'Eng. Appl. of Artificial Intelligence'),
    '3 (2).pdf': ('Hierarchical ensemble deep learning for data-driven lead time prediction', 'Aslan et al.', 2023, 'Int. J. Adv. Manuf. Technol.'),
    '5.pdf': ('Lead-Time Prediction in Wind Tower Manufacturing: A Machine Learning-Based Approach', 'Flores-Huamán et al.', 2024, 'Mathematics'),
    '6.pdf': ('Comparative analysis of machine learning algorithms for predicting standard time in a manufacturing environment', 'Çakıt & Dağdeviren', 2023, 'AI EDAM'),
    '7.pdf': ('Production Improvement Rate with Time Series Data on Standard Time at Manufacturing Sites', 'Ki et al.', 2023, 'Applied Sciences'),
    '8.pdf': ('Case study on delivery time determination using a machine learning approach in small batch production companies', 'Rokoss et al.', 2024, 'J. Intelligent Manufacturing'),
    '9.pdf': ('Machine Learning in Small and Medium-Sized Enterprises, Methodology for the Estimation of the Production Time', 'Urban et al.', 2024, 'Applied Sciences'),
    '11.pdf': ('Machine learning-supported manufacturing: a review and directions for future research', 'Ördek et al.', 2024, 'Production & Manufacturing Research'),
    '12.pdf': ('Sustainable optimisation approaches for production planning and control to evolve towards industry 5.0', 'Guerrero et al.', 2025, 'Int. J. Production Research'),
    '13.pdf': ('Implementation and Improvement of the Total Productive Maintenance Concept in an Organization', 'Wolska et al.', 2023, 'Encyclopedia'),
    '14.pdf': ('Coping with the uncertainties of make-to-order production: a new approach for determining reliable delivery times with the throughput diagram', 'Mundt & Lödding', 2025, 'Production Planning & Control'),
    '15.pdf': ('Sustainable Production Planning and Control in Manufacturing Contexts: A Bibliometric Review', 'De Simone et al.', 2023, 'Sustainability'),
    '16.pdf': ('Sustainable Short-Term Production Planning Optimization', 'Zanella & Vaz', 2023, 'SN Computer Science'),
    '17.pdf': ('Integrated scheduling of production and material delivery for the intelligent manufacturing system', 'Liang et al.', 2025, 'Int. J. Production Research'),
    '18.pdf': ('A Supervised Machine Learning-Based Approach for Task Workload Prediction in Manufacturing: A Case Study Application', 'De Simone et al.', 2025, 'Machines'),
    '19.pdf': ('Integrated Application of Overall Equipment Effectiveness and Free Generative-AI Tools to Improve Productivity in a CNC Machining Cell', 'Hollerweger et al.', 2026, 'Machines'),
    '20.pdf': ('Potentials of using real-time data to increase the update frequency of production planning and control strategies in MTO: a discrete event simulation study', 'Woschank et al.', 2024, 'Flex. Serv. Manuf. J.'),
    '21.pdf': ('Manufacturing Execution System Application within Manufacturing Small–Medium Enterprises towards Key Performance Indicators Development and Their Implementation in the Production Line', 'Bianchini et al.', 2024, 'Sustainability'),
    '22.pdf': ('Capacity planning with limited information', 'Anand et al.', 2023, 'Production and Operations Management'),
    '23.pdf': ('Manufacturing Management Processes Integration Framework', 'Pereira et al.', 2025, 'Applied Sciences'),
    '24.pdf': ('A machine learning based EMA-DCPM algorithm for production scheduling', 'Wang et al.', 2024, 'Scientific Reports'),
    '25.pdf': ('Managing product-inherent constraints with artificial intelligence: production control for time constraints in semiconductor manufacturing', 'May et al.', 2024, 'J. Intelligent Manufacturing'),
    '26.pdf': ('Comparative Analysis of Human and Artificial Intelligence Planning in Production Processes', 'Roblek et al.', 2024, 'Processes'),
    '27.pdf': ('A self-learning framework combining association rules and mathematical models to solve production scheduling programs', 'Del Gallo et al.', 2024, 'Production & Manufacturing Research'),
    '28.pdf': ('Applying Learning and Self-Adaptation to Dynamic Scheduling', 'Werth et al.', 2024, 'Applied Sciences'),
    '29.pdf': ('Automated machine learning methodology for optimizing production processes in small and medium-sized enterprises', 'Cruz et al.', 2024, 'Operations Research Perspectives'),
}


def nombre_archivo(titulo):
    n = re.sub(r'\s*:\s*', ' - ', titulo)
    n = re.sub(r'[<>"/\\|?*]', '', n).strip()
    if len(n) > MAX_NOMBRE:
        n = n[:MAX_NOMBRE - 3].rsplit(' ', 1)[0] + '...'
    return n + '.pdf'


def main():
    filas = []
    for viejo, (titulo, autores, anio, revista) in TITULOS.items():
        nuevo = nombre_archivo(titulo)
        origen, destino = CARPETA / viejo, CARPETA / nuevo
        if origen.exists():
            assert not destino.exists(), f'ya existe {nuevo}'
            origen.rename(destino)
            estado = 'renombrado'
        elif destino.exists():
            estado = 'ya renombrado'
        else:
            estado = 'NO ENCONTRADO'
        filas.append([viejo, nuevo, titulo, autores, anio, revista, estado])
        print(f'{estado:14} {viejo:10} -> {nuevo}')
    out = RAIZ / 'docs' / 'analisis' / 'papers_mapeo.csv'
    with open(out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['archivo_original', 'archivo_nuevo', 'titulo', 'autores', 'anio', 'revista', 'estado'])
        w.writerows(filas)


if __name__ == '__main__':
    main()
