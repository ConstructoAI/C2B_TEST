"""
Catégories complètes détaillées pour les soumissions Heritage
Version étendue avec tous les items de construction
"""

CATEGORIES_COMPLETE = {
    '0': {
        'name': '0.0 - Travaux Préparatoires et Démolition',
        'items': [
            {'id': '0-1', 'title': 'Permis et études',
             'description': 'Permis de construction, étude géotechnique, certificat de localisation, test de percolation (si requis).'},
            {'id': '0-2', 'title': 'Démolition et décontamination',
             'description': 'Démolition de structures existantes, décontamination (amiante, vermiculite si applicable), disposition des débris.'},
            {'id': '0-3', 'title': 'Préparation du terrain et services temporaires',
             'description': 'Déboisement, essouchement, nivellement, protection des arbres, électricité temporaire, toilette de chantier, clôture.'}
        ]
    },
    '1': {
        'name': '1.0 - Fondation, Infrastructure et Services',
        'items': [
            {'id': '1-1', 'title': 'Excavation et remblai',
             'description': 'Excavation générale, remblai granulaire compacté, pierre concassée, membrane géotextile.'},
            {'id': '1-2', 'title': 'Fondation complète',
             'description': 'Béton 30 MPA, armature 15M, coffrage, coulée, finition, cure, isolant R-10 sous-dalle, pare-vapeur.'},
            {'id': '1-3', 'title': 'Drainage et imperméabilisation',
             'description': 'Drain français, membrane d\'imperméabilisation, panneau de drainage, pompe de puisard.'},
            {'id': '1-4', 'title': 'Raccordements et services',
             'description': 'Égout, aqueduc, pluvial (jusqu\'à 50\'), système septique si applicable (fosse et champ selon Q-2, r.22).'}
        ]
    },
    '2': {
        'name': '2.0 - Structure et Charpente',
        'items': [
            {'id': '2-1', 'title': 'Structure de plancher',
             'description': 'Poutrelles ajourées 14", solives de rive, contreventement, sous-plancher 3/4" collé-vissé.'},
            {'id': '2-2', 'title': 'Murs porteurs et cloisons',
             'description': 'Montants 2x6 @ 16" c/c murs extérieurs, 2x4 @ 16" c/c cloisons, lisses, sablières doubles, linteaux.'},
            {'id': '2-3', 'title': 'Structure de toit',
             'description': 'Fermes préfabriquées ou chevrons/solives selon plans, contreventement, support de toit 5/8".'},
            {'id': '2-4', 'title': 'Éléments structuraux spéciaux',
             'description': 'Poutres et colonnes d\'acier, poutres LVL, colonnes décoratives, quincaillerie structurale.'}
        ]
    },
    '3': {
        'name': '3.0 - Enveloppe Extérieure',
        'items': [
            {'id': '3-1', 'title': 'Toiture - Matériaux',
             'description': 'Bardeaux architecturaux 30 ans, membrane autocollante, papier #15, ventilation de toit, évents de plomberie.'},
            {'id': '3-2', 'title': 'Toiture - Main-d\'œuvre et ferblanterie',
             'description': 'Installation bardeaux, solins, noues, faîtières, gouttières 5", descentes pluviales, protège-gouttières.'},
            {'id': '3-3', 'title': 'Revêtements muraux - Matériaux',
             'description': 'Maçonnerie ([%]), fibrociment ([%]), vinyle/acier ([%]), fourrures, pare-air Tyvek, solins.'},
            {'id': '3-4', 'title': 'Revêtements muraux - Main-d\'œuvre',
             'description': 'Installation complète des revêtements, calfeutrage, scellants, finition des coins et jonctions.'},
            {'id': '3-5', 'title': 'Portes et fenêtres',
             'description': '[X] fenêtres PVC/hybride, double vitrage Low-E argon, [X] portes extérieures, porte patio, portes de garage isolées.'},
            {'id': '3-6', 'title': 'Soffites, fascias et accessoires',
             'description': 'Soffites ventilés aluminium, fascias aluminium, moulures de finition, ventilation d\'entretoit.'},
            {'id': '3-7', 'title': 'Structures extérieures',
             'description': 'Balcons, terrasses, garde-corps aluminium/verre, escaliers extérieurs, auvents, pergola (si applicable).'},
            {'id': '3-8', 'title': 'Maçonnerie décorative et cheminée',
             'description': 'Cheminée préfabriquée, revêtement de pierre/brique, couronnement, chapeau de cheminée.'}
        ]
    },
    '4': {
        'name': '4.0 - Systèmes Mécaniques et Électriques',
        'items': [
            {'id': '4-1', 'title': 'Plomberie - Distribution et drainage',
             'description': 'Tuyauterie PEX/cuivre, drainage ABS, valves d\'arrêt, clapets antiretour, supports et isolant de tuyaux.'},
            {'id': '4-2', 'title': 'Plomberie - Appareils et accessoires',
             'description': '[X] salles de bain complètes, évier cuisine double, chauffe-eau [X]gal, adoucisseur d\'eau, robinetterie extérieure.'},
            {'id': '4-3', 'title': 'Chauffage au sol (si applicable)',
             'description': 'Plancher radiant [X] zones, chaudière haute efficacité, pompes de circulation, contrôles.'},
            {'id': '4-4', 'title': 'Électricité - Distribution principale',
             'description': 'Panneau 200A/40 circuits, mise à terre, câblage principal, sous-panneau garage, protection surtension.'},
            {'id': '4-5', 'title': 'Électricité - Filage et dispositifs',
             'description': 'Câblage complet Romex, [X] prises, [X] interrupteurs, circuits dédiés, prises DDFT, détecteurs.'},
            {'id': '4-6', 'title': 'Éclairage et contrôles',
             'description': '[X] luminaires encastrés, éclairage sous-armoires, gradateurs, éclairage extérieur, commandes intelligentes.'},
            {'id': '4-7', 'title': 'CVAC - Équipements principaux',
             'description': 'Thermopompe centrale [X] tonnes, fournaise d\'appoint gaz/électrique, humidificateur, filtre HEPA.'},
            {'id': '4-8', 'title': 'CVAC - Distribution et ventilation',
             'description': 'Conduits isolés, grilles et diffuseurs, VRC/VRE [X] PCM, ventilateurs salles de bain, hotte cuisine.'},
            {'id': '4-9', 'title': 'Systèmes spécialisés',
             'description': 'Pré-filage alarme/caméras, aspirateur central, audio intégré, réseau informatique Cat6, borne VÉ 240V.'}
        ]
    },
    '5': {
        'name': '5.0 - Isolation et Étanchéité',
        'items': [
            {'id': '5-1', 'title': 'Isolation thermique',
             'description': 'Murs ext. R-24.5, plafond cathédrale R-31, grenier R-50, sous-sol R-20, solives de rive R-20.'},
            {'id': '5-2', 'title': 'Étanchéité à l\'air',
             'description': 'Pare-vapeur 6 mil, scellant acoustique, ruban Tuck Tape, mousse expansive, coupe-froid.'},
            {'id': '5-3', 'title': 'Insonorisation',
             'description': 'Laine acoustique entre étages, barres résilientes, scellant acoustique, isolant plomberie.'},
            {'id': '5-4', 'title': 'Tests et certification',
             'description': 'Test d\'infiltrométrie, thermographie, certification Novoclimat Select, rapport de conformité.'}
        ]
    },
    '6': {
        'name': '6.0 - Finitions Intérieures',
        'items': [
            {'id': '6-1', 'title': 'Cloisons sèches - Gypse',
             'description': 'Gypse 1/2" régulier et hydrofuge, gypse 5/8" plafonds, coins métalliques, finition niveau 4.'},
            {'id': '6-2', 'title': 'Peinture et finition murale',
             'description': 'Apprêt, peinture 2 couches (murs/plafonds), peinture émail (boiseries), papier-peint (si applicable).'},
            {'id': '6-3', 'title': 'Revêtements de plancher',
             'description': 'Bois franc/ingénierie [X]pi², céramique [X]pi², tapis [X]pi², vinyle luxe [X]pi², sous-planchers.'},
            {'id': '6-4', 'title': 'Carrelage et dosseret',
             'description': 'Céramique salles de bain (plancher/murs douche), dosseret cuisine, membrane Schluter, joints époxy.'},
            {'id': '6-5', 'title': 'Ébénisterie - Cuisine',
             'description': 'Armoires thermoplastique/bois, comptoir quartz/granit [X]pi lin, îlot, pantry, quincaillerie soft-close.'},
            {'id': '6-6', 'title': 'Ébénisterie - Salles de bain et autres',
             'description': 'Vanités [X] salles de bain, lingerie, walk-in aménagé, rangement entrée, bureau intégré.'},
            {'id': '6-7', 'title': 'Menuiserie intérieure',
             'description': '[X] portes intérieures, cadres et moulures, plinthes, cimaises, tablettes décoratives.'},
            {'id': '6-8', 'title': 'Escaliers et rampes',
             'description': '[X] escaliers bois franc/MDF, main courante, barreaux métal/bois, poteaux décoratifs.'},
            {'id': '6-9', 'title': 'Finition sous-sol (si applicable)',
             'description': 'Divisions, isolation, gypse, plancher flottant/époxy, plafond suspendu, salle mécanique finie.'},
            {'id': '6-10', 'title': 'Accessoires et quincaillerie',
             'description': 'Poignées de porte, crochets, barres à serviettes, miroirs, tablettes garde-robes, cache-radiateurs.'}
        ]
    },
    '7': {
        'name': '7.0 - Aménagement Extérieur et Garage',
        'items': [
            {'id': '7-1', 'title': 'Terrassement et nivellement',
             'description': 'Nivellement final, terre végétale, ensemencement gazon, arbres et arbustes de base.'},
            {'id': '7-2', 'title': 'Surfaces dures',
             'description': 'Entrée asphalte/pavé uni, trottoirs béton/pavé, bordures, patio béton/composite.'},
            {'id': '7-3', 'title': 'Clôtures et structures',
             'description': 'Clôture [type], portail, muret décoratif, pergola, cabanon préfabriqué.'},
            {'id': '7-4', 'title': 'Éclairage extérieur et irrigation',
             'description': 'Éclairage paysager, lampadaires, système d\'irrigation (si applicable), minuteries.'},
            {'id': '7-5', 'title': 'Finition garage',
             'description': 'Dalle béton finie, murs gypse peint, éclairage, prises électriques, rangement, porte de service.'}
        ]
    }
}