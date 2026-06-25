from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """RMA-Konfigurationsfelder für die allgemeinen Odoo-Einstellungen."""

    _inherit = 'res.config.settings'

    rma_default_return_deadline_days = fields.Integer(
        string='Standard-Rückgabefrist (Tage)',
        config_parameter='rma_management.default_return_deadline_days',
        default=14,
    )
    rma_location_id = fields.Many2one(
        'stock.location',
        string='RMA-Standardlager',
        config_parameter='rma_management.location_rma_id',
        domain="[('usage', '=', 'internal')]",
    )
    rma_b_location_id = fields.Many2one(
        'stock.location',
        string='B-Ware Prüflager',
        config_parameter='rma_management.location_b_goods_id',
        domain="[('usage', '=', 'internal')]",
    )
    rma_c_location_id = fields.Many2one(
        'stock.location',
        string='C-Ware Schrottlager',
        config_parameter='rma_management.location_scrap_id',
        domain="[('usage', 'in', ['internal', 'inventory'])]",
    )
    rma_a_location_id = fields.Many2one(
        'stock.location',
        string='A-/Wiederverkaufs-Lager',
        config_parameter='rma_management.location_a_goods_id',
        domain="[('usage', '=', 'internal')]",
    )
    rma_repair_location_id = fields.Many2one(
        'stock.location',
        string='Reparatur-Lager',
        config_parameter='rma_management.location_repair_id',
        domain="[('usage', '=', 'internal')]",
    )
    rma_incoming_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='RMA-Eingang Vorgangsart',
        config_parameter='rma_management.picking_type_incoming_id',
    )
    rma_a_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='A-Ware Vorgangsart',
        config_parameter='rma_management.picking_type_a_goods_id',
    )
    rma_b_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='B-Ware Vorgangsart',
        config_parameter='rma_management.picking_type_b_goods_id',
    )
    rma_c_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='C-Ware Vorgangsart',
        config_parameter='rma_management.picking_type_scrap_id',
    )
    rma_use_serial_numbers = fields.Boolean(
        string='Seriennummern in RMA verwenden',
        config_parameter='rma_management.use_serial_numbers',
        default=True,
        help='Wenn deaktiviert, arbeitet RMA rein mengenbasiert und blendet Seriennummern-Auswahl sowie Q-Klassen je Seriennummer aus.',
    )
    rma_bware_ticket_name = fields.Char(
        string='B-Ware Ticket-Name',
        config_parameter='rma_management.bware_ticket_name',
        default='Prüfware',
    )
    rma_bware_helpdesk_team_id = fields.Many2one(
        'helpdesk.team',
        string='B-Ware Kundendienst-Team',
        config_parameter='rma_management.bware_helpdesk_team_id',
    )
    rma_bware_auto_create_tickets = fields.Boolean(
        string='B-Ware Tickets automatisch erstellen',
        config_parameter='rma_management.bware_auto_create_tickets',
        default=True,
    )
    rma_bware_sla_days = fields.Integer(
        string='B-Ware QS-SLA (Tage)',
        config_parameter='rma_management.bware_sla_days',
        default=5,
    )
    rma_reason_ids = fields.Many2many(
        'rma.reason',
        string='RMA-Gründe',
        compute='_compute_rma_reason_ids',
        inverse='_inverse_rma_reason_ids',
        help='Aktive Rückgabegründe, die im RMA-Erstellungswizard auswählbar sind.',
    )

    def _compute_rma_reason_ids(self):
        """Zeigt alle aktiven RMA-Gründe in den Einstellungen an."""
        reasons = self.env['rma.reason'].search([('active', '=', True)])
        for settings in self:
            settings.rma_reason_ids = reasons

    def _inverse_rma_reason_ids(self):
        """Aktiviert ausgewählte Gründe und archiviert abgewählte Gründe."""
        reason_model = self.env['rma.reason']
        for settings in self:
            selected_reasons = settings.rma_reason_ids
            reason_model.search([('id', 'not in', selected_reasons.ids)]).write({'active': False})
            selected_reasons.write({'active': True})
