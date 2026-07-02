from odoo import _, fields, models
from odoo.exceptions import UserError


class RmaRejectWizard(models.TransientModel):
    _name = 'rma.reject.wizard'
    _description = 'RMA-Anfrage ablehnen'

    request_id = fields.Many2one('rma.portal.request', required=True, readonly=True)
    partner_name = fields.Char(related='request_id.partner_id.name', readonly=True)
    request_name = fields.Char(related='request_id.name', readonly=True)
    rejection_reason = fields.Text(
        string='Ablehnungsgrund',
        required=True,
        placeholder='z. B. Rückgabefrist abgelaufen, Artikel zeigt keine Mängel, ...',
    )

    def action_confirm_reject(self):
        self.ensure_one()
        req = self.request_id
        if req.state not in ('submitted', 'approved'):
            raise UserError(_('Diese Anfrage kann nicht mehr abgelehnt werden.'))

        req.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        req._send_rejection_email(self.rejection_reason)
        return {'type': 'ir.actions.act_window_close'}
