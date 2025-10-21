mongosh
exit
use catcin_db;
mongosh -u catcin_user -p --authenticationDatabase catcin_db
mongodb://catcin_user:qwe123@mongodb:27017/catcin_db?authSource=catcin_db
mongosh -u catcin_user -p qwe123 --authenticationDatabase catcin_db
exit
# 사용자명(catcin_user), 비밀번호(qwe123), 인증DB(catcin_db)를 사용
mongosh -u catcin_user -p qwe123 --authenticationDatabase catcin_db
exit
mongosh -u catcin_user -p qwe123 --authenticationDatabase catcin_db
exit
