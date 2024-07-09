with ops_main as (
    select
        awb
    ,   warehouse_city
    ,   pickuptime
    ,   pickup_vehicle
    from public.ops_main
    where 1=1
    and pickup_vehicle is not null
    and shipping_partner = 'Hyperlocal'
    and date_trunc('day', pickuptime) = date_trunc('day', now() + interval'5.5 hours' - interval '2 day')
    and op_owner not in ('GS', '81')
    and user_name not in ('Purplle', 'Lenskart')
)
,
shipment_order_details as (
    select
        awb
    ,   user_id
    ,   warehouse_id
    from public.shipment_order_details
)
,
base as (
    select
        concat(s.user_id, '-', s.warehouse_id, '-', o.warehouse_city) as key1
    ,   s.warehouse_id
    ,   o.pickup_vehicle
    ,   o.pickuptime
    ,   o.awb
    from ops_main o
    left join shipment_order_details s on o.awb = s.awb
    order by 1, 2, 3, 4
)

select * from base