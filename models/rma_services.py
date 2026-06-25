import logging

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class RmaOrderService(models.AbstractModel):
    """Service-Schicht für dauerhafte Aktionen aus dem RMA-Erstellungswizard."""

    _name = 'rma.order.service'
    _description = 'RMA Management Erstellungsservice'

    def _raise_unexpected_error(self, message, error):
        """Loggt technische Fehler und zeigt im UI eine fachliche Meldung."""
        _logger.exception("%s", message)
        raise UserError(_(
            "%(message)s\n\nBitte prüfe die RMA-Konfiguration oder kontaktiere einen Administrator."
        ) % {
            'message': message,
        }) from error

    def _get_rma_stock_configuration(self):
        return self.env['rma.stock.configuration']

    def _get_audit_log(self):
        return self.env['rma.audit.log']

    def _get_valid_return_lines(self, wizard):
        """Filtert leere Zeilen heraus und validiert die gewünschten Rückgabemengen."""
        wizard.ensure_one()
        valid_lines = wizard.line_ids.filtered(lambda line: line.return_qty > 0 and line.product_id.type != 'service')

        if not valid_lines:
            raise ValidationError(_('Keine gültigen Belegpositionen mit Rückgabemenge gefunden.'))

        for line in valid_lines:
            line._validate_return_quantity()

        return valid_lines

    @api.model
    def create_return_picking(self, wizard):
        """Erzeugt den echten RMA-Eingangsbeleg aus dem temporären Wizard.

        Ab hier entstehen dauerhafte Odoo-Daten: stock.picking, stock.move und
        optional stock.move.line je ausgewählter Seriennummer.
        """
        wizard.ensure_one()

        try:
            with self.env.cr.savepoint():
                picking_type = self._get_rma_stock_configuration()._get_picking_type('incoming')
                valid_lines = self._get_valid_return_lines(wizard)

                picking = self.env['stock.picking'].create({
                    'picking_type_id': picking_type.id,
                    'partner_id': wizard.partner_id.id,
                    'origin': f"RMA: {wizard.sale_order_id.name}",
                    'location_id': picking_type.default_location_src_id.id or wizard.partner_id.property_stock_customer.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    'rma_reason_id': wizard.rma_reason_id.id,
                    'rma_sale_order_id': wizard.sale_order_id.id,
                })

                move_model = self.env['stock.move']
                moves_by_line = {}
                for line in valid_lines:
                    # sale_line_id wird nur gesetzt, wenn die verwendete Odoo-Version das Feld kennt.
                    move_values = {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.return_qty,
                        'product_uom': line.product_uom.id,
                        'picking_id': picking.id,
                        'location_id': picking.location_id.id,
                        'location_dest_id': picking.location_dest_id.id,
                        'description_picking': line.product_id.display_name,
                    }
                    if 'sale_line_id' in move_model._fields:
                        move_values['sale_line_id'] = line.sale_order_line_id.id
                    moves_by_line[line] = move_model.create(move_values)

                picking.action_confirm()
                # Bei Seriennummern ersetzen wir die automatisch erzeugten Move-Lines
                # durch exakte Zeilen je ausgewählter Seriennummer.
                self._create_selected_serial_move_lines(moves_by_line)

                for original_picking in wizard.sale_order_id.picking_ids:
                    if original_picking.picking_type_code == 'outgoing':
                        original_picking.rma_receipt_created = True

                self._get_audit_log().log_event(
                    'receipt_created',
                    _('RMA-Eingang %(picking)s aus %(order)s erstellt') % {
                        'picking': picking.name,
                        'order': wizard.sale_order_id.name,
                    },
                    sale_order=wizard.sale_order_id,
                    picking=picking,
                    details=self._get_audit_log()._build_quantity_details(valid_lines),
                )

                return picking
        except (UserError, ValidationError):
            raise
        except Exception as error:
            self._raise_unexpected_error(_('Der RMA-Eingang konnte nicht erstellt werden.'), error)

    @api.model
    def get_already_returned_quantity(self, sale_order_line, product, product_uom):
        """Summiert erledigte RMA-Eingänge, damit nicht mehr retourniert wird als verkauft."""
        if not sale_order_line:
            return 0.0

        move_model = self.env['stock.move']
        order = sale_order_line.order_id
        picking_type = self._get_rma_stock_configuration()._get_picking_type('incoming')
        move_domain = [
            ('picking_id.picking_type_id', '=', picking_type.id),
            ('state', '=', 'done'),
            ('product_id', '=', product.id),
        ]

        moves = move_model.browse()
        if 'sale_line_id' in move_model._fields:
            # Primär wird über sale_line_id gezählt. Der Origin-Fallback deckt ältere
            # oder manuell erzeugte Bewegungen ohne Verkaufspositionsverweis ab.
            moves |= move_model.search(move_domain + [('sale_line_id', '=', sale_order_line.id)])
            order_product_lines = order.order_line.filtered(
                lambda order_line: (
                    not order_line.display_type
                    and order_line.product_id == product
                    and order_line.product_id.type != 'service'
                )
            )
            if len(order_product_lines) == 1:
                moves |= move_model.search(move_domain + [
                    ('sale_line_id', '=', False),
                    ('picking_id.origin', '=', f"RMA: {order.name}"),
                ])
        else:
            order_product_lines = order.order_line.filtered(
                lambda order_line: (
                    not order_line.display_type
                    and order_line.product_id == product
                    and order_line.product_id.type != 'service'
                )
            )
            if len(order_product_lines) == 1:
                moves |= move_model.search(move_domain + [('picking_id.origin', '=', f"RMA: {order.name}")])

        returned_qty = 0.0
        for move in moves:
            returned_qty += move.product_uom._compute_quantity(move.product_uom_qty, product_uom)
        return returned_qty

    @api.model
    def get_already_returned_lots(self, sale_order_line, product):
        """Findet bereits retournierte Seriennummern per Move-Line-Domain."""
        if not sale_order_line or product.tracking == 'none':
            return self.env['stock.lot']

        move_model = self.env['stock.move']
        picking_type = self._get_rma_stock_configuration()._get_picking_type('incoming')
        move_line_domain = [
            ('picking_id.picking_type_id', '=', picking_type.id),
            ('picking_id.state', '!=', 'cancel'),
            ('product_id', '=', product.id),
            ('lot_id', '!=', False),
        ]
        if 'sale_line_id' in move_model._fields:
            move_line_domain.append(('move_id.sale_line_id', '=', sale_order_line.id))
        else:
            move_line_domain.append(('picking_id.origin', '=', f"RMA: {sale_order_line.order_id.name}"))
        return self.env['stock.move.line'].search(move_line_domain).lot_id

    def _create_selected_serial_move_lines(self, moves_by_line):
        """Legt pro gewählter Seriennummer eine konkrete Move-Line im RMA-Eingang an."""
        move_line_model = self.env['stock.move.line']
        for line, move in moves_by_line.items():
            if not line.selected_serial_lot_ids:
                continue

            move.move_line_ids.unlink()
            for serial_lot in line.selected_serial_lot_ids:
                move_line_model.create({
                    'picking_id': move.picking_id.id,
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': 1.0,
                    'lot_id': serial_lot.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })


