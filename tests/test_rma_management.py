from datetime import timedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestRmaManagement(TransactionCase):
    """Regressionstests für RMA-Erstellung, Prüfung, Seriennummern und Audit."""

    @classmethod
    def setUpClass(cls):
        """Gemeinsame Stammdaten für alle Tests vorbereiten."""
        super().setUpClass()
        cls.config = cls.env['rma.stock.configuration']
        cls.config._ensure_rma_stock_configuration()
        cls.reason_defect = cls.env.ref('rma_management.rma_reason_defect')
        cls.reason_transport_damage = cls.env.ref('rma_management.rma_reason_transport_damage')
        cls.reason_goodwill = cls.env.ref('rma_management.rma_reason_goodwill')
        cls.reason_warranty = cls.env.ref('rma_management.rma_reason_warranty')
        cls.partner = cls.env['res.partner'].create({
            'name': 'RMA Testkunde',
            'rma_return_deadline_days': 14,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'RMA Testprodukt',
            'is_storable': True,
            'list_price': 100.0,
        })

    def _create_sale_order(self, quantity=5.0, product=None):
        """Hilfsmethode: Verkaufsauftrag mit genau einer echten Produktposition."""
        product = product or self.product
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': product.id,
                'product_uom_qty': quantity,
                'price_unit': product.list_price,
            })],
        })
        sale_order.action_confirm()
        return sale_order, sale_order.order_line.filtered(lambda line: not line.display_type)[:1]

    def _deliver_serial_sale_order(self, sale_order, serial_lots):
        """Hilfsmethode: Seriennummern im zugehörigen Lieferbeleg ausliefern."""
        picking = sale_order.picking_ids.filtered(lambda picking: picking.picking_type_code == 'outgoing')[:1]
        move = picking.move_ids.filtered(lambda move: move.product_id == serial_lots[:1].product_id)[:1]
        move.move_line_ids.unlink()
        for serial_lot in serial_lots:
            self.env['stock.move.line'].create({
                'picking_id': picking.id,
                'move_id': move.id,
                'product_id': move.product_id.id,
                'product_uom_id': move.product_uom.id,
                'quantity': 1.0,
                'lot_id': serial_lot.id,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
            })
        move.picked = True
        picking._action_done()
        return picking

    def _create_rma_incoming_picking(self, sale_order_line, quantity, done=True):
        """Hilfsmethode: bestehenden RMA-Eingang für Mengenberechnungen erzeugen."""
        picking_type = self.config._get_picking_type('incoming')
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': sale_order_line.order_id.partner_id.id,
            'origin': f"RMA: {sale_order_line.order_id.name}",
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'rma_reason_id': self.reason_defect.id,
            'rma_sale_order_id': sale_order_line.order_id.id,
        })
        move_values = {
            'product_id': sale_order_line.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': sale_order_line.product_uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'description_picking': sale_order_line.product_id.display_name,
        }
        if 'sale_line_id' in self.env['stock.move']._fields:
            move_values['sale_line_id'] = sale_order_line.id
        self.env['stock.move'].create(move_values)
        picking.action_confirm()

        if done:
            for move in picking.move_ids:
                self.env['stock.move.line'].create({
                    'picking_id': picking.id,
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': move.product_uom_qty,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })
                move.picked = True
            picking._action_done()

        return picking

    def test_stock_configuration_creates_expected_records(self):
        """Die automatische Lagerkonfiguration muss alle RMA-Orte und Typen bereitstellen."""
        self.config._ensure_rma_stock_configuration()

        rma_location = self.env.ref('rma_management.stock_location_rma')
        b_goods_location = self.env.ref('rma_management.stock_location_rma_b_goods')
        scrap_location = self.env.ref('rma_management.stock_location_rma_scrap')
        incoming_type = self.config._get_picking_type('incoming')
        b_goods_type = self.config._get_picking_type('b_goods')
        scrap_type = self.config._get_picking_type('scrap')

        self.assertEqual(incoming_type.default_location_dest_id, rma_location)
        self.assertEqual(b_goods_type.default_location_src_id, rma_location)
        self.assertEqual(b_goods_type.default_location_dest_id, b_goods_location)
        self.assertEqual(scrap_type.default_location_src_id, rma_location)
        self.assertEqual(scrap_type.default_location_dest_id, scrap_location)

    def test_missing_sale_line_reference_is_filled_on_create(self):
        """One2many-Zeilen ohne sale_order_line_id werden serverseitig repariert."""
        sale_order, sale_order_line = self._create_sale_order(quantity=3.0)

        wizard = self.env['rma.order'].create({
            'sale_order_id': sale_order.id,
            'rma_reason_id': self.reason_defect.id,
            'line_ids': [Command.create({'return_qty': 1.0})],
        })

        self.assertEqual(wizard.line_ids.sale_order_line_id, sale_order_line)

    def test_create_return_picking_uses_configured_rma_type(self):
        """RMA-Erstellung nutzt den konfigurierten Eingangstyp und schreibt Audit."""
        sale_order, sale_order_line = self._create_sale_order(quantity=4.0)
        wizard = self.env['rma.order'].create({
            'sale_order_id': sale_order.id,
            'rma_reason_id': self.reason_transport_damage.id,
            'line_ids': [Command.create({
                'sale_order_line_id': sale_order_line.id,
                'return_qty': 2.0,
            })],
        })

        action = wizard.action_create_return_picking()
        picking = self.env['stock.picking'].search([
            ('origin', '=', f"RMA: {sale_order.name}"),
        ], order='id desc', limit=1)

        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(picking.picking_type_id, self.config._get_picking_type('incoming'))
        self.assertEqual(picking.rma_reason_id, self.reason_transport_damage)
        self.assertEqual(picking.rma_sale_order_id, sale_order)
        self.assertEqual(picking.rma_status, 'open')
        self.assertEqual(picking.move_ids.product_uom_qty, 2.0)
        if 'sale_line_id' in self.env['stock.move']._fields:
            self.assertEqual(picking.move_ids.sale_line_id, sale_order_line)
        self.assertTrue(sale_order.picking_ids.filtered(lambda picking: picking.picking_type_code == 'outgoing').rma_receipt_created)

        audit_log = self.env['rma.audit.log'].search([
            ('action', '=', 'receipt_created'),
            ('sale_order_id', '=', sale_order.id),
            ('picking_id', '=', picking.id),
        ], limit=1)
        self.assertTrue(audit_log)
        self.assertTrue(picking.message_ids.filtered(lambda message: 'RMA Audit' in message.body))
        self.assertTrue(sale_order.message_ids.filtered(lambda message: 'RMA Audit' in message.body))

    def test_returned_quantity_counts_done_rma_moves_only(self):
        """Nur erledigte RMA-Eingänge reduzieren die noch mögliche Rückgabemenge."""
        sale_order, sale_order_line = self._create_sale_order(quantity=5.0)
        self._create_rma_incoming_picking(sale_order_line, 2.0, done=True)
        self._create_rma_incoming_picking(sale_order_line, 3.0, done=False)

        wizard = self.env['rma.order'].create({
            'sale_order_id': sale_order.id,
            'rma_reason_id': self.reason_defect.id,
            'line_ids': [Command.create({'sale_order_line_id': sale_order_line.id})],
        })
        line = wizard.line_ids[:1]

        self.assertEqual(line.returned_qty, 2.0)
        self.assertEqual(line.available_qty, 3.0)

    def test_split_creates_follow_up_pickings_and_marks_receipt_done(self):
        """Mengenprüfung erzeugt Folgebelege, hängt Dateien an und erledigt den RMA-Eingang."""
        sale_order, sale_order_line = self._create_sale_order(quantity=6.0)
        wizard = self.env['rma.order'].create({
            'sale_order_id': sale_order.id,
            'rma_reason_id': self.reason_warranty.id,
            'line_ids': [Command.create({
                'sale_order_line_id': sale_order_line.id,
                'return_qty': 6.0,
            })],
        })
        wizard.action_create_return_picking()
        rma_picking = self.env['stock.picking'].search([
            ('origin', '=', f"RMA: {sale_order.name}"),
        ], order='id desc', limit=1)

        split = self.env['rma.splitting'].create({'rma_order_id': rma_picking.id})
        split.line_ids[:1].write({
            'rma_qty_a': 2.0,
            'rma_qty_b': 3.0,
            'rma_qty_c': 1.0,
            'rma_qty_return': 1.0,
            'rma_qty_refund': 1.0,
        })
        attachment = self.env['ir.attachment'].create({
            'name': 'rma-prueffoto.png',
            'type': 'binary',
            'datas': b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/ax7z6kAAAAASUVORK5CYII=',
            'mimetype': 'image/png',
        })
        split.rma_attachment_ids = [Command.link(attachment.id)]
        action = split.action_execute_split()

        created_pickings = self.env['stock.picking'].search(action['domain'])
        self.assertEqual(rma_picking.state, 'done')
        self.assertTrue(rma_picking.rma_processing_done)
        self.assertEqual(rma_picking.rma_reason_id, self.reason_warranty)
        self.assertEqual(rma_picking.rma_status, 'done')
        self.assertIn(attachment, rma_picking.rma_attachment_ids)
        self.assertEqual(len(created_pickings), 3)
        self.assertIn(self.config._get_warehouse_receipt_type(), created_pickings.picking_type_id)
        self.assertIn(self.config._get_picking_type('b_goods'), created_pickings.picking_type_id)
        self.assertIn(self.config._get_picking_type('scrap'), created_pickings.picking_type_id)
        for picking in created_pickings:
            self.assertEqual(picking.rma_reason_id, self.reason_warranty)
            self.assertEqual(picking.rma_sale_order_id, sale_order)
            self.assertIn(attachment, picking.rma_attachment_ids)

        audit_log = self.env['rma.audit.log'].search([
            ('action', '=', 'split_completed'),
            ('picking_id', '=', rma_picking.id),
        ], limit=1)
        self.assertEqual(audit_log.generated_picking_ids, created_pickings)
        self.assertTrue(rma_picking.message_ids.filtered(lambda message: attachment in message.attachment_ids))
        for picking in created_pickings:
            self.assertTrue(picking.message_ids.filtered(lambda message: 'RMA Audit' in message.body))

    def test_serial_selection_and_quality_classes_are_carried_to_pickings(self):
        """Seriennummern laufen von Auswahl bis Q-Klasse durch alle RMA-Belege."""
        serial_product = self.env['product.product'].create({
            'name': 'RMA Seriengerät',
            'is_storable': True,
            'tracking': 'serial',
            'list_price': 250.0,
        })
        serial_lots = self.env['stock.lot'].create([
            {'name': 'SN-RMA-001', 'product_id': serial_product.id},
            {'name': 'SN-RMA-002', 'product_id': serial_product.id},
            {'name': 'SN-RMA-003', 'product_id': serial_product.id},
        ])
        sale_order, sale_order_line = self._create_sale_order(quantity=3.0, product=serial_product)
        self._deliver_serial_sale_order(sale_order, serial_lots)

        wizard = self.env['rma.order'].create({
            'sale_order_id': sale_order.id,
            'rma_reason_id': self.reason_defect.id,
            'line_ids': [Command.create({
                'sale_order_line_id': sale_order_line.id,
            })],
        })
        line = wizard.line_ids[:1]
        selected_lots = serial_lots[:2]
        self.assertEqual(line.available_serial_lot_ids, serial_lots)

        line.selected_serial_lot_ids = [Command.set(selected_lots.ids)]
        line.action_apply_serial_selection()
        self.assertEqual(line.return_qty, 2.0)

        wizard.action_create_return_picking()
        rma_picking = self.env['stock.picking'].search([
            ('origin', '=', f"RMA: {sale_order.name}"),
        ], order='id desc', limit=1)
        self.assertEqual(rma_picking.move_line_ids.lot_id, selected_lots)
        self.assertEqual(rma_picking.move_ids.product_uom_qty, 2.0)

        split = self.env['rma.splitting'].create({'rma_order_id': rma_picking.id})
        split_line = split.line_ids[:1]
        self.assertEqual(split_line.serial_quality_line_ids.lot_id, selected_lots)
        split_line.serial_quality_line_ids.filtered(lambda serial_line: serial_line.lot_id == selected_lots[0]).quality_class = 'a'
        split_line.serial_quality_line_ids.filtered(lambda serial_line: serial_line.lot_id == selected_lots[1]).quality_class = 'c'
        split_line.action_apply_serial_quality()
        self.assertEqual(split_line.rma_qty_a, 1.0)
        self.assertEqual(split_line.rma_qty_b, 0.0)
        self.assertEqual(split_line.rma_qty_c, 1.0)

        action = split.action_execute_split()
        created_pickings = self.env['stock.picking'].search(action['domain'])
        self.assertEqual(len(created_pickings), 2)

        self.assertEqual(
            rma_picking.move_line_ids.filtered(lambda move_line: move_line.lot_id == selected_lots[0]).rma_quality_class,
            'a',
        )
        self.assertEqual(
            rma_picking.move_line_ids.filtered(lambda move_line: move_line.lot_id == selected_lots[1]).rma_quality_class,
            'c',
        )
        a_picking = created_pickings.filtered(lambda picking: picking.picking_type_id == self.config._get_warehouse_receipt_type())
        c_picking = created_pickings.filtered(lambda picking: picking.picking_type_id == self.config._get_picking_type('scrap'))
        self.assertEqual(a_picking.move_line_ids.lot_id, selected_lots[0])
        self.assertEqual(a_picking.move_line_ids.rma_quality_class, 'a')
        self.assertEqual(c_picking.move_line_ids.lot_id, selected_lots[1])
        self.assertEqual(c_picking.move_line_ids.rma_quality_class, 'c')

    def test_serial_selection_can_be_disabled_for_rma(self):
        """Bei deaktivierter RMA-Serienlogik bleibt der Prozess rein mengenbasiert."""
        self.env['ir.config_parameter'].sudo().set_param(
            'rma_management.use_serial_numbers',
            'False',
        )
        serial_product = self.env['product.product'].create({
            'name': 'RMA Seriengerät ohne RMA-Serienprozess',
            'is_storable': True,
            'tracking': 'serial',
            'list_price': 250.0,
        })
        serial_lot = self.env['stock.lot'].create({
            'name': 'SN-RMA-OFF-001',
            'product_id': serial_product.id,
        })
        sale_order, sale_order_line = self._create_sale_order(quantity=1.0, product=serial_product)
        self._deliver_serial_sale_order(sale_order, serial_lot)

        wizard = self.env['rma.order'].create({
            'sale_order_id': sale_order.id,
            'rma_reason_id': self.reason_defect.id,
            'line_ids': [Command.create({
                'sale_order_line_id': sale_order_line.id,
                'return_qty': 1.0,
            })],
        })
        line = wizard.line_ids[:1]

        self.assertFalse(wizard.has_serial_lots)
        self.assertFalse(line.has_serial_lots)
        self.assertFalse(line.available_serial_lot_ids)
        self.assertEqual(line.return_qty, 1.0)

    def test_deadline_confirmation_is_logged_in_chatter(self):
        """Fristüberschreitungen werden nach Bestätigung im Audit und Chatter sichtbar."""
        sale_order, sale_order_line = self._create_sale_order(quantity=2.0)
        sale_order.date_order = fields.Datetime.now() - timedelta(days=30)
        sale_order.partner_id.rma_return_deadline_days = 1
        wizard = self.env['rma.order'].create({
            'sale_order_id': sale_order.id,
            'rma_reason_id': self.reason_goodwill.id,
            'line_ids': [Command.create({
                'sale_order_line_id': sale_order_line.id,
                'return_qty': 1.0,
            })],
        })

        confirmation_action = wizard.action_create_return_picking()
        confirmation = self.env['rma.deadline.confirmation'].browse(confirmation_action['res_id'])
        confirmation.action_confirm_create_rma()

        audit_log = self.env['rma.audit.log'].search([
            ('action', '=', 'deadline_confirmed'),
            ('sale_order_id', '=', sale_order.id),
        ], limit=1)
        self.assertTrue(audit_log)
        self.assertTrue(sale_order.message_ids.filtered(lambda message: 'Fristüberschreitung' in message.body))

    def test_default_return_deadline_uses_settings_parameter(self):
        """Neue Kunden übernehmen die konfigurierte Standard-Rückgabefrist."""
        self.env['ir.config_parameter'].sudo().set_param(
            'rma_management.default_return_deadline_days',
            '21',
        )

        partner = self.env['res.partner'].create({
            'name': 'RMA Frist Kunde',
        })

        self.assertEqual(partner.rma_return_deadline_days, 21)

    def test_bware_split_creates_helpdesk_ticket_and_decision_picking(self):
        """B-Ware erzeugt genau ein Helpdesk-Ticket je Artikel und bucht die Entscheidung."""
        sale_order, sale_order_line = self._create_sale_order(quantity=4.0)
        wizard = self.env['rma.order'].create({
            'sale_order_id': sale_order.id,
            'rma_reason_id': self.reason_defect.id,
            'line_ids': [Command.create({
                'sale_order_line_id': sale_order_line.id,
                'return_qty': 4.0,
            })],
        })
        wizard.action_create_return_picking()
        rma_picking = self.env['stock.picking'].search([
            ('origin', '=', f"RMA: {sale_order.name}"),
        ], order='id desc', limit=1)

        split = self.env['rma.splitting'].create({'rma_order_id': rma_picking.id})
        split.line_ids[:1].write({'rma_qty_b': 4.0})
        split.action_execute_split()

        bware_picking = self.env['stock.picking'].search([
            ('rma_sale_order_id', '=', sale_order.id),
            ('picking_type_id', '=', self.config._get_picking_type('b_goods').id),
        ], order='id desc', limit=1)
        tickets = self.env['helpdesk.ticket'].search([
            ('rma_is_bware_ticket', '=', True),
            ('rma_bware_picking_id', '=', bware_picking.id),
        ])

        self.assertEqual(len(tickets), 1)
        ticket = tickets[:1]
        self.assertEqual(ticket.rma_product_id, self.product)
        self.assertEqual(ticket.rma_bware_quantity, 4.0)
        self.assertEqual(ticket.rma_reason_id, self.reason_defect)
        self.assertEqual(ticket.rma_sale_order_id, sale_order)

        ticket.action_rma_bware_assign_to_me()
        ticket.action_rma_bware_start()
        ticket.action_rma_bware_finish_qs()
        ticket.rma_decision_note = 'Wiederverkauf nach QS'
        ticket.action_rma_bware_decide_resale()

        self.assertEqual(ticket.rma_decision, 'resale')
        self.assertTrue(ticket.rma_decision_picking_id)
        self.assertEqual(ticket.rma_decision_picking_id.state, 'done')
        self.assertEqual(ticket.rma_decision_picking_id.move_ids.product_uom_qty, 4.0)
