# Módulo F+mefi (`monitoreo_fetal`)

Simulador docente y evaluador determinístico de parámetros cardiotocográficos intraparto para Fricke Store, desarrollado por la **Unidad de Parto Integral (SAIP)** junto a la **Unidad de Innovación y Desarrollo**.

## Qué hace

- Permite a los funcionarios clínicos practicar y simular la clasificación determinística de trazados de monitoreo fetal intraparto según:
  - **Protocolo de Vigilancia del Bienestar Fetal Intraparto V2** (septiembre 2025).
  - **ACOG Clinical Practice Guideline No. 10** (*Obstet Gynecol* 2025;146:583–599).
  - **FIGO 2015** y **NICE NG229**.
- Entrega en cada simulación:
  - **Categoría MEFI (FIGO/NICE)** de alta sensibilidad (validada sobre 552 registros CTU-UHB con sensibilidad 95,0 % y VPN 96,6 %).
  - **Categoría ACOG CPG No. 10 estricta** comparativa.
  - **Estratificación de riesgo en Categoría II** (Box 3 ACOG: alto, intermedio, con rasgos protectores).
  - **Variabilidad en 4 categorías NICHD** (`ausente`, `minima`, `moderada`, `marcada`).
  - **Tipificación determinística de hipoxia** (`sin_hipoxia`, `aguda`, `subaguda`, `progresiva`, `cronica`).
  - **Conducta clínica sugerida** según Protocolo V2 y ACOG CPG No. 10.
- Incluye 4 **casos docentes sintéticos** listos para cargar en un clic.
- **Cumplimiento Ley 21.719 (Etapa 1):** no solicita, procesa ni almacena datos de pacientes. Solo guarda el `autor_id` del funcionario que realiza la simulación docente, con exportación en *Descargar mis datos* (`exportar_titular`) y depuración automática al cumplir 365 días (`depurar`).

## Cómo probarlo

```bash
python backend/gestionar.py modulos
pytest modulos/monitoreo_fetal
pytest
```
