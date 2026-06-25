from datetime import timedelta

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class HelpdeskTicket(models.Model):
    """RMA-Erweiterung für B-Ware-QS-Tickets im nativen Helpdesk."""

    _inherit = 'helpdesk.ticket'

    RMA_BWARE_STAGE_XMLIDS = {
        'new': 'rma_management.helpdesk_stage_rma_bware_new',
        'assigned': 'rma_management.helpdesk_stage_rma_bware_assigned',
        'progress': 'rma_management.helpdesk_stage_rma_bware_progress',
        'decision': 'rma_management.helpdesk_stage_rma_bware_decision',
        'done': 'rma_management.helpdesk_stage_rma_bware_done',
    }

    rma_is_bware_ticket = fields.Boolean(string='RMA B-Ware Ticket', index=True, copy=False)
    rma_product_id = fields.Many2one('product.product', string='Artikel', readonly=True, copy=False)
    rma_product_default_code = fields.Char(related='rma_product_id.default_code', string='Artikelnummer', readonly=True)
    rma_product_categ_id = fields.Many2one(related='rma_product_id.categ_id', string='Kategorie', readonly=True)
    rma_product_uom_id = fields.Many2one('uom.uom', string='Einheit', readonly=True, copy=False)
    rma_bware_quantity = fields.Float(string='B-Ware Menge', readonly=True, copy=False)
    rma_unit_price = fields.Monetary(string='Preis pro Stück', readonly=True, copy=False)
    rma_total_value = fields.Monetary(string='Gesamtwert', compute='_compute_rma_total_value', store=True)
    rma_sale_order_id = fields.Many2one('sale.order', string='Verkaufsauftrag', readonly=True, copy=False)
    rma_rma_picking_id = fields.Many2one('stock.picking', string='RMA-Eingang', readonly=True, copy=False)
    rma_bware_picking_id = fields.Many2one('stock.picking', string='B-Ware Beleg', readonly=True, copy=False)
    rma_bware_move_ids = fields.Many2many(
        'stock.move',
        'rma_bware_ticket_stock_move_rel',
        'ticket_id',
        'move_id',
        string='B-Ware Bewegungen',
        readonly=True,
        copy=False,
    )
    currency_id = fields.Many2one(related='company_id.currency_id', string='Währung', readonly=True)
    rma_reason_id = fields.Many2one('rma.reason', string='RMA-Grund', readonly=True, copy=False)
    rma_purchase_date = fields.Datetime(related='rma_sale_order_id.date_order', string='Kaufdatum', readonly=True)
    rma_delivery_date = fields.Datetime(string='Lieferdatum', compute='_compute_rma_dates', store=True)
    rma_return_date = fields.Datetime(related='rma_rma_picking_id.date_done', string='Rückgabedatum', readonly=True)
    rma_days_since_purchase = fields.Integer(string='Tage seit Kauf', compute='_compute_rma_dates', store=True)
    rma_days_since_delivery = fields.Integer(string='Tage seit Lieferung', compute='_compute_rma_dates', store=True)
    rma_due_date = fields.Date(string='QS-Fälligkeitsdatum', readonly=True, copy=False)
    rma_attachment_ids = fields.Many2many(
        'ir.attachment',
        'rma_bware_ticket_attachment_rel',
        'ticket_id',
        'attachment_id',
        string='RMA Bilder / Anhänge',
        copy=False,
    )

    rma_functional_ok = fields.Boolean(string='Funktioniert einwandfrei?')
    rma_cosmetic_defects = fields.Boolean(string='Kosmetische Mängel?')
    rma_cosmetic_description = fields.Text(string='Beschreibung kosmetische Mängel')
    rma_missing_parts = fields.Boolean(string='Fehlende Teile?')
    rma_missing_parts_description = fields.Text(string='Beschreibung fehlende Teile')
    rma_inspection_date = fields.Datetime(string='Prüfdatum', readonly=True, copy=False)
    rma_inspection_notes = fields.Text(string='QS-Notizen')

    rma_decision = fields.Selection(
        [
            ('resale', 'Wiederverkauf'),
            ('scrap', 'Schrottlager'),
            ('repair', 'Reparatur'),
        ],
        string='Entscheidung',
        readonly=True,
        copy=False,
    )
    rma_decision_note = fields.Text(string='Entscheidungsbegründung')
    rma_target_location_id = fields.Many2one('stock.location', string='Ziel-Lagerort', readonly=True, copy=False)
    rma_decision_picking_id = fields.Many2one('stock.picking', string='Entscheidungs-Umlagerung', readonly=True, copy=False)
    rma_decision_user_id = fields.Many2one('res.users', string='Entscheidung getroffen von', readonly=True, copy=False)
    rma_decision_date = fields.Datetime(string='Entscheidungsdatum', readonly=True, copy=False)
    rma_scrap_reason = fields.Char(string='Verschrottungsgrund')
    rma_scrap_cost = fields.Monetary(string='Verschrottungskosten')
    rma_repair_description = fields.Text(string='Reparaturbeschreibung')
    rma_repair_cost = fields.Monetary(string='Geschätzte Reparaturkosten')
    rma_repair_partner_id = fields.Many2one('res.partner', string='Reparaturpartner')

    @api.depends('rma_bware_quantity', 'rma_unit_price')
    def _compute_rma_total_value(self):
        for ticket in self:
            ticket.rma_total_value = ticket.rma_bware_quantity * ticket.rma_unit_price

    @api.depends('rma_sale_order_id.date_order', 'rma_sale_order_id.picking_ids.date_done')
    def _compute_rma_dates(self):
        today = fields.Date.context_today(self)
        for ticket in self:
            delivery_pickings = ticket.rma_sale_order_id.picking_ids.filtered(
                lambda picking: picking.picking_type_code == 'outgoing' and picking.state == 'done' and picking.date_done
            )
            delivery_date = max(delivery_pickings.mapped('date_done')) if delivery_pickings else False
            ticket.rma_delivery_date = delivery_date
            purchase_date = fields.Date.to_date(ticket.rma_sale_order_id.date_order) if ticket.rma_sale_order_id.date_order else False
            delivery_day = fields.Date.to_date(delivery_date) if delivery_date else False
            ticket.rma_days_since_purchase = (today - purchase_date).days if purchase_date else 0
            ticket.rma_days_since_delivery = (today - delivery_day).days if delivery_day else 0

    @api.model
    def _get_rma_stock_configuration(self):
        return self.env['rma.stock.configuration']

    @api.model
    def _get_bware_config_record(self, model_name, config_key, fallback=False):
        record_id = self.env['ir.config_parameter'].sudo().get_param(config_key)
        if record_id:
            record = self.env[model_name].browse(int(record_id)).exists()
            if record:
                return record
        return fallback or self.env[model_name]

    @api.model
    def _get_bware_helpdesk_team(self):
        fallback = self.env.ref('rma_management.helpdesk_team_rma_bware_qs', raise_if_not_found=False)
        return self._get_bware_config_record('helpdesk.team', 'rma_management.bware_helpdesk_team_id', fallback=fallback)

    @api.model
    def _get_bware_stage(self, stage_key, team=False):
        stage = self.env.ref(self.RMA_BWARE_STAGE_XMLIDS[stage_key])
        team = team or self._get_bware_helpdesk_team()
        if team and team not in stage.team_ids:
            stage.team_ids = [(4, team.id)]
        return stage

    @api.model
    def _get_bware_ticket_name_prefix(self):
        return self.env['ir.config_parameter'].sudo().get_param('rma_management.bware_ticket_name', 'Prüfware') or 'Prüfware'

    @api.model
    def _get_bware_sla_days(self):
        value = self.env['ir.config_parameter'].sudo().get_param('rma_management.bware_sla_days', '5')
        try:
            return int(value)
        except (TypeError, ValueError):
            return 5

    @api.model
    def _is_bware_auto_ticket_enabled(self):
        value = self.env['ir.config_parameter'].sudo().get_param('rma_management.bware_auto_create_tickets', 'True')
        return value not in ('False', 'false', '0', '', False)

    @api.model
    def _create_rma_bware_tickets_from_picking(self, bware_picking, rma_picking):
        """Erstellt pro Artikel genau ein Helpdesk-Ticket für einen B-Ware-Beleg."""
        if not self._is_bware_auto_ticket_enabled() or not bware_picking:
            return self.env['helpdesk.ticket']

        team = self._get_bware_helpdesk_team()
        if not team:
            raise UserError(_('Bitte konfiguriere ein Helpdesk-Team für B-Ware Tickets.'))

        created_tickets = self.env['helpdesk.ticket']
        new_stage = self._get_bware_stage('new', team)
        due_date = fields.Date.context_today(self) + timedelta(days=self._get_bware_sla_days())

        moves_by_product = {}
        for move in bware_picking.move_ids.filtered(lambda stock_move: stock_move.state != 'cancel'):
            moves_by_product.setdefault(move.product_id, self.env['stock.move'])
            moves_by_product[move.product_id] |= move

        for product, moves in moves_by_product.items():
            existing_ticket = self.search([
                ('rma_is_bware_ticket', '=', True),
                ('rma_bware_picking_id', '=', bware_picking.id),
                ('rma_product_id', '=', product.id),
            ], limit=1)
            if existing_ticket:
                continue

            quantity = sum(move.product_uom._compute_quantity(move.product_uom_qty, product.uom_id) for move in moves)
            sale_line = bware_picking.rma_sale_order_id.order_line.filtered(
                lambda line: not line.display_type and line.product_id == product
            )[:1]
            unit_price = sale_line.price_unit if sale_line else product.lst_price
            ticket_name = _('%(prefix)s - %(product)s - %(quantity)s %(uom)s') % {
                'prefix': self._get_bware_ticket_name_prefix(),
                'product': product.display_name,
                'quantity': quantity,
                'uom': product.uom_id.display_name,
            }
            attachments = rma_picking.rma_attachment_ids or bware_picking.rma_attachment_ids

            ticket = self.create({
                'name': ticket_name,
                'description': self._prepare_rma_bware_description(product, quantity, bware_picking, rma_picking),
                'team_id': team.id,
                'stage_id': new_stage.id,
                'partner_id': bware_picking.partner_id.id,
                'partner_name': bware_picking.partner_id.name,
                'partner_email': bware_picking.partner_id.email,
                'partner_phone': bware_picking.partner_id.phone,
                'priority': '1',
                'rma_is_bware_ticket': True,
                'rma_product_id': product.id,
                'rma_product_uom_id': product.uom_id.id,
                'rma_bware_quantity': quantity,
                'rma_unit_price': unit_price,
                'rma_sale_order_id': bware_picking.rma_sale_order_id.id,
                'rma_rma_picking_id': rma_picking.id,
                'rma_bware_picking_id': bware_picking.id,
                'rma_bware_move_ids': [(6, 0, moves.ids)],
                'rma_reason_id': bware_picking.rma_reason_id.id,
                'rma_due_date': due_date,
                'rma_attachment_ids': [(6, 0, attachments.ids)],
            })
            if attachments:
                ticket.message_post(
                    body=_('RMA-Prüfbilder wurden aus dem RMA-Eingang übernommen.'),
                    attachment_ids=attachments.ids,
                    subtype_xmlid='mail.mt_note',
                )
            self.env['rma.audit.log'].log_event(
                'bware_ticket_created',
                _('B-Ware Helpdesk-Ticket %(ticket)s für %(product)s erstellt') % {
                    'ticket': ticket.ticket_ref or ticket.name,
                    'product': product.display_name,
                },
                sale_order=bware_picking.rma_sale_order_id,
                picking=bware_picking,
                helpdesk_ticket=ticket,
                details=_('Menge: %(quantity)s %(uom)s') % {
                    'quantity': quantity,
                    'uom': product.uom_id.display_name,
                },
            )
            created_tickets |= ticket
        return created_tickets

    @api.model
    def _prepare_rma_bware_description(self, product, quantity, bware_picking, rma_picking):
        return Markup(
            '<p><strong>%s</strong></p>'
            '<ul>'
            '<li>%s</li>'
            '<li>%s</li>'
            '<li>%s</li>'
            '<li>%s</li>'
            '</ul>'
        ) % (
            escape(_('Automatisch aus RMA B-Ware erzeugt')),
            escape(_('Artikel: %(product)s') % {'product': product.display_name}),
            escape(_('Menge: %(quantity)s %(uom)s') % {'quantity': quantity, 'uom': product.uom_id.display_name}),
            escape(_('RMA-Beleg: %(picking)s') % {'picking': rma_picking.name}),
            escape(_('B-Ware Beleg: %(picking)s') % {'picking': bware_picking.name}),
        )

    def action_rma_bware_assign_to_me(self):
        for ticket in self:
            ticket.write({
                'user_id': self.env.user.id,
                'stage_id': ticket._get_bware_stage('assigned', ticket.team_id).id,
            })
            ticket._log_bware_ticket_event('bware_ticket_assigned', _('B-Ware Ticket zugewiesen'))
        return True

    def action_rma_bware_start(self):
        for ticket in self:
            ticket.write({
                'stage_id': ticket._get_bware_stage('progress', ticket.team_id).id,
                'kanban_state': 'normal',
            })
        return True

    def action_rma_bware_finish_qs(self):
        for ticket in self:
            ticket.write({
                'stage_id': ticket._get_bware_stage('decision', ticket.team_id).id,
                'kanban_state': 'blocked',
                'rma_inspection_date': fields.Datetime.now(),
            })
            ticket._log_bware_ticket_event('bware_ticket_qs_done', _('B-Ware QS abgeschlossen'))
        return True

    def action_rma_bware_decide_resale(self):
        return self._execute_bware_decision('resale')

    def action_rma_bware_decide_scrap(self):
        return self._execute_bware_decision('scrap')

    def action_rma_bware_decide_repair(self):
        return self._execute_bware_decision('repair')

    def _execute_bware_decision(self, decision):
        for ticket in self:
            if not ticket.rma_is_bware_ticket:
                continue
            if ticket.rma_decision_picking_id:
                raise ValidationError(_('Für dieses Ticket wurde bereits eine Entscheidung gebucht.'))

            target_location = ticket._get_decision_target_location(decision)
            decision_picking = ticket._create_decision_picking(decision, target_location)
            ticket.write({
                'rma_decision': decision,
                'rma_target_location_id': target_location.id,
                'rma_decision_picking_id': decision_picking.id,
                'rma_decision_user_id': self.env.user.id,
                'rma_decision_date': fields.Datetime.now(),
                'stage_id': ticket._get_bware_stage('done', ticket.team_id).id,
                'kanban_state': 'done',
            })
            ticket._log_bware_ticket_event(
                'bware_ticket_decision',
                _('B-Ware Entscheidung getroffen: %(decision)s') % {
                    'decision': dict(ticket._fields['rma_decision'].selection).get(decision),
                },
                generated_picking=decision_picking,
            )
        return True

    def _get_decision_target_location(self, decision):
        self.ensure_one()
        stock_configuration = self._get_rma_stock_configuration()
        if decision == 'resale':
            return stock_configuration._get_location('a_goods')
        if decision == 'scrap':
            return stock_configuration._get_location('scrap')
        return stock_configuration._get_location('repair')

    def _get_decision_picking_type(self):
        self.ensure_one()
        warehouse = self._get_rma_stock_configuration()._get_warehouse()
        if warehouse.int_type_id:
            return warehouse.int_type_id
        return self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

    def _create_decision_picking(self, decision, target_location):
        self.ensure_one()
        source_location = self.rma_bware_picking_id.location_dest_id or self._get_rma_stock_configuration()._get_location('b_goods')
        picking_type = self._get_decision_picking_type()
        if not picking_type:
            raise UserError(_('Es wurde keine interne Vorgangsart für die B-Ware Entscheidung gefunden.'))

        title_by_decision = {
            'resale': _('Wiederverkauf'),
            'scrap': _('Schrottlager'),
            'repair': _('Reparatur'),
        }
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id,
            'origin': '%s - %s' % (self.ticket_ref or self.name, title_by_decision[decision]),
            'location_id': source_location.id,
            'location_dest_id': target_location.id,
            'rma_reason_id': self.rma_reason_id.id,
            'rma_sale_order_id': self.rma_sale_order_id.id,
        })
        move = self.env['stock.move'].create({
            'product_id': self.rma_product_id.id,
            'product_uom_qty': self.rma_bware_quantity,
            'product_uom': self.rma_product_uom_id.id,
            'picking_id': picking.id,
            'partner_id': self.partner_id.id,
            'location_id': source_location.id,
            'location_dest_id': target_location.id,
            'description_picking': self.rma_product_id.display_name,
            'origin': self.ticket_ref or self.name,
        })
        picking.action_confirm()
        self._create_decision_move_lines(move)
        for stock_move in picking.move_ids:
            stock_move.picked = True
        picking._action_done()
        return picking

    def _create_decision_move_lines(self, move):
        self.ensure_one()
        serial_lots = self.rma_bware_move_ids.move_line_ids.lot_id
        move.move_line_ids.unlink()
        if serial_lots:
            for lot in serial_lots:
                self.env['stock.move.line'].create({
                    'picking_id': move.picking_id.id,
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': 1.0,
                    'lot_id': lot.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })
            return
        self.env['stock.move.line'].create({
            'picking_id': move.picking_id.id,
            'move_id': move.id,
            'product_id': move.product_id.id,
            'product_uom_id': move.product_uom.id,
            'quantity': self.rma_bware_quantity,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
        })

    def _log_bware_ticket_event(self, action, name, generated_picking=False):
        self.ensure_one()
        self.env['rma.audit.log'].log_event(
            action,
            name,
            sale_order=self.rma_sale_order_id,
            picking=self.rma_bware_picking_id,
            helpdesk_ticket=self,
            generated_pickings=generated_picking,
            details=self.rma_decision_note or self.rma_inspection_notes or False,
        )
