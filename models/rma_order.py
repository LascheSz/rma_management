import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class RmaOrder(models.TransientModel):
    """Temporärer Wizard für die RMA-Erstellung aus einem Verkaufsauftrag.

    Der Wizard speichert selbst keine dauerhaften RMA-Daten. Dauerhaft angelegt
    wird erst beim Ausführen der RMA-Eingangsbeleg inklusive Lagerbewegungen.
    """

    _name = 'rma.order'
    _description = 'RMA Management Erstellung'

    @api.depends('sale_order_id.name')
    def _compute_display_name(self):
        for wizard in self:
            wizard.display_name = wizard.sale_order_id.name or _('Neue RMA-Erstellung')

    def _raise_unexpected_error(self, message, error):
        """Wandelt unerwartete technische Fehler in eine verständliche Odoo-Meldung um."""
        _logger.exception("%s", message)
        raise UserError(_(
            "%(message)s\n\nBitte prüfe die RMA-Konfiguration oder kontaktiere einen Administrator."
        ) % {
            'message': message,
        }) from error

    def _get_rma_order_service(self):
        return self.env['rma.order.service']

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Verkaufsauftrag',
        required=True,
        domain=[('state', 'in', ['sale', 'done'])],
    )
    line_ids = fields.One2many(
        'rma.order.line',
        'wizard_id',
        string='Belegpositionen',
    )
    has_serial_lots = fields.Boolean(
        string='Hat Seriennummern',
        compute='_compute_has_serial_lots',
    )
    rma_reason_id = fields.Many2one(
        'rma.reason',
        string='RMA-Grund',
        required=True,
        domain=[('active', '=', True)],
    )

    is_company = fields.Boolean(related='sale_order_id.partner_id.is_company', string='Ist Firma', readonly=True)
    partner_id = fields.Many2one('res.partner', related='sale_order_id.partner_id', string='Kunde', readonly=True)
    image_1920 = fields.Image(related='partner_id.image_1920', string='', readonly=True)
    partner_street = fields.Char(related='sale_order_id.partner_id.street', string='Straße', readonly=True)
    partner_plz = fields.Char(related='sale_order_id.partner_id.zip', string='PLZ', readonly=True)
    partner_city = fields.Char(related='sale_order_id.partner_id.city', string='Stadt', readonly=True)
    vat = fields.Char(related='sale_order_id.partner_id.vat', string='USTD', readonly=True)
    website = fields.Char(related='sale_order_id.partner_id.website', string='Webseite', readonly=True)
    partner_email = fields.Char(related='sale_order_id.partner_id.email', string='E-Mail', readonly=True)
    partner_phone = fields.Char(related='sale_order_id.partner_id.phone', string='Telefon', readonly=True)
    return_deadline_days = fields.Integer(
        related='sale_order_id.partner_id.rma_return_deadline_days',
        string='Rückgabefrist (Tage)',
        readonly=True,
    )
    return_deadline_date = fields.Date(
        string='Frist bis',
        compute='_compute_return_deadline_information',
        readonly=True,
    )
    return_days_remaining = fields.Integer(
        string='Resttage',
        compute='_compute_return_deadline_information',
        readonly=True,
    )
    return_days_expired = fields.Integer(
        string='Tage abgelaufen',
        compute='_compute_return_deadline_information',
        readonly=True,
    )
    return_deadline_text = fields.Char(
        string='Friststatus',
        compute='_compute_return_deadline_information',
        readonly=True,
    )

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Lädt beim Wechsel des Verkaufsauftrags die retourenfähigen Positionen neu."""
        for wizard in self:
            wizard.line_ids = [(5, 0, 0)] + wizard._get_order_line_commands()

    @api.depends('line_ids.has_serial_lots')
    def _compute_has_serial_lots(self):
        """Steuert die Sichtbarkeit der Seriennummern-Spalten auf Wizard-Ebene."""
        for wizard in self:
            wizard.has_serial_lots = any(wizard.line_ids.mapped('has_serial_lots'))

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            self._fill_missing_line_references(values, values.get('sale_order_id'))
        return super().create(vals_list)

    def write(self, values):
        if not self:
            return True

        for wizard in self:
            wizard_values = dict(values)
            sale_order_id = wizard_values.get('sale_order_id') or wizard.sale_order_id.id
            self._fill_missing_line_references(wizard_values, sale_order_id)
            super(RmaOrder, wizard).write(wizard_values)
        return True

    @api.model
    def _fill_missing_line_references(self, values, sale_order_id):
        """Ergänzt Pflichtverweise, wenn Odoo One2many-Zeilen ohne Kontext speichert.

        In editierbaren Listen kann der Client neue Transient-Zeilen ohne die
        referenzierte Verkaufsauftragsposition schicken. Die Reihenfolge der
        sichtbaren Auftragspositionen wird deshalb als Fallback verwendet.
        """
        line_commands = values.get('line_ids')
        if not line_commands or not sale_order_id:
            return

        sale_order = self.env['sale.order'].browse(sale_order_id).exists()
        if not sale_order:
            return

        selectable_lines = sale_order.order_line.filtered(
            lambda line: not line.display_type and line.product_id.type != 'service'
        )
        line_index = 0

        for command in line_commands:
            if not isinstance(command, (list, tuple)) or len(command) < 3 or command[0] != 0:
                continue

            command_values = command[2]
            if not isinstance(command_values, dict):
                continue

            if not command_values.get('sale_order_line_id') and line_index < len(selectable_lines):
                command_values['sale_order_line_id'] = selectable_lines[line_index].id
            line_index += 1

    def _get_order_line_commands(self):
        """Erzeugt One2many-Kommandos für alle physischen Verkaufspositionen."""
        self.ensure_one()
        commands = []

        if not self.sale_order_id:
            return commands

        for order_line in self.sale_order_id.order_line:
            if order_line.display_type or order_line.product_id.type == 'service':
                continue
            commands.append((0, 0, {
                'sale_order_line_id': order_line.id,
            }))

        return commands

    @api.depends('sale_order_id', 'sale_order_id.date_order', 'sale_order_id.partner_id.rma_return_deadline_days')
    def _compute_return_deadline_information(self):
        """Berechnet die Rückgabefrist für die Hinweis- und Bestätigungslogik."""
        for record in self:
            record.return_deadline_date = False
            record.return_days_remaining = 0
            record.return_days_expired = 0
            record.return_deadline_text = ''

            if not record.sale_order_id or not record.sale_order_id.date_order:
                continue

            order_date = fields.Date.to_date(record.sale_order_id.date_order)
            today = fields.Date.context_today(record)
            return_deadline_days = record.return_deadline_days or 14
            return_deadline_date = order_date + timedelta(days=return_deadline_days)
            remaining_days = (return_deadline_date - today).days

            record.return_deadline_date = return_deadline_date

            if remaining_days >= 0:
                record.return_days_remaining = remaining_days
                record.return_deadline_text = f"Noch {remaining_days} Tage Rückgabefrist"
            else:
                record.return_days_expired = abs(remaining_days)
                record.return_deadline_text = f"Frist seit {abs(remaining_days)} Tagen abgelaufen"

    def _is_return_deadline_expired(self):
        """Kapselt die Fristentscheidung, damit die Button-Logik lesbar bleibt."""
        self.ensure_one()
        return self.return_days_expired > 0

    def _open_return_deadline_confirmation(self):
        """Öffnet den Bestätigungsdialog, wenn die Rückgabefrist überschritten ist."""
        self.ensure_one()

        try:
            deadline_confirmation = self.env['rma.deadline.confirmation'].create({
                'rma_id': self.id,
                'days_expired': self.return_days_expired,
            })

            return {
                'name': _('Rückgabefrist überschritten'),
                'type': 'ir.actions.act_window',
                'res_model': 'rma.deadline.confirmation',
                'view_mode': 'form',
                'res_id': deadline_confirmation.id,
                'target': 'new',
            }
        except (UserError, ValidationError):
            raise
        except Exception as error:
            self._raise_unexpected_error(_('Die Fristprüfung konnte nicht geöffnet werden.'), error)

    def _open_rma_splitting_for_picking(self, picking):
        """Leitet nach der Erstellung direkt in die Mengenprüfung für den Beleg."""
        self.ensure_one()

        try:
            action_id = self.env.ref('rma_management.action_rma_management_splitting').id
            rma_splitting = self.env['rma.splitting'].create({
                'rma_order_id': picking.id,
            })

            return {
                'type': 'ir.actions.act_url',
                'target': 'self',
                'url': f'/odoo/{picking.id}/action-{action_id}/{rma_splitting.id}',
            }
        except (UserError, ValidationError):
            raise
        except Exception as error:
            self._raise_unexpected_error(_('Die Mengenprüfung konnte nicht geöffnet werden.'), error)

    def _get_valid_return_lines(self):
        """Delegiert die Validierung an den Service, hält den Wizard aber als Einstiegspunkt."""
        self.ensure_one()
        return self._get_rma_order_service()._get_valid_return_lines(self)

    def _create_return_picking_record(self):
        """Erstellt den echten RMA-Eingang und öffnet anschließend die Prüfung."""
        self.ensure_one()
        picking = self._get_rma_order_service().create_return_picking(self)
        return self._open_rma_splitting_for_picking(picking)

    def action_create_return_picking(self):
        """Button-Aktion: Frist prüfen, danach RMA-Eingang erzeugen."""
        self.ensure_one()

        if self._is_return_deadline_expired():
            return self._open_return_deadline_confirmation()

        return self._create_return_picking_record()

    def action_create_return_picking_after_deadline_confirmation(self):
        """Wird vom Fristdialog aufgerufen, wenn der Benutzer die Überschreitung bestätigt."""
        self.ensure_one()
        return self._create_return_picking_record()


class RmaOrderLine(models.TransientModel):
    """Temporäre Positionszeile des Erstellungswizards."""

    _name = 'rma.order.line'
    _description = 'RMA Management Erstellungsposition'

    wizard_id = fields.Many2one(
        'rma.order',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Auftragsposition',
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        related='sale_order_line_id.product_id',
        string='Produkt',
        readonly=True,
    )
    product_uom = fields.Many2one(
        'uom.uom',
        related='sale_order_line_id.product_uom_id',
        string='Einheit',
        readonly=True,
    )
    product_uom_qty = fields.Float(
        related='sale_order_line_id.product_uom_qty',
        string='Bestellt',
        readonly=True,
    )
    returned_qty = fields.Float(
        string='Bereits retourniert',
        compute='_compute_return_quantities',
        readonly=True,
    )
    available_qty = fields.Float(
        string='Noch möglich',
        compute='_compute_return_quantities',
        readonly=True,
    )
    return_qty = fields.Float(string='Rückgabemenge', default=0.0)
    available_serial_lot_ids = fields.Many2many(
        'stock.lot',
        compute='_compute_available_serial_lot_ids',
        string='Verfügbare Seriennummern',
    )
    selected_serial_lot_ids = fields.Many2many(
        'stock.lot',
        string='Ausgewählte Seriennummern',
        domain="[('id', 'in', available_serial_lot_ids)]",
    )
    has_serial_lots = fields.Boolean(
        compute='_compute_available_serial_lot_ids',
        string='Hat Seriennummern',
    )
    selected_serial_count = fields.Integer(
        string='Anzahl Seriennummern',
        compute='_compute_selected_serial_count',
    )

    @api.depends('sale_order_line_id', 'sale_order_line_id.product_uom_qty')
    def _compute_return_quantities(self):
        """Zeigt je Position an, was bereits retourniert wurde und was noch möglich ist."""
        for line in self:
            returned_qty = line._get_already_returned_quantity()
            line.returned_qty = returned_qty
            line.available_qty = max(line.product_uom_qty - returned_qty, 0.0)

    def _get_already_returned_quantity(self):
        """Liest bereits abgeschlossene RMA-Eingänge für diese Verkaufsposition."""
        self.ensure_one()
        return self.env['rma.order.service'].get_already_returned_quantity(
            self.sale_order_line_id,
            self.product_id,
            self.product_uom,
        )

    @api.depends('sale_order_line_id', 'product_id')
    def _compute_available_serial_lot_ids(self):
        """Lädt nur Seriennummern, die ausgeliefert und noch nicht retourniert wurden."""
        for line in self:
            serial_lots = line._get_returnable_serial_lots()
            line.available_serial_lot_ids = serial_lots
            line.has_serial_lots = bool(serial_lots)

    @api.depends('selected_serial_lot_ids')
    def _compute_selected_serial_count(self):
        """Kleine Zählhilfe für die Listenansicht."""
        for line in self:
            line.selected_serial_count = len(line.selected_serial_lot_ids)

    @api.onchange('selected_serial_lot_ids')
    def _onchange_selected_serial_lot_ids(self):
        """Seriennummern zählen automatisch als Rückgabemenge."""
        for line in self:
            if line.has_serial_lots:
                line.return_qty = len(line.selected_serial_lot_ids)

    def _get_returnable_serial_lots(self):
        """Ermittelt die auswählbaren Seriennummern aus erledigten Lieferungen."""
        self.ensure_one()
        if (
            not self._is_rma_serial_tracking_enabled()
            or not self.sale_order_line_id
            or self.product_id.tracking == 'none'
        ):
            return self.env['stock.lot']

        delivered_move_lines = self.sale_order_line_id.move_ids.filtered(
            lambda move: move.state == 'done' and move.picking_id.picking_type_code == 'outgoing'
        ).move_line_ids.filtered(lambda move_line: move_line.lot_id and move_line.quantity > 0)
        delivered_lots = delivered_move_lines.lot_id
        if not delivered_lots:
            return delivered_lots

        returned_lots = self.env['rma.order.service'].get_already_returned_lots(
            self.sale_order_line_id,
            self.product_id,
        )
        return delivered_lots - returned_lots

    def _is_rma_serial_tracking_enabled(self):
        """Globale RMA-Option: Seriennummern können für reine Mengenprozesse deaktiviert werden."""
        value = self.env['ir.config_parameter'].sudo().get_param(
            'rma_management.use_serial_numbers',
            'True',
        )
        return value not in ('False', 'false', '0', '', False)

    def action_open_serial_selection(self):
        """Öffnet die Seriennummernauswahl für eine einzelne RMA-Position."""
        self.ensure_one()
        if not self.available_serial_lot_ids:
            raise UserError(_('Für diese Position sind keine Seriennummern im Lieferbeleg hinterlegt.'))

        return {
            'name': _('Seriennummern auswählen'),
            'type': 'ir.actions.act_window',
            'res_model': 'rma.order.line',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('rma_management.view_rma_order_line_serial_selection_form').id,
            'target': 'new',
        }

    def action_apply_serial_selection(self):
        """Übernimmt die Auswahl und synchronisiert die Menge."""
        for line in self:
            line.return_qty = len(line.selected_serial_lot_ids)
        return {'type': 'ir.actions.act_window_close'}

    @api.constrains('return_qty')
    def _check_return_qty_limit(self):
        """Odoo-Constraint für negative oder zu hohe Rückgabemengen."""
        for line in self:
            line._validate_return_quantity()

    def _validate_return_quantity(self):
        """Prüft Mengenlimit und Seriennummern-Vollständigkeit."""
        self.ensure_one()

        if self.return_qty < 0:
            raise ValidationError(_('Die Rückgabemenge darf nicht negativ sein.'))

        if self.has_serial_lots and self.return_qty:
            selected_serial_count = len(self.selected_serial_lot_ids)
            precision_rounding = self.product_uom.rounding if self.product_uom else 0.01
            if float_compare(self.return_qty, selected_serial_count, precision_rounding=precision_rounding) != 0:
                raise ValidationError(_(
                    "Für %(product)s müssen die Seriennummern ausgewählt werden.\n\n"
                    "Rückgabemenge: %(quantity)s | Ausgewählte Seriennummern: %(serial_count)s"
                ) % {
                    'product': self.product_id.display_name,
                    'quantity': self.return_qty,
                    'serial_count': selected_serial_count,
                })

        precision_rounding = self.product_uom.rounding if self.product_uom else 0.01
        if float_compare(self.return_qty, self.available_qty, precision_rounding=precision_rounding) > 0:
            raise ValidationError(_(
                "Position: %(product)s\n"
                "Bestellt: %(ordered)s | Bereits retourniert: %(returned)s\n"
                "Du versuchst: %(current)s | Max. noch möglich: %(available)s"
            ) % {
                'product': self.product_id.display_name,
                'ordered': self.product_uom_qty,
                'returned': self.returned_qty,
                'current': self.return_qty,
                'available': self.available_qty,
            })


class SaleOrder(models.Model):
    """Erweitert die Auftragssuche um Rechnungsnummern für schnelleres Finden."""

    _inherit = 'sale.order'

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        ids = super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
        if name and operator in ('ilike', 'like', '=', '=like', '=ilike'):
            invoice_orders = self.search(
                (domain or []) + [('invoice_ids.name', operator, name)],
                limit=limit,
            )
            extra_ids = [invoice_id for invoice_id in invoice_orders.ids if invoice_id not in ids]
            ids = ids + extra_ids
        return ids[:limit] if limit else ids


class ResPartner(models.Model):
    """Kundenbezogene Standardfrist für Rückgaben."""

    _inherit = 'res.partner'

    rma_return_deadline_days = fields.Integer(
        string='Rückgabefrist (Tage)',
        default=lambda self: int(self.env['ir.config_parameter'].sudo().get_param(
            'rma_management.default_return_deadline_days',
            14,
        )),
    )


class RmaDeadlineConfirmation(models.TransientModel):
    """Modaler Bestätigungsdialog für überschrittene Rückgabefristen."""

    _name = 'rma.deadline.confirmation'
    _description = 'RMA Management Rückgabefrist Bestätigung'

    rma_id = fields.Many2one(
        'rma.order',
        string='RMA Vorgang',
        required=True,
        ondelete='cascade',
    )
    days_expired = fields.Integer(
        string='Tage abgelaufen',
        readonly=True,
    )
    message_text = fields.Text(
        string='Hinweis',
        compute='_compute_message_text',
        readonly=True,
    )

    @api.depends('days_expired')
    def _compute_message_text(self):
        """Formatiert den Hinweistext im Dialog."""
        for record in self:
            record.message_text = (
                f"Die Rückgabefrist ist seit {record.days_expired} Tagen abgelaufen.\n"
                f"Soll trotzdem ein RMA-Eingang erstellt werden?"
            )

    def action_confirm_create_rma(self):
        """Bestätigung protokollieren und RMA-Erstellung fortsetzen."""
        self.ensure_one()
        self.env['rma.audit.log'].log_event(
            'deadline_confirmed',
            _('Fristüberschreitung für %(order)s bestätigt') % {
                'order': self.rma_id.sale_order_id.name,
            },
            sale_order=self.rma_id.sale_order_id,
            details=_('Die Rückgabefrist war seit %(days)s Tagen abgelaufen.') % {
                'days': self.days_expired,
            },
        )
        return self.rma_id.action_create_return_picking_after_deadline_confirmation()

    def action_cancel_create_rma(self):
        """Bricht nur den Dialog ab; es wird kein RMA-Eingang erzeugt."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