class RmaSplittingService(models.AbstractModel):
    """Service-Schicht für die dauerhafte Mengenprüfung und Folgebelege."""

    _name = 'rma.splitting.service'
    _description = 'RMA Management Mengenprüfungsservice'

    def _raise_unexpected_error(self, message, error):
        """Loggt technische Fehler und zeigt im UI eine fachliche Meldung."""
        _logger.exception("%s", message)
        raise UserError(_(
            "%(message)s\n\nBitte prüfe die RMA-Konfiguration oder kontaktiere einen Administrator."
        ) % {
            'message': message,
        }) from error

    def _get_rma_stock_configuration(self):
        return self.env['rma.stock.configuration']

    def _get_audit_log(self):
        return self.env['rma.audit.log']

    def _validate_rma_and_quantities(self, wizard):
        """Sammelt die fachlichen Vorbedingungen für die Mengenprüfung."""
        wizard.ensure_one()

        if not wizard.rma_order_id:
            raise ValidationError(_('Bitte waehle zuerst einen RMA Beleg aus.'))

        if wizard.rma_order_id.rma_processing_done:
            raise ValidationError(_('Dieser RMA-Eingang wurde bereits vollstaendig verarbeitet und kann nicht erneut durchgefuehrt werden.'))

        if not wizard.line_ids:
            raise ValidationError(_('Der ausgewaehlte RMA Beleg enthaelt keine Positionen.'))

        for line in wizard.line_ids:
            line._validate_checked_quantities()

    def _create_follow_up_pickings(self, wizard):
        """Erzeugt je Qualitätsklasse einen Folgebeleg für A-, B- oder C-Ware."""
        wizard.ensure_one()
        created_pickings = self.env['stock.picking']
        stock_configuration = self._get_rma_stock_configuration()

        picking_type_by_field = {
            'rma_qty_a': stock_configuration._get_warehouse_receipt_type(),
            'rma_qty_b': stock_configuration._get_picking_type('b_goods'),
            'rma_qty_c': stock_configuration._get_picking_type('scrap'),
        }
        section_title_by_field = {
            'rma_qty_a': _('A-Ware'),
            'rma_qty_b': _('B-Ware'),
            'rma_qty_c': _('C-Ware'),
        }
        quality_class_by_field = {
            'rma_qty_a': 'a',
            'rma_qty_b': 'b',
            'rma_qty_c': 'c',
        }

        for field_name in ['rma_qty_a', 'rma_qty_b', 'rma_qty_c']:
            section_title = section_title_by_field[field_name]
            quality_class = quality_class_by_field[field_name]

            lines_with_quantity = wizard.line_ids.filtered(lambda line: line[field_name] > 0)
            if not lines_with_quantity:
                continue

            picking_type = picking_type_by_field[field_name]
            serial_moves = []

            # Jeder Qualitätsbereich erhält einen eigenen Zielbeleg, damit Lager,
            # Schrott und wiederverkaufsfähige Ware sauber getrennt bleiben.
            new_picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'partner_id': wizard.partner_id.id,
                'origin': f"{wizard.rma_order_id.name} - {section_title}",
                'location_id': wizard.rma_order_id.location_dest_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'rma_reason_id': wizard.rma_order_id.rma_reason_id.id,
                'rma_sale_order_id': wizard.rma_order_id.rma_sale_order_id.id,
            })

            for line in lines_with_quantity:
                move = line.stock_move_id
                quantity_to_move = line[field_name]
                new_move = self.env['stock.move'].create({
                    'product_id': move.product_id.id,
                    'product_uom_qty': quantity_to_move,
                    'product_uom': move.product_uom.id,
                    'picking_id': new_picking.id,
                    'partner_id': wizard.partner_id.id,
                    'location_id': new_picking.location_id.id,
                    'location_dest_id': new_picking.location_dest_id.id,
                    'description_picking': move.description_picking or move.product_id.display_name,
                    'origin': wizard.rma_order_id.name,
                })
                serial_lots = line.serial_quality_line_ids.filtered(
                    lambda serial_line: serial_line.quality_class == quality_class
                ).lot_id
                if serial_lots:
                    # Seriennummern werden erst nach action_confirm geschrieben,
                    # damit Odoo die Bewegungen korrekt vorbereitet.
                    serial_moves.append((new_move, serial_lots, quality_class))

            new_picking.action_confirm()
            self._create_quality_serial_move_lines(serial_moves)
            created_pickings |= new_picking

        if not created_pickings:
            raise ValidationError(_('Es wurde keine Ware fuer A-, B- oder C-Ware eingetragen.'))

        return created_pickings

    def _create_quality_serial_move_lines(self, serial_moves):
        """Überträgt geprüfte Seriennummern inklusive RMA-Q-Klasse auf Folgebelege."""
        move_line_model = self.env['stock.move.line']
        for move, serial_lots, quality_class in serial_moves:
            move.move_line_ids.unlink()
            for serial_lot in serial_lots:
                move_line_model.create({
                    'picking_id': move.picking_id.id,
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': 1.0,
                    'lot_id': serial_lot.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'rma_quality_class': quality_class,
                })

    def _prepare_exchange(self, wizard):
        """Bereitet eine textuelle Übersicht für spätere Umtauschbearbeitung vor."""
        wizard.ensure_one()
        return [
            '%s: %s' % (line.product_id.display_name, line.rma_qty_return)
            for line in wizard.line_ids
            if line.rma_qty_return > 0
        ]

    def _prepare_refund(self, wizard):
        """Bereitet eine textuelle Übersicht für spätere Rückerstattung vor."""
        wizard.ensure_one()
        return [
            '%s: %s' % (line.product_id.display_name, line.rma_qty_refund)
            for line in wizard.line_ids
            if line.rma_qty_refund > 0
        ]

    def _write_note_and_mark_done(self, wizard):
        """Schreibt das Prüfungsergebnis in den RMA-Beleg und setzt die RMA-Flags."""
        wizard.ensure_one()
        note_sections = []
        section_title_by_field = {
            'rma_qty_a': _('A-Ware'),
            'rma_qty_b': _('B-Ware'),
            'rma_qty_c': _('C-Ware'),
        }

        for field_name in ['rma_qty_a', 'rma_qty_b', 'rma_qty_c']:
            section_title = section_title_by_field[field_name]

            section_lines = [
                self._format_quality_note_line(line, field_name)
                for line in wizard.line_ids
                if line[field_name] > 0
            ]

            if section_lines:
                note_sections.append(section_title + "\n" + "\n".join(section_lines))

        exchange_lines = self._prepare_exchange(wizard)
        if exchange_lines:
            note_sections.append(_('Umtausch vorbereitet') + "\n" + "\n".join(exchange_lines))

        refund_lines = self._prepare_refund(wizard)
        if refund_lines:
            note_sections.append(_('Rueckerstattung vorbereitet') + "\n" + "\n".join(refund_lines))

        if note_sections:
            new_note_text = "\n\n".join(note_sections)
            old_note_text = wizard.rma_order_id.note or ''
            wizard.rma_order_id.note = old_note_text + "\n\n" + new_note_text if old_note_text else new_note_text

        wizard.rma_order_id.write({
            'rma_split_done': True,
            'rma_exchange_prepared': bool(exchange_lines),
            'rma_refund_prepared': bool(refund_lines),
            'rma_processing_done': True,
        })

    def _create_bware_helpdesk_tickets(self, wizard, created_pickings):
        """Erzeugt Helpdesk-QS-Tickets ausschließlich für B-Ware-Folgebelege."""
        b_goods_type = self._get_rma_stock_configuration()._get_picking_type('b_goods')
        bware_pickings = created_pickings.filtered(lambda picking: picking.picking_type_id == b_goods_type)
        tickets = self.env['helpdesk.ticket']
        for bware_picking in bware_pickings:
            tickets |= self.env['helpdesk.ticket']._create_rma_bware_tickets_from_picking(
                bware_picking,
                wizard.rma_order_id,
            )
        return tickets

    def _format_quality_note_line(self, line, field_name):
        """Formatiert eine Prüfposition für das interne Notizfeld des Belegs."""
        quality_class_by_field = {
            'rma_qty_a': 'a',
            'rma_qty_b': 'b',
            'rma_qty_c': 'c',
        }
        serial_lots = line.serial_quality_line_ids.filtered(
            lambda serial_line: serial_line.quality_class == quality_class_by_field[field_name]
        ).lot_id
        if serial_lots:
            return '%s: %s (%s)' % (
                line.product_id.display_name,
                line[field_name],
                ', '.join(serial_lots.mapped('name')),
            )
        return '%s: %s' % (line.product_id.display_name, line[field_name])

    def _complete_rma_receipt(self, wizard):
        """Validiert/erledigt den ursprünglichen RMA-Eingang nach der Prüfung."""
        wizard.ensure_one()

        if wizard.rma_order_id.state == 'done':
            return

        split_line_by_move = {
            line.stock_move_id.id: line
            for line in wizard.line_ids
        }

        for move in wizard.rma_order_id.move_ids:
            split_line = split_line_by_move.get(move.id)
            if split_line and split_line.serial_quality_line_ids:
                # Bei Seriennummern erhält jede Move-Line ihre geprüfte Q-Klasse.
                split_line._sync_serial_quality_quantities()
                quality_by_lot_id = {
                    serial_line.lot_id.id: serial_line.quality_class
                    for serial_line in split_line.serial_quality_line_ids
                }
                for move_line in move.move_line_ids.filtered('lot_id'):
                    move_line.write({
                        'quantity': 1.0,
                        'rma_quality_class': quality_by_lot_id.get(move_line.lot_id.id),
                    })
                move.picked = True
                continue

            move_line = move.move_line_ids[:1]

            if move_line:
                # Mengenware braucht nur eine Move-Line mit der geprüften Gesamtmenge.
                move_line.quantity = move.product_uom_qty
            else:
                self.env['stock.move.line'].create({
                    'picking_id': wizard.rma_order_id.id,
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': move.product_uom_qty,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })

            move.picked = True

        wizard.rma_order_id._action_done()

    @api.model
    def execute_split(self, wizard):
        """Führt die komplette Mengenprüfung transaktional aus."""
        wizard.ensure_one()

        try:
            with self.env.cr.savepoint():
                self._validate_rma_and_quantities(wizard)
                created_pickings = self._create_follow_up_pickings(wizard)
                self._attach_inspection_files(wizard, created_pickings)
                self._create_bware_helpdesk_tickets(wizard, created_pickings)
                self._write_note_and_mark_done(wizard)
                self._complete_rma_receipt(wizard)
                self._get_audit_log().log_event(
                    'split_completed',
                    _('Mengenprüfung für %(picking)s abgeschlossen') % {
                        'picking': wizard.rma_order_id.name,
                    },
                    picking=wizard.rma_order_id,
                    generated_pickings=created_pickings,
                    details=self._prepare_split_audit_details(wizard, created_pickings),
                    attachment_ids=wizard.rma_attachment_ids.ids,
                )
                return created_pickings
        except (UserError, ValidationError):
            raise
        except Exception as error:
            self._raise_unexpected_error(_('Die Mengenprüfung konnte nicht durchgeführt werden.'), error)

    def _prepare_split_audit_details(self, wizard, created_pickings):
        """Erzeugt den lesbaren Audit-Text für Chatter und Audit-Liste."""
        detail_lines = []
        for line in wizard.line_ids:
            serial_details = line.serial_quality_line_ids.filtered('quality_class')
            if serial_details:
                quality_labels = dict(serial_details._fields['quality_class'].selection)
                serial_text = ', '.join(
                    '%s=%s' % (serial_line.lot_id.name, quality_labels.get(serial_line.quality_class))
                    for serial_line in serial_details
                )
            else:
                serial_text = '-'
            detail_lines.append(
                _('%(product)s: A=%(a)s, B=%(b)s, C=%(c)s, Umtausch=%(exchange)s, Rückerstattung=%(refund)s, Serien=%(serials)s') % {
                    'product': line.product_id.display_name,
                    'a': line.rma_qty_a,
                    'b': line.rma_qty_b,
                    'c': line.rma_qty_c,
                    'exchange': line.rma_qty_return,
                    'refund': line.rma_qty_refund,
                    'serials': serial_text,
                }
            )
        if created_pickings:
            detail_lines.append('')
            detail_lines.append(_('Erzeugte Belege: %(pickings)s') % {
                'pickings': ', '.join(created_pickings.mapped('name')),
            })
        return '\n'.join(detail_lines)

    def _attach_inspection_files(self, wizard, created_pickings):
        """Hängt Prüf-Fotos an RMA-Eingang und Folgebelege an."""
        attachments = wizard.rma_attachment_ids
        if not attachments:
            return

        attachments.sudo().write({
            'res_model': 'stock.picking',
            'res_id': wizard.rma_order_id.id,
        })
        wizard.rma_order_id.rma_attachment_ids = [(4, attachment.id) for attachment in attachments]
        for picking in created_pickings:
            picking.rma_attachment_ids = [(4, attachment.id) for attachment in attachments]
