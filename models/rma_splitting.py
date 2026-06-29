from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class RmaSplitting(models.TransientModel):
    """Temporärer Wizard für die Mengen- und Qualitätsprüfung eines RMA-Eingangs."""

    _name = 'rma.splitting'
    _description = 'RMA Management Mengenprüfung'

    @api.depends('rma_order_id.name')
    def _compute_display_name(self):
        for wizard in self:
            wizard.display_name = wizard.rma_order_id.name or _('Neue Mengenprüfung')

    def _get_rma_stock_configuration(self):
        return self.env['rma.stock.configuration']

    def _get_rma_splitting_service(self):
        return self.env['rma.splitting.service']

    def _compute_rma_incoming_picking_type_id(self):
        """Stellt den RMA-Eingangstyp für Domains und View-Logik bereit."""
        picking_type = self._get_rma_stock_configuration()._get_picking_type('incoming')
        for wizard in self:
            wizard.rma_incoming_picking_type_id = picking_type

    @api.model
    def default_get(self, fields_list):
        """Öffnet den Wizard direkt mit dem aktiven RMA-Eingang, wenn möglich."""
        values = super().default_get(fields_list)

        if 'rma_order_id' in fields_list and not values.get('rma_order_id'):
            active_picking_id = self.env.context.get('active_id')
            if active_picking_id:
                picking = self.env['stock.picking'].browse(active_picking_id).exists()
                rma_incoming_type = self._get_rma_stock_configuration()._get_picking_type('incoming')
                if picking and picking.picking_type_id == rma_incoming_type:
                    values['rma_order_id'] = picking.id

        return values

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            self._fill_missing_line_references(values, values.get('rma_order_id'))

        records = super().create(vals_list)
        for record in records:
            if record.rma_order_id and not record.line_ids:
                record._reload_lines_from_picking()
        return records

    def write(self, values):
        if not self:
            return True

        for wizard in self:
            wizard_values = dict(values)
            picking_id = wizard_values.get('rma_order_id') or wizard.rma_order_id.id
            self._fill_missing_line_references(wizard_values, picking_id)
            super(RmaSplitting, wizard).write(wizard_values)
        return True

    @api.model
    def _fill_missing_line_references(self, values, picking_id):
        """Ergänzt fehlende Lagerbewegungs-Verweise in editierbaren One2many-Zeilen."""
        line_commands = values.get('line_ids')
        if not line_commands or not picking_id:
            return

        picking = self.env['stock.picking'].browse(picking_id).exists()
        if not picking:
            return

        selectable_moves = picking.move_ids.filtered_domain([('state', '!=', 'cancel')])
        move_index = 0

        for command in line_commands:
            if not isinstance(command, (list, tuple)) or len(command) < 3 or command[0] != 0:
                continue

            command_values = command[2]
            if not isinstance(command_values, dict):
                continue

            if not command_values.get('stock_move_id') and move_index < len(selectable_moves):
                command_values['stock_move_id'] = selectable_moves[move_index].id
            move_index += 1

    rma_order_id = fields.Many2one(
        'stock.picking',
        string='RMA Beleg',
        required=True,
    )
    rma_incoming_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='RMA Eingang Vorgangstyp',
        compute='_compute_rma_incoming_picking_type_id',
        readonly=True,
    )
    line_ids = fields.One2many(
        'rma.splitting.line',
        'wizard_id',
        string='RMA Positionen',
    )
    has_serial_lots = fields.Boolean(
        string='Hat Seriennummern',
        compute='_compute_has_serial_lots',
    )
    barcode_active = fields.Boolean(
        string='Barcode-Scanner aktivieren',
        default=False,
        store=False,
    )
    barcode_quality_class = fields.Selection(
        [('a', 'A-Ware'), ('b', 'B-Ware'), ('c', 'C-Ware')],
        string='Q-Klasse für Scan',
        store=False,
    )
    barcode_scan = fields.Char(
        string='Seriennummer scannen',
        store=False,
        help='Q-Klasse wählen, dann Barcode scannen — Zuweisung erfolgt sofort.',
    )
    rma_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Prüf-Fotos / Anhänge',
        help='Fotos oder Dokumente zur Zustandsprüfung. Sie werden beim Durchführen am RMA-Beleg gespeichert.',
    )

    partner_id = fields.Many2one('res.partner', related='rma_order_id.partner_id', string='Kunde', readonly=True)
    image_1920 = fields.Image(related='partner_id.image_1920', string='', readonly=True)
    partner_street = fields.Char(related='rma_order_id.partner_id.street', string='Straße', readonly=True)
    partner_plz = fields.Char(related='rma_order_id.partner_id.zip', string='PLZ', readonly=True)
    partner_city = fields.Char(related='rma_order_id.partner_id.city', string='Stadt', readonly=True)
    state_code = fields.Char(related='rma_order_id.partner_id.state_id.code', string='Bundesland', readonly=True)
    vat = fields.Char(related='rma_order_id.partner_id.vat', string='USTD', readonly=True)
    website = fields.Char(related='rma_order_id.partner_id.website', string='Webseite', readonly=True)
    partner_email = fields.Char(related='rma_order_id.partner_id.email', string='E-Mail', readonly=True)
    partner_phone = fields.Char(related='rma_order_id.partner_id.phone', string='Telefon', readonly=True)
    origin = fields.Char(related='rma_order_id.origin', string='Referenz', readonly=True)
    rma_reason_id = fields.Many2one(related='rma_order_id.rma_reason_id', string='RMA-Grund', readonly=True)
    processing_done = fields.Boolean(related='rma_order_id.rma_processing_done', readonly=True)

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        """Weist einer Seriennummer direkt im Hauptformular die Q-Klasse zu — kein Dialog nötig."""
        if not self.barcode_scan:
            return
        scanned = self.barcode_scan.strip()
        self.barcode_scan = False

        if not self.barcode_quality_class:
            return {'warning': {
                'title': _('Q-Klasse fehlt'),
                'message': _('Bitte zuerst eine Q-Klasse (A / B / C) auswählen, dann scannen.'),
            }}

        for line in self.line_ids:
            matching = line.serial_quality_line_ids.filtered_domain([('lot_id.name', '=', scanned)])
            if matching:
                if matching.quality_class:
                    return {'warning': {
                        'title': _('Bereits zugewiesen'),
                        'message': _('"%s" hat bereits Q-Klasse %s.') % (
                            scanned, dict(matching._fields['quality_class'].selection).get(matching.quality_class)
                        ),
                    }}
                matching.quality_class = self.barcode_quality_class
                return

        return {'warning': {
            'title': _('Seriennummer nicht gefunden'),
            'message': _('"%s" ist in keiner Position dieses RMA-Eingangs.') % scanned,
        }}

    @api.depends('line_ids.has_serial_lots')
    def _compute_has_serial_lots(self):
        """Blendet Seriennummern-Spalten nur ein, wenn mindestens eine Position Serien hat."""
        for wizard in self:
            wizard.has_serial_lots = any(wizard.line_ids.mapped('has_serial_lots'))

    @api.onchange('rma_order_id')
    def _onchange_rma_order_id(self):
        """Lädt die Prüfpositionen aus dem gewählten RMA-Eingang."""
        for wizard in self:
            wizard.line_ids = [(5, 0, 0)] + wizard._get_move_line_commands()

    def _reload_lines_from_picking(self):
        """Wird nach automatischer Wizard-Erstellung genutzt, wenn noch keine Zeilen existieren."""
        self.ensure_one()
        self.line_ids = [(5, 0, 0)] + self._get_move_line_commands()

    def _get_move_line_commands(self):
        """Baut die Prüfliste aus allen nicht stornierten Bewegungen des RMA-Eingangs."""
        self.ensure_one()
        commands = []

        if not self.rma_order_id:
            return commands

        for move in self.rma_order_id.move_ids.filtered_domain([('state', '!=', 'cancel')]):
            commands.append((0, 0, {
                'stock_move_id': move.id,
            }))

        return commands

    def _validate_rma_and_quantities(self):
        """Validierung bleibt im Service zentral, der Wizard bietet nur den UI-Einstieg."""
        self.ensure_one()
        self._get_rma_splitting_service()._validate_rma_and_quantities(self)

    def _create_follow_up_pickings(self):
        self.ensure_one()
        return self._get_rma_splitting_service()._create_follow_up_pickings(self)

    def _prepare_exchange(self):
        self.ensure_one()
        return self._get_rma_splitting_service()._prepare_exchange(self)

    def _prepare_refund(self):
        self.ensure_one()
        return self._get_rma_splitting_service()._prepare_refund(self)

    def _write_note_and_mark_done(self):
        self.ensure_one()
        self._get_rma_splitting_service()._write_note_and_mark_done(self)

    def _complete_rma_receipt(self):
        self.ensure_one()
        self._get_rma_splitting_service()._complete_rma_receipt(self)

    def action_execute_split(self):
        """Button-Aktion: Mengenprüfung durchführen und erzeugte Folgebelege anzeigen."""
        self.ensure_one()
        created_pickings = self._get_rma_splitting_service().execute_split(self)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Erzeugte Umlagerungen'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('id', 'in', created_pickings.ids)],
            'target': 'current',
        }


