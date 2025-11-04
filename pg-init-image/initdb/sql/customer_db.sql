CREATE TABLE IF NOT EXISTS customer (
    id SERIAL PRIMARY KEY,
    business_db_name VARCHAR(50) NOT NULL DEFAULT 'business_db1',
    org_name VARCHAR(255) NOT NULL,
    org_email VARCHAR(255) UNIQUE,
    org_tel VARCHAR(50) NOT NULL,
    org_adress_plz VARCHAR(10) NOT NULL,
    org_adress_city VARCHAR(100) NOT NULL,
    org_adress_street VARCHAR(100) NOT NULL,
    org_adress_building VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    contact_first_name VARCHAR(100),
    contact_last_name VARCHAR(100),
    contact_role VARCHAR(100),
    contact_email VARCHAR(255),
    contact_tel VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS banking (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    card_owner VARCHAR(255),
    bank_name VARCHAR(255) NOT NULL,
    iban VARCHAR(34) UNIQUE NOT NULL,
    blz VARCHAR(20),
    bic VARCHAR(11) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    price NUMERIC(10,2) DEFAULT 0,
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_subscriptions (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    subscription_id INT NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    start_date TIMESTAMPTZ DEFAULT now(),
    end_date TIMESTAMPTZ,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS addons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    price NUMERIC(10,2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_addons (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    addon_id INT NOT NULL REFERENCES addons(id) ON DELETE CASCADE,
    start_date TIMESTAMPTZ DEFAULT now(),
    active BOOLEAN DEFAULT TRUE
);
