

INSERT INTO WMS_DB_SCHEMA_DETAIL
(
    table_name,
    related_table_name,
    relationship_type,
    table_area,
    join_columns,
    business_reason
)
VALUES
('serv_ins','wh_serv','1:M','Configuration',
 'serv_id',
 'Warehouse Service attached to Service Instruction'),

('serv_ins','serv_ins_action','1:M','Configuration',
 'serv_ins_id',
 'Actions attached to Service Instruction'),

('serv_ins','wh_serv_exitpnt','1:M','Configuration',
 'serv_id',
 'Service exit points attached to service'),

('wh_serv_exitpnt','wh_serv_exitpnt_mov_zone','1:M','Configuration',
 'serv_id',
 'Move zone routing for exit points'),

('locmst','zonmst','M:1','Warehouse Layout',
 'wrk_zone_id',
 'Location belongs to work zone'),

('locmst','pck_zone','M:1','Warehouse Layout',
 'pck_zone_id',
 'Location belongs to pick zone'),

('locmst','sto_zone','M:1','Warehouse Layout',
 'sto_zone_id',
 'Location belongs to storage zone'),

('locmst','mov_zone','M:1','Warehouse Layout',
 'mov_zone_id',
 'Location belongs to movement zone'),

('locmst','cntzon','M:1','Warehouse Layout',
 'cnt_zone_id',
 'Location belongs to count zone'),

('locmst','inventory_view','1:M','Inventory',
 'stoloc,wh_id',
 'Inventory stored in location'),

('inventory_view','prtmst','M:1','Inventory',
 'prtnum,prt_client_id,wh_id',
 'Inventory references item master'),

('prtmst','prtfam','M:1','Item Master',
 'prtfam',
 'Item belongs to product family'),

('inventory_view','inv_ser_num','1:M','Inventory',
 'dtlnum=invtid',
 'Inventory serial number records'),

('trlr','rcvtrk','1:M','Inbound',
 'trlr_id',
 'Receiving trailer contains shipments'),

('rcvtrk','rcvlin','1:M','Inbound',
 'trknum',
 'Receiving shipment contains lines'),

('rcvlin','rcvinv','M:1','Inbound',
 'invnum,trknum',
 'Receiving line attached to ASN'),

('rcvlin','inventory_view','1:M','Inbound',
 'rcvkey',
 'Received inventory'),

('rcvlin','supmst','M:1','Inbound',
 'supnum,client_id',
 'Receiving line references supplier'),

('supmst','adrmst','M:1','Supplier Master',
 'adr_id',
 'Supplier address'),

('ord','ord_line','1:M','Outbound',
 'client_id,ordnum,wh_id',
 'Order header to order lines'),

('ord_line','ord_line_note','1:M','Outbound',
 'client_id,ordnum,ordlin,ordsln,wh_id',
 'Order line notes'),

('ord_line','shipment_line','1:M','Outbound',
 'client_id,ordnum,ordlin,ordsln,prtnum,prt_client_id',
 'Order line allocated to shipment line'),

('shipment','shipment_line','1:M','Outbound',
 'ship_id,wh_id',
 'Shipment header to shipment lines'),

('shipment','stop','M:1','Transportation',
 'stop_id',
 'Shipment assigned to stop'),

('stop','car_move','M:1','Transportation',
 'car_move_id',
 'Stop assigned to load'),

('car_move','trlr','M:1','Transportation',
 'trlr_id',
 'Load assigned to trailer'),

('shipment_line','pckwrk_view','1:M','Picking',
 'ship_line_id',
 'Shipment line generates picking work'),

('shipment_line','pckbat','M:1','Picking',
 'schbat',
 'Shipment assigned to wave'),

('ord_line','prtmst','M:1','Outbound',
 'prtnum,prt_client_id',
 'Order line references item'),

('ord','adrmst','M:1','Customer Master',
 'st_adr_id',
 'Ship-to address'),

('ord','adrmst','M:1','Customer Master',
 'rt_adr_id',
 'Route/depot address'),

('ord','adrmst','M:1','Customer Master',
 'bt_adr_id',
 'Bill-to address'),

('inventory_view','prtftp','M:1','Footprints',
 'prtnum,ftpcod,wh_id',
 'Inventory footprint'),

('prtftp','prtftp_dtl','1:M','Footprints',
 'prtnum,ftpcod,prt_client_id',
 'Footprint UOM hierarchy'),

('pckwrk_view','prtftp_view','M:1','Picking',
 'prtnum,prt_client_id',
 'Picking uses footprint'),

('prtftp_view','prtmst','M:1','Item Master',
 'prtnum',
 'Footprint linked to item'),

('pckwrk_view','cstmst','M:1','Customer Master',
 'rtcust=cstnum',
 'Routing customer'),

('cstmst','adrmst','M:1','Customer Master',
 'adr_id',
 'Customer address'),

('pcklst_rule','pcklst_select_cri','1:M','Picking Configuration',
 'pcklst_rule_id',
 'Selection criteria per pick rule'),

('pcklst_rule','pcklst_rule_grp_dtl','1:M','Picking Configuration',
 'pcklst_rule_id',
 'Rule group assignments'),

('pcklst_rule_grp_dtl','pcklst_break_on_cri','1:M','Picking Configuration',
 'pcklst_rule_id',
 'Break criteria per rule'),

('dlytrn','rethdr','1:M','Returns',
 'ordnum=rmanum,wh_id',
 'Return transaction history'),

('rethdr','retdtl','1:M','Returns',
 'rmanum,wh_id',
 'Return header to detail lines'),

('rethdr','ord','M:1','Returns',
 'ret_ship_ref=cpotyp',
 'Return linked to original order'),

('pckwrk_view','all_inventory_view','1:M','Inventory',
 'ship_line_id,wrkref,prtnum',
 'Inventory consumed by picking'),

('trlr','car_move','1:M','Transportation',
 'trlr_id',
 'Trailer can have multiple loads'),

('car_move','stop','1:M','Transportation',
 'car_move_id',
 'Load can have multiple stops'),

('stop','shipment','1:M','Transportation',
 'stop_id',
 'Stop can contain multiple shipments');
