# Config-Serveur


Installation des dépendances:
>sudo apt-get update  

>python3 --version  

>sudo apt install python3-pip 


Installation du bot:
>git clone https://github.com/BottaCrypto/cBot-Project.git  

>pip install testresources  

>pip install packaging  

>pip install -r /home/ubuntu/cBot-Project/requirements.txt  

>pip install jupyter 

>sudo apt install jupyter-core  

>sudo apt install jupyter-notebook


Utliser jupyter pour les backtest:
>jupyter notebook --generate-config  

>key=$(python3 -c "from notebook.auth import passwd; print(passwd())")  

>cd ~  
mkdir certs  
cd certs  
certdir=$(pwd)  
openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout mycert.key -out mycert.pem  

>cd ~  
sed -i "1a\  
c = get_config()\\  
c.NotebookApp.certfile = u\'$certdir/mycert.pem\'\\  
c.NotebookApp.keyfile = u\'$certdir/mycert.key\'\\  
c.NotebookApp.ip = u\'0.0.0.0\'\\  
c.NotebookApp.open_browser = False\\  
c.NotebookApp.password = u\'$key\'\\  
c.NotebookApp.port = 8888" .jupyter/jupyter_notebook_config.py  


Lancer jupyter pour faire des backtest:
>jupyter notebook
