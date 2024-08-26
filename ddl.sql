create database dbmonthly default charset utf8 COLLATE utf8_general_ci;
create user 'dbmonthly_user'@'%' IDENTIFIED BY 'Qwer12345';
grant all on dbmonthly.* to dbmonthly_user;
flush privileges;