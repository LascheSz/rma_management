from markupsafe import Markup, escape

from odoo import _, api, fields, models


class RmaAuditLog(models.Model):
    """Zentrales Audit-Protokoll für RMA-Ereignisse.

    Zusätzlich zur Liste wird jeder Eintrag in den Chatter der betroffenen Belege
    geschrieben, damit Benutzer die Historie direkt am Vorgang sehen.
    """

    _name = 'rma.audit.log'
    _description = 'RMA Management Audit-Log'
    _order = 'create_date desc, id desc'

    def _default_user_id(self):
        return self.env.user

    action = fields.Selection(
        selection=[
            ('deadline_confirmed', 'Fristüberschreitung bestätigt'),
            ('receipt_created', 'RMA-Eingang erstellt'),
            ('split_completed', 'Mengenprüfung abgeschlossen'),
        ],
        string='Aktion',
        required=True,
        index=True,
    )
    name = fields.Char(string='Beschreibung', required=True)
    user_id = fields.Many2one(
        'res.users',
        string='Benutzer',
        default='_default_user_id',
        required=True,
        readonly=True,
    )
    sale_order_id = fields.Many2one('sale.order', string='Verkaufsauftrag', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='RMA Beleg', readonly=True)
    generated_picking_ids = fields.Many2many(
        'stock.picking',
        'rma_audit_log_generated_picking_rel',
        'audit_log_id',
        'picking_id',
        string='Erzeugte Belege',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Kunde',
        compute='_compute_partner_id',
        store=True,
        readonly=True,
    )
    details = fields.Text(string='Details', readonly=True)

    @api.depends('sale_order_id.partner_id', 'picking_id.partner_id')
    def _compute_partner_id(self):
        """Ermittelt den Kunden aus Auftrag oder RMA-Beleg für Filter und Sichten."""
        for log in self:
            log.partner_id = log.sale_order_id.partner_id or log.picking_id.partner_id

    @api.model
    def _build_quantity_details(self, lines):
        """Formatiert Mengenzeilen einheitlich für Audit-Details."""
        detail_lines = []
        for line in lines:
            if hasattr(line, 'return_qty'):
                quantity = line.return_qty
            else:
                quantity = line.product_uom_qty
            detail_lines.append('%s: %s %s' % (
                line.product_id.display_name,
                quantity,
                line.product_uom.display_name if line.product_uom else '',
            ))
        return '\n'.join(detail_lines)

    @api.model
    def log_event(self, action, name, sale_order=False, picking=False, generated_pickings=False, details=False, attachment_ids=False):
        """Erstellt einen Audit-Eintrag und spiegelt ihn direkt in den Chatter."""
        values = {
            'action': action,
            'name': name,
            'user_id': self.env.user.id,
            'details': details or False,
        }
        if sale_order:
            values['sale_order_id'] = sale_order.id
        if picking:
            values['picking_id'] = picking.id
        if generated_pickings:
            values['generated_picking_ids'] = [(6, 0, generated_pickings.ids)]
        audit_log = self.sudo().create(values)
        audit_log._post_to_chatter(attachment_ids=attachment_ids)
        return audit_log

    def _post_to_chatter(self, attachment_ids=False):
        """Postet dieselbe Audit-Nachricht auf alle fachlich beteiligten Belege."""
        for log in self:
            records = []
            if log.picking_id:
                records.append(log.picking_id)
            if log.sale_order_id:
                records.append(log.sale_order_id)
            records.extend(log.generated_picking_ids)

            body = log._prepare_chatter_body()
            for record in records:
                if hasattr(record, 'message_post'):
                    record.sudo().message_post(
                        body=body,
                        author_id=log.user_id.partner_id.id,
                        subtype_xmlid='mail.mt_note',
                        attachment_ids=attachment_ids or [],
                    )

    def _prepare_chatter_body(self):
        """Baut HTML sicher zusammen; Nutzdaten werden escaped."""
        self.ensure_one()
        parts = [
            Markup('<p><strong>RMA Audit:</strong> %s</p>') % escape(self.name),
        ]
        if self.details:
            parts.append(Markup('<pre>%s</pre>') % escape(self.details))
        if self.generated_picking_ids:
            generated_names = ', '.join(self.generated_picking_ids.mapped('name'))
            parts.append(Markup('<p><strong>%s</strong> %s</p>') % (
                escape(_('Erzeugte Belege:')),
                escape(generated_names),
            ))
        return Markup('').join(parts)
