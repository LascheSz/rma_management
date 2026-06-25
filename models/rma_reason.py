from odoo import fields, models


class RmaReason(models.Model):
    """Konfigurierbarer Rückgabegrund für den RMA-Erstellungswizard."""

    _name = 'rma.reason'
    _description = 'RMA Rückgabegrund'
    _order = 'sequence, name, id'

    name = fields.Char(string='Grund', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
