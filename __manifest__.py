{
    # Modulmetadaten für Odoo Apps und Update-Mechanismus.
    'name': 'RMA Management',
    'version': '1.0',
    'summary': 'RMA-Erstellung und Mengenprüfung',
    'description': 'Erfassen von RMAs basierend auf Verkaufsaufträgen.',
    'author': 'MSV Systemhaus Martin Schlaak GmbH',
    'license': 'Proprietary',
    'copyright': 'Copyright © 2026 MSV Systemhaus Martin Schlaak GmbH. All rights reserved.',
    'category': 'Inventory',
    'depends': ['sale_management', 'stock', 'base', 'product', 'web'],
    # Reihenfolge ist wichtig: Rechte/Daten zuerst, danach Views und Menüs.
    'data': [
        'security/rma_security.xml',
        'security/ir.model.access.csv',
        'data/rma_stock_data.xml',
        'data/rma_reason_data.xml',
        'views/rma_settings.xml',
        'views/rma_head.xml',
        'views/rma_splitting.xml',
        'views/rma_menu.xml',
        'views/rma_overview.xml',
        'views/rma_audit.xml',
    ],
    # Backend-Styles sind bewusst getrennt nach Grundlayout, Kundendaten,
    # Tabellen und Mengenprüfung, damit spätere UI-Änderungen gezielt bleiben.
    'assets': {
        'web.assets_backend': [
            'rma_management/static/src/scss/rma_base.scss',
            'rma_management/static/src/scss/rma_customer.scss',
            'rma_management/static/src/scss/rma_tables.scss',
            'rma_management/static/src/scss/rma_split.scss',
        ],
    },
    'installable': True,
    'application': True,
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
}
