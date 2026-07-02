import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RmaPortalRequest(models.Model):
    _name = 'rma.portal.request'
    _description = 'Kunden-RMA-Anfrage (Portal)'
    _order = 'create_date desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Anfrage-Nr.', readonly=True, default='Neu', copy=False)
    partner_id = fields.Many2one('res.partner', string='Kunde', required=True, readonly=True, index=True)
    invoice_id = fields.Many2one('account.move', string='Rechnung', required=True, readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Verkaufsauftrag', readonly=True)
    rma_reason_id = fields.Many2one('rma.reason', string='Rückgabegrund', required=True, tracking=True)
    description = fields.Text(string='Problembeschreibung')
    state = fields.Selection([
        ('submitted', 'Eingereicht'),
        ('approved', 'Genehmigt'),
        ('processing', 'In Bearbeitung'),
        ('done', 'Erledigt'),
        ('rejected', 'Abgelehnt'),
    ], string='Status', default='submitted', tracking=True, index=True)
    rejection_reason = fields.Text(string='Ablehnungsgrund')
    picking_id = fields.Many2one('stock.picking', string='RMA-Eingang', readonly=True)
    line_ids = fields.One2many('rma.portal.request.line', 'request_id', string='Positionen')
    create_date = fields.Datetime(string='Eingereicht am', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Neu') == 'Neu':
                vals['name'] = self.env['ir.sequence'].next_by_code('rma.portal.request') or 'Neu'
        records = super().create(vals_list)
        records._notify_rma_users_new_request()
        return records

    def _notify_rma_users_new_request(self):
        rma_user_group = self.env.ref('rma_management.group_rma_user').sudo()
        rma_manager_group = self.env.ref('rma_management.group_rma_manager').sudo()
        partner_ids = (rma_user_group.user_ids | rma_manager_group.user_ids).mapped('partner_id').ids
        if not partner_ids:
            return
        for rec in self:
            rec.sudo().message_subscribe(partner_ids=partner_ids)
            rec.sudo().message_post(
                body=_(
                    'Neue Portal-Anfrage <b>%s</b> von <b>%s</b> wurde eingereicht.',
                    rec.name,
                    rec.partner_id.name,
                ),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

    def action_approve(self):
        """Genehmigt die Anfrage und schickt dem Kunden eine Bestätigungs-E-Mail."""
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_('Nur eingereichte Anfragen können genehmigt werden.'))

        # Verkaufsauftrag aus Rechnung ermitteln und speichern
        sale_orders = self.invoice_id.invoice_line_ids.sale_line_ids.order_id
        if sale_orders:
            self.sale_order_id = sale_orders[0]

        self.write({'state': 'approved'})
        self._send_approval_email()
        return True

    def _send_approval_email(self):
        """Baut die Genehmigungs-E-Mail direkt in Python und sendet sie."""
        self.ensure_one()
        if not self.partner_id.email:
            return

        company = self.env.company
        article_rows = ''.join(
            f'<tr style="border-bottom:1px solid #eee;">'
            f'<td style="padding:8px 12px;">{line.product_id.display_name}</td>'
            f'<td style="padding:8px 12px;text-align:right;">{line.qty_requested}</td>'
            f'</tr>'
            for line in self.line_ids
        )
        address_lines = ''
        if company.street:
            address_lines += f'{company.street}<br/>'
        if company.zip or company.city:
            address_lines += f'{company.zip or ""} {company.city or ""}<br/>'

        body = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#714b67;padding:24px 32px;border-radius:8px 8px 0 0;">
    <h2 style="color:#fff;margin:0;font-size:1.3rem;">RMA-Rücksendung genehmigt</h2>
  </div>
  <div style="background:#fff;border:1px solid #e0e0e0;border-top:none;padding:28px 32px;border-radius:0 0 8px 8px;">
    <p>Guten Tag {self.partner_id.name},</p>
    <p>Ihre RMA-Anfrage wurde geprüft und genehmigt. Sie können die Ware nun an uns zurücksenden.</p>

    <div style="background:#f5f6f8;border-radius:8px;padding:16px 20px;margin:20px 0;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="color:#888;padding:4px 0;width:40%;">Anfrage-Nr.</td>
            <td style="font-weight:bold;">{self.name}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Rechnung</td>
            <td>{self.invoice_id.name}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Rückgabegrund</td>
            <td>{self.rma_reason_id.name}</td></tr>
      </table>
    </div>

    <h3 style="font-size:1rem;margin-top:24px;">Zurückzusendende Artikel</h3>
    <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
      <thead>
        <tr style="background:#f0eaf3;">
          <th style="text-align:left;padding:8px 12px;border-radius:4px 0 0 4px;">Artikel</th>
          <th style="text-align:right;padding:8px 12px;border-radius:0 4px 4px 0;">Menge</th>
        </tr>
      </thead>
      <tbody>{article_rows}</tbody>
    </table>

    <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:6px;padding:14px 18px;margin:24px 0;">
      <strong>Bitte beachten:</strong> Bitte schreiben Sie die Anfrage-Nr.
      <strong>{self.name}</strong> gut sichtbar auf das Paket oder legen Sie dieses Schreiben bei.
    </div>

    <h3 style="font-size:1rem;">Rücksendeadresse</h3>
    <p style="margin:0;">{company.name}<br/>{address_lines}</p>

    <p style="margin-top:24px;">Bei Fragen stehen wir Ihnen gerne zur Verfügung.</p>
    <p>Mit freundlichen Grüßen<br/>{company.name}</p>
  </div>
</div>"""

        report = self.env['ir.actions.report'].sudo()
        pdf_content, _ = report._render_qweb_pdf(
            'rma_management.action_report_rma_portal_request',
            res_ids=[self.id],
        )
        attachment = self.env['ir.attachment'].sudo().create({
            'name': f'Rücksendeschein-{self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'mimetype': 'application/pdf',
            'res_model': self._name,
            'res_id': self.id,
        })

        mail_values = {
            'subject': f'Ihre RMA-Anfrage {self.name} wurde genehmigt',
            'email_to': self.partner_id.email,
            'email_from': company.email or self.env.user.email,
            'body_html': body,
            'attachment_ids': [(4, attachment.id)],
            'auto_delete': True,
        }
        self.env['mail.mail'].create(mail_values).send()

    def action_reject(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Anfrage ablehnen'),
            'res_model': 'rma.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def _send_rejection_email(self, reason):
        """Schickt dem Kunden eine E-Mail mit dem Ablehnungsgrund."""
        self.ensure_one()
        if not self.partner_id.email:
            return

        company = self.env.company
        article_rows = ''.join(
            f'<tr style="border-bottom:1px solid #eee;">'
            f'<td style="padding:8px 12px;">{line.product_id.display_name}</td>'
            f'<td style="padding:8px 12px;text-align:right;">{line.qty_requested}</td>'
            f'</tr>'
            for line in self.line_ids
        )

        body = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#c0392b;padding:24px 32px;border-radius:8px 8px 0 0;">
    <h2 style="color:#fff;margin:0;font-size:1.3rem;">RMA-Anfrage abgelehnt</h2>
  </div>
  <div style="background:#fff;border:1px solid #e0e0e0;border-top:none;padding:28px 32px;border-radius:0 0 8px 8px;">
    <p>Guten Tag {self.partner_id.name},</p>
    <p>leider müssen wir Ihre RMA-Anfrage ablehnen.</p>

    <div style="background:#f5f6f8;border-radius:8px;padding:16px 20px;margin:20px 0;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="color:#888;padding:4px 0;width:40%;">Anfrage-Nr.</td>
            <td style="font-weight:bold;">{self.name}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Rechnung</td>
            <td>{self.invoice_id.name}</td></tr>
        <tr><td style="color:#888;padding:4px 0;">Rückgabegrund</td>
            <td>{self.rma_reason_id.name}</td></tr>
      </table>
    </div>

    <h3 style="font-size:1rem;margin-top:24px;">Angegebene Artikel</h3>
    <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
      <thead>
        <tr style="background:#f0eaf3;">
          <th style="text-align:left;padding:8px 12px;">Artikel</th>
          <th style="text-align:right;padding:8px 12px;">Menge</th>
        </tr>
      </thead>
      <tbody>{article_rows}</tbody>
    </table>

    <div style="background:#fdecea;border:1px solid #e74c3c;border-radius:6px;padding:14px 18px;margin:24px 0;">
      <strong>Grund der Ablehnung:</strong><br/>
      {reason}
    </div>

    <p>Bei Fragen stehen wir Ihnen gerne zur Verfügung.</p>
    <p>Mit freundlichen Grüßen<br/>{company.name}</p>
  </div>
</div>"""

        self.env['mail.mail'].create({
            'subject': f'Ihre RMA-Anfrage {self.name} wurde abgelehnt',
            'email_to': self.partner_id.email,
            'email_from': company.email or self.env.user.email,
            'body_html': body,
            'auto_delete': True,
        }).send()

    def action_mark_done(self):
        self.ensure_one()
        self.write({'state': 'done'})

    def action_link_picking(self, picking):
        """Wird aus der RMA-Erstellung aufgerufen um den erzeugten Beleg zu verknüpfen."""
        self.ensure_one()
        self.write({'state': 'processing', 'picking_id': picking.id})


class RmaPortalRequestLine(models.Model):
    _name = 'rma.portal.request.line'
    _description = 'Kunden-RMA-Anfrage Position'

    request_id = fields.Many2one('rma.portal.request', required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Artikel', required=True, readonly=True)
    qty_invoiced = fields.Float(string='Berechnet', readonly=True, digits='Product Unit of Measure')
    qty_requested = fields.Float(string='Rückgabemenge', digits='Product Unit of Measure')
    note = fields.Text(string='Bemerkung des Kunden')
