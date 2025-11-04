-- Admin-Benutzer, die sich auf auth_db.users beziehen (nur per ID, kein FK cross-DB)
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    auth_user_id INT UNIQUE NOT NULL,         -- ID aus auth_db.users (nur Referenz, kein FK)
    email VARCHAR(255) UNIQUE NOT NULL,       -- gespiegelt für Bequemlichkeit/Joins
    display_name VARCHAR(255),
    is_superadmin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Rollen (z. B. superadmin, org_admin, support)
CREATE TABLE IF NOT EXISTS admin_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Berechtigungen als feingranulare Flags (z. B. "users.read", "invoices.write")
CREATE TABLE IF NOT EXISTS admin_permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Zuweisung: Rolle ↔ Berechtigung (n:n)
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    PRIMARY KEY (role_id, permission_id)
    -- absichtlich ohne FKs, um cross-DB/Migrationskopfschmerzen zu vermeiden; 
    -- du kannst FKs hinzufügen, wenn alles sicher in EINER DB bleibt.
);

-- Zuweisung: Admin-User ↔ Rolle (n:n)
CREATE TABLE IF NOT EXISTS admin_user_roles (
    admin_user_id INT NOT NULL,
    role_id INT NOT NULL,
    PRIMARY KEY (admin_user_id, role_id)
);

-- Audit-Log: wer hat was gemacht?
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id SERIAL PRIMARY KEY,
    admin_user_id INT,                -- optionaler Bezug auf admin_users.id
    email VARCHAR(255),               -- redundante Info, wenn du schnell filtern willst
    action VARCHAR(200) NOT NULL,     -- z. B. "create_customer", "assign_role"
    target VARCHAR(255),              -- frei: "customer:42", "user:15", etc.
    meta JSONB,                       -- zusätzliche Details (IP, alte/neue Werte, etc.)
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Optionale Defaults (Rollen & Permissions)
INSERT INTO admin_roles (name, description) 
VALUES 
  ('superadmin', 'Vollzugriff'),
  ('org_admin', 'Organisation verwalten'),
  ('support', 'Support-Funktionen')
ON CONFLICT (name) DO NOTHING;

-- Beispiel-Permissions (erweitere nach Bedarf)
INSERT INTO admin_permissions (name, description) VALUES
  ('users.read', 'Benutzer lesen'),
  ('users.write', 'Benutzer anlegen/ändern'),
  ('customers.read', 'Kunden lesen'),
  ('customers.write', 'Kunden anlegen/ändern'),
  ('invoices.read', 'Rechnungen lesen'),
  ('invoices.write', 'Rechnungen anlegen/ändern')
ON CONFLICT (name) DO NOTHING;

-- Beispiel-Zuordnung: superadmin bekommt alles
-- (Wenn du später Permissions ergänzt, kannst du das in der API/Seeds dynamisch pflegen)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM admin_roles r, admin_permissions p
WHERE r.name = 'superadmin'
ON CONFLICT DO NOTHING;
