python -m venv labenv
.\labenv\Scripts\activate.ps1

pip install python-dotenv azure-identity semantic-kernel --upgrade 

.\runAzLogin.ps1

python semantic-kernel.py
