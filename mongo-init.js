db = db.getSiblingDB('catcin_db');
db.createUser({
  user: 'catcin_user',
  pwd: 'qwe123',
  roles: [{ role: 'readWrite', db: 'catcin_db' }]
});