class RmaSplittingLine(models.TransientModel):
    """Temporäre Prüfposition mit A/B/C-Aufteilung und optionaler Serien-Q-Klasse."""

    _name = 'rma.splitting.line'
    _description = 'RMA Management Prüfposition'

    wizard_id = fields.Many2one(
        'rma.splitting',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Lagerbewegung',
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        related='stock_move_id.product_id',
        string='Produkt',
        readonly=True,
    )
    product_uom = fields.Many2one(
        'uom.uom',
        related='stock_move_id.product_uom',
        string='Einheit',
        readonly=True,
    )
    product_uom_qty = fields.Float(
        related='stock_move_id.product_uom_qty',
        string='Erwartet',
        readonly=True,
    )
    serial_quality_line_ids = fields.One2many(
        'rma.splitting.serial.line',
        'splitting_line_id',
        string='Seriennummern / Qualitätsklassen',
    )
    has_serial_lots = fields.Boolean(
        string='Hat Seriennummern',
        compute='_compute_serial_information',
    )
    lot_serial_names = fields.Char(
        string='Serien/Chargen',
        compute='_compute_serial_information',
        readonly=True,
    )
    serial_quality_summary = fields.Char(
        string='Serien/Q-Klasse',
        compute='_compute_serial_information',
        readonly=True,
    )
    rma_qty_a = fields.Float(
        string='A-Ware',
        default=0.0,
        help='Neuwertiger Zustand: direkt wiederverkaufsfaehig.',
    )
    rma_qty_b = fields.Float(
        string='B-Ware',
        default=0.0,
        help='Gebrauchter Zustand: leichte optische Maengel, technisch in Ordnung.',
    )
    rma_qty_c = fields.Float(
        string='C-Ware',
        default=0.0,
        help='Defekt oder stark beschaedigt: nicht fuer den direkten Wiederverkauf geeignet.',
    )
    rma_qty_return = fields.Float(
        string='Umtausch',
        default=0.0,
        help='Menge, die fuer einen spaeteren Umtausch vorgemerkt wird.',
    )
    rma_qty_refund = fields.Float(
        string='Rückerstattung',
        default=0.0,
        help='Menge, die fuer eine spaetere Rueckerstattung vorgemerkt wird.',
    )

    @api.constrains('rma_qty_a', 'rma_qty_b', 'rma_qty_c', 'rma_qty_return', 'rma_qty_refund')
    def _check_non_negative_quantities(self):
        """Alle Prüf- und Folgeprozessmengen müssen positiv oder null sein."""
        for line in self:
            for field_name in ['rma_qty_a', 'rma_qty_b', 'rma_qty_c', 'rma_qty_return', 'rma_qty_refund']:
                if line[field_name] < 0:
                    raise ValidationError(_('Mengen dürfen nicht negativ sein.'))

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._ensure_serial_quality_lines()
        return lines

    def write(self, values):
        result = super().write(values)
        if 'stock_move_id' in values:
            self._ensure_serial_quality_lines()
        return result

    @api.depends(
        'stock_move_id.move_line_ids.lot_id',
        'stock_move_id.move_line_ids.lot_name',
        'serial_quality_line_ids.quality_class',
        'serial_quality_line_ids.lot_id',
    )
    def _compute_serial_information(self):
        """Fasst Seriennummern und ihre Qualitätsklassen für Listenansichten zusammen."""
        for line in self:
            names = []
            for move_line in line.stock_move_id.move_line_ids:
                if move_line.lot_id:
                    names.append(move_line.lot_id.name)
                elif move_line.lot_name:
                    names.append(move_line.lot_name)
            line.lot_serial_names = ', '.join(names)
            line.has_serial_lots = line._is_rma_serial_tracking_enabled() and bool(line.stock_move_id.move_line_ids.lot_id)
            summary_parts = []
            for serial_line in line.serial_quality_line_ids.filtered('quality_class'):
                summary_parts.append('%s: %s' % (
                    serial_line.lot_id.name,
                    dict(serial_line._fields['quality_class'].selection).get(serial_line.quality_class),
                ))
            line.serial_quality_summary = ', '.join(summary_parts)

    def _ensure_serial_quality_lines(self):
        """Hält die temporären Serien-Prüfzeilen synchron mit den Move-Lines des Belegs."""
        serial_line_model = self.env['rma.splitting.serial.line']
        for line in self:
            if not line._is_rma_serial_tracking_enabled():
                line.serial_quality_line_ids.unlink()
                continue

            serial_lots = line.stock_move_id.move_line_ids.lot_id
            if not serial_lots:
                continue

            existing_lots = line.serial_quality_line_ids.lot_id
            for serial_lot in serial_lots - existing_lots:
                serial_line_model.create({
                    'splitting_line_id': line.id,
                    'lot_id': serial_lot.id,
                })
            obsolete_lines = line.serial_quality_line_ids.filtered_domain([('lot_id', 'not in', serial_lots.ids)])
            obsolete_lines.unlink()

    @api.onchange('barcode_scan')
    def action_open_serial_quality(self):
        """Öffnet die Q-Klassen-Erfassung für Seriennummern einer Prüfposition."""
        self.ensure_one()
        self._ensure_serial_quality_lines()
        if not self.serial_quality_line_ids:
            raise ValidationError(_('Für diese Position sind keine Seriennummern im RMA-Eingang hinterlegt.'))

        return {
            'name': _('Seriennummern prüfen'),
            'type': 'ir.actions.act_window',
            'res_model': 'rma.splitting.line',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('rma_management.view_rma_splitting_line_serial_quality_form').id,
            'target': 'new',
        }

    def action_apply_serial_quality(self):
        """Übernimmt die Q-Klassen und zählt A/B/C automatisch hoch."""
        for line in self:
            line._sync_serial_quality_quantities()
        return {'type': 'ir.actions.act_window_close'}

    def _sync_serial_quality_quantities(self):
        """Synchronisiert A/B/C-Mengen aus den je Seriennummer gewählten Q-Klassen."""
        self.ensure_one()
        if not self.serial_quality_line_ids:
            return

        missing_serials = self.serial_quality_line_ids.filtered_domain([('quality_class', '=', False)])
        if missing_serials:
            raise ValidationError(_(
                "Bitte ordne jeder Seriennummer eine Qualitätsklasse zu.\n\n"
                "Offen: %(serials)s"
            ) % {
                'serials': ', '.join(missing_serials.mapped('lot_id.name')),
            })

        self.write({
            'rma_qty_a': len(self.serial_quality_line_ids.filtered_domain([('quality_class', '=', 'a')])),
            'rma_qty_b': len(self.serial_quality_line_ids.filtered_domain([('quality_class', '=', 'b')])),
            'rma_qty_c': len(self.serial_quality_line_ids.filtered_domain([('quality_class', '=', 'c')])),
        })

    def _is_rma_serial_tracking_enabled(self):
        """Globale RMA-Option für Betriebe ohne Seriennummernprozess."""
        value = self.env['ir.config_parameter'].sudo().get_param(
            'rma_management.use_serial_numbers',
            'True',
        )
        return value not in ('False', 'false', '0', '', False)

    def _validate_checked_quantities(self):
        """Prüft, dass A+B+C exakt der erwarteten RMA-Eingangsmenge entspricht."""
        self.ensure_one()
        self._sync_serial_quality_quantities()
        self._check_non_negative_quantities()

        total_checked_quantity = self.rma_qty_a + self.rma_qty_b + self.rma_qty_c
        precision_rounding = self.product_uom.rounding if self.product_uom else 0.01

        if float_compare(total_checked_quantity, self.product_uom_qty, precision_rounding=precision_rounding) != 0:
            raise ValidationError(_(
                "Die Summe aus A-, B- und C-Ware muss genau der erwarteten RMA Menge entsprechen.\n\n"
                "Produkt: %(product)s\n"
                "Erwartet: %(expected)s\n"
                "Eingegeben: %(entered)s"
            ) % {
                'product': self.product_id.display_name,
                'expected': self.product_uom_qty,
                'entered': total_checked_quantity,
            })


class RmaSplittingSerialLine(models.TransientModel):
    """Temporäre Q-Klassen-Zeile für genau eine Seriennummer."""

    _name = 'rma.splitting.serial.line'
    _description = 'RMA Management Seriennummernprüfung'
    _order = 'lot_id'

    splitting_line_id = fields.Many2one(
        'rma.splitting.line',
        string='Prüfposition',
        required=True,
        ondelete='cascade',
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Seriennummer',
        required=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        related='lot_id.product_id',
        string='Produkt',
        readonly=True,
    )
    quality_class = fields.Selection(
        [
            ('a', 'A-Ware'),
            ('b', 'B-Ware'),
            ('c', 'C-Ware'),
        ],
        string='Q-Klasse',
    )


class StockPicking(models.Model):
    """RMA-spezifische Felder und Statuslogik auf dem echten Lagerbeleg."""

    _inherit = 'stock.picking'

    RMA_STATUS_SELECTION = [
        ('open', 'Offen'),
        ('checked', 'Geprüft'),
        ('done', 'Erledigt'),
        ('cancel', 'Abgebrochen'),
    ]

    @api.depends('picking_type_id')
    def _compute_rma_is_receipt(self):
        """Kennzeichnet Lagerbelege, die mit dem konfigurierten RMA-Eingangstyp laufen."""
        rma_incoming_type = self.env['rma.stock.configuration']._get_picking_type('incoming')
        for picking in self:
            picking.rma_is_receipt = picking.picking_type_id == rma_incoming_type

    @api.depends('state', 'rma_is_receipt', 'rma_split_done', 'rma_processing_done')
    def _compute_rma_status(self):
        """Verdichtet Odoo-Status und RMA-Flags für Liste/Kanban."""
        for picking in self:
            if not picking.rma_is_receipt:
                picking.rma_status = False
            elif picking.state == 'cancel':
                picking.rma_status = 'cancel'
            elif picking.rma_processing_done:
                picking.rma_status = 'done'
            elif picking.rma_split_done:
                picking.rma_status = 'checked'
            else:
                picking.rma_status = 'open'

    rma_is_receipt = fields.Boolean(string='Ist RMA-Eingang', compute='_compute_rma_is_receipt', store=True)
    rma_status = fields.Selection(selection=RMA_STATUS_SELECTION, string='RMA-Status', compute='_compute_rma_status', store=True)
    rma_reason_id = fields.Many2one('rma.reason', string='RMA-Grund', readonly=True)
    rma_sale_order_id = fields.Many2one('sale.order', string='RMA Verkaufsauftrag', readonly=True)
    rma_attachment_ids = fields.Many2many(
        'ir.attachment',
        'stock_picking_rma_attachment_rel',
        'picking_id',
        'attachment_id',
        string='RMA Prüf-Fotos / Anhänge',
    )
    rma_has_serial_lots = fields.Boolean(
        string='Hat RMA-Seriennummern',
        compute='_compute_rma_has_serial_lots',
    )
    rma_repair_count = fields.Integer(
        string='Reparaturen',
        compute='_compute_rma_repair_count',
    )
    rma_receipt_created = fields.Boolean(string='RMA-Eingang erstellt', default=False)
    rma_split_done = fields.Boolean(string='RMA Mengenpruefung durchgeführt', default=False)
    rma_exchange_prepared = fields.Boolean(string='Umtausch vorbereitet', default=False)
    rma_refund_prepared = fields.Boolean(string='Rueckerstattung vorbereitet', default=False)
    rma_processing_done = fields.Boolean(string='RMA vollstaendig verarbeitet', default=False)

    def _compute_rma_repair_count(self):
        for picking in self:
            picking.rma_repair_count = self.env['repair.order'].search_count([
                ('picking_id', '=', picking.id),
            ])

    def action_view_rma_repairs(self):
        self.ensure_one()
        repairs = self.env['repair.order'].search([('picking_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reparaturaufträge',
            'res_model': 'repair.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', repairs.ids)],
        }

    @api.depends('move_line_ids.lot_id')
    def _compute_rma_has_serial_lots(self):
        """Steuert Seriennummern-Ansichten auf dem Beleg abhängig von Inhalt und Einstellung."""
        value = self.env['ir.config_parameter'].sudo().get_param(
            'rma_management.use_serial_numbers',
            'True',
        )
        use_serial_numbers = value not in ('False', 'false', '0', '', False)
        for picking in self:
            picking.rma_has_serial_lots = use_serial_numbers and bool(picking.move_line_ids.lot_id)


class StockMoveLine(models.Model):
    """Speichert die geprüfte RMA-Q-Klasse auf Seriennummer-/Move-Line-Ebene."""

    _inherit = 'stock.move.line'

    rma_quality_class = fields.Selection(
        [
            ('a', 'A-Ware'),
            ('b', 'B-Ware'),
            ('c', 'C-Ware'),
        ],
        string='RMA Q-Klasse',
        readonly=True,
    )
