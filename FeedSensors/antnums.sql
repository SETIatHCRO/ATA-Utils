-- MySQL dump 10.13  Distrib 5.7.22, for Linux (x86_64)
--
-- Host: localhost    Database: ants
-- ------------------------------------------------------
-- Server version	5.7.22-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `antnus`
--

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `antnums` (
  `ant` VARCHAR(2) NOT NULL,
  `num` tinyint(4) NOT NULL,
  PRIMARY KEY (`ant`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-04-07 16:47:54

insert into antnums set ant='1a', num= 1;
insert into antnums set ant='1b', num=2;
insert into antnums set ant='1c', num=3;
insert into antnums set ant='1d', num=4;
insert into antnums set ant='1e', num=5;
insert into antnums set ant='1f', num=6;
insert into antnums set ant='1g', num=7;
insert into antnums set ant='1h', num=8;
insert into antnums set ant='1j', num=9;
insert into antnums set ant='1k', num=10;
insert into antnums set ant='2a', num=11;
insert into antnums set ant='2b', num=12;
insert into antnums set ant='2c', num=13;
insert into antnums set ant='2d', num=14;
insert into antnums set ant='2e', num=15;
insert into antnums set ant='2f', num=16;
insert into antnums set ant='2g', num=17;
insert into antnums set ant='2h', num=18;
insert into antnums set ant='2j', num=19;
insert into antnums set ant='2k', num=20;
insert into antnums set ant='2l', num=21;
insert into antnums set ant='2m', num=22;
insert into antnums set ant='3c', num=23;
insert into antnums set ant='3d', num=24;
insert into antnums set ant='3e', num=25;
insert into antnums set ant='3f', num=26;
insert into antnums set ant='3g', num=27;
insert into antnums set ant='3h', num=28;
insert into antnums set ant='3j', num=29;
insert into antnums set ant='3l', num=30;
insert into antnums set ant='4e', num=31;
insert into antnums set ant='4f', num=32;
insert into antnums set ant='4g', num=33;
insert into antnums set ant='4h', num=34;
insert into antnums set ant='4j', num=35;
insert into antnums set ant='4k', num=36;
insert into antnums set ant='4l', num=37;
insert into antnums set ant='5b', num=38;
insert into antnums set ant='5c', num=39;
insert into antnums set ant='5e', num=40;
insert into antnums set ant='5g', num=41;
insert into antnums set ant='5h', num=42;
