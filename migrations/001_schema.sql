CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE cities (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL CHECK (btrim(name) <> ''),
    country_code text NOT NULL CHECK (country_code ~ '^[A-Z]{2}$'),
    timezone text NOT NULL,
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    UNIQUE (name, country_code)
);
CREATE TABLE categories (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    description text NOT NULL DEFAULT ''
);
CREATE TABLE venues (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_id bigint NOT NULL REFERENCES cities(id),
    name text NOT NULL CHECK (btrim(name) <> ''),
    address text,
    latitude double precision CHECK (latitude BETWEEN -90 AND 90),
    longitude double precision CHECK (longitude BETWEEN -180 AND 180),
    location geography(Point, 4326) GENERATED ALWAYS AS (
        CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL
        THEN ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography END
    ) STORED,
    neighborhood text,
    website text,
    CHECK ((latitude IS NULL) = (longitude IS NULL))
);
CREATE INDEX venues_location_idx ON venues USING gist(location);
CREATE INDEX venues_city_idx ON venues(city_id);

CREATE TABLE sources (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    url text NOT NULL,
    source_type text NOT NULL CHECK (source_type IN ('api', 'feed', 'html', 'manual')),
    last_scraped_at timestamptz,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'paused', 'error')),
    ingestion_approved boolean NOT NULL DEFAULT false,
    compliance_checked_at timestamptz,
    compliance_notes text,
    CHECK (NOT ingestion_approved OR (compliance_checked_at IS NOT NULL AND
        compliance_notes IS NOT NULL AND btrim(compliance_notes) <> ''))
);
CREATE TABLE events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title text NOT NULL CHECK (btrim(title) <> ''),
    description text NOT NULL DEFAULT '',
    short_description text,
    category_id bigint REFERENCES categories(id),
    venue_id bigint NOT NULL REFERENCES venues(id),
    start_time timestamptz NOT NULL,
    end_time timestamptz,
    price_min numeric(12,2) CHECK (price_min >= 0),
    price_max numeric(12,2) CHECK (price_max >= 0),
    currency text CHECK (currency ~ '^[A-Z]{3}$'),
    image_url text,
    source_url text NOT NULL,
    source_name text NOT NULL,
    language text,
    age_restriction smallint CHECK (age_restriction >= 0),
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (end_time IS NULL OR end_time >= start_time),
    CHECK (price_max IS NULL OR price_min IS NULL OR price_max >= price_min),
    CHECK ((price_min IS NULL AND price_max IS NULL) OR currency IS NOT NULL)
);
COMMENT ON COLUMN events.price_min IS 'NULL means unknown; zero means free.';
CREATE INDEX events_active_start_idx ON events(start_time) WHERE status = 'active';
CREATE INDEX events_venue_start_idx ON events(venue_id, start_time);
CREATE INDEX events_category_idx ON events(category_id);

CREATE TABLE raw_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id bigint NOT NULL REFERENCES sources(id),
    external_id text,
    source_url text NOT NULL,
    fetched_at timestamptz NOT NULL DEFAULT now(),
    payload jsonb NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'loaded', 'rejected')),
    validation_errors jsonb,
    event_id bigint REFERENCES events(id)
);
CREATE INDEX raw_events_source_idx ON raw_events(source_id, fetched_at);
CREATE TABLE event_sources (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id bigint NOT NULL REFERENCES events(id),
    source_id bigint NOT NULL REFERENCES sources(id),
    external_id text,
    source_url text NOT NULL,
    first_seen timestamptz NOT NULL DEFAULT now(),
    last_seen timestamptz NOT NULL DEFAULT now(),
    CHECK (last_seen >= first_seen),
    UNIQUE (source_id, external_id),
    UNIQUE (source_id, source_url)
);
CREATE INDEX event_sources_event_idx ON event_sources(event_id);

-- Defense in depth: a collector cannot write source records before review.
CREATE FUNCTION require_approved_source() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM id FROM sources WHERE id = NEW.source_id
        AND ingestion_approved AND status = 'active' FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Source must be active and approved before ingestion';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER raw_events_approved_source BEFORE INSERT OR UPDATE ON raw_events
    FOR EACH ROW EXECUTE FUNCTION require_approved_source();
CREATE TRIGGER event_sources_approved_source BEFORE INSERT OR UPDATE ON event_sources
    FOR EACH ROW EXECUTE FUNCTION require_approved_source();

-- These are storage contracts for teammates; no auth or endpoints are implemented.
CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL,
    name text,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX users_email_idx ON users(lower(email));
CREATE TABLE user_preferences (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id bigint NOT NULL REFERENCES categories(id),
    preference_score double precision NOT NULL DEFAULT 0 CHECK (preference_score BETWEEN 0 AND 1),
    UNIQUE (user_id, category_id)
);
CREATE TABLE saved_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id bigint NOT NULL REFERENCES events(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, event_id)
);
CREATE INDEX saved_events_event_idx ON saved_events(event_id);
CREATE TABLE user_interactions (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id bigint REFERENCES users(id) ON DELETE SET NULL,
    event_id bigint NOT NULL REFERENCES events(id),
    interaction_type text NOT NULL CHECK (interaction_type IN ('view', 'click', 'save', 'share', 'external_click')),
    timestamp timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX user_interactions_event_idx ON user_interactions(event_id, timestamp);
CREATE INDEX user_interactions_user_idx ON user_interactions(user_id);
CREATE TABLE event_embeddings (
    event_id bigint PRIMARY KEY REFERENCES events(id),
    embedding vector NOT NULL,
    model text NOT NULL,
    dimensions integer NOT NULL CHECK (dimensions > 0),
    content_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (vector_dims(embedding) = dimensions)
);
-- Dimension-specific vector indexes follow model selection in phase 5.
CREATE TABLE search_log (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id bigint REFERENCES users(id) ON DELETE SET NULL,
    query text NOT NULL,
    parsed_filters jsonb,
    results jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(results) = 'array'),
    latency_ms integer CHECK (latency_ms >= 0),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE FUNCTION touch_event_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;
CREATE TRIGGER events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION touch_event_updated_at();
