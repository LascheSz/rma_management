from odoo import _, api, fields, models


class RmaRepairOrder(models.Model):
    _inherit = 'repair.order'

    rma_repair_destination = fields.Selection([
        ('sellable', 'Wieder verkaufsfähig → Hauptlager'),
        ('scrap', 'Nicht verkaufsfähig → Schrottlager'),
    ], string='Reparaturergebnis', default='sellable')

    @api.depends('picking_type_id', 'rma_repair_destination', 'picking_id')
    def _compute_product_location_dest_id(self):
        rma_repair_orders = self.filtered(lambda r: r.picking_id and r.picking_id.rma_is_receipt)
        for repair in rma_repair_orders:
            config = repair.env['rma.stock.configuration']
            if repair.rma_repair_destination == 'scrap':
                repair.product_location_dest_id = config._get_location('scrap')
            else:
                repair.product_location_dest_id = config._get_warehouse_receipt_type().default_location_dest_id
        super(RmaRepairOrder, self - rma_repair_orders)._compute_product_location_dest_id()

    def action_repair_end(self):
        res = super().action_repair_end()
        for repair in self.filtered(lambda r: r.picking_id and r.picking_id.rma_is_receipt):
            picking = repair.picking_id
            if picking.state not in ('done', 'cancel'):
                repair._auto_validate_b_ware_picking(picking)
        return res

    def _auto_validate_b_ware_picking(self, picking):
        for move in picking.move_ids:
            if move.move_line_ids.filtered('lot_id'):
                move.picked = True
                continue
            move_line = move.move_line_ids[:1]
            if move_line:
                move_line.quantity = move.product_uom_qty
            else:
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
