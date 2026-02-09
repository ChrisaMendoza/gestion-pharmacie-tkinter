PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
                                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                                     username TEXT UNIQUE,
                                     password_hash TEXT,
                                     role TEXT,
                                     nom TEXT,
                                     prenom TEXT,
                                     email TEXT,
                                     actif INTEGER DEFAULT 1
);


CREATE TABLE IF NOT EXISTS laboratoires (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            nom TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medicaments (
                                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                                           code TEXT UNIQUE NOT NULL,
                                           nom_commercial TEXT NOT NULL,
                                           nom_generique TEXT,
                                           forme TEXT,
                                           dosage TEXT,
                                           categorie TEXT,
                                           prix_vente REAL CHECK(prix_vente > 0),
                                           stock_actuel INTEGER DEFAULT 0,
                                           seuil_alerte INTEGER DEFAULT 5,
                                           date_peremption DATE
);

CREATE TABLE IF NOT EXISTS entrees_stock (
                                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                                             medicament_id INTEGER,
                                             quantite INTEGER,
                                             prix_achat REAL,
                                             date_peremption DATE,
                                             date_entree DATE DEFAULT CURRENT_DATE,
                                             FOREIGN KEY (medicament_id) REFERENCES medicaments(id)
);

CREATE TABLE IF NOT EXISTS sorties_stock (
                                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                                             medicament_id INTEGER,
                                             quantite INTEGER,
                                             motif TEXT,
                                             date_sortie DATE DEFAULT CURRENT_DATE,
                                             FOREIGN KEY (medicament_id) REFERENCES medicaments(id)
);

CREATE TABLE IF NOT EXISTS logs (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    user_id INTEGER,
                                    action TEXT,
                                    date_action DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    telephone TEXT NOT NULL UNIQUE,
    email TEXT,
    carte_fidelite TEXT,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ventes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    type_vente TEXT CHECK(type_vente IN ('LIBRE','ORDONNANCE')) NOT NULL DEFAULT 'LIBRE',
    total REAL NOT NULL CHECK(total >= 0),
    remise REAL NOT NULL DEFAULT 0 CHECK(remise >= 0),
    date_vente DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS vente_lignes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vente_id INTEGER NOT NULL,
    medicament_id INTEGER NOT NULL,
    quantite INTEGER NOT NULL CHECK(quantite > 0),
    prix_unitaire REAL NOT NULL CHECK(prix_unitaire >= 0),
    sous_total REAL NOT NULL CHECK(sous_total >= 0),
    FOREIGN KEY (vente_id) REFERENCES ventes(id) ON DELETE CASCADE,
    FOREIGN KEY (medicament_id) REFERENCES medicaments(id)
);

CREATE TABLE IF NOT EXISTS ordonnances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    numero TEXT,
    medecin TEXT,
    date_ordonnance DATE,
    date_saisie DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ordonnance_lignes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ordonnance_id INTEGER NOT NULL,
    medicament_id INTEGER NOT NULL,
    quantite INTEGER NOT NULL CHECK(quantite > 0),
    FOREIGN KEY (ordonnance_id) REFERENCES ordonnances(id) ON DELETE CASCADE,
    FOREIGN KEY (medicament_id) REFERENCES medicaments(id)
);

-- Index pour recherche / stats
CREATE INDEX IF NOT EXISTS idx_clients_nom_prenom ON clients(nom, prenom);
CREATE INDEX IF NOT EXISTS idx_ventes_date ON ventes(date_vente);
CREATE INDEX IF NOT EXISTS idx_vente_lignes_med ON vente_lignes(medicament_id);

