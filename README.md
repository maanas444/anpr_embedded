# ANPR
Automatic Number Plate Recognition system for ENSE810 - Embedded Software Engineering

## Setup
### General setup (Linux):
```
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
```

#### How to exit virtual environment:
```
deactivate
```

### Node setup:
```
sudo apt update
sudo apt install -y swig python3-dev build-essential liblgpio-dev
sudo apt install -y tesseract-ocr
pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision
pip install -e .[node]
```
Then set `NODE_ID` in the [Node Main](node/main.py).

### Server setup:
DB Setup (MySQL):
```
sudo apt install mariadb-server
sudo systemctl start mariadb
sudo mysql_secure_installation
```
```
sudo mysql -u root -p
```

SQL setup:
```mysql
CREATE DATABASE anpr_db;

CREATE USER 'anpr_user'@'localhost' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON anpr_db.* TO 'anpr_user'@'localhost';
FLUSH PRIVILEGES;
exit
```

Add user to DB:
```
mysql -u anpr_user -p anpr_db
```

Install packages:
```
pip install -e .[server]
```

Initialise DB:
```
python3 ./server/database/db_manager.py init
```

Move code into Web directory:
```
cp -r ./server/* /var/www/html
```

Update file permissions:
```
sudo chown www-data:www-data receiver.php
sudo chgrp www-data database/ database/*.py
sudo chmod 750 database/ database/*.py
```
*(Replace `www-data` with your web user).*

Change `SERVER_URL` to match, in the [Node Sender Script](node/sender.py).


## How to use (Custom commands)
The project is split over two Raspberry Pi's

### Start commands
Camera Node:
```
node
```

(Server runs via PHP)
```
python3 /var/www/html/database/db_manager.py list
```