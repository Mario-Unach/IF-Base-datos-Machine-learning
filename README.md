<!-- 
  README.md - Proyecto Investigación Formativa
  Infraestructura de Persistencia Híbrida + ML
  Repositorio colaborativo
-->

<div align="center">

# 🧠 Machine Learning & Admin. Bases de Datos
## Proyecto de Investigación Formativa

**DESARROLLO DE UN SISTEMA PREDICTIVO PARA EVALUAR LA PROBABILIDAD DE IMPAGO EN CLIENTES FINANCIEROS**

</div>

<div align="center">

![Status](https://img.shields.io/badge/status-en%20progreso-yellow?logo=progress)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2022-red)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen?logo=mongodb)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red?logo=streamlit)

</div>

--- 
<div align="center">

## 👥 Roles y Responsabilidades

| <span style="font-size:1.2rem">👤 Miembro</span> | <span style="font-size:1.2rem">📌 Asignación principal</span> | <span style="font-size:1.2rem">🏷️ Etiquetas</span> |
|---------------------------------------------------|---------------------------------------------------------------|------------------------------------------------------|
| **Lenin Lopez**                                   | Base de datos SQL (modelado, índices, vistas, triggers, DRP)  | `SQL` `modelado` `seguridad`                         |
| **Brayan Cardenas**                               | Base de datos SQL (población, backups, roles, MongoDB)        | `SQL` `MongoDB` `backups`                            |
| **Dennis Sanches**                                | Machine Learning – Random Forest                              | `ML` `RandomForest` `supervisado`                    |
| **Dennis Becerra**                                | Machine Learning – Red Neuronal (MLP)                         | `ML` `RedNeuronal` `deep learning`                   |
| **Mario Camacho**                                 | Machine Learning – Gradient Boosting (XGBoost/LightGBM)       | `ML` `GradientBoosting` `supervisado`                |

</div>

---
<!-- ---------------------------------------------------------------->
<!-- talvez quitar -->
<!-- ---------------------------------------------------------------->
<div align="center">

## 📋 Tabla de Contenidos

</div>

- [🎯 Objetivos](#-objetivos)
- [📦 Dataset Y Tecnologías](#-dataset-y-tecnologías)
- [🗓️ Resumen de hitos y fechas límite](#-resumen-de-hitos-y-fechas-límite)
- [📅 Calendario de Trabajo (Checklist Semanal)](#-calendario-de-trabajo-checklist-semanal)
- [🔍 Checklist Detallada de Tareas](#-checklist-detallada-de-tareas)
- [📚 Referencias](#-referencias)

---

<div align="center">

## 🎯 Objetivos

</div>

<details>
<summary><b>Objetivo General</b> (clic para expandir)</summary>

> 

</details>

<details>
<summary><b>Objetivos Específicos</b></summary>

- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ]

</details>

---

<div align="center">

<h2>📦 Dataset Y Tecnologías ⚙️</h2>
</div>


| 📦 Dataset Seleccionado | ⚙️ Tecnologías |
| :--- | :--- |
| ➡️ **Nombre:** Default of Credit Card Clients <br>➡️ **Fuente:** [UCIrvine](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients) <br>➡️ **Registros:** 30000 <br>➡️ **Variables:** SEX, EDUCATION,	MARRIAGE,	AGE | 🗄️ **BD Relacional:** SQL Server 2022 <br>🍃 **BD NoSQL:** MongoDB <br>🐍 **Procesamiento y ML:** Python 3.12, Jupyter, pandas, scikit-learn <br>📊 **Visualización:** Streamlit, matplotlib <br>🐙 **Control de versiones:** Git + GitHub |



---

<div align="center">

## 📐 Estructura de la Base de Datos Relacional (SQL Server)

[![](https://mermaid.ink/img/pako:eNqNVE-vojAQ_yqkZzXyVFCuu9nLu-x5Y0KadsTJ0pYMxbgP_e7b4hPBV31yIZ35_ZnODLRMGAksY0A_kRfE1VZH7pGocqgtlyYXeMAyai9x_6C2Ecpx-vf7LX_gJPacIgm1IKwEGj0CX5Dnrb5Z1XA0AYsu_J20BwUkQTaCe0Co9D4XEtd4gPKCsXgIaYsSQVsIKF8zQ93hZX69PykmlBw2-T4PkstbZFcabqMSFVrIBYFEe187IdSF-Uyi83x6g8mXerRoVOUdHMLkFZkjKpMrqEP9d5Xbps4rXpgH2-PSLy2OwwUMLIKqOveAvI-GpF08J9gBgRbIxzRDEnS-x9oaQn6_pn28u1HIs0eEpn9ta2DGvtYHo-8bOMxfBq2Mn8F1PxonzsMQz8-58yY09GBQ_YqdTtOpaUdLnkVb5nqtYcvuPthXwbcNf5VxTXb4U2BvPasyNTxmtV8m5jkEvMQPPqpu2OcnVFHyGncoRuTBEj51LVyUHJNNWEEoWWapgQlTQIr7I-vWyXViD8rdyZMkp7_e6uw4Fdd_jFFXGpmm2LNsx8vanZpKcgufv-8eAloC_TCNtiyLV2mnwbKWHVk2jTfpbLNerzZvabJcrd1rwv6xbDGfJcvl5i2J03W6SJN4cZ6wj843ns3jzXzuwIvFau1Yyfk_vOwEjg?type=png)](https://mermaid.live/edit#pako:eNqNVE1v4jAQ_SuRz7QC8gHkuqu99NLzCimy7CGMNrajiYNogf--dighoYbim-e9N288M8mBCSOB5QzoN_KSuFrryB2JqoDGcmkKgTusosM57g9qG6Ecw-9vV3zHSWw5RRIaQVgLNHpEPjNPa321amBvAhZd-KfUnhRICbIV3BNCpfdYKLnGHVRnjsVdKLeoELSFQOYLMsw7fMyftwfFhMBhk29xkFxeI5vKcBtVqNBCIQgk2tvaCaEpzReIzvPhCybf6tGiVbV3cAxT1GT2qEyhoAn131Vu26aoeWnubI-Dn1ocxwsYWARVd-6B9D4aSu3iBcEGCLRAPpYZkqCLLTbWEPLbNe3j3YtCnj0jNP1LWwMz9rXeGX3fwCF-HrQyfgaX_Whdch6meH3BnTehoTuD6lfseHx5MYfRkufRmrlea1izmw_2WfJ1w59VXMCOfwzsrVfVpoH7qsO3iXkNAa_wk4-qG_b5gVRUvMENipF4sIQPXUsXJadkE1YSSpZbamHCFJDi_sq6dXKd2IJyb_Iiyemftzo5Tc31X2PURUamLbcs3_Cqcbe2ltzC1--7p4CWQL9Mqy3LZ_NVl4PlB7ZneZa-TmezeLmczxfLZBFnE_bB8uQ1S5LVPJ1lWTxNp0l8mrDPznTm6KvpNEmXcZwuF1mSnf4DrUsDzg)

</div>

---

<div align="center">

## 🗓️ Resumen de hitos y fechas límite</h2></b></summary>

</div>

| Hito | Fecha | Responsables |
|------|-------|---------------|
| Dataset seleccionado y documentado | 18 junio | Todos |
| Script SQL completo + índices + vistas | 28 junio | Lenin, Brayan |
| Triggers, roles, DRP y MongoDB operativo | 5 julio | Lenin, Brayan |
| Clustering terminado + MongoDB actualizado | 12 julio | Todos (ML) |
| Modelos supervisados entrenados y comparados | 16 julio | Dennis S., Dennis B., Mario |
| Aplicación Streamlit funcionando | 19 julio (mañana) | Todos |
| Entrega final (PDF, código, notebook, README) | 19 julio (noche) | Todos |

---

<div align="center">

## 📅 Calendario de Trabajo (Checklist Semanal)

</div>

---

<div align="center">

## 🔍 Checklist Detallada de Tareas

</div>

<div align="center">

## 📚 Referencias

</div>

- Géron, A. (2019). *Hands‑on Machine Learning with Scikit‑Learn, Keras, and TensorFlow* (2nd ed.). O’Reilly.
- Kleppmann, M. (2017). *Designing Data‑Intensive Applications*. O’Reilly.
- Streamlit Documentation (2024). [https://docs.streamlit.io/](https://docs.streamlit.io/)
- Scikit‑learn: [Classifier comparison](https://scikit-learn.org/stable/auto_examples/classification/plot_classifier_comparison.html)

---

## 📎 Notas para el equipo

- Cada vez que se complete una tarea, actualizar la checklist correspondiente.
- Usar **issues** y **projects** de GitHub para asignar responsabilidades.
- El archivo `README.md` debe mantenerse actualizado durante todo el proyecto.

---

<div align="center">

**¡Manos a la obra!** 🚀

</div>
