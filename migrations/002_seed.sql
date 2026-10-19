INSERT INTO cities (name, country_code, timezone, currency)
VALUES ('Tbilisi', 'GE', 'Asia/Tbilisi', 'GEL')
ON CONFLICT (name, country_code) DO NOTHING;

-- Initial product taxonomy, not claims about any source's categories.
INSERT INTO categories (name, description) VALUES
    ('music', 'Concerts and live music'),
    ('nightlife', 'Parties and nightlife'),
    ('exhibition', 'Art and exhibitions'),
    ('theatre', 'Theatre and performances'),
    ('workshop', 'Workshops and learning'),
    ('technology', 'Technology events'),
    ('sports', 'Sports and physical activities'),
    ('festival', 'Festivals'),
    ('market', 'Markets'),
    ('family', 'Family activities'),
    ('talk', 'Talks and lectures'),
    ('film', 'Film screenings'),
    ('food', 'Food and drink'),
    ('social', 'Social activities'),
    ('other', 'Unclassified activities')
ON CONFLICT (name) DO NOTHING;
