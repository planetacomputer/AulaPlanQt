# 🏫 AulaPlan — Distribució i Gestió de la Classe

**AulaPlan** és una aplicació d'escriptori desenvolupada en Python i PyQt per a la gestió visual, intuïtiva i flexible de la distribució d'alumnes a l'aula. Permet als docents organitzar els seients mitjançant l'arrossegament i soltada (*drag & drop*), configurar les mides de la graella, afegir un passadís personalitzat i exportar el resultat en múltiples formats.

---
![Captura de pantalla d'AulaPlan](./docs/aulaplan.png)

## 🚀 Característiques Principals

- **Visualització d'Aula Interactiva**:
  - Interfície adaptada a la mida de la classe amb vista de la pissarra a la part superior.
  - Targetes de seient grans i llegibles amb identificació de fila i columna (ex: `F1-C2`).
  - Indicació clara dels seients ocupats i lliures.
  - Casella de selecció a cada seient per indicar si l'ordinador funciona.
  - Opció **Mostra l'estat dels ordinadors** per ocultar o mostrar els indicadors sense modificar-ne l'estat; també s'aplica a les exportacions HTML i SVG.

- **Funció Arrossegar i Soltar (*Drag & Drop*)**:
  - Assigna alumnes des de la llista lateral cap a qualsevol seient buit.
  - Intercanvia alumnes de posició arrossegant-los entre seients.
  - Desassigna un alumne arrossegant-lo des del seu seient de tornada a la llista lateral.

- **Gestió d'Alumnes**: La llista lateral mostra primer els alumnes no assignats i després els assignats; cada grup s'ordena alfabèticament pel cognom. Fes doble clic sobre un alumne per canviar-ne el nom; el canvi també s'aplica al seient assignat i es pot desfer. Pots eliminar la foto assignada amb el botó del costat; el fitxer d'imatge es conserva.

- **Guia ràpida**: Prem el botó **Guia ràpida**, amb la icona d'informació i situat a la dreta de **Mostra l'estat dels ordinadors**, per consultar les instruccions d'ús dins de l'aplicació.

- **Passadissos verticals**: Indica'n el nombre amb el control **Passadissos** (fins a un per separació entre columnes). Es col·loquen inicialment de manera uniforme i es poden arrossegar a una altra separació. Les posicions es desen al JSON i es respecten a les exportacions HTML i SVG.

- **Configuració Dinàmica de la Graella**:
  - Nombre personalitzable de files i columnes (de 1 a 10).
  - Els passadissos es poden col·locar entre les columnes per dividir blocs de taules.

  - **Gestió Multi-selecció d'Alumnes**: Selecció múltiple d'alumnes a la llista lateral (fent servir Ctrl o Shift) per eliminar diversos registres a la vegada, amb diàleg de confirmació prèvia.

- **Gestió d'Històrial (Desfer / Refer)**:
  - Botons ↩ **Desfer** i ↪ **Refer** per revertir o recuperar qualsevol canvi en la distribució o en la llista d'alumnes.

- **Càrrega Automàtica de Configuració**:
  - En iniciar, l'aplicació detecta i carrega automàticament el fitxer `config_default.json` si existeix al mateix directori.

- **Exportació i Importació**:
  - **Importació CSV**: Carrega llistes d'alumnes ràpidament des de fitxers `.csv`.
  - **JSON**: Guarda i carrega l'estat complet de l'aula (mides, llista d'alumnes, posicions, estat dels ordinadors i visibilitat dels indicadors).
  - **SVG Vectorial**: Exporta la distribució i l'estat dels ordinadors en format `.svg` d'alta resolució apte per a impressió o modificació gràfica.
  - **HTML**: Genera una pàgina web amb l'estat dels ordinadors, dissenyada per ser impresa directament.

## Requisits

- Python 3.10 o posterior.
- `pip` i `venv` (normalment inclosos amb Python).
- Linux o Windows per executar l'aplicació.

No cal instal·lar dependències addicionals per al model o l'emmagatzematge: les
dependències externes de l'aplicació són PyQt6 i, per crear l'executable,
PyInstaller.

## Preparar l'entorn de desenvolupament

Obriu un terminal a la carpeta del projecte.

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install PyQt6 PyInstaller
python main.py
```

Per sortir de l'entorn virtual:

```bash
deactivate
```

## Executar les proves

Executeu les ordres des de la carpeta del projecte. Instal·leu PyTest al mateix
entorn virtual que feu servir per executar les proves:

```bash
source .venv/bin/activate
python -m pip install pytest
python3 -m pytest -q
```

Si no voleu activar l'entorn virtual, indiqueu-ne directament l'intèrpret:

```bash
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest -q
```

Les proves cobreixen el model de l'aula, la persistència JSON, la importació CSV
i les exportacions HTML i SVG.

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install PyQt6 PyInstaller
python main.py
```

Si PowerShell no permet activar l'entorn virtual, també podeu executar les
ordres amb el Python de l'entorn sense activar-lo:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install PyQt6 PyInstaller
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe main.py
```

## Crear una aplicació per a Linux

Des de la carpeta del projecte, executeu l'script inclòs:

```bash
./package_linux.sh
```

L'script crea l'entorn `.venv-build`, hi instal·la PyInstaller i PyQt6, i
empaqueta `config_default.json` dins de l'aplicació. El fitxer executable es
desa a:

```text
dist/AulaPlan
```

Si el sistema de fitxers no conserva el permís d'execució de l'script, feu-lo
executable abans:

```bash
chmod +x package_linux.sh
```

Podeu executar l'aplicació amb:

```bash
./dist/AulaPlan
```

## Crear una aplicació per a Windows

PyInstaller no és un compilador creuat: l'executable de Windows s'ha de crear
des de Windows. Obriu PowerShell a la carpeta del projecte i executeu:

```powershell
py -3 -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install PyQt6 PyInstaller
pyinstaller --clean --noconfirm --onefile --windowed --name AulaPlan --add-data "config_default.json;." main.py
```

L'executable es crearà a:

```text
dist\AulaPlan.exe
```

Per distribuir-lo, copieu `dist\AulaPlan.exe` a l'ordinador Windows de destí.
Feu la compilació al sistema operatiu i a l'arquitectura de destinació: un
paquet creat per a Windows no serveix a Linux, ni a l'inrevés. En particular,
els binaris de Linux poden dependre de les biblioteques del sistema instal·lades
a l'ordinador on s'executin.

## Fitxers del projecte

- `main.py`: interfície gràfica i lògica d'interacció.
- `model.py`: model de dades de l'aula i dels alumnes.
- `storage.py`: importació i exportació de dades i plans.
- `config_default.json`: configuració inicial carregada en iniciar l'aplicació.
- `config_default2.json`: configuració del grup ASIX amb els noms en format `Primer cognom, N.`; carregueu-la amb **Carregar JSON** i manteniu la carpeta local `images/` al costat del fitxer per mostrar les fotografies i la identificació sota cadascuna.
- `package_linux.sh`: script per empaquetar l'aplicació a Linux.
