DROP DATABASE IF EXISTS photoshare;
CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
#DROP TABLE IF EXISTS Pictures CASCADE;
#DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users (
    uid int4  NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(10) NOT NULL,
    last_name VARCHAR(10) NOT NULL,
    birth DATE NOT NULL,
    hometown VARCHAR(20) DEFAULT "none",
    gender VARCHAR(10) DEFAULT "none",
  CONSTRAINT users_pk PRIMARY KEY (uid)
);

CREATE TABLE Albums
(
  aid INTEGER AUTO_INCREMENT,
  aname VARCHAR(20) NOT NULL,
  adate DATETIME DEFAULT CURRENT_TIMESTAMP,
  uid INTEGER NOT NULL,
  PRIMARY KEY (aid),
  FOREIGN KEY (uid) REFERENCES Users (uid)
  ON DELETE CASCADE
);

CREATE TABLE Pictures
(
  pid int4  AUTO_INCREMENT,
  uid int4,
  imgdata longblob,
  caption VARCHAR(255),
  aid int4 NOT NULL,
  INDEX upid_idx (uid),
  CONSTRAINT pictures_pk PRIMARY KEY (pid),
  FOREIGN KEY (aid) REFERENCES Albums (aid)
  ON DELETE CASCADE,
  FOREIGN KEY (uid) REFERENCES Users (uid)
);

CREATE TABLE Comments
(
  cid INTEGER AUTO_INCREMENT,
  text TEXT NOT NULL,
  cdate DATETIME DEFAULT CURRENT_TIMESTAMP,
  uid INTEGER NOT NULL,
  pid INTEGER NOT NULL,
  PRIMARY KEY (cid),
  FOREIGN KEY (pid) REFERENCES Pictures (pid)
  ON DELETE CASCADE
);

CREATE TABLE has
(
  uid INTEGER NOT NULL,
  aid INTEGER,
  PRIMARY KEY (uid, aid),
  FOREIGN KEY (uid) REFERENCES Users (uid)
  ON DELETE CASCADE,
  FOREIGN KEY (aid) REFERENCES Albums (aid)
  ON DELETE CASCADE
);

CREATE TABLE contains
(
  aid INTEGER NOT NULL,
  pid INTEGER,
  FOREIGN KEY (aid) REFERENCES Albums (aid)
  ON DELETE CASCADE,
  FOREIGN KEY (pid) REFERENCES Pictures (pid)
  ON DELETE CASCADE
);

CREATE TABLE Tags
(
  name VARCHAR(20),
  tid INTEGER AUTO_INCREMENT,
  PRIMARY KEY (tid)
);

CREATE TABLE relate_to
(
  pid INTEGER,
  tid INTEGER,
  PRIMARY KEY (pid, tid),
  FOREIGN KEY (pid) REFERENCES Pictures (pid),
  FOREIGN KEY (tid) REFERENCES Tags (tid)
);

CREATE TABLE makes
(
  uid INTEGER NOT NULL,
  pid INTEGER NOT NULL,
  cid INTEGER NOT NULL,
  PRIMARY KEY (uid, cid),
  FOREIGN KEY (cid) REFERENCES Comments (cid)
  ON DELETE CASCADE,
  FOREIGN KEY (pid) REFERENCES Pictures (pid)
  ON DELETE CASCADE
);

CREATE TABLE is_friend
(
  uid1 INTEGER NOT NULL,
  uid2 INTEGER NOT NULL,
  CHECK (uid1 <> uid2),
  PRIMARY KEY (uid1, uid2),
  FOREIGN KEY (uid1) REFERENCES Users (uid) 
  ON DELETE CASCADE,
  FOREIGN KEY (uid2) REFERENCES Users (uid) 
  ON DELETE CASCADE
);

CREATE TABLE left_on
(
  pid INTEGER NOT NULL,
  cid INTEGER NOT NULL,
  PRIMARY KEY (pid, cid),
  FOREIGN KEY (pid) REFERENCES Pictures (pid)
  ON DELETE CASCADE,
  FOREIGN KEY (cid) REFERENCES Comments (cid)
  ON DELETE CASCADE
);


CREATE TABLE likes
(
  pid INTEGER NOT NULL,
  uid INTEGER NOT NULL,
  PRIMARY KEY (pid, uid),
  FOREIGN KEY (pid) REFERENCES Pictures (pid)
  ON DELETE CASCADE
);
