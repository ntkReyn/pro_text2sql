BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE analytics.dim_supplier (
    supplier_id text PRIMARY KEY,
    supplier_name text NOT NULL,
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE analytics.dim_supplier IS
    'MVP grain: one current row per supplier. History strategy is not yet approved.';

CREATE TABLE analytics.dim_warehouse (
    warehouse_id text PRIMARY KEY,
    warehouse_name text NOT NULL,
    region_name text NOT NULL,
    timezone_name text NOT NULL,
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE analytics.dim_warehouse IS
    'MVP grain: one current row per warehouse. timezone_name must be an IANA timezone.';

CREATE TABLE analytics.fact_purchase_order_line (
    po_line_id text PRIMARY KEY,
    purchase_order_id text NOT NULL,
    supplier_id text NOT NULL REFERENCES analytics.dim_supplier (supplier_id),
    warehouse_id text NOT NULL REFERENCES analytics.dim_warehouse (warehouse_id),
    product_sku text NOT NULL,
    ordered_quantity numeric(20, 4) NOT NULL CHECK (ordered_quantity > 0),
    ordered_at timestamptz NOT NULL,
    promised_delivery_date date NOT NULL,
    status text NOT NULL CHECK (status IN ('open', 'completed', 'cancelled')),
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE analytics.fact_purchase_order_line IS
    'Grain: one current row per purchase order line.';

CREATE TABLE analytics.fact_delivery_line (
    delivery_line_id text PRIMARY KEY,
    po_line_id text NOT NULL REFERENCES analytics.fact_purchase_order_line (po_line_id),
    delivered_quantity numeric(20, 4) NOT NULL CHECK (delivered_quantity > 0),
    delivered_at timestamptz NOT NULL,
    status text NOT NULL CHECK (status IN ('received', 'cancelled')),
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE analytics.fact_delivery_line IS
    'Grain: one delivery receipt event linked to one purchase order line.';

CREATE INDEX fact_purchase_order_line_supplier_idx
    ON analytics.fact_purchase_order_line (supplier_id);
CREATE INDEX fact_purchase_order_line_warehouse_idx
    ON analytics.fact_purchase_order_line (warehouse_id);
CREATE INDEX fact_delivery_line_po_time_idx
    ON analytics.fact_delivery_line (po_line_id, delivered_at, delivery_line_id);

CREATE VIEW analytics.supplier_delivery_performance_v1 AS
WITH delivery_progress AS (
    SELECT
        po.po_line_id,
        delivery.delivery_line_id,
        delivery.delivered_quantity,
        delivery.delivered_at,
        po.ordered_quantity,
        SUM(delivery.delivered_quantity) OVER (
            PARTITION BY po.po_line_id
            ORDER BY delivery.delivered_at, delivery.delivery_line_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_delivered_quantity
    FROM analytics.fact_purchase_order_line AS po
    INNER JOIN analytics.fact_delivery_line AS delivery
        ON delivery.po_line_id = po.po_line_id
       AND delivery.status = 'received'
    WHERE po.status <> 'cancelled'
),
delivery_summary AS (
    SELECT
        po_line_id,
        SUM(delivered_quantity) AS delivered_quantity,
        MIN(delivered_at) FILTER (
            WHERE cumulative_delivered_quantity >= ordered_quantity
        ) AS completed_at
    FROM delivery_progress
    GROUP BY po_line_id
)
SELECT
    po.po_line_id,
    po.purchase_order_id,
    po.product_sku,
    po.ordered_quantity,
    COALESCE(summary.delivered_quantity, 0) AS delivered_quantity,
    po.promised_delivery_date,
    summary.completed_at,
    supplier.supplier_id,
    supplier.supplier_name,
    warehouse.warehouse_id,
    warehouse.warehouse_name,
    warehouse.region_name,
    warehouse.timezone_name,
    summary.completed_at IS NOT NULL AS is_completed,
    CASE
        WHEN summary.completed_at IS NULL THEN NULL
        ELSE (summary.completed_at AT TIME ZONE warehouse.timezone_name)::date
             <= po.promised_delivery_date
    END AS is_on_time,
    CASE
        WHEN summary.completed_at IS NULL THEN NULL
        ELSE (summary.completed_at AT TIME ZONE warehouse.timezone_name)::date
             > po.promised_delivery_date
    END AS is_late,
    CASE
        WHEN summary.completed_at IS NULL THEN NULL
        ELSE GREATEST(
            (summary.completed_at AT TIME ZONE warehouse.timezone_name)::date
                - po.promised_delivery_date,
            0
        )
    END AS delay_days,
    GREATEST(po.source_updated_at, supplier.source_updated_at, warehouse.source_updated_at) AS source_updated_at,
    now() AS model_built_at
FROM analytics.fact_purchase_order_line AS po
INNER JOIN analytics.dim_supplier AS supplier
    ON supplier.supplier_id = po.supplier_id
INNER JOIN analytics.dim_warehouse AS warehouse
    ON warehouse.warehouse_id = po.warehouse_id
LEFT JOIN delivery_summary AS summary
    ON summary.po_line_id = po.po_line_id
WHERE po.status <> 'cancelled';

COMMENT ON VIEW analytics.supplier_delivery_performance_v1 IS
    'Grain: one non-cancelled purchase order line. Completion is the first receipt event at which cumulative delivered quantity reaches ordered quantity.';

COMMIT;
