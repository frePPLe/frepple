
/* This SQl statement has been tested on MySQL only.
   On other databases this will surely fail... Thanks to all nonstandard
   syntax and extensions every database provides :-(
*/

DROP PROCEDURE IF EXISTS frepple.createDates;

delimiter //

CREATE PROCEDURE frepple.createDates (IN startdate DATE, IN enddate DATE)
BEGIN

  /* Loop over all dates between the start and end. */
  WHILE startdate <= enddate DO

    /* Insert a record in the dates table. */
    INSERT INTO frepple.output_dates
      (date, week, week_start, month, month_start, quarter, quarter_start, year, year_start)
      VALUES(
        /* Date */
        startdate,
        /* Week */
        DATE_FORMAT(startdate,'%XW%V '),
        DATE_SUB(startdate, INTERVAL DAYOFWEEK(startdate) - 1 DAY),
        /* Month */
        DATE_FORMAT(startdate,'%b %Y'),
        DATE_SUB(startdate, INTERVAL DAYOFMONTH(startdate) - 1 DAY),
        /* Quarter */
        CASE DATE_FORMAT(startdate,'%m')
           WHEN 0 THEN DATE_FORMAT(startdate,'%YQ1')
           WHEN 1 THEN DATE_FORMAT(startdate,'%YQ1')
           WHEN 2 THEN DATE_FORMAT(startdate,'%YQ1')
           WHEN 3 THEN DATE_FORMAT(startdate,'%YQ1')
           WHEN 4 THEN DATE_FORMAT(startdate,'%YQ2')
           WHEN 5 THEN DATE_FORMAT(startdate,'%YQ2')
           WHEN 6 THEN DATE_FORMAT(startdate,'%YQ2')
           WHEN 7 THEN DATE_FORMAT(startdate,'%YQ3')
           WHEN 8 THEN DATE_FORMAT(startdate,'%YQ3')
           WHEN 9 THEN DATE_FORMAT(startdate,'%YQ3')
           WHEN 10 THEN DATE_FORMAT(startdate,'%YQ4')
           WHEN 11 THEN DATE_FORMAT(startdate,'%YQ4')
           WHEN 12 THEN DATE_FORMAT(startdate,'%YQ4')
        END,
        CASE DATE_FORMAT(startdate,'%m')
           WHEN 0 THEN DATE(DATE_FORMAT(startdate,'%Y-01-01 00:00:00'))
           WHEN 1 THEN DATE(DATE_FORMAT(startdate,'%Y-01-01 00:00:00'))
           WHEN 2 THEN DATE(DATE_FORMAT(startdate,'%Y-01-01 00:00:00'))
           WHEN 3 THEN DATE(DATE_FORMAT(startdate,'%Y-01-01 00:00:00'))
           WHEN 4 THEN DATE(DATE_FORMAT(startdate,'%Y-04-01 00:00:00'))
           WHEN 5 THEN DATE(DATE_FORMAT(startdate,'%Y-04-01 00:00:00'))
           WHEN 6 THEN DATE(DATE_FORMAT(startdate,'%Y-04-01 00:00:00'))
           WHEN 7 THEN DATE(DATE_FORMAT(startdate,'%Y-07-01 00:00:00'))
           WHEN 8 THEN DATE(DATE_FORMAT(startdate,'%Y-07-01 00:00:00'))
           WHEN 9 THEN DATE(DATE_FORMAT(startdate,'%Y-07-01 00:00:00'))
           WHEN 10 THEN DATE(DATE_FORMAT(startdate,'%Y-10-01 00:00:00'))
           WHEN 11 THEN DATE(DATE_FORMAT(startdate,'%Y-10-01 00:00:00'))
           WHEN 12 THEN DATE(DATE_FORMAT(startdate,'%Y-10-01 00:00:00'))
        END,
        /* Year */
        DATE_FORMAT(startdate,'%Y'),
        DATE(DATE_FORMAT(startdate,'%Y-01-01 00:00:00'))
        );

    /* Increment to next day. */
    SET startdate = date_add(startdate, INTERVAL 1 DAY);
  END WHILE;
  COMMIT;

END;
//
delimiter ;

CALL frepple.createDates(DATE('2007-01-01 00:00:00'), DATE('2007-12-31 00:00:00'));
