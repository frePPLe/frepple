insert into `user_preferences` 
  (`id`,`user_id`,`buckets`,`startdate`,`enddate`,`dummy`) 
  values (1,1,'day',now(),date_add(now(), interval 1 month),0)