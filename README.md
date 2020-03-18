### ① gitを入れる
`$ sudo yum install git -y`  
### ② python(.pyenv)を入れる
EC2サーバにPython3環境構築  
https://qiita.com/tisk_jdb/items/01bd6ef9209acc3a275f  
.pyenvをgit経由で入れる  
`$ git clone https://github.com/yyuu/pyenv.git ~/.pyenv`  
.bash_profileにrootを記述  
```
$ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile  
$ echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile  
$ echo 'eval "$(pyenv init -)"' >> ~/.bash_profile  
$ source ~/.bash_profile  
$ pyenv -v  
$ sudo yum install gcc zlib-devel bzip2 bzip2-devel readline readline-devel sqlite sqlite-devel openssl openssl-devel -y  
$ pyenv install 3.6.6  
$ pyenv global 3.6.6  
$ python --version  
$ pip install --upgrade pip  
$ ~/.pyenv/bin/pyenv --version
```  
### ③ nginxを入れて起動
```
$ sudo yum install -y nginx  
$ sudo amazon-linux-extras install nginx1.12  
$ sudo service nginx start  
```
“Redirecting to /bin/systemctl start nginx.service” がでたら成功  
nginxの自動起動
`$ sudo systemctl enable nginx.service`  
起動の確認
`$ systemctl status nginx`  
### ④ git clone ,fetch 用の ssh key の作成
AES EC2上でsshを使ってgit clone を成功させるまでの手順  
https://qiita.com/konuma1022/items/986eb58d4b94bef0c0a5  
`$ cd ~/.ssh/`  
`$ ssh-keygen -t rsa -C <gitで使っているメールアドレス>`  
`$ Enter file in which to save the key (/home/ec2-user/.ssh/id_rsa) : e-paper-key-file`  
`$ Enter passphrase (empty for no passphrase) : epaper`  
configファイルの作成  
`$ vim config` 
ファイルの階層  
`~/.ssh/config`  
に下記を書き込む
``` config 
Host github  
  HostName github.com  
  IdentityFile ~/.ssh/e-paper-key-file  
  User git  
```
e-paper-key-file.pubの中身をhttps://github.com/settings/keys に登録  
ssh-addにはevalが必要  
```
$ eval "$(ssh-agent)"  
$ ssh-add ~/.ssh/e-paper-key-file  
passphrase : epaper  
$ ssh -T git@github.com
```
### ⑤ project を git clone  
`$ git clone git@github.com:pres-inc/epapers-api-django.git`  
### ⑥ mysql(pip install mysqlclient)に必要なものを入れる  
```  
$ sudo yum install mysql  
$ sudo yum install -y mysql-devel  
```  

### ⑦ pdf2imageに必要なツールをインストール  
```
$ yum install poppler
$ yum install poppler-utils
```

### ⑧ requirements.txt からライブラリ群をインストール  
`$ pip install -r requirements.txt`  

### ⑨ settings.py を編集してから起動まで  
settings.py の DATABASES を 設定する  
  
データベース作成  
`$mysql -u <RDSで設定したユーザ名> -h <RDSエンドポイント> -p`  
`pass: <RDSで設定したpassword>`  
`(mysql)$ create database epaper_default character set utf8mb4;` 
`(mysql)$ create database epaper_v1 character set utf8mb4;`  
`(mysql)$ exit`  

admin 用 superuser作成  
`$ cd <manage.pyファイルがあるところまで>`  
`$ python manage.py makemigrations epaper_api_v1`  
`$ python manage.py migrate`  
`$ python manage.py migrate --database=v2`  
`$ python manage.py createsuperuser`  
`username : <RDSで設定したユーザ名にしておくと管理しやすい>`  
`mailadless : [Enter]`  
`password : <任意のpassword>`  

nginx 起動  
`$ vim /etc/nginx/nginx.conf`  
以下をコピペし、**パブリックIPを書き換え**、上書き  
```
user ec2-user;
worker_processes auto;
pid /run/nginx.pid;
error_log /var/log/nginx/error.log;
# Load dynamic modules. See /usr/share/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
   worker_connections 1024;
}

http {
   log_format  main  ‘$remote_addr - $remote_user [$time_local] “$request” ’
                     ‘$status $body_bytes_sent “$http_referer” ’
                     ‘“$http_user_agent” “$http_x_forwarded_for”’;

   access_log  /var/log/nginx/access.log  main;

   sendfile            on;
   tcp_nopush          on;
   tcp_nodelay         on;
   keepalive_timeout   65;
   types_hash_max_size 2048;

   include             /etc/nginx/mime.types;
   default_type        application/octet-stream;

   # Load modular configuration files from the /etc/nginx/conf.d directory.
   # See http://nginx.org/en/docs/ngx_core_module.html#include
   # for more information.

   include  /etc/nginx/conf.d/*.conf;
   index    index.html index.htm;
   upstream app_server {
      server 0.0.0.0:8000 fail_timeout=0;
   }
   server {
       listen    80;
       server_name    <ec2インスタンスのパブリックIP>;  # (EC2のドメイン or プライベートIPアドレス)
       client_max_body_size    6G;
       include /etc/nginx/default.d/*.conf;

       location / {
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header Host $http_host;
               proxy_redirect off;
               proxy_pass   http://app_server;
       }
       location /static {
               alias /home/ec2-user/palao-api-django/palao_api_django/static;
       }
   }
}
```
`$ sudo service nginx restart`  


`$ gunicorn epaper_api_django.wsgi --bind=0.0.0.0:8000` 