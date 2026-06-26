import logging

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class RmaStockConfiguration(models.AbstractModel):
    """Zentrale, idempotente RMA-Lagerkonfiguration.

    Das Modell legt fehlende Standardlager und Vorgangsarten automatisch an,
    verwendet aber zuerst explizite Einstellungen aus den Odoo-Einstellungen.
    """

    _name = 'rma.stock.configuration'
    _description = 'RMA Management Lagerkonfiguration'

    # Technische Defaults für automatisch angelegte RMA-Lagerorte.
    _LOCATION_SPECS = {
        'rma': {
            'xml_id': 'rma_management.stock_location_rma',
            'name': 'RMA',
            'usage': 'internal',
        },
        'b_goods': {
            'xml_id': 'rma_management.stock_location_rma_b_goods',
            'name': 'RMA-Prüflager B-Ware',
            'usage': 'internal',
        },
        'scrap': {
            'xml_id': 'rma_management.stock_location_rma_scrap',
            'name': 'RMA-Schrottlager',
            'usage': 'inventory',
        },
    }

    # Technische Defaults für automatisch angelegte RMA-Vorgangsarten.
    _PICKING_TYPE_SPECS = {
        'incoming': {
            'xml_id': 'rma_management.picking_type_rma_incoming',
            'name': 'RMA-Eingang',
            'code': 'incoming',
            'sequence_code': 'RMA/%(range_year)s/%(month)s/',
            'auto_print_return_slip': False,
        },
        'b_goods': {
            'xml_id': 'rma_management.picking_type_rma_b_goods',
            'name': 'RMA-Prüflager B-Ware',
            'code': 'internal',
            'sequence_code': 'RMA/PRUEF/',
            'auto_print_return_slip': False,
        },
        'scrap': {
            'xml_id': 'rma_management.picking_type_rma_scrap',
            'name': 'RMA Schrottlager C-Ware',
            'code': 'internal',
            'sequence_code': 'RMA/SCHROTT/',
            'auto_print_return_slip': False,
        },
    }

    # ir.config_parameter-Schlüssel für vom Benutzer gewählte Lagerorte.
    _LOCATION_CONFIG_KEYS = {
        'rma': 'rma_management.location_rma_id',
        'b_goods': 'rma_management.location_b_goods_id',
        'scrap': 'rma_management.location_scrap_id',
    }

    # ir.config_parameter-Schlüssel für vom Benutzer gewählte Vorgangsarten.
    _PICKING_TYPE_CONFIG_KEYS = {
        'incoming': 'rma_management.picking_type_incoming_id',
        'a_goods': 'rma_management.picking_type_a_goods_id',
        'b_goods': 'rma_management.picking_type_b_goods_id',
        'scrap': 'rma_management.picking_type_scrap_id',
    }

    @api.model
    def _get_config_record(self, model_name, config_key):
        """Liest eine konfigurierte Datensatz-ID robust aus ir.config_parameter."""
        record_id = self.env['ir.config_parameter'].sudo().get_param(config_key)
        if not record_id:
            return self.env[model_name]
        try:
            return self.env[model_name].browse(int(record_id)).exists()
        except (TypeError, ValueError):
            _logger.warning("Ignoring invalid RMA config parameter %s=%s", config_key, record_id)
            return self.env[model_name]

    @api.model
    def _get_existing_xml_record(self, xml_id):
        """Sucht einen bestehenden Datensatz über XML-ID, ohne bei fehlender ID zu scheitern."""
        record = self.env.ref(xml_id, raise_if_not_found=False)
        return record.exists() if record else record

    @api.model
    def _link_xml_id(self, xml_id, record):
        """Verknüpft gefundene/angelegte Datensätze mit stabilen XML-IDs."""
        self.env['ir.model.data']._update_xmlids([{
            'xml_id': xml_id,
            'record': record,
            'noupdate': False,
        }], update=True)

    @api.model
    def _get_warehouse(self):
        """Findet das Hauptlager als Basis für RMA-Orte und Vorgangsarten."""
        warehouse = self.env.ref('stock.warehouse0', raise_if_not_found=False)
        warehouse = warehouse.exists() if warehouse else warehouse
        if not warehouse:
            warehouse = self.env['stock.warehouse'].search([], limit=1)
        if not warehouse:
            raise UserError(_('Es wurde kein Lager gefunden. Bitte lege zuerst ein Lager in Odoo an.'))
        return warehouse

    @api.model
    def _ensure_location(self, key, warehouse):
        """Legt einen RMA-Lagerort an oder aktualisiert den vorhandenen Ort."""
        spec = self._LOCATION_SPECS[key]
        location = self._get_existing_xml_record(spec['xml_id'])
        parent_location = warehouse.lot_stock_id

        if not location:
            domain = [
                ('name', '=', spec['name']),
                ('usage', '=', spec['usage']),
                ('company_id', 'in', [warehouse.company_id.id, False]),
            ]
            if spec['usage'] == 'internal':
                domain.append(('location_id', '=', parent_location.id))
            location = self.env['stock.location'].search(domain, limit=1)

        values = {
            'name': spec['name'],
            'usage': spec['usage'],
            'company_id': warehouse.company_id.id,
            'active': True,
        }
        if spec['usage'] == 'internal':
            values['location_id'] = parent_location.id

        if location:
            location.write(values)
        else:
            location = self.env['stock.location'].create(values)

        self._link_xml_id(spec['xml_id'], location)
        return location

    @api.model
    def _ensure_picking_type(self, key, warehouse, locations):
        """Legt eine RMA-Vorgangsart an oder aktualisiert die vorhandene Vorgangsart."""
        spec = self._PICKING_TYPE_SPECS[key]
        picking_type = self._get_existing_xml_record(spec['xml_id'])

        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([
                ('name', '=', spec['name']),
                ('code', '=', spec['code']),
                ('warehouse_id', '=', warehouse.id),
                ('company_id', '=', warehouse.company_id.id),
            ], limit=1)

        if key == 'incoming':
            # RMA-Eingänge kommen fachlich vom Kunden/Lieferanten in das RMA-Lager.
            source_location = self.env.ref('stock.stock_location_suppliers')
            destination_location = locations['rma']
        elif key == 'b_goods':
            source_location = locations['rma']
            destination_location = locations['b_goods']
        else:
            source_location = locations['rma']
            destination_location = locations['scrap']

        values = {
            'name': spec['name'],
            'code': spec['code'],
            'sequence_code': spec['sequence_code'],
            'warehouse_id': warehouse.id,
            'company_id': warehouse.company_id.id,
            'default_location_src_id': source_location.id,
            'default_location_dest_id': destination_location.id,
            'active': True,
            'reservation_method': 'at_confirm',
            'auto_print_return_slip': spec.get('auto_print_return_slip', False),
        }

        if picking_type:
            # sequence_code wird bei vorhandenen Typen nicht überschrieben, damit
            # bereits verwendete Nummernkreise stabil bleiben.
            existing_values = dict(values)
            existing_values.pop('sequence_code', None)
            picking_type.write(existing_values)
        else:
            picking_type = self.env['stock.picking.type'].create(values)

        self._link_xml_id(spec['xml_id'], picking_type)
        return picking_type

    @api.model
    def _ensure_rma_stock_configuration(self):
        """Stellt alle Standard-RMA-Lagerorte und Vorgangsarten idempotent bereit."""
        warehouse = self._get_warehouse()
        locations = {
            key: self._ensure_location(key, warehouse)
            for key in self._LOCATION_SPECS
        }
        picking_types = {
            key: self._ensure_picking_type(key, warehouse, locations)
            for key in self._PICKING_TYPE_SPECS
        }
        _logger.info(
            "RMA stock configuration ready: locations=%s picking_types=%s",
            {key: location.display_name for key, location in locations.items()},
            {key: picking_type.display_name for key, picking_type in picking_types.items()},
        )
        return True

    @api.model
    def _get_location(self, key):
        """Gibt den konfigurierten oder automatisch bereitgestellten Lagerort zurück."""
        configured_location = self._get_config_record('stock.location', self._LOCATION_CONFIG_KEYS[key])
        if configured_location:
            return configured_location
        location = self._get_existing_xml_record(self._LOCATION_SPECS[key]['xml_id'])
        if location:
            return location
        self._ensure_rma_stock_configuration()
        return self.env.ref(self._LOCATION_SPECS[key]['xml_id'])

    @api.model
    def _get_picking_type(self, key):
        """Gibt die konfigurierte oder automatisch bereitgestellte Vorgangsart zurück."""
        configured_picking_type = self._get_config_record('stock.picking.type', self._PICKING_TYPE_CONFIG_KEYS[key])
        if configured_picking_type:
            return configured_picking_type
        picking_type = self._get_existing_xml_record(self._PICKING_TYPE_SPECS[key]['xml_id'])
        if picking_type:
            return picking_type
        self._ensure_rma_stock_configuration()
        return self.env.ref(self._PICKING_TYPE_SPECS[key]['xml_id'])

    @api.model
    def _get_warehouse_receipt_type(self):
        """A-Ware geht standardmäßig zurück in den normalen Wareneingang des Lagers."""
        configured_picking_type = self._get_config_record('stock.picking.type', self._PICKING_TYPE_CONFIG_KEYS['a_goods'])
        if configured_picking_type:
            return configured_picking_type
        warehouse = self._get_warehouse()
        return warehouse.in_type_id or self.env.ref('stock.picking_type_in')

    @api.model
    def _get_internal_transfer_type(self):
        """Gibt den normalen internen Umbuchungstyp des Hauptlagers zurück."""
        warehouse = self._get_warehouse()
        return warehouse.int_type_id or self.env.ref('stock.picking_type_internal')
