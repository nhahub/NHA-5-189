# DEPI Gap Analyzer

## Python environment setup

Use Python 3.11 or newer. The virtual environment is stored in `.venv`; it is
local to your computer and intentionally excluded from Git.

### Linux and macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows Command Prompt

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

After activation, run the notebook with:

```bash
jupyter lab src/resume_skill_gap.ipynb
```

To leave the environment on any operating system, run `deactivate`.

If your editor asks you to choose a Python interpreter or notebook kernel,
select the one inside `.venv`.
