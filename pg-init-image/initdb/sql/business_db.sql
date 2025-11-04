CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    customer_id INT,   -- nur ID, kein FK
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'eingang',
    status_changed_at TIMESTAMPTZ DEFAULT now(),
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE org_invoices (
    id SERIAL PRIMARY KEY,
    customer_id INT,   -- nur ID, kein FK
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    betrag NUMERIC(10,2) NOT NULL,
    waehrung VARCHAR(10) DEFAULT 'EUR',
    status VARCHAR(20) DEFAULT 'entwurf',
    faelligkeit TIMESTAMPTZ,
    pdf_path TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);