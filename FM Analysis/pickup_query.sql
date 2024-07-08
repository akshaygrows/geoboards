with ops_main as (
    select
        awb
    ,   pickuptime
    from public.ops_main
    where 1=1
    and pickuptime is not null
    and shipping_partner = 'Hyperlocal'
    and date_trunc('day', pickuptime) = date_trunc('day', now() + interval'5.5 hours' - interval '2 day')
    and op_owner not in ('GS', '81')
    and user_name not in ('Purplle', 'Lenskart')
)
,
shipment_order_details as (
    select
        awb
    ,   warehouse_id
    from public.shipment_order_details
)
,
base as (
    select
        s.warehouse_id
    ,   o.pickuptime
    ,   o.awb
    from ops_main o
    left join shipment_order_details s on o.awb = s.awb
    order by 1, 2
)

select * from base