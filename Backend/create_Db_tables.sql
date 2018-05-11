/*
deltalab Database - table creation and loading queries
Updated July 28, 2017

Copyright (C) 2017, Tatonetti Lab
Tal Lorberbaum <tal.lorberbaum@columbia.edu>
Nicholas P. Tatonetti <nick.tatonetti@columbia.edu>
Julie Prost <jap2277@columbia.edu>
All rights reserved.

Released under a CC BY-NC-SA 4.0 license.
For full license details see LICENSE.txt or go to:
http://creativecommons.org/licenses/by-nc-sa/4.0/

-------------------------------------------------------
Run `create_Db.py` to generate 3 output CSV files.
Then use these queries to create the 3 deltalab MySQL
tables and load the data.
*/

loinc_code = '' #loinc code corresponding to the adverse event of interest. See create_Db.py for more information.

# Drug table
CREATE TABLE `Drug` (
  `drug_concept_id` int(11) unsigned NOT NULL,
  `drug_name` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`drug_concept_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOAD DATA LOCAL INFILE '%s_db_Drug.csv'%loinc_code
INTO TABLE Drug
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;

# Patient table
CREATE TABLE `Patient` (
  `pt_id_era` varchar(11) NOT NULL DEFAULT '',
  `pt_id` int(11) NOT NULL,
  `era` int(11) NOT NULL,
  `age` int(11) NOT NULL,
  `sex` varchar(1) NOT NULL DEFAULT '',
  `race` varchar(1) NOT NULL,
  `num_drugs` int(11) NOT NULL,
  `pre_test_high` int(1) NOT NULL DEFAULT '0',
  `post_test_high` int(1) NOT NULL DEFAULT '0',
  `delta_test` int(11) NOT NULL,
  PRIMARY KEY (`pt_id_era`),
  KEY `pt_id` (`pt_id`,`era`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOAD DATA LOCAL INFILE '%s_db_Patient.csv'%loinc_code
INTO TABLE Patient
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;

# Patient to drug mapping table
CREATE TABLE `Patient2Drug` (
  `pt_id_era` varchar(11) NOT NULL DEFAULT '',
  `drug_concept_id` int(11) NOT NULL,
  PRIMARY KEY (`pt_id_era`,`drug_concept_id`),
  UNIQUE KEY `ix_ReversePK` (`drug_concept_id`,`pt_id_era`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOAD DATA LOCAL INFILE '%s_db_Patient2Drug.csv'%loinc_code
INTO TABLE Patient2Drug
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;
