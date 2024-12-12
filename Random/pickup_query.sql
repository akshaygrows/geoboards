with ops_main as (
    select
        awb
    ,   warehouse_city
    ,   pickuptime
    ,   created_date
    ,   pickup_vehicle
    ,   shipment_id
    from public.ops_main
    where 1=1
    and pickup_vehicle is not null
    and shipping_partner = 'Hyperlocal'
    and pickuptime >= '2024-07-01'
    and op_owner not in ('GS', '81')
    and user_name not in ('Purplle', 'Lenskart')
)
,
base as (
    select
        concat(s.user_id, '-', s.warehouse_id, '-', o.warehouse_city) as key
    ,   s.warehouse_id
    ,   o.pickup_vehicle
    ,   o.pickuptime
    ,   o.created_date
    ,   o.awb
    from ops_main o
    left join shipment_order_details s on o.shipment_id = s.shipment_id
    order by 1, 2, 3, 4
)

select * from base