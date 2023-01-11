CREATE TABLE `CAR_EVENT` (
  `id` INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
  `vitesse` VARCHAR(42),
  `geo_lat` VARCHAR(42),
  `geo_lon` VARCHAR(42),
  `timestamp_record` TIMESTAMP,
  `recorded_by` VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=UTF8MB4;

CREATE TABLE `TRAFFIC_EVENT` (
  `id` INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
  `type` ENUM('accident', 'embouteillage'),
  `geo_lat` VARCHAR(42),
  `geo_lon` VARCHAR(42),
  `timestamp_occur` TIMESTAMP,
  `reported_by` VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=UTF8MB4;