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
-- Table structure for table `feed_sensors`
--

DROP TABLE IF EXISTS `feed_sensors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `feed_sensors` (
  `ts` datetime NOT NULL,
  `ant` varchar(3) NOT NULL,
  `state` tinyint(4) NOT NULL DEFAULT '0',
  `fanpwm` varchar(8) DEFAULT NULL,
  `fanspeed` float DEFAULT '-99',
  `cryoattemp` varchar(8) DEFAULT NULL,
  `controlboardtemp` float DEFAULT '-99',
  `outsideairtemp` float DEFAULT '-99',
  `paxairtemp` float DEFAULT '-99',
  `exhausttemp` float DEFAULT '-99',
  `coolerrejectiontemp` float DEFAULT '-99',
  `coolerhousingtemp` float DEFAULT '-99',
  `lnatemp` float DEFAULT '-99',
  `lnadiodevoltage` float DEFAULT '-99',
  `accelminx` float DEFAULT '-99',
  `accelmeanx` float DEFAULT '-99',
  `accelstdx` float DEFAULT '-99',
  `accelmaxx` float DEFAULT '-99',
  `accelminy` float DEFAULT '-99',
  `accelmeany` float DEFAULT '-99',
  `accelstdy` float DEFAULT '-99',
  `accelmaxy` float DEFAULT '-99',
  `accelminz` float DEFAULT '-99',
  `accelmeanz` float DEFAULT '-99',
  `accelstdz` float DEFAULT '-99',
  `accelmaxz` float DEFAULT '-99',
  `relaystate` varchar(8) DEFAULT NULL,
  `feedstartmode` varchar(8) DEFAULT NULL,
  `cryotempregulating` varchar(8) DEFAULT NULL,
  `cryotempnoregulating` varchar(8) DEFAULT NULL,
  `vdc24volt` float DEFAULT '-99',
  `errormessages` varchar(8) DEFAULT NULL,
  `displayexcesstemp` int(11) DEFAULT '-99',
  `excesstempturbo` int(11) DEFAULT '-99',
  `turbocurrrent` int(11) DEFAULT '-99',
  `ophours` int(11) DEFAULT '-99',
  `turbospeednominal` int(11) DEFAULT '-99',
  `turbopower` int(11) DEFAULT '-99',
  `electronicsboardtemp` int(11) DEFAULT '-99',
  `turbobottomtemp` int(11) DEFAULT '-99',
  `turbobearingtemp` int(11) DEFAULT '-99',
  `turbomotortemp` int(11) DEFAULT '-99',
  `turbospeedactual` int(11) DEFAULT '-99',
  `cryopower` float DEFAULT '-99',
  `cryotemp` float DEFAULT '-99',
  PRIMARY KEY (`ts`,`ant`),
  KEY `idx` (`ant`,`ts`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `feed_sensors_orig`
--

DROP TABLE IF EXISTS `feed_sensors_orig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `feed_sensors_orig` (
  `ts` datetime NOT NULL,
  `ant` varchar(3) NOT NULL,
  `state` tinyint(4) NOT NULL DEFAULT '0',
  `fanpwm` varchar(8) DEFAULT NULL,
  `fanspeed` float DEFAULT '-99',
  `cryoattemp` varchar(8) DEFAULT NULL,
  `controlboardtemp` float DEFAULT '-99',
  `outsideairtemp` float DEFAULT '-99',
  `paxairtemp` float DEFAULT '-99',
  `exhausttemp` float DEFAULT '-99',
  `coolerrejectiontemp` float DEFAULT '-99',
  `coolerhousingtemp` float DEFAULT '-99',
  `lnatemp` float DEFAULT '-99',
  `lnadiodevoltage` float DEFAULT '-99',
  `accelminx` float DEFAULT '-99',
  `accelmeanx` float DEFAULT '-99',
  `accelstdx` float DEFAULT '-99',
  `accelmaxx` float DEFAULT '-99',
  `accelminy` float DEFAULT '-99',
  `accelmeany` float DEFAULT '-99',
  `accelstdy` float DEFAULT '-99',
  `accelmaxy` float DEFAULT '-99',
  `accelminz` float DEFAULT '-99',
  `accelmeanz` float DEFAULT '-99',
  `accelstdz` float DEFAULT '-99',
  `accelmaxz` float DEFAULT '-99',
  `relaystate` varchar(8) DEFAULT NULL,
  `feedstartmode` varchar(8) DEFAULT NULL,
  `cryotempregulating` varchar(8) DEFAULT NULL,
  `cryotempnoregulating` varchar(8) DEFAULT NULL,
  `vdc24volt` float DEFAULT '-99',
  `errormessages` varchar(8) DEFAULT NULL,
  `displayexcesstemp` int(11) DEFAULT '-99',
  `excesstempturbo` int(11) DEFAULT '-99',
  `turbocurrrent` int(11) DEFAULT '-99',
  `ophours` int(11) DEFAULT '-99',
  `turbospeednominal` int(11) DEFAULT '-99',
  `turbopower` int(11) DEFAULT '-99',
  `electronicsboardtemp` int(11) DEFAULT '-99',
  `turbobottomtemp` int(11) DEFAULT '-99',
  `turbobearingtemp` int(11) DEFAULT '-99',
  `turbomotortemp` int(11) DEFAULT '-99',
  `turbospeedactual` int(11) DEFAULT '-99',
  `cryopower` float DEFAULT '-99',
  `cryotemp` float DEFAULT '-99',
  PRIMARY KEY (`ant`,`ts`),
  KEY `idx` (`ant`,`ts`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `feed_sensors_short`
--

DROP TABLE IF EXISTS `feed_sensors_short`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `feed_sensors_short` (
  `ts` datetime NOT NULL,
  `ant` varchar(3) NOT NULL,
  `state` tinyint(4) NOT NULL,
  `turbocurrrent` int(11) DEFAULT '-99',
  `turbopower` int(11) DEFAULT '-99',
  `turbospeedactual` int(11) DEFAULT '-99',
  `cryopower` float DEFAULT '-99',
  `cryotemp` float DEFAULT '-99',
  PRIMARY KEY (`ant`,`ts`),
  KEY `idx` (`ant`,`ts`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `info`
--

DROP TABLE IF EXISTS `info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `info` (
  `mirnum` smallint(5) unsigned NOT NULL,
  `name` varchar(6) NOT NULL,
  `birth` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `comment` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`mirnum`),
  UNIQUE KEY `info_constraint` (`mirnum`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `observations`
--

DROP TABLE IF EXISTS `observations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `observations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ts_start` datetime NOT NULL,
  `ts_stop` datetime DEFAULT NULL,
  `ants` varchar(255) NOT NULL,
  `az_offset` float DEFAULT '0',
  `el_offset` float DEFAULT '0',
  `freq` float NOT NULL,
  `target` varchar(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1415 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rfswitch`
--

DROP TABLE IF EXISTS `rfswitch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rfswitch` (
  `ts` datetime NOT NULL,
  `ant` varchar(3) NOT NULL,
  `pol` varchar(1) NOT NULL,
  `switch` int(11) DEFAULT '0',
  `port` int(11) DEFAULT '0',
  PRIMARY KEY (`ts`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sefd`
--

DROP TABLE IF EXISTS `sefd`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sefd` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `obsid` int(11) NOT NULL,
  `ant` varchar(3) NOT NULL,
  `sefd` float NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx` (`obsid`,`ant`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `snap_onoff_atten`
--

DROP TABLE IF EXISTS `snap_onoff_atten`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `snap_onoff_atten` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ant` varchar(4) NOT NULL,
  `obsid` int(11) NOT NULL,
  `source` varchar(64) NOT NULL,
  `freq` float NOT NULL,
  `db` float NOT NULL,
  KEY `idx` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30380 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `snap_onoff_obs`
--

DROP TABLE IF EXISTS `snap_onoff_obs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `snap_onoff_obs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `snap` varchar(16) NOT NULL,
  `obsid` int(11) NOT NULL,
  `ant` varchar(4) NOT NULL,
  `source` varchar(64) NOT NULL,
  `freq` float NOT NULL,
  `onoff` varchar(15) DEFAULT NULL,
  `rep` int(11) NOT NULL,
  KEY `idx` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=102475 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_observations`
--

DROP TABLE IF EXISTS `test_observations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_observations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ts_start` datetime NOT NULL,
  `ts_stop` datetime DEFAULT NULL,
  `ants` varchar(255) NOT NULL,
  `az_offset` float DEFAULT '0',
  `el_offset` float DEFAULT '0',
  `freq` float NOT NULL,
  `target` varchar(32) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_snap_onoff_atten`
--

DROP TABLE IF EXISTS `test_snap_onoff_atten`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_snap_onoff_atten` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ant` varchar(4) NOT NULL,
  `obsid` int(11) NOT NULL,
  `source` varchar(64) NOT NULL,
  `freq` float NOT NULL,
  `db` float NOT NULL,
  KEY `idx` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `test_snap_onoff_obs`
--

DROP TABLE IF EXISTS `test_snap_onoff_obs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_snap_onoff_obs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `snap` varchar(16) NOT NULL,
  `obsid` int(11) NOT NULL,
  `ant` varchar(4) NOT NULL,
  `source` varchar(64) NOT NULL,
  `freq` float NOT NULL,
  `onoff` varchar(15) DEFAULT NULL,
  `rep` int(11) NOT NULL,
  KEY `idx` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `various_sensors`
--

DROP TABLE IF EXISTS `various_sensors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `various_sensors` (
  `ts` datetime NOT NULL,
  `ant` varchar(3) NOT NULL,
  `state` tinyint(4) NOT NULL DEFAULT '0',
  `DriveBoxTemp` float DEFAULT '-99',
  `ControlBoxTemp` float DEFAULT '-99',
  `PAXBoxTemp` float DEFAULT '-99',
  `RimBoxTemp` float DEFAULT '-99',
  `ADC01` float DEFAULT '-99',
  `ADC02` float DEFAULT '-99',
  `ADC03` float DEFAULT '-99',
  `ADC04` float DEFAULT '-99',
  `ADC07` float DEFAULT '-99',
  `ADC08` float DEFAULT '-99',
  `ADC09` float DEFAULT '-99',
  `ADC10` float DEFAULT '-99',
  `ADC11` float DEFAULT '-99',
  `CryoRejTemp` float DEFAULT '-99',
  `CryoTemp` float DEFAULT '-99',
  `CryoPower` float DEFAULT '-99',
  PRIMARY KEY (`ant`,`ts`),
  KEY `idx` (`ant`,`ts`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-11-08 17:19:59
