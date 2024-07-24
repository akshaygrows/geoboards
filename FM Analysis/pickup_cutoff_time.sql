select *
from (
    select 
        key
    ,   replace(warehouse_id, ',', '')::integer as warehouse_id
    ,   warehouse_name
    ,   user_name
    ,   replace(user_id, ',', '')::integer as user_id
    ,   warehouse_city
    ,   NULLIF(TRIM(pickup_cutoff), '')::time as pickup_cutoff
    ,   accounts_poc_number
    ,   fm_poc_number
    ,   client_poc_number
    ,   ach_number
    from excel.pickup_cutoff_time
) as a
where pickup_cutoff is not null