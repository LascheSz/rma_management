# RMA Management ER-Diagramm

Die Datei kann in Editoren oder Doku-Tools mit Mermaid-Unterstützung direkt als ER-Diagramm gerendert werden.

```mermaid
erDiagram
    RMA_ORDER {
        string transient "wizard"
        int sale_order_id FK
        boolean is_company
        int partner_id FK
        string partner_street
        string partner_plz
        string partner_city
        string vat
        string website
        string partner_email
        string partner_phone
        int return_deadline_days
        date return_deadline_date
        int return_days_remaining
        int return_days_expired
        string return_deadline_text
    }

    RMA_ORDER_LINE {
        string transient "wizard"
        int wizard_id FK
        int sale_order_line_id FK
        float returned_qty
        float available_qty
        float return_qty
    }

    SALE_ORDER {
        int id PK
        int partner_id FK
    }

    SALE_ORDER_LINE {
        int id PK
        int order_id FK
    }

    RES_PARTNER {
        int id PK
        int rma_return_deadline_days
    }

    RMA_DEADLINE_CONFIRMATION {
        string transient "wizard"
        int id PK
        int rma_id FK
        int days_expired
        string message_text
    }

    RMA_SPLITTING {
        string transient "wizard"
        int id PK
        int rma_order_id FK
        int partner_id FK
        string partner_street
        string partner_plz
        string partner_city
        string state_code
        string vat
        string website
        string partner_email
        string partner_phone
        string origin
        boolean processing_done
    }

    RMA_SPLITTING_LINE {
        string transient "wizard"
        int wizard_id FK
        int stock_move_id FK
        float product_uom_qty
        float rma_qty_a
        float rma_qty_b
        float rma_qty_c
        float rma_qty_return
        float rma_qty_refund
    }

    STOCK_PICKING {
        int id PK
        boolean rma_split_done
        boolean rma_exchange_prepared
        boolean rma_refund_prepared
        boolean rma_processing_done
    }

    STOCK_MOVE {
        int id PK
        int picking_id FK
    }

    RES_PARTNER ||--o{ SALE_ORDER : "hat"
    SALE_ORDER ||--o{ SALE_ORDER_LINE : "enthaelt"
    SALE_ORDER ||--o{ RMA_ORDER : "ist Basis fuer"
    RMA_ORDER ||--o{ RMA_ORDER_LINE : "enthaelt temporaer"
    SALE_ORDER_LINE ||--o{ RMA_ORDER_LINE : "ist Basis fuer"
    RES_PARTNER ||--o{ RMA_ORDER : "ist Kunde von"
    RMA_ORDER ||--o{ RMA_DEADLINE_CONFIRMATION : "hat Bestaetigung"
    STOCK_PICKING ||--o{ RMA_SPLITTING : "ist Basis fuer"
    RMA_SPLITTING ||--o{ RMA_SPLITTING_LINE : "enthaelt temporaer"
    STOCK_MOVE ||--o{ RMA_SPLITTING_LINE : "ist Basis fuer"
    RES_PARTNER ||--o{ RMA_SPLITTING : "ist Kunde von"
    STOCK_PICKING ||--o{ STOCK_MOVE : "enthaelt"
```

## Hinweis

Das ER-Diagramm unterscheidet zwischen echten Odoo-Belegen und temporären Wizard-Zeilen. Dauerhaft gespeichert werden im RMA-Prozess nur die Lagerbelege, Lagerbewegungen und Statusinformationen auf dem Lagerbeleg; Eingabemengen der Formulare liegen nur in TransientModels.
