from odoo import api, fields, models


class RmaAnalytics(models.Model):
    """Persistente Auswertungszeile je Artikel und Mengenprüfung."""

    _name = 'rma.analytics'
    _description = 'RMA Qualitätsauswertung'
    _order = 'split_date desc'
    _rec_name = 'picking_id'

    picking_id = fields.Many2one(
        'stock.picking', string='RMA-Eingang', readonly=True, index=True, ondelete='set null',
    )
    partner_id = fields.Many2one(
        'res.partner', string='Kunde', readonly=True, index=True,
    )
    rma_reason_id = fields.Many2one(
        'rma.reason', string='Rückgabegrund', readonly=True, index=True, ondelete='set null',
    )
    product_id = fields.Many2one(
        'product.product', string='Artikel', readonly=True, index=True, ondelete='set null',
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        related='product_id.product_tmpl_id',
        store=True,
        readonly=True,
    )
    split_date = fields.Date(string='Prüfdatum', readonly=True, index=True)
    user_id = fields.Many2one('res.users', string='Geprüft von', readonly=True)

    qty_a = fields.Float(string='A-Ware', readonly=True, digits='Product Unit of Measure')
    qty_b = fields.Float(string='B-Ware', readonly=True, digits='Product Unit of Measure')
    qty_c = fields.Float(string='C-Ware', readonly=True, digits='Product Unit of Measure')
    qty_return = fields.Float(string='Umtausch', readonly=True, digits='Product Unit of Measure')
    qty_refund = fields.Float(string='Rückerstattung', readonly=True, digits='Product Unit of Measure')
    qty_total = fields.Float(
        string='Gesamt (A+B+C)',
        compute='_compute_qty_total',
        store=True,
        readonly=True,
        digits='Product Unit of Measure',
    )
    pct_a = fields.Float(
        string='A-Ware %',
        compute='_compute_percentages',
        store=True,
        readonly=True,
        digits=(5, 1),
    )
    pct_b = fields.Float(
        string='B-Ware %',
        compute='_compute_percentages',
        store=True,
        readonly=True,
        digits=(5, 1),
    )
    pct_c = fields.Float(
        string='C-Ware %',
        compute='_compute_percentages',
        store=True,
        readonly=True,
        digits=(5, 1),
    )
    dominant_quality = fields.Selection(
        [('a', 'A-Ware'), ('b', 'B-Ware'), ('c', 'C-Ware'), ('mixed', 'Gemischt')],
        string='Hauptklasse',
        compute='_compute_percentages',
        store=True,
        readonly=True,
    )

    @api.depends('qty_a', 'qty_b', 'qty_c')
    def _compute_qty_total(self):
        for record in self:
            record.qty_total = record.qty_a + record.qty_b + record.qty_c

    @api.depends('qty_a', 'qty_b', 'qty_c', 'qty_total')
    def _compute_percentages(self):
        for rec in self:
            total = rec.qty_total
            if total:
                rec.pct_a = round(rec.qty_a / total * 100, 1)
                rec.pct_b = round(rec.qty_b / total * 100, 1)
                rec.pct_c = round(rec.qty_c / total * 100, 1)
            else:
                rec.pct_a = rec.pct_b = rec.pct_c = 0.0

            # Hauptklasse: nur wenn >50 % auf eine Klasse entfällt
            if rec.qty_c > 0 and rec.qty_a == 0 and rec.qty_b == 0:
                rec.dominant_quality = 'c'
            elif rec.qty_b > 0 and rec.qty_a == 0 and rec.qty_c == 0:
                rec.dominant_quality = 'b'
            elif rec.qty_a > 0 and rec.qty_b == 0 and rec.qty_c == 0:
                rec.dominant_quality = 'a'
            elif total:
                rec.dominant_quality = 'mixed'
            else:
                rec.dominant_quality = False
