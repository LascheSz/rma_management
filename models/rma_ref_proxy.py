from odoo import fields, models
from odoo.tools import drop_view_if_exists

_SALE_OFFSET = 1_000_000_000


class RmaRefProxy(models.Model):
    """Read-only SQL-Union-View über Portal-Anfragen und Verkaufsaufträge."""

    _name = 'rma.ref.proxy'
    _description = 'RMA-Referenz (Portal-Anfrage oder Verkaufsauftrag)'
    _auto = False
    _rec_name = 'ref_name'
    _order = 'ref_type, ref_name'

    ref_name = fields.Char(string='Referenz', readonly=True)
    ref_type = fields.Selection(
        [('portal', 'Portal-Anfrage'), ('sale', 'Verkaufsauftrag')],
        string='Typ', readonly=True,
    )
    portal_request_id = fields.Many2one('rma.portal.request', readonly=True)
    sale_order_id = fields.Many2one('sale.order', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW rma_ref_proxy AS (
                SELECT
                    r.id                             AS id,
                    concat('[Anfrage] ', r.name)     AS ref_name,
                    'portal'::text                   AS ref_type,
                    r.id                             AS portal_request_id,
                    NULL::integer                    AS sale_order_id
                FROM rma_portal_request r
                WHERE r.state IN ('submitted', 'approved')
                UNION ALL
                SELECT
                    s.id + {_SALE_OFFSET}            AS id,
                    concat('[Auftrag] ', s.name)     AS ref_name,
                    'sale'::text                     AS ref_type,
                    NULL::integer                    AS portal_request_id,
                    s.id                             AS sale_order_id
                FROM sale_order s
                WHERE s.state IN ('sale', 'done')
            )
        """)
