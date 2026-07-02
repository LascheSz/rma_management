from odoo import api, fields, models


class RmaReportWizard(models.TransientModel):
    _name = 'rma.report.wizard'
    _description = 'RMA Auswertungs-Konfiguration'

    partner_ids = fields.Many2many(
        'res.partner',
        string='Kunden',
        help='Leer lassen = alle Kunden',
    )
    product_ids = fields.Many2many(
        'product.product',
        string='Artikel',
        help='Leer lassen = alle Artikel',
    )
    rma_reason_ids = fields.Many2many(
        'rma.reason',
        string='Rückgabegründe',
        help='Leer lassen = alle Gründe',
    )
    date_from = fields.Date(
        string='Von',
        default=lambda self: fields.Date.today().replace(month=1, day=1),
    )
    date_to = fields.Date(
        string='Bis',
        default=fields.Date.today,
    )
    show_a = fields.Boolean(string='A-Ware', default=True)
    show_b = fields.Boolean(string='B-Ware', default=True)
    show_c = fields.Boolean(string='C-Ware', default=True)
    group_by = fields.Selection([
        ('partner_id', 'Kunde'),
        ('product_tmpl_id', 'Artikel'),
        ('split_date:month', 'Monat'),
        ('split_date:quarter', 'Quartal'),
        ('rma_reason_id', 'Rückgabegrund'),
        ('dominant_quality', 'Hauptklasse'),
    ], string='Gruppierung X-Achse', default='split_date:month', required=True)
    graph_type = fields.Selection([
        ('bar', 'Balken'),
        ('line', 'Linie'),
        ('pie', 'Torte'),
    ], string='Diagrammtyp', default='bar', required=True)

    def action_open_report(self):
        self.ensure_one()

        domain = []
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        if self.rma_reason_ids:
            domain.append(('rma_reason_id', 'in', self.rma_reason_ids.ids))
        if self.date_from:
            domain.append(('split_date', '>=', str(self.date_from)))
        if self.date_to:
            domain.append(('split_date', '<=', str(self.date_to)))

        measures = []
        if self.show_a:
            measures.append('qty_a')
        if self.show_b:
            measures.append('qty_b')
        if self.show_c:
            measures.append('qty_c')
        if not measures:
            measures = ['qty_total']

        context = {
            'graph_groupbys': [self.group_by],
            'graph_measure': measures[0],
            'graph_mode': self.graph_type,
            'graph_stacked': True,
            'rma_report_measures': measures,
            'rma_report_group_by': self.group_by,
            'rma_report_graph_type': self.graph_type,
        }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Qualitätsauswertung',
            'res_model': 'rma.analytics',
            'view_mode': 'graph,pivot,list',
            'domain': domain,
            'context': context,
            'views': [
                (self.env.ref('rma_management.view_rma_analytics_graph').id, 'graph'),
                (self.env.ref('rma_management.view_rma_analytics_pivot').id, 'pivot'),
                (self.env.ref('rma_management.view_rma_analytics_list').id, 'list'),
            ],
        }
