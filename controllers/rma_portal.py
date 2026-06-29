from odoo import http
from odoo.http import request


class RmaPublicPortal(http.Controller):

    @http.route('/rma/anfrage', auth='public', type='http', methods=['GET'], csrf=False)
    def rma_step1(self, error=None, email='', invoice_number='', **kwargs):
        return request.render('rma_management.rma_portal_step1', {
            'error': error,
            'email': email,
            'invoice_number': invoice_number,
        })

    @http.route('/rma/anfrage/verify', auth='public', type='http', methods=['POST'], csrf=False)
    def rma_verify(self, email='', invoice_number='', **kwargs):
        env = request.env
        email = (email or '').strip().lower()
        invoice_number = (invoice_number or '').strip().upper()

        def back(error):
            return request.render('rma_management.rma_portal_step1', {
                'error': error,
                'email': email,
                'invoice_number': invoice_number,
            })

        if not email or not invoice_number:
            return back('Bitte E-Mail-Adresse und Rechnungsnummer eingeben.')

        invoice = env['account.move'].sudo().search([
            ('name', '=', invoice_number),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ], limit=1)

        if not invoice:
            return back(f'Rechnung „{invoice_number}" nicht gefunden oder noch nicht gebucht.')

        # E-Mail gegen Rechnungspartner und dessen übergeordneten Kontakt prüfen
        partner = invoice.partner_id
        known_emails = set()
        for p in (partner, partner.commercial_partner_id):
            if p.email:
                known_emails.add(p.email.strip().lower())

        if email not in known_emails:
            return back('Die E-Mail-Adresse stimmt nicht mit dieser Rechnung überein.')

        # Verifizierung in Session speichern
        request.session['rma_invoice_id'] = invoice.id
        request.session['rma_partner_id'] = partner.id

        invoice_lines = invoice.invoice_line_ids.filtered_domain([
            ('display_type', '=', 'product'),
            ('product_id', '!=', False),
        ])
        reasons = env['rma.reason'].sudo().search([])

        return request.render('rma_management.rma_portal_step2', {
            'invoice': invoice,
            'partner': partner,
            'invoice_lines': invoice_lines,
            'reasons': reasons,
        })

    @http.route('/rma/anfrage/submit', auth='public', type='http', methods=['POST'], csrf=False)
    def rma_submit(self, **post):
        env = request.env
        invoice_id = request.session.get('rma_invoice_id')
        partner_id = request.session.get('rma_partner_id')

        if not invoice_id or not partner_id:
            return request.redirect('/rma/anfrage?error=Sitzung+abgelaufen.+Bitte+neu+starten.')

        invoice = env['account.move'].sudo().browse(invoice_id)
        partner = env['res.partner'].sudo().browse(partner_id)

        invoice_lines = invoice.invoice_line_ids.filtered_domain([
            ('display_type', '=', 'product'),
            ('product_id', '!=', False),
        ])
        reasons = env['rma.reason'].sudo().search([])

        def back(error):
            return request.render('rma_management.rma_portal_step2', {
                'invoice': invoice,
                'partner': partner,
                'invoice_lines': invoice_lines,
                'reasons': reasons,
                'error': error,
                'post': post,
            })

        reason_id = int(post.get('reason_id') or 0)
        description = (post.get('description') or '').strip()

        if not reason_id:
            return back('Bitte einen Rückgabegrund auswählen.')

        lines_data = []
        for line in invoice_lines:
            qty = float(post.get(f'qty_{line.id}') or 0)
            if qty > 0:
                lines_data.append({
                    'product_id': line.product_id.id,
                    'qty_invoiced': line.quantity,
                    'qty_requested': min(qty, line.quantity),
                    'note': (post.get(f'note_{line.id}') or '').strip(),
                })

        if not lines_data:
            return back('Bitte bei mindestens einem Artikel eine Rückgabemenge eintragen.')

        portal_request = env['rma.portal.request'].sudo().create({
            'partner_id': partner_id,
            'invoice_id': invoice_id,
            'rma_reason_id': reason_id,
            'description': description,
            'line_ids': [(0, 0, l) for l in lines_data],
        })

        request.session.pop('rma_invoice_id', None)
        request.session.pop('rma_partner_id', None)

        return request.render('rma_management.rma_portal_confirm', {
            'portal_request': portal_request,
            'partner': partner,
            'invoice': invoice,
        })
