import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RmaAiInspector(models.TransientModel):
    _name = 'rma.ai.inspector'
    _description = 'KI-gestützte A/B/C-Ware Klassifizierung'

    image = fields.Binary(string='Produktfoto', required=True)
    image_filename = fields.Char(string='Dateiname')
    notes = fields.Text(
        string='Hinweise an die KI',
        placeholder='Optional: Besonderheiten beschreiben (z.B. "Verpackung beschädigt, Gerät optisch ok")',
    )
    result_text = fields.Text(string='KI-Antwort', readonly=True)
    quality_suggestion = fields.Selection(
        [('a', 'A-Ware'), ('b', 'B-Ware'), ('c', 'C-Ware')],
        string='Empfehlung',
        readonly=True,
    )
    splitting_line_id = fields.Many2one(
        'rma.splitting.line',
        string='Prüfposition',
    )

    def _get_ai_provider(self):
        params = self.env['ir.config_parameter'].sudo()
        if params.get_param('ai.openai_key') or __import__('os').getenv('ODOO_AI_CHATGPT_TOKEN'):
            return 'openai', 'gpt-4o'
        if params.get_param('ai.google_key') or __import__('os').getenv('ODOO_AI_GEMINI_TOKEN'):
            return 'google', 'gemini-2.5-flash'
        raise UserError(_(
            'Kein KI-Provider konfiguriert. Bitte unter Einstellungen → KI einen API-Schlüssel hinterlegen.'
        ))

    def action_classify(self):
        self.ensure_one()
        if not self.image:
            raise UserError(_('Bitte zuerst ein Produktfoto hochladen.'))

        provider, model = self._get_ai_provider()

        # MIME-Typ aus Dateiname ableiten oder Standard
        filename = (self.image_filename or '').lower()
        if filename.endswith('.png'):
            mimetype = 'image/png'
        elif filename.endswith('.gif'):
            mimetype = 'image/gif'
        elif filename.endswith('.webp'):
            mimetype = 'image/webp'
        else:
            mimetype = 'image/jpeg'

        image_b64 = self.image.decode('utf-8') if isinstance(self.image, bytes) else self.image

        system_prompt = (
            'Du bist ein Experte für die Klassifizierung von Retouren-Ware (RMA) in einem IT-Systemhaus. '
            'Du bewertest Produktfotos und ordnest sie einer der drei Qualitätskategorien zu:\n\n'
            'A-Ware: Neuwertig, keine sichtbaren Mängel, vollständige/originale Verpackung, '
            'sofort wiederverkäufig als Neuware.\n\n'
            'B-Ware: Leichte Gebrauchsspuren, Kratzer oder beschädigte Verpackung, aber voll '
            'funktionsfähig — nur als B-Ware oder mit Preisabschlag verkäufig.\n\n'
            'C-Ware: Erhebliche Schäden, kaputte Displays/Gehäuse, stark beschädigte oder '
            'fehlende Verpackung — nicht oder nur als Ersatzteilspender weiterverkäufig.\n\n'
            'Antworte immer auf Deutsch. Beginne mit einer klaren Klassifizierung (A-Ware, B-Ware '
            'oder C-Ware), gefolgt von einer kurzen Begründung (2-4 Sätze) basierend auf dem Foto.'
        )

        user_prompt = 'Bitte klassifiziere dieses Produktfoto.'
        if self.notes:
            user_prompt += f'\n\nZusätzliche Hinweise: {self.notes}'

        from odoo.addons.ai.utils.llm_api_service import LLMApiService
        service = LLMApiService(self.env, provider=provider)

        files = [{'mimetype': mimetype, 'value': image_b64, 'file_ref': '<file_#1>'}]
        responses = service.request_llm(
            llm_model=model,
            system_prompts=[system_prompt],
            user_prompts=[user_prompt],
            files=files,
        )

        result = ' '.join(responses) if responses else ''

        # Empfehlung aus Antwort extrahieren
        result_lower = result.lower()
        if result_lower.startswith('a-ware') or '\na-ware' in result_lower or 'a-ware:' in result_lower:
            suggestion = 'a'
        elif result_lower.startswith('b-ware') or '\nb-ware' in result_lower or 'b-ware:' in result_lower:
            suggestion = 'b'
        elif result_lower.startswith('c-ware') or '\nc-ware' in result_lower or 'c-ware:' in result_lower:
            suggestion = 'c'
        else:
            # Fallback: im gesamten Text suchen
            if 'a-ware' in result_lower and 'b-ware' not in result_lower and 'c-ware' not in result_lower:
                suggestion = 'a'
            elif 'c-ware' in result_lower:
                suggestion = 'c'
            elif 'b-ware' in result_lower:
                suggestion = 'b'
            else:
                suggestion = False

        self.write({'result_text': result, 'quality_suggestion': suggestion})

        # Wizard neu öffnen, damit Ergebnis sichtbar wird
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply_suggestion(self):
        self.ensure_one()
        if not self.quality_suggestion or not self.splitting_line_id:
            return {'type': 'ir.actions.act_window_close'}
        self.splitting_line_id.write({'rma_quality_class_suggestion': self.quality_suggestion})
        return {'type': 'ir.actions.act_window_close'}
