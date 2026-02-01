PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
                                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                                     username TEXT UNIQUE NOT NULL,
                                     password_hash TEXT NOT NULL,
                                     role TEXT CHECK(role IN ('ADMIN','PHARMACIEN','ASSISTANT')) NOT NULL,
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
