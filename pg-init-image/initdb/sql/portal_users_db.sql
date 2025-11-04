CREATE TABLE portal_users (
    id SERIAL PRIMARY KEY,
    pers_first_name VARCHAR(100) NOT NULL,
    pers_second_name VARCHAR(100) NOT NULL,
    pers_email VARCHAR(255) UNIQUE,
    pers_tel VARCHAR(50) NOT NULL,
    pers_adress_plz VARCHAR(10) NOT NULL,
    pers_adress_city VARCHAR(100) NOT NULL,
    pers_adress_street VARCHAR(100) NOT NULL,
    pers_adress_building VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE auftraege (
    id SERIAL PRIMARY KEY,
    customer_id INT,       -- nur ID, kein FK (da cross-DB)
    portal_user_id INT NOT NULL REFERENCES portal_users(id) ON DELETE CASCADE,
    description TEXT,
    status VARCHAR(50) DEFAULT 'eingang',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE org_pers_invoices (
    id SERIAL PRIMARY KEY,
    customer_id INT,       -- nur ID, kein FK
    portal_user_id INT NOT NULL REFERENCES portal_users(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    pdf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);