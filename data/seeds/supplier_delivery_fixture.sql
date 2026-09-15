BEGIN;

INSERT INTO analytics.dim_supplier (
    supplier_id, supplier_name, source_updated_at
) VALUES
    ('SUP-001', 'An Phat', '2026-09-14T00:00:00Z'),
    ('SUP-002', 'Binh Minh', '2026-09-14T00:00:00Z'),
    ('SUP-003', 'Cuu Long', '2026-09-14T00:00:00Z');

INSERT INTO analytics.dim_warehouse (
    warehouse_id, warehouse_name, region_name, timezone_name, source_updated_at
) VALUES
    ('WH-HAN', 'Kho Ha Noi', 'Mien Bac', 'Asia/Ho_Chi_Minh', '2026-09-14T00:00:00Z'),
    ('WH-HCM', 'Kho Ho Chi Minh', 'Mien Nam', 'Asia/Ho_Chi_Minh', '2026-09-14T00:00:00Z');

INSERT INTO analytics.fact_purchase_order_line (
    po_line_id,
    purchase_order_id,
    supplier_id,
    warehouse_id,
    product_sku,
    ordered_quantity,
    ordered_at,
    promised_delivery_date,
    status,
    source_updated_at
) VALUES
    ('POL-001', 'PO-001', 'SUP-001', 'WH-HAN', 'SKU-001', 100, '2026-07-01T01:00:00Z', '2026-07-10', 'completed', '2026-07-12T00:00:00Z'),
    ('POL-002', 'PO-002', 'SUP-001', 'WH-HAN', 'SKU-002', 80,  '2026-07-02T01:00:00Z', '2026-07-12', 'completed', '2026-07-12T00:00:00Z'),
    ('POL-003', 'PO-003', 'SUP-001', 'WH-HAN', 'SKU-003', 20,  '2026-07-03T01:00:00Z', '2026-07-15', 'cancelled', '2026-07-04T00:00:00Z'),
    ('POL-004', 'PO-004', 'SUP-002', 'WH-HCM', 'SKU-001', 100, '2026-07-04T01:00:00Z', '2026-07-20', 'completed', '2026-07-23T00:00:00Z'),
    ('POL-005', 'PO-005', 'SUP-003', 'WH-HCM', 'SKU-004', 100, '2026-07-05T01:00:00Z', '2026-07-25', 'open',      '2026-07-26T00:00:00Z'),
    ('POL-006', 'PO-006', 'SUP-003', 'WH-HCM', 'SKU-005', 60,  '2026-07-06T01:00:00Z', '2026-07-30', 'completed', '2026-07-29T00:00:00Z');

INSERT INTO analytics.fact_delivery_line (
    delivery_line_id,
    po_line_id,
    delivered_quantity,
    delivered_at,
    status,
    source_updated_at
) VALUES
    ('DEL-001', 'POL-001', 50, '2026-07-09T03:00:00Z', 'received',  '2026-07-09T04:00:00Z'),
    ('DEL-002', 'POL-001', 50, '2026-07-11T03:00:00Z', 'received',  '2026-07-11T04:00:00Z'),
    ('DEL-003', 'POL-002', 80, '2026-07-12T03:00:00Z', 'received',  '2026-07-12T04:00:00Z'),
    ('DEL-004', 'POL-003', 20, '2026-07-10T03:00:00Z', 'cancelled', '2026-07-10T04:00:00Z'),
    ('DEL-005', 'POL-004', 40, '2026-07-18T03:00:00Z', 'received',  '2026-07-18T04:00:00Z'),
    ('DEL-006', 'POL-004', 60, '2026-07-22T03:00:00Z', 'received',  '2026-07-22T04:00:00Z'),
    ('DEL-007', 'POL-005', 40, '2026-07-24T03:00:00Z', 'received',  '2026-07-24T04:00:00Z'),
    ('DEL-008', 'POL-006', 60, '2026-07-29T03:00:00Z', 'received',  '2026-07-29T04:00:00Z');

COMMIT;
