--
-- PostgreSQL database dump
--

\restrict Uax6iozAoYyb6DKENBnkMT12mbw17dsgOaIu5vtOmaRYScUzi7dvUsMMOkOKBTY

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg12+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: unaccent; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;


--
-- Name: EXTENSION unaccent; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION unaccent IS 'text search dictionary that removes accents';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_telemetry_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.agent_telemetry_logs (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    agent_name character varying NOT NULL,
    intent_hash character varying NOT NULL,
    input_tokens integer NOT NULL,
    output_tokens integer NOT NULL,
    cost_token double precision NOT NULL,
    duration_ms integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    tenant_id character varying NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.agent_telemetry_logs OWNER TO postgres;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: appointments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.appointments (
    id character varying NOT NULL,
    title character varying NOT NULL,
    description text,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    type character varying NOT NULL,
    status character varying NOT NULL,
    campaign_id character varying,
    metadata_json json,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    recurring_type character varying NOT NULL,
    recurring_metadata json
);


ALTER TABLE public.appointments OWNER TO postgres;

--
-- Name: article_embeddings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_embeddings (
    id character varying NOT NULL,
    article_id character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    embedding public.vector(384) NOT NULL
);


ALTER TABLE public.article_embeddings OWNER TO postgres;

--
-- Name: articles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.articles (
    id character varying NOT NULL,
    title character varying NOT NULL,
    slug character varying NOT NULL,
    excerpt character varying,
    content text,
    status character varying NOT NULL,
    category character varying NOT NULL,
    views integer NOT NULL,
    author_id character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    seo_title character varying,
    seo_description character varying,
    featured_image character varying,
    seo_keywords character varying,
    seo_og_image character varying
);


ALTER TABLE public.articles OWNER TO postgres;

--
-- Name: banners; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.banners (
    id character varying NOT NULL,
    title character varying NOT NULL,
    description text,
    image_url character varying NOT NULL,
    link_url character varying,
    "position" character varying DEFAULT 'home_main'::character varying NOT NULL,
    order_index integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    device_type character varying DEFAULT 'all'::character varying NOT NULL,
    tenant_id character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.banners OWNER TO postgres;

--
-- Name: campaign_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.campaign_events (
    id character varying NOT NULL,
    campaign_id character varying NOT NULL,
    event_type character varying NOT NULL,
    payload json NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    tenant_id character varying NOT NULL
);


ALTER TABLE public.campaign_events OWNER TO postgres;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categories (
    id character varying NOT NULL,
    name character varying NOT NULL,
    slug character varying NOT NULL,
    parent_id character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    description text,
    seo_title character varying,
    seo_description character varying,
    image character varying
);


ALTER TABLE public.categories OWNER TO postgres;

--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_messages (
    id character varying NOT NULL,
    session_id character varying NOT NULL,
    user_id character varying,
    role character varying NOT NULL,
    content json NOT NULL,
    modality character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL
);


ALTER TABLE public.chat_messages OWNER TO postgres;

--
-- Name: content_campaigns; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.content_campaigns (
    id character varying NOT NULL,
    source_input text NOT NULL,
    reviewer_type character varying NOT NULL,
    current_step integer NOT NULL,
    status character varying NOT NULL,
    gold_metadata json,
    topic_data json,
    assets_data json,
    outline_data json,
    draft_content text,
    unique_score double precision NOT NULL,
    final_html text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    search_count integer DEFAULT 0 NOT NULL,
    user_id character varying,
    category character varying DEFAULT 'CREATIVE_CONTENT'::character varying NOT NULL
);


ALTER TABLE public.content_campaigns OWNER TO postgres;

--
-- Name: content_scouts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.content_scouts (
    id character varying NOT NULL,
    topic character varying NOT NULL,
    report_data json NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL
);


ALTER TABLE public.content_scouts OWNER TO postgres;

--
-- Name: drafts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.drafts (
    id character varying NOT NULL,
    proposed_by character varying NOT NULL,
    target_model character varying NOT NULL,
    target_id character varying,
    action character varying NOT NULL,
    payload json NOT NULL,
    status character varying NOT NULL,
    reviewer_id character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL
);


ALTER TABLE public.drafts OWNER TO postgres;

--
-- Name: media_registry; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.media_registry (
    id character varying NOT NULL,
    filename character varying NOT NULL,
    file_path character varying NOT NULL,
    file_size integer NOT NULL,
    mime_type character varying(50) NOT NULL,
    dimensions character varying(20),
    blurhash character varying(100),
    alt_text character varying,
    campaign_id character varying,
    owner_id character varying,
    media_metadata json NOT NULL,
    provider character varying(20) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    is_public boolean DEFAULT true NOT NULL,
    linked_post_id character varying,
    linked_post_type character varying(30)
);


ALTER TABLE public.media_registry OWNER TO postgres;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id character varying NOT NULL,
    user_id character varying,
    type character varying NOT NULL,
    message character varying NOT NULL,
    is_read boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.orders (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    total_amount double precision NOT NULL,
    status character varying NOT NULL,
    items json,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    cancellation_reason character varying,
    history json,
    is_spam boolean DEFAULT false NOT NULL,
    spam_score double precision DEFAULT '0'::double precision NOT NULL,
    fingerprint character varying,
    spam_reason character varying
);


ALTER TABLE public.orders OWNER TO postgres;

--
-- Name: permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.permissions (
    id character varying NOT NULL,
    name character varying NOT NULL,
    code character varying NOT NULL,
    description character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.permissions OWNER TO postgres;

--
-- Name: product_bases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_bases (
    id character varying NOT NULL,
    name character varying NOT NULL,
    description text,
    sku character varying,
    price double precision NOT NULL,
    stock integer NOT NULL,
    status character varying NOT NULL,
    type character varying NOT NULL,
    category_id character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    slug character varying NOT NULL,
    seo_title character varying,
    seo_description character varying,
    images json,
    attributes json,
    seo_keywords character varying,
    tier_variations json
);


ALTER TABLE public.product_bases OWNER TO postgres;

--
-- Name: product_embeddings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_embeddings (
    id character varying NOT NULL,
    product_base_id character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    embedding public.vector(384) NOT NULL
);


ALTER TABLE public.product_embeddings OWNER TO postgres;

--
-- Name: product_variants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_variants (
    id character varying NOT NULL,
    product_base_id character varying NOT NULL,
    sku character varying NOT NULL,
    price double precision NOT NULL,
    stock integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tier_index json
);


ALTER TABLE public.product_variants OWNER TO postgres;

--
-- Name: rental_contracts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rental_contracts (
    id character varying NOT NULL,
    product_base_id character varying NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone NOT NULL,
    status character varying NOT NULL,
    terms json,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone
);


ALTER TABLE public.rental_contracts OWNER TO postgres;

--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.role_permissions (
    role_id character varying NOT NULL,
    permission_id character varying NOT NULL
);


ALTER TABLE public.role_permissions OWNER TO postgres;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id character varying NOT NULL,
    name character varying NOT NULL,
    code character varying NOT NULL,
    description character varying,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.system_settings (
    key character varying NOT NULL,
    value json NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.system_settings OWNER TO postgres;

--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_roles (
    user_id character varying NOT NULL,
    role_id character varying NOT NULL
);


ALTER TABLE public.user_roles OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id character varying NOT NULL,
    email character varying NOT NULL,
    name character varying,
    password character varying,
    status character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id character varying NOT NULL,
    username character varying NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: voice_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.voice_profiles (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    wake_words json NOT NULL,
    sleep_words json NOT NULL,
    greeting_template character varying NOT NULL,
    capabilities json NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    farewell_template character varying NOT NULL,
    chat_settings json DEFAULT '{}'::json NOT NULL,
    stt_anchors json NOT NULL,
    mic_sensitivity double precision NOT NULL,
    gemini_keys_enc text,
    ai_models json NOT NULL,
    primary_model character varying,
    discovered_models json NOT NULL
);


ALTER TABLE public.voice_profiles OWNER TO postgres;

--
-- Data for Name: agent_telemetry_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.agent_telemetry_logs (id, session_id, agent_name, intent_hash, input_tokens, output_tokens, cost_token, duration_ms, created_at, tenant_id, updated_at) FROM stdin;
e0db445a-5ca6-43e0-9546-4734eb6b8a5b		Groq-Whisper-STT	fcfad04d7ab6da90	0	0	0	330	2026-03-25 05:31:24.911617+00	default	2026-03-25 05:31:24.911631+00
35260a03-7b5c-449e-a9b2-5cce2bada9ce	8edb4d23-ebc5-4b66-a61a-3554eec2006d	TrinityCore-Tier_1	b7079b4c1dab3c69	0	0	0	2972	2026-03-25 05:31:27.893262+00	default	2026-03-25 05:31:27.893268+00
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
8989f4681a47
\.


--
-- Data for Name: appointments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.appointments (id, title, description, start_time, end_time, type, status, campaign_id, metadata_json, created_at, updated_at, deleted_at, tenant_id, recurring_type, recurring_metadata) FROM stdin;
375ce472-c261-4d8d-aa25-8d7698ff1dd2	Elite Strategic Planning	Phiên làm việc Neural đầu tiên để thiết lập lộ trình 2026.	2026-03-25 07:18:14.614022+00	2026-03-25 08:18:14.614022+00	STRATEGY	UPCOMING	\N	{}	2026-03-25 05:18:14.61578+00	2026-03-25 05:18:14.615785+00	\N	smartshop	none	{}
6a84d3b0-7453-45f6-8484-2c560179e041	Neural Scout: Competitor Audit	Tự động quét và phân tích chiến lược của đối thủ hàng tuần.	2026-03-26 15:18:14.614022+00	2026-03-26 16:18:14.614022+00	STRATEGY	UPCOMING	\N	{}	2026-03-25 05:18:14.618109+00	2026-03-25 05:18:14.618113+00	\N	smartshop	weekly	{"days": [1]}
\.


--
-- Data for Name: article_embeddings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.article_embeddings (id, article_id, created_at, updated_at, embedding) FROM stdin;
\.


--
-- Data for Name: articles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.articles (id, title, slug, excerpt, content, status, category, views, author_id, created_at, updated_at, deleted_at, tenant_id, seo_title, seo_description, featured_image, seo_keywords, seo_og_image) FROM stdin;
81766af0-0382-4dda-9564-a10d9f3b637c	Thời trang dạo phố #1	art-1-a4a8	\N	<p>Dữ liệu mẫu từ hệ thống AI 2026. Công nghệ lõi đang được kích hoạt...</p>	PUBLISHED	Chính sách	0	user_admin	2026-02-26 05:18:14.604393+00	2026-03-25 05:18:14.606569+00	\N	smartshop	\N	\N	\N	\N	\N
02cc060e-f972-4537-ba9e-ed5b652de7b7	Cập nhật BST mới #2	art-2-87a3	\N	<p>Dữ liệu mẫu từ hệ thống AI 2026. Công nghệ lõi đang được kích hoạt...</p>	PUBLISHED	Tin tức	0	user_admin	2026-03-02 05:18:14.604577+00	2026-03-25 05:18:14.606574+00	\N	smartshop	\N	\N	\N	\N	\N
432fff2d-183e-407e-bb78-7db9e5892d91	Tips bảo quản quần áo #3	art-3-1622	\N	<p>Dữ liệu mẫu từ hệ thống AI 2026. Công nghệ lõi đang được kích hoạt...</p>	PUBLISHED	Tin tức	0	user_admin	2026-03-24 05:18:14.604678+00	2026-03-25 05:18:14.606575+00	\N	smartshop	\N	\N	\N	\N	\N
\.


--
-- Data for Name: banners; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.banners (id, title, description, image_url, link_url, "position", order_index, is_active, device_type, tenant_id, created_at, updated_at, deleted_at) FROM stdin;
\.


--
-- Data for Name: campaign_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.campaign_events (id, campaign_id, event_type, payload, created_at, updated_at, tenant_id) FROM stdin;
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.categories (id, name, slug, parent_id, created_at, updated_at, deleted_at, tenant_id, description, seo_title, seo_description, image) FROM stdin;
cat_nam	Thời trang Nam	nam	\N	2026-03-25 05:18:14.595413+00	2026-03-25 05:18:14.595416+00	\N	smartshop	\N	\N	\N	\N
cat_nu	Thời trang Nữ	nu	\N	2026-03-25 05:18:14.595417+00	2026-03-25 05:18:14.595418+00	\N	smartshop	\N	\N	\N	\N
cat_ao_so_mi	Áo Sơ Mi	ao-so-mi	cat_nam	2026-03-25 05:18:14.597439+00	2026-03-25 05:18:14.597441+00	\N	smartshop	\N	\N	\N	\N
cat_quan_jean	Quần Jean	quan-jean	cat_nam	2026-03-25 05:18:14.597443+00	2026-03-25 05:18:14.597443+00	\N	smartshop	\N	\N	\N	\N
cat_dam_vay	Đầm & Váy	dam-vay	cat_nu	2026-03-25 05:18:14.597445+00	2026-03-25 05:18:14.597445+00	\N	smartshop	\N	\N	\N	\N
\.


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_messages (id, session_id, user_id, role, content, modality, created_at, updated_at, deleted_at, tenant_id) FROM stdin;
9dcb1cd3-b9e3-436f-bced-4b94bcbdfec8	account	user_admin	user	{"text": "manage skills"}	text	2026-03-25 05:30:57.006781+00	2026-03-25 05:30:57.014222+00	\N	default
795bfdf5-55de-463c-8a72-3589274a2707	8edb4d23-ebc5-4b66-a61a-3554eec2006d	user_admin	user	{"text": "Vi\\u1ebft b\\u00e0i Th\\u1eddi trang Na cao c\\u1ea5p"}	voice	2026-03-25 05:31:27.935992+00	2026-03-25 05:31:27.935996+00	\N	default
a2e7b8f2-3b3e-491d-b662-67efc4d8eaa3	8edb4d23-ebc5-4b66-a61a-3554eec2006d	user_admin	assistant	{"text": "D\\u1ea1 th\\u01b0a S\\u1ebfp, em \\u0111ang kh\\u1edfi t\\u1ea1o XoHi Core \\u0111\\u1ec3 ph\\u00e2n t\\u00edch \\u00fd t\\u01b0\\u1edfng c\\u1ee7a S\\u1ebfp \\u0111\\u00e2y \\u1ea1. S\\u1ebfp \\u0111\\u1ee3i em m\\u1ed9t ch\\u00fat nh\\u00e9! \\ud83d\\ude80", "ui_action": "CONTENT_CREATE", "router_tier": "1", "category": "CONTENT_CREATE", "campaign_id": "180197df-f39e-43a5-b95d-5d25a8c1a6eb", "step": 1, "status": "PROCESSING", "action": "STEP1_REVIEW"}	voice	2026-03-25 05:31:27.940643+00	2026-03-25 05:31:27.940648+00	\N	default
49a996d3-5374-4ff9-a644-b1fe4412ebe7	account	user_admin	assistant	{"text": "[Content] Ho\\u00e0n th\\u00e0nh B\\u01b0\\u1edbc 1. \\u0110ang ch\\u1edd s\\u1ebfp duy\\u1ec7t.", "category": "CONTENT_CREATE", "campaign_id": "180197df-f39e-43a5-b95d-5d25a8c1a6eb", "step": 1, "status": "WAITING_FOR_REVIEW"}	text	2026-03-25 05:31:39.098517+00	2026-03-25 05:31:39.098517+00	\N	default
6c1df38b-53ea-4dea-ad49-1ae5b8d07283	account	user_admin	assistant	{"text": "[Content] Ho\\u00e0n th\\u00e0nh B\\u01b0\\u1edbc 1. \\u0110ang ch\\u1edd s\\u1ebfp duy\\u1ec7t.", "category": "CONTENT_CREATE", "campaign_id": "180197df-f39e-43a5-b95d-5d25a8c1a6eb", "step": 1, "status": "WAITING_FOR_REVIEW"}	text	2026-03-25 05:31:39.098918+00	2026-03-25 05:31:39.098918+00	\N	default
\.


--
-- Data for Name: content_campaigns; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.content_campaigns (id, source_input, reviewer_type, current_step, status, gold_metadata, topic_data, assets_data, outline_data, draft_content, unique_score, final_html, created_at, updated_at, deleted_at, tenant_id, search_count, user_id, category) FROM stdin;
180197df-f39e-43a5-b95d-5d25a8c1a6eb	Viết bài Thời trang Na cao cấp	ADMIN_MANUAL	1	WAITING_FOR_REVIEW	{"content_mode": "viral", "creation_config": {"scouting_active": true}}	{"title": "Th\\u1eddi trang nam cao c\\u1ea5p: N\\u00e2ng t\\u1ea7m kh\\u00ed ch\\u1ea5t, \\u0111\\u1ecbnh h\\u00ecnh v\\u1ecb th\\u1ebf!", "primary_keyword": "th\\u1eddi trang nam cao c\\u1ea5p", "secondary_keywords": ["\\u00e1o kho\\u00e1c nam cao c\\u1ea5p", "th\\u1eddi trang golf nam", "ph\\u1ee5 ki\\u1ec7n da nam", "th\\u1eddi trang c\\u00f4ng s\\u1edf nam cao c\\u1ea5p"], "persona": "S\\u1eafc s\\u1ea3o/Viral", "description": "Kh\\u00e1m ph\\u00e1 th\\u1ebf gi\\u1edbi th\\u1eddi trang nam cao c\\u1ea5p, t\\u1eeb nh\\u1eefng b\\u1ed9 c\\u00e1nh c\\u00f4ng s\\u1edf l\\u1ecbch l\\u00e3m \\u0111\\u1ebfn trang ph\\u1ee5c golf \\u0111\\u1eb3ng c\\u1ea5p v\\u00e0 ph\\u1ee5 ki\\u1ec7n da tinh t\\u1ebf. N\\u00e2ng t\\u1ea7m phong c\\u00e1ch v\\u00e0 kh\\u1eb3ng \\u0111\\u1ecbnh v\\u1ecb th\\u1ebf ph\\u00e1i m\\u1ea1nh.", "category": "Tin t\\u1ee9c", "ground_truth": "D\\u1ef1a tr\\u00ean d\\u1eef li\\u1ec7u Google, 'th\\u1eddi trang na cao c\\u1ea5p' \\u0111\\u01b0\\u1ee3c x\\u00e1c \\u0111\\u1ecbnh l\\u00e0 l\\u1ed7i ch\\u00ednh t\\u1ea3 v\\u00e0 th\\u1ef1c th\\u1ec3 m\\u1ee5c ti\\u00eau l\\u00e0 'th\\u1eddi trang nam cao c\\u1ea5p'. C\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u v\\u00e0 s\\u1ea3n ph\\u1ea9m n\\u1ed5i b\\u1eadt bao g\\u1ed3m NORESSY (th\\u1eddi trang golf nam), ERKE (\\u00e1o kho\\u00e1c gi\\u00f3 nam), Butuni (th\\u1eddi trang da cao c\\u1ea5p, ph\\u1ee5 ki\\u1ec7n), v\\u00e0 May10 (th\\u1eddi trang c\\u00f4ng s\\u1edf, veston nam). B\\u00e0i vi\\u1ebft s\\u1ebd t\\u1eadp trung v\\u00e0o xu h\\u01b0\\u1edbng v\\u00e0 c\\u00e1ch ch\\u1ecdn l\\u1ef1a trang ph\\u1ee5c cao c\\u1ea5p cho ph\\u00e1i m\\u1ea1nh.", "creation_config": {"style": "Viral", "word_count": 500, "max_assets": 10, "max_sections": 3, "scouting_active": true, "scheduling": {"is_active": true, "frequency": "daily", "schedule_at": "09:00", "timezone": "UTC+7", "notifications": true}}, "scout_report": {"topic": "th\\u1eddi trang nam cao c\\u1ea5p", "headlines": [{"title": "B\\u00ed Quy\\u1ebft N\\u00e2ng T\\u1ea7m Phong C\\u00e1ch Qu\\u00fd \\u00d4ng: Kh\\u00e1m ph\\u00e1 'Th\\u1eddi Trang Nam Cao C\\u1ea5p' KH\\u00d4NG TH\\u1ec2 B\\u1ece L\\u1ee0!", "type": "ADS"}, {"title": "TOP 15 Th\\u01b0\\u01a1ng Hi\\u1ec7u Th\\u1eddi Trang Nam Cao C\\u1ea5p '\\u0110\\u1eb3ng C\\u1ea5p Nh\\u1ea5t' T\\u1ea1i Vi\\u1ec7t Nam (2026 UPDATE)", "type": "TOP_10"}, {"title": "Gi\\u1ea3i M\\u00e3 S\\u1ee9c H\\u00fat C\\u1ee7a 'Th\\u1eddi Trang Nam Cao C\\u1ea5p': H\\u01a1n C\\u1ea3 Qu\\u1ea7n \\u00c1o, \\u0110\\u00f3 L\\u00e0 Tuy\\u00ean Ng\\u00f4n Phong C\\u00e1ch!", "type": "AI_AUGMENTED"}, {"title": "Th\\u1eddi Trang C\\u00f4ng S\\u1edf Cao C\\u1ea5p: Ch\\u1ecdn L\\u1ef1a \\u0110\\u00daNG CHU\\u1ea8N cho Ng\\u01b0\\u1eddi \\u0110\\u00e0n \\u00d4ng Hi\\u1ec7n \\u0110\\u1ea1i", "type": "TOP_10"}, {"title": "Kh\\u00e1m Ph\\u00e1 Ch\\u1ea5t Li\\u1ec7u & K\\u1ef9 Thu\\u1eadt May \\u0110o \\u0110\\u1ec9nh Cao Trong Th\\u1eddi Trang Nam Cao C\\u1ea5p", "type": "AI_AUGMENTED"}, {"title": "\\u0110\\u1eb3ng C\\u1ea5p Th\\u01b0\\u1ee3ng L\\u01b0u: C\\u00e1ch \\u0110\\u1ea7u T\\u01b0 V\\u00e0o T\\u1ee7 \\u0110\\u1ed3 Th\\u1eddi Trang Nam Cao C\\u1ea5p \\u0110\\u00e1ng Gi\\u00e1", "type": "ADS"}, {"title": "5 Sai L\\u1ea7m Ph\\u1ed5 Bi\\u1ebfn Khi Ch\\u1ecdn 'Th\\u1eddi Trang Nam Cao C\\u1ea5p' & Gi\\u1ea3i Ph\\u00e1p T\\u1eeb Chuy\\u00ean Gia", "type": "AI_AUGMENTED"}, {"title": "ARISTINO, Adam Store, Owen: Cu\\u1ed9c Chi\\u1ebfn Phong C\\u00e1ch Gi\\u1eefa C\\u00e1c Th\\u01b0\\u01a1ng Hi\\u1ec7u Nam Cao C\\u1ea5p Vi\\u1ec7t", "type": "TOP_10"}], "semantic_keywords": ["th\\u1eddi trang nam cao c\\u1ea5p", "th\\u01b0\\u01a1ng hi\\u1ec7u th\\u1eddi trang nam cao c\\u1ea5p", "qu\\u1ea7n \\u00e1o nam cao c\\u1ea5p", "phong c\\u00e1ch qu\\u00fd \\u00f4ng", "th\\u1eddi trang c\\u00f4ng s\\u1edf nam cao c\\u1ea5p", "\\u00e1o vest nam cao c\\u1ea5p", "ph\\u1ee5 ki\\u1ec7n th\\u1eddi trang nam cao c\\u1ea5p", "ch\\u1ea5t li\\u1ec7u cao c\\u1ea5p nam", "mua th\\u1eddi trang nam ch\\u00ednh h\\u00e3ng", "l\\u1ecbch l\\u00e3m v\\u00e0 m\\u1ea1nh m\\u1ebd", "\\u0111\\u1eb3ng c\\u1ea5p th\\u1eddi trang nam", "xu h\\u01b0\\u1edbng th\\u1eddi trang nam cao c\\u1ea5p"], "strategic_analysis": "## B\\u1ea2N TR\\u00ccNH B\\u00c1O CHI\\u1ebeN L\\u01af\\u1ee2C N\\u1ed8I DUNG \\u2014 TH\\u1edcI TRANG NAM CAO C\\u1ea4P\\n\\n### 1. Search Intent Decoding (Gi\\u1ea3i M\\u00e3 M\\u1ee5c \\u0110\\u00edch & N\\u1ed7i \\u0110au Ng\\u01b0\\u1eddi D\\u00f9ng)\\n\\nKhi t\\u00ecm ki\\u1ebfm \\"th\\u1eddi trang nam cao c\\u1ea5p\\", ng\\u01b0\\u1eddi d\\u00f9ng kh\\u00f4ng ch\\u1ec9 \\u0111\\u01a1n thu\\u1ea7n mu\\u1ed1n mua s\\u1eafm qu\\u1ea7n \\u00e1o. H\\u1ecd \\u0111ang t\\u00ecm ki\\u1ebfm:\\n\\n*   **Aspiration (Kh\\u00e1t v\\u1ecdng):** Tr\\u1edf th\\u00e0nh m\\u1ed9t \\"qu\\u00fd \\u00f4ng l\\u1ecbch l\\u00e3m\\", \\"sang tr\\u1ecdng\\", \\"\\u0111\\u1eb3ng c\\u1ea5p\\" nh\\u01b0 nh\\u1eefng g\\u00ec c\\u00e1c \\u0111\\u1ed1i th\\u1ee7 (Aristino, An Ph\\u01b0\\u1edbc) \\u0111\\u00e3 \\u0111\\u1ecbnh v\\u1ecb. H\\u1ecd mu\\u1ed1n th\\u1ec3 hi\\u1ec7n \\u0111\\u1ecba v\\u1ecb, s\\u1ef1 t\\u1ef1 tin v\\u00e0 gu th\\u1ea9m m\\u1ef9 c\\u00e1 nh\\u00e2n.\\n*   **Quality Assurance (\\u0110\\u1ea3m b\\u1ea3o ch\\u1ea5t l\\u01b0\\u1ee3ng):** N\\u1ed7i s\\u1ee3 mua ph\\u1ea3i h\\u00e0ng nh\\u00e1i, h\\u00e0ng k\\u00e9m ch\\u1ea5t l\\u01b0\\u1ee3ng, kh\\u00f4ng x\\u1ee9ng \\u0111\\u00e1ng v\\u1edbi s\\u1ed1 ti\\u1ec1n b\\u1ecf ra. H\\u1ecd t\\u00ecm ki\\u1ebfm \\"h\\u00e0ng hi\\u1ec7u\\", \\"ch\\u00ednh h\\u00e3ng\\", \\"ch\\u1ea5t li\\u1ec7u cao c\\u1ea5p\\" (May10, Owen, Vua H\\u00e0ng Hi\\u1ec7u).\\n*   **Guidance & Discovery (H\\u01b0\\u1edbng d\\u1eabn & Kh\\u00e1m ph\\u00e1):** H\\u1ecd mu\\u1ed1n bi\\u1ebft \\u0111\\u00e2u l\\u00e0 nh\\u1eefng \\"th\\u01b0\\u01a1ng hi\\u1ec7u h\\u00e0ng \\u0111\\u1ea7u\\" (Adam Store, ACFC), \\"m\\u1eabu m\\u00e3 \\u0111a d\\u1ea1ng tinh t\\u1ebf\\" v\\u00e0 c\\u00e1ch ph\\u1ed1i \\u0111\\u1ed3 sao cho ph\\u00f9 h\\u1ee3p v\\u1edbi v\\u00f3c d\\u00e1ng, m\\u1ee5c \\u0111\\u00edch s\\u1eed d\\u1ee5ng (c\\u00f4ng s\\u1edf, s\\u1ef1 ki\\u1ec7n, d\\u1ea1o ph\\u1ed1).\\n*   **Value (Gi\\u00e1 tr\\u1ecb):** D\\u00f9 l\\u00e0 s\\u1ea3n ph\\u1ea9m cao c\\u1ea5p, h\\u1ecd v\\u1eabn quan t\\u00e2m \\u0111\\u1ebfn c\\u00e1c ch\\u01b0\\u01a1ng tr\\u00ecnh \\"khuy\\u1ebfn m\\u00e3i h\\u1ea5p d\\u1eabn\\" (ACFC) ho\\u1eb7c \\"\\u0111\\u1ea7u t\\u01b0\\" v\\u00e0o nh\\u1eefng m\\u00f3n \\u0111\\u1ed3 c\\u00f3 gi\\u00e1 tr\\u1ecb s\\u1eed d\\u1ee5ng l\\u00e2u d\\u00e0i.\\n*   **Experience (Tr\\u1ea3i nghi\\u1ec7m):** Mong mu\\u1ed1n tr\\u1ea3i nghi\\u1ec7m mua s\\u1eafm ti\\u1ec7n l\\u1ee3i (online, giao h\\u00e0ng to\\u00e0n qu\\u1ed1c) v\\u00e0 d\\u1ecbch v\\u1ee5 t\\u01b0 v\\u1ea5n chuy\\u00ean nghi\\u1ec7p.\\n\\n### 2. Competitor Gap Analysis (Ph\\u00e2n T\\u00edch Kho\\u1ea3ng Tr\\u1ed1ng \\u0110\\u1ed1i Th\\u1ee7)\\n\\nC\\u00e1c \\u0111\\u1ed1i th\\u1ee7 hi\\u1ec7n t\\u1ea1i ch\\u1ee7 y\\u1ebfu t\\u1eadp trung v\\u00e0o vi\\u1ec7c:\\n\\n*   **T\\u1ef1 qu\\u1ea3ng b\\u00e1 th\\u01b0\\u01a1ng hi\\u1ec7u:** Nh\\u1ea5n m\\u1ea1nh s\\u1ea3n ph\\u1ea9m c\\u1ee7a ri\\u00eang h\\u1ecd (Aristino, Owen, May10, An Ph\\u01b0\\u1edbc).\\n*   **Li\\u1ec7t k\\u00ea th\\u01b0\\u01a1ng hi\\u1ec7u/s\\u1ea3n ph\\u1ea9m:** Cung c\\u1ea5p danh s\\u00e1ch c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u ho\\u1eb7c t\\u1ed5ng h\\u1ee3p s\\u1ea3n ph\\u1ea9m m\\u00e0 kh\\u00f4ng \\u0111i s\\u00e2u v\\u00e0o chi ti\\u1ebft (ACFC, Vua H\\u00e0ng Hi\\u1ec7u, c\\u00e1c b\\u00e0i \\"Top 15\\").\\n*   **\\u0110\\u1ecbnh v\\u1ecb chung chung:** S\\u1eed d\\u1ee5ng c\\u00e1c t\\u1eeb kh\\u00f3a \\"l\\u1ecbch l\\u00e3m\\", \\"sang tr\\u1ecdng\\", \\"\\u0111\\u1eb3ng c\\u1ea5p\\" nh\\u01b0ng \\u00edt khi gi\\u1ea3i th\\u00edch *t\\u1ea1i sao* s\\u1ea3n ph\\u1ea9m c\\u1ee7a h\\u1ecd ho\\u1eb7c m\\u1ed9t phong c\\u00e1ch c\\u1ee5 th\\u1ec3 l\\u1ea1i \\u0111\\u1ea1t \\u0111\\u01b0\\u1ee3c \\u0111i\\u1ec1u \\u0111\\u00f3.\\n\\n**Nh\\u1eefng m\\u1ea3ng n\\u1ed9i dung/insight m\\u00e0 \\u0111\\u1ed1i th\\u1ee7 \\u0111ang b\\u1ecf tr\\u1ed1ng ho\\u1eb7c l\\u00e0m h\\u1eddi h\\u1ee3t:**\\n\\n*   **Chuy\\u00ean s\\u00e2u v\\u1ec1 ch\\u1ea5t li\\u1ec7u & k\\u1ef9 thu\\u1eadt:** Kh\\u00f4ng c\\u00f3 b\\u00e0i vi\\u1ebft n\\u00e0o th\\u1ef1c s\\u1ef1 \\u0111i s\\u00e2u v\\u00e0o ph\\u00e2n t\\u00edch c\\u00e1c lo\\u1ea1i v\\u1ea3i cao c\\u1ea5p (len cashmere, l\\u1ee5a, cotton Ai C\\u1eadp, da th\\u1eadt...), k\\u1ef9 thu\\u1eadt may \\u0111o (bespoke, made-to-measure), quy tr\\u00ecnh s\\u1ea3n xu\\u1ea5t t\\u1ea1o n\\u00ean s\\u1ef1 kh\\u00e1c bi\\u1ec7t c\\u1ee7a \\"cao c\\u1ea5p\\" so v\\u1edbi \\"ph\\u1ed5 th\\u00f4ng\\". \\u0110\\u00e2y l\\u00e0 \\"Information Gain\\" c\\u1ef1c l\\u1edbn.\\n*   **H\\u01b0\\u1edbng d\\u1eabn phong c\\u00e1ch c\\u00e1 nh\\u00e2n h\\u00f3a:** Thi\\u1ebfu c\\u00e1c b\\u00e0i vi\\u1ebft t\\u01b0 v\\u1ea5n c\\u1ee5 th\\u1ec3 cho t\\u1eebng d\\u00e1ng ng\\u01b0\\u1eddi, \\u0111\\u1ed9 tu\\u1ed5i, ngh\\u1ec1 nghi\\u1ec7p ho\\u1eb7c s\\u1ef1 ki\\u1ec7n c\\u1ee5 th\\u1ec3. V\\u00ed d\\u1ee5: \\"Ch\\u1ecdn vest cao c\\u1ea5p cho ng\\u01b0\\u1eddi c\\u00f3 vai r\\u1ed9ng\\", \\"Phong c\\u00e1ch smart casual cao c\\u1ea5p cho bu\\u1ed5i h\\u1eb9n cu\\u1ed1i tu\\u1ea7n\\".\\n*   **B\\u00ed quy\\u1ebft \\u0111\\u1ea7u t\\u01b0 t\\u1ee7 \\u0111\\u1ed3 th\\u00f4ng minh:** Kh\\u00f4ng c\\u00f3 n\\u1ed9i dung v\\u1ec1 c\\u00e1ch x\\u00e2y d\\u1ef1ng m\\u1ed9t t\\u1ee7 \\u0111\\u1ed3 capsule (t\\u1ed1i gi\\u1ea3n nh\\u01b0ng \\u0111\\u1ee7 d\\u00f9ng), c\\u00e1c m\\u00f3n \\u0111\\u1ed3 \\"must-have\\" \\u0111\\u00e1ng \\u0111\\u1ec3 \\u0111\\u1ea7u t\\u01b0 l\\u00e2u d\\u00e0i, ho\\u1eb7c c\\u00e1ch b\\u1ea3o qu\\u1ea3n trang ph\\u1ee5c cao c\\u1ea5p \\u0111\\u1ec3 t\\u0103ng tu\\u1ed5i th\\u1ecd.\\n*   **So s\\u00e1nh & \\u0111\\u00e1nh gi\\u00e1 kh\\u00e1ch quan:** Thi\\u1ebfu c\\u00e1c b\\u00e0i so s\\u00e1nh chi ti\\u1ebft gi\\u1eefa c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u cao c\\u1ea5p (v\\u00ed d\\u1ee5: Aristino vs. Adam Store v\\u1ec1 ch\\u1ea5t l\\u01b0\\u1ee3ng v\\u1ea3i, \\u0111\\u01b0\\u1eddng may, \\u0111\\u1ed9 b\\u1ec1n) ho\\u1eb7c gi\\u1eefa th\\u01b0\\u01a1ng hi\\u1ec7u n\\u1ed9i \\u0111\\u1ecba v\\u00e0 qu\\u1ed1c t\\u1ebf v\\u1ec1 gi\\u00e1 tr\\u1ecb nh\\u1eadn \\u0111\\u01b0\\u1ee3c so v\\u1edbi chi ph\\u00ed.\\n*   **C\\u00e2u chuy\\u1ec7n th\\u01b0\\u01a1ng hi\\u1ec7u & gi\\u00e1 tr\\u1ecb c\\u1ed1t l\\u00f5i:** Ngo\\u00e0i slogan, \\u00edt th\\u01b0\\u01a1ng hi\\u1ec7u k\\u1ec3 c\\u00e2u chuy\\u1ec7n s\\u00e2u s\\u1eafc v\\u1ec1 tri\\u1ebft l\\u00fd thi\\u1ebft k\\u1ebf, ngu\\u1ed3n c\\u1ea3m h\\u1ee9ng, ho\\u1eb7c cam k\\u1ebft v\\u1ec1 \\u0111\\u1ea1o \\u0111\\u1ee9c/b\\u1ec1n v\\u1eefng (n\\u1ebfu c\\u00f3) trong ng\\u00e0nh th\\u1eddi trang cao c\\u1ea5p.\\n*   **Kh\\u00e1m ph\\u00e1 xu h\\u01b0\\u1edbng & d\\u1ef1 b\\u00e1o:** C\\u00e1c b\\u00e0i vi\\u1ebft th\\u01b0\\u1eddng ch\\u1ec9 c\\u1eadp nh\\u1eadt s\\u1ea3n ph\\u1ea9m m\\u1edbi, \\u00edt \\u0111i s\\u00e2u v\\u00e0o ph\\u00e2n t\\u00edch xu h\\u01b0\\u1edbng th\\u1eddi trang nam cao c\\u1ea5p to\\u00e0n c\\u1ea7u v\\u00e0 c\\u00e1ch \\u00e1p d\\u1ee5ng t\\u1ea1i Vi\\u1ec7t Nam.\\n\\n### 3. Elite Execution Roadmap (C\\u00f4ng Th\\u1ee9c \\u0110\\u1ec3 \\u0110\\u1ea1t Information Gain V\\u01b0\\u1ee3t Top 1)\\n\\n\\u0110\\u1ec3 t\\u1ea1o ra n\\u1ed9i dung c\\u00f3 \\"Information Gain\\" cao nh\\u1ea5t v\\u00e0 v\\u01b0\\u1ee3t xa c\\u00e1c \\u0111\\u1ed1i th\\u1ee7, XoHi Intelligence c\\u1ea7n t\\u1eadp trung v\\u00e0o s\\u1ef1 chuy\\u00ean s\\u00e2u, c\\u00e1 nh\\u00e2n h\\u00f3a v\\u00e0 gi\\u00e1 tr\\u1ecb th\\u1ef1c s\\u1ef1 cho ng\\u01b0\\u1eddi d\\u00f9ng:\\n\\n1.  **\\"Ultimate Guide\\" v\\u1ec1 Ch\\u1ea5t Li\\u1ec7u & K\\u1ef9 Thu\\u1eadt May \\u0110o:**\\n    *   **N\\u1ed9i dung:** B\\u00e0i vi\\u1ebft chuy\\u00ean s\\u00e2u v\\u1ec1 c\\u00e1c lo\\u1ea1i v\\u1ea3i (cotton Pima, len merino, l\\u1ee5a t\\u01a1 t\\u1eb1m, linen cao c\\u1ea5p, v.v.), c\\u00f4ng ngh\\u1ec7 d\\u1ec7t, quy tr\\u00ecnh may th\\u1ee7 c\\u00f4ng (hand-stitched details), v\\u00e0 s\\u1ef1 kh\\u00e1c bi\\u1ec7t v\\u1ec1 form d\\u00e1ng, \\u0111\\u1ed9 b\\u1ec1n. \\u0110i k\\u00e8m h\\u00ecnh \\u1ea3nh/video minh h\\u1ecda c\\u1eadn c\\u1ea3nh.\\n    *   **M\\u1ee5c ti\\u00eau:** \\u0110\\u1ecbnh v\\u1ecb l\\u00e0 ngu\\u1ed3n th\\u00f4ng tin uy t\\u00edn, chi ti\\u1ebft nh\\u1ea5t, gi\\u1ea3i quy\\u1ebft tri\\u1ec7t \\u0111\\u1ec3 n\\u1ed7i \\u0111au v\\u1ec1 ch\\u1ea5t l\\u01b0\\u1ee3ng v\\u00e0 s\\u1ef1 am hi\\u1ec3u.\\n\\n2.  **\\"Masterclass\\" Phong C\\u00e1ch C\\u00e1 Nh\\u00e2n H\\u00f3a:**\\n    *   **N\\u1ed9i dung:** Chu\\u1ed7i b\\u00e0i vi\\u1ebft/video h\\u01b0\\u1edbng d\\u1eabn c\\u00e1ch ch\\u1ecdn v\\u00e0 ph\\u1ed1i \\u0111\\u1ed3 cao c\\u1ea5p cho t\\u1eebng d\\u00e1ng ng\\u01b0\\u1eddi (d\\u00e1ng V, ch\\u1eef nh\\u1eadt, qu\\u1ea3 l\\u00ea), t\\u1eebng \\u0111\\u1ed9 tu\\u1ed5i (25-35, 35-45, 45+), v\\u00e0 c\\u00e1c s\\u1ef1 ki\\u1ec7n c\\u1ee5 th\\u1ec3 (business casual, black-tie, ti\\u1ec7c t\\u00f9ng, du l\\u1ecbch cao c\\u1ea5p). \\u0110\\u1ec1 xu\\u1ea5t c\\u00e1c m\\u00f3n \\u0111\\u1ed3 \\"linh h\\u1ed3n\\" cho t\\u1eebng phong c\\u00e1ch.\\n    *   **M\\u1ee5c ti\\u00eau:** Cung c\\u1ea5p gi\\u00e1 tr\\u1ecb th\\u1ef1c ti\\u1ec5n, gi\\u00fap ng\\u01b0\\u1eddi d\\u00f9ng t\\u1ef1 tin h\\u01a1n trong vi\\u1ec7c \\u0111\\u1ecbnh h\\u00ecnh phong c\\u00e1ch ri\\u00eang.\\n\\n3.  **\\"T\\u1ee7 \\u0110\\u1ed3 Qu\\u00fd \\u00d4ng Th\\u00f4ng Th\\u00e1i\\" \\u2013 H\\u01b0\\u1edbng D\\u1eabn \\u0110\\u1ea7u T\\u01b0 & B\\u1ea3o Qu\\u1ea3n:**\\n    *   **N\\u1ed9i dung:** B\\u00e0i vi\\u1ebft chi\\u1ebfn l\\u01b0\\u1ee3c v\\u1ec1 c\\u00e1ch x\\u00e2y d\\u1ef1ng t\\u1ee7 \\u0111\\u1ed3 \\"capsule\\" th\\u1eddi trang nam cao c\\u1ea5p (5-7 m\\u00f3n \\u0111\\u1ed3 c\\u1ed1t l\\u00f5i c\\u00f3 th\\u1ec3 ph\\u1ed1i th\\u00e0nh 20+ outfit). H\\u01b0\\u1edbng d\\u1eabn ch\\u1ecdn c\\u00e1c m\\u00f3n \\u0111\\u1ed3 v\\u01b0\\u1ee3t th\\u1eddi gian, m\\u1eb9o b\\u1ea3o qu\\u1ea3n (gi\\u1eb7t \\u1ee7i, c\\u1ea5t gi\\u1eef, s\\u1eeda ch\\u1eefa) \\u0111\\u1ec3 k\\u00e9o d\\u00e0i tu\\u1ed5i th\\u1ecd s\\u1ea3n ph\\u1ea9m cao c\\u1ea5p.\\n    *   **M\\u1ee5c ti\\u00eau:** Gi\\u1ea3i quy\\u1ebft n\\u1ed7i lo v\\u1ec1 chi ph\\u00ed v\\u00e0 gi\\u00fap ng\\u01b0\\u1eddi d\\u00f9ng t\\u1ed1i \\u01b0u h\\u00f3a kho\\u1ea3n \\u0111\\u1ea7u t\\u01b0 v\\u00e0o th\\u1eddi trang.\\n\\n4.  **\\"B\\u00f3c T\\u00e1ch S\\u1ef1 Th\\u1eadt\\": So S\\u00e1nh Th\\u01b0\\u01a1ng Hi\\u1ec7u & Ti\\u00eau Ch\\u00ed \\u0110\\u00e1nh Gi\\u00e1 Th\\u1ef1c T\\u1ebf:**\\n    *   **N\\u1ed9i dung:** Ph\\u00e2n t\\u00edch kh\\u00e1ch quan c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u (v\\u00ed d\\u1ee5: ARISTINO vs. Owen \\u2013 \\u0111i\\u1ec3m m\\u1ea1nh v\\u1ec1 vest, \\u0111i\\u1ec3m y\\u1ebfu v\\u1ec1 ph\\u1ee5 ki\\u1ec7n; May10 vs. An Ph\\u01b0\\u1edbc \\u2013 kh\\u00e1c bi\\u1ec7t v\\u1ec1 ph\\u00e2n kh\\u00fac c\\u00f4ng s\\u1edf) d\\u1ef1a tr\\u00ean ti\\u00eau ch\\u00ed: ch\\u1ea5t li\\u1ec7u, \\u0111\\u01b0\\u1eddng may, \\u0111\\u1ed9 b\\u1ec1n, d\\u1ecbch v\\u1ee5 kh\\u00e1ch h\\u00e0ng, gi\\u00e1 tr\\u1ecb th\\u01b0\\u01a1ng hi\\u1ec7u. C\\u00f3 th\\u1ec3 m\\u1edf r\\u1ed9ng so s\\u00e1nh v\\u1edbi c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u qu\\u1ed1c t\\u1ebf.\\n    *   **M\\u1ee5c ti\\u00eau:** Cung c\\u1ea5p th\\u00f4ng tin minh b\\u1ea1ch, gi\\u00fap ng\\u01b0\\u1eddi d\\u00f9ng \\u0111\\u01b0a ra quy\\u1ebft \\u0111\\u1ecbnh mua s\\u1eafm th\\u00f4ng th\\u00e1i, tr\\u00e1nh nh\\u1eefng l\\u1eddi qu\\u1ea3ng c\\u00e1o chung chung.\\n\\n5.  **C\\u00e2u Chuy\\u1ec7n \\u0110\\u1eb1ng Sau \\"\\u0110\\u1eb3ng C\\u1ea5p\\":**\\n    *   **N\\u1ed9i dung:** Ph\\u1ecfng v\\u1ea5n nh\\u00e0 thi\\u1ebft k\\u1ebf, th\\u1ee3 may l\\u00e0nh ngh\\u1ec1, ho\\u1eb7c k\\u1ec3 c\\u00e2u chuy\\u1ec7n v\\u1ec1 ngu\\u1ed3n g\\u1ed1c ch\\u1ea5t li\\u1ec7u, qu\\u00e1 tr\\u00ecnh t\\u1ea1o ra m\\u1ed9t s\\u1ea3n ph\\u1ea9m cao c\\u1ea5p. L\\u1ed3ng gh\\u00e9p y\\u1ebfu t\\u1ed1 b\\u1ec1n v\\u1eefng, tr\\u00e1ch nhi\\u1ec7m x\\u00e3 h\\u1ed9i n\\u1ebfu c\\u00f3.\\n    *   **M\\u1ee5c ti\\u00eau:** T\\u1ea1o chi\\u1ec1u s\\u00e2u c\\u1ea3m x\\u00fac, k\\u1ebft n\\u1ed1i ng\\u01b0\\u1eddi d\\u00f9ng v\\u1edbi gi\\u00e1 tr\\u1ecb c\\u1ed1t l\\u00f5i c\\u1ee7a th\\u1eddi trang cao c\\u1ea5p, kh\\u00f4ng ch\\u1ec9 l\\u00e0 v\\u1ebb b\\u1ec1 ngo\\u00e0i.\\n\\n**Ch\\u1ec9 s\\u1ed1 Th\\u00e0nh c\\u00f4ng (KPIs):** T\\u0103ng th\\u1eddi gian \\u1edf l\\u1ea1i trang, gi\\u1ea3m t\\u1ef7 l\\u1ec7 tho\\u00e1t, t\\u0103ng l\\u01b0\\u1ee3ng chia s\\u1ebb n\\u1ed9i dung, t\\u0103ng t\\u1ef7 l\\u1ec7 chuy\\u1ec3n \\u0111\\u1ed5i t\\u1eeb b\\u00e0i vi\\u1ebft th\\u00f4ng tin sang trang s\\u1ea3n ph\\u1ea9m (n\\u1ebfu c\\u00f3), c\\u1ea3i thi\\u1ec7n v\\u1ecb tr\\u00ed x\\u1ebfp h\\u1ea1ng cho c\\u00e1c t\\u1eeb kh\\u00f3a ng\\u00e1ch v\\u00e0 t\\u1ed5ng th\\u1ec3.\\n\\n### 4. Ground Truth Summary (T\\u00f3m T\\u1eaft B\\u1ed1i C\\u1ea3nh Trinh S\\u00e1t)\\n\\nTh\\u1ecb tr\\u01b0\\u1eddng \\"th\\u1eddi trang nam cao c\\u1ea5p\\" t\\u1ea1i Vi\\u1ec7t Nam \\u0111ang s\\u00f4i \\u0111\\u1ed9ng v\\u1edbi s\\u1ef1 g\\u00f3p m\\u1eb7t c\\u1ee7a c\\u1ea3 c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u n\\u1ed9i \\u0111\\u1ecba c\\u00f3 v\\u1ecb th\\u1ebf v\\u1eefng ch\\u1eafc (Aristino, Adam Store, May10, Owen, An Ph\\u01b0\\u1edbc) v\\u00e0 c\\u00e1c nh\\u00e0 ph\\u00e2n ph\\u1ed1i th\\u01b0\\u01a1ng hi\\u1ec7u qu\\u1ed1c t\\u1ebf (ACFC, Vua H\\u00e0ng Hi\\u1ec7u). C\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u t\\u1eadp trung v\\u00e0o \\u0111\\u1ecbnh v\\u1ecb \\"qu\\u00fd \\u00f4ng\\", \\"l\\u1ecbch l\\u00e3m\\", \\"sang tr\\u1ecdng\\", \\"\\u0111\\u1eb3ng c\\u1ea5p\\" v\\u1edbi \\"ch\\u1ea5t li\\u1ec7u cao c\\u1ea5p\\" v\\u00e0 \\"thi\\u1ebft k\\u1ebf tinh t\\u1ebf\\". Tuy nhi\\u00ean, h\\u1ea7u h\\u1ebft n\\u1ed9i dung hi\\u1ec7n t\\u1ea1i d\\u1eebng l\\u1ea1i \\u1edf vi\\u1ec7c gi\\u1edbi thi\\u1ec7u s\\u1ea3n ph\\u1ea9m, li\\u1ec7t k\\u00ea th\\u01b0\\u01a1ng hi\\u1ec7u ho\\u1eb7c qu\\u1ea3ng b\\u00e1 chung chung, b\\u1ecf qua c\\u01a1 h\\u1ed9i cung c\\u1ea5p th\\u00f4ng tin chuy\\u00ean s\\u00e2u, c\\u00e1 nh\\u00e2n h\\u00f3a v\\u00e0 gi\\u1ea3i quy\\u1ebft tri\\u1ec7t \\u0111\\u1ec3 c\\u00e1c \\"n\\u1ed7i \\u0111au\\" ti\\u1ec1m \\u1ea9n c\\u1ee7a ng\\u01b0\\u1eddi d\\u00f9ng v\\u1ec1 s\\u1ef1 am hi\\u1ec3u ch\\u1ea5t l\\u01b0\\u1ee3ng, c\\u00e1ch th\\u1ee9c x\\u00e2y d\\u1ef1ng phong c\\u00e1ch v\\u00e0 \\u0111\\u1ea7u t\\u01b0 th\\u00f4ng minh. \\u0110\\u00e2y l\\u00e0 c\\u01a1 h\\u1ed9i l\\u1edbn \\u0111\\u1ec3 XoHi Intelligence t\\u1ea1o ra n\\u1ed9i dung v\\u01b0\\u1ee3t tr\\u1ed9i v\\u1edbi \\"Information Gain\\" cao.))throw_tool_code_error(FinalResultHeadlines, [", "ground_truth_summary": "Th\\u1ecb tr\\u01b0\\u1eddng \\"th\\u1eddi trang nam cao c\\u1ea5p\\" t\\u1ea1i Vi\\u1ec7t Nam \\u0111ang s\\u00f4i \\u0111\\u1ed9ng v\\u1edbi s\\u1ef1 g\\u00f3p m\\u1eb7t c\\u1ee7a c\\u1ea3 c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u n\\u1ed9i \\u0111\\u1ecba c\\u00f3 v\\u1ecb th\\u1ebf v\\u1eefng ch\\u1eafc (Aristino, Adam Store, May10, Owen, An Ph\\u01b0\\u1edbc) v\\u00e0 c\\u00e1c nh\\u00e0 ph\\u00e2n ph\\u1ed1i th\\u01b0\\u01a1ng hi\\u1ec7u qu\\u1ed1c t\\u1ebf (ACFC, Vua H\\u00e0ng Hi\\u1ec7u). C\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u t\\u1eadp trung v\\u00e0o \\u0111\\u1ecbnh v\\u1ecb \\"qu\\u00fd \\u00f4ng\\", \\"l\\u1ecbch l\\u00e3m\\", \\"sang tr\\u1ecdng\\", \\"\\u0111\\u1eb3ng c\\u1ea5p\\" v\\u1edbi \\"ch\\u1ea5t li\\u1ec7u cao c\\u1ea5p\\" v\\u00e0 \\"thi\\u1ebft k\\u1ebf tinh t\\u1ebf\\". Tuy nhi\\u00ean, h\\u1ea7u h\\u1ebft n\\u1ed9i dung hi\\u1ec7n t\\u1ea1i d\\u1eebng l\\u1ea1i \\u1edf vi\\u1ec7c gi\\u1edbi thi\\u1ec7u s\\u1ea3n ph\\u1ea9m, li\\u1ec7t k\\u00ea th\\u01b0\\u01a1ng hi\\u1ec7u ho\\u1eb7c qu\\u1ea3ng b\\u00e1 chung chung, b\\u1ecf qua c\\u01a1 h\\u1ed9i cung c\\u1ea5p th\\u00f4ng tin chuy\\u00ean s\\u00e2u, c\\u00e1 nh\\u00e2n h\\u00f3a v\\u00e0 gi\\u1ea3i quy\\u1ebft tri\\u1ec7t \\u0111\\u1ec3 c\\u00e1c \\"n\\u1ed7i \\u0111au\\" ti\\u1ec1m \\u1ea9n c\\u1ee7a ng\\u01b0\\u1eddi d\\u00f9ng v\\u1ec1 s\\u1ef1 am hi\\u1ec3u ch\\u1ea5t l\\u01b0\\u1ee3ng, c\\u00e1ch th\\u1ee9c x\\u00e2y d\\u1ef1ng phong c\\u00e1ch v\\u00e0 \\u0111\\u1ea7u t\\u01b0 th\\u00f4ng minh. \\u0110\\u00e2y l\\u00e0 c\\u01a1 h\\u1ed9i l\\u1edbn \\u0111\\u1ec3 XoHi Intelligence t\\u1ea1o ra n\\u1ed9i dung v\\u01b0\\u1ee3t tr\\u1ed9i v\\u1edbi \\"Information Gain\\" cao.", "logs": []}}	[]	{}	\N	1	\N	2026-03-25 05:31:27.88379+00	2026-03-25 06:07:05.567259+00	\N	default	0	user_admin	CREATIVE_CONTENT
\.


--
-- Data for Name: content_scouts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.content_scouts (id, topic, report_data, expires_at, created_at, updated_at, deleted_at, tenant_id) FROM stdin;
cfbf4195-68e9-48f1-beae-544d96a52eb4	thời trang nam cao cấp	{"topic": "th\\u1eddi trang nam cao c\\u1ea5p", "headlines": [{"title": "B\\u00ed Quy\\u1ebft N\\u00e2ng T\\u1ea7m Phong C\\u00e1ch Qu\\u00fd \\u00d4ng: Kh\\u00e1m ph\\u00e1 'Th\\u1eddi Trang Nam Cao C\\u1ea5p' KH\\u00d4NG TH\\u1ec2 B\\u1ece L\\u1ee0!", "type": "ADS"}, {"title": "TOP 15 Th\\u01b0\\u01a1ng Hi\\u1ec7u Th\\u1eddi Trang Nam Cao C\\u1ea5p '\\u0110\\u1eb3ng C\\u1ea5p Nh\\u1ea5t' T\\u1ea1i Vi\\u1ec7t Nam (2026 UPDATE)", "type": "TOP_10"}, {"title": "Gi\\u1ea3i M\\u00e3 S\\u1ee9c H\\u00fat C\\u1ee7a 'Th\\u1eddi Trang Nam Cao C\\u1ea5p': H\\u01a1n C\\u1ea3 Qu\\u1ea7n \\u00c1o, \\u0110\\u00f3 L\\u00e0 Tuy\\u00ean Ng\\u00f4n Phong C\\u00e1ch!", "type": "AI_AUGMENTED"}, {"title": "Th\\u1eddi Trang C\\u00f4ng S\\u1edf Cao C\\u1ea5p: Ch\\u1ecdn L\\u1ef1a \\u0110\\u00daNG CHU\\u1ea8N cho Ng\\u01b0\\u1eddi \\u0110\\u00e0n \\u00d4ng Hi\\u1ec7n \\u0110\\u1ea1i", "type": "TOP_10"}, {"title": "Kh\\u00e1m Ph\\u00e1 Ch\\u1ea5t Li\\u1ec7u & K\\u1ef9 Thu\\u1eadt May \\u0110o \\u0110\\u1ec9nh Cao Trong Th\\u1eddi Trang Nam Cao C\\u1ea5p", "type": "AI_AUGMENTED"}, {"title": "\\u0110\\u1eb3ng C\\u1ea5p Th\\u01b0\\u1ee3ng L\\u01b0u: C\\u00e1ch \\u0110\\u1ea7u T\\u01b0 V\\u00e0o T\\u1ee7 \\u0110\\u1ed3 Th\\u1eddi Trang Nam Cao C\\u1ea5p \\u0110\\u00e1ng Gi\\u00e1", "type": "ADS"}, {"title": "5 Sai L\\u1ea7m Ph\\u1ed5 Bi\\u1ebfn Khi Ch\\u1ecdn 'Th\\u1eddi Trang Nam Cao C\\u1ea5p' & Gi\\u1ea3i Ph\\u00e1p T\\u1eeb Chuy\\u00ean Gia", "type": "AI_AUGMENTED"}, {"title": "ARISTINO, Adam Store, Owen: Cu\\u1ed9c Chi\\u1ebfn Phong C\\u00e1ch Gi\\u1eefa C\\u00e1c Th\\u01b0\\u01a1ng Hi\\u1ec7u Nam Cao C\\u1ea5p Vi\\u1ec7t", "type": "TOP_10"}], "semantic_keywords": ["th\\u1eddi trang nam cao c\\u1ea5p", "th\\u01b0\\u01a1ng hi\\u1ec7u th\\u1eddi trang nam cao c\\u1ea5p", "qu\\u1ea7n \\u00e1o nam cao c\\u1ea5p", "phong c\\u00e1ch qu\\u00fd \\u00f4ng", "th\\u1eddi trang c\\u00f4ng s\\u1edf nam cao c\\u1ea5p", "\\u00e1o vest nam cao c\\u1ea5p", "ph\\u1ee5 ki\\u1ec7n th\\u1eddi trang nam cao c\\u1ea5p", "ch\\u1ea5t li\\u1ec7u cao c\\u1ea5p nam", "mua th\\u1eddi trang nam ch\\u00ednh h\\u00e3ng", "l\\u1ecbch l\\u00e3m v\\u00e0 m\\u1ea1nh m\\u1ebd", "\\u0111\\u1eb3ng c\\u1ea5p th\\u1eddi trang nam", "xu h\\u01b0\\u1edbng th\\u1eddi trang nam cao c\\u1ea5p"], "strategic_analysis": "## B\\u1ea2N TR\\u00ccNH B\\u00c1O CHI\\u1ebeN L\\u01af\\u1ee2C N\\u1ed8I DUNG \\u2014 TH\\u1edcI TRANG NAM CAO C\\u1ea4P\\n\\n### 1. Search Intent Decoding (Gi\\u1ea3i M\\u00e3 M\\u1ee5c \\u0110\\u00edch & N\\u1ed7i \\u0110au Ng\\u01b0\\u1eddi D\\u00f9ng)\\n\\nKhi t\\u00ecm ki\\u1ebfm \\"th\\u1eddi trang nam cao c\\u1ea5p\\", ng\\u01b0\\u1eddi d\\u00f9ng kh\\u00f4ng ch\\u1ec9 \\u0111\\u01a1n thu\\u1ea7n mu\\u1ed1n mua s\\u1eafm qu\\u1ea7n \\u00e1o. H\\u1ecd \\u0111ang t\\u00ecm ki\\u1ebfm:\\n\\n*   **Aspiration (Kh\\u00e1t v\\u1ecdng):** Tr\\u1edf th\\u00e0nh m\\u1ed9t \\"qu\\u00fd \\u00f4ng l\\u1ecbch l\\u00e3m\\", \\"sang tr\\u1ecdng\\", \\"\\u0111\\u1eb3ng c\\u1ea5p\\" nh\\u01b0 nh\\u1eefng g\\u00ec c\\u00e1c \\u0111\\u1ed1i th\\u1ee7 (Aristino, An Ph\\u01b0\\u1edbc) \\u0111\\u00e3 \\u0111\\u1ecbnh v\\u1ecb. H\\u1ecd mu\\u1ed1n th\\u1ec3 hi\\u1ec7n \\u0111\\u1ecba v\\u1ecb, s\\u1ef1 t\\u1ef1 tin v\\u00e0 gu th\\u1ea9m m\\u1ef9 c\\u00e1 nh\\u00e2n.\\n*   **Quality Assurance (\\u0110\\u1ea3m b\\u1ea3o ch\\u1ea5t l\\u01b0\\u1ee3ng):** N\\u1ed7i s\\u1ee3 mua ph\\u1ea3i h\\u00e0ng nh\\u00e1i, h\\u00e0ng k\\u00e9m ch\\u1ea5t l\\u01b0\\u1ee3ng, kh\\u00f4ng x\\u1ee9ng \\u0111\\u00e1ng v\\u1edbi s\\u1ed1 ti\\u1ec1n b\\u1ecf ra. H\\u1ecd t\\u00ecm ki\\u1ebfm \\"h\\u00e0ng hi\\u1ec7u\\", \\"ch\\u00ednh h\\u00e3ng\\", \\"ch\\u1ea5t li\\u1ec7u cao c\\u1ea5p\\" (May10, Owen, Vua H\\u00e0ng Hi\\u1ec7u).\\n*   **Guidance & Discovery (H\\u01b0\\u1edbng d\\u1eabn & Kh\\u00e1m ph\\u00e1):** H\\u1ecd mu\\u1ed1n bi\\u1ebft \\u0111\\u00e2u l\\u00e0 nh\\u1eefng \\"th\\u01b0\\u01a1ng hi\\u1ec7u h\\u00e0ng \\u0111\\u1ea7u\\" (Adam Store, ACFC), \\"m\\u1eabu m\\u00e3 \\u0111a d\\u1ea1ng tinh t\\u1ebf\\" v\\u00e0 c\\u00e1ch ph\\u1ed1i \\u0111\\u1ed3 sao cho ph\\u00f9 h\\u1ee3p v\\u1edbi v\\u00f3c d\\u00e1ng, m\\u1ee5c \\u0111\\u00edch s\\u1eed d\\u1ee5ng (c\\u00f4ng s\\u1edf, s\\u1ef1 ki\\u1ec7n, d\\u1ea1o ph\\u1ed1).\\n*   **Value (Gi\\u00e1 tr\\u1ecb):** D\\u00f9 l\\u00e0 s\\u1ea3n ph\\u1ea9m cao c\\u1ea5p, h\\u1ecd v\\u1eabn quan t\\u00e2m \\u0111\\u1ebfn c\\u00e1c ch\\u01b0\\u01a1ng tr\\u00ecnh \\"khuy\\u1ebfn m\\u00e3i h\\u1ea5p d\\u1eabn\\" (ACFC) ho\\u1eb7c \\"\\u0111\\u1ea7u t\\u01b0\\" v\\u00e0o nh\\u1eefng m\\u00f3n \\u0111\\u1ed3 c\\u00f3 gi\\u00e1 tr\\u1ecb s\\u1eed d\\u1ee5ng l\\u00e2u d\\u00e0i.\\n*   **Experience (Tr\\u1ea3i nghi\\u1ec7m):** Mong mu\\u1ed1n tr\\u1ea3i nghi\\u1ec7m mua s\\u1eafm ti\\u1ec7n l\\u1ee3i (online, giao h\\u00e0ng to\\u00e0n qu\\u1ed1c) v\\u00e0 d\\u1ecbch v\\u1ee5 t\\u01b0 v\\u1ea5n chuy\\u00ean nghi\\u1ec7p.\\n\\n### 2. Competitor Gap Analysis (Ph\\u00e2n T\\u00edch Kho\\u1ea3ng Tr\\u1ed1ng \\u0110\\u1ed1i Th\\u1ee7)\\n\\nC\\u00e1c \\u0111\\u1ed1i th\\u1ee7 hi\\u1ec7n t\\u1ea1i ch\\u1ee7 y\\u1ebfu t\\u1eadp trung v\\u00e0o vi\\u1ec7c:\\n\\n*   **T\\u1ef1 qu\\u1ea3ng b\\u00e1 th\\u01b0\\u01a1ng hi\\u1ec7u:** Nh\\u1ea5n m\\u1ea1nh s\\u1ea3n ph\\u1ea9m c\\u1ee7a ri\\u00eang h\\u1ecd (Aristino, Owen, May10, An Ph\\u01b0\\u1edbc).\\n*   **Li\\u1ec7t k\\u00ea th\\u01b0\\u01a1ng hi\\u1ec7u/s\\u1ea3n ph\\u1ea9m:** Cung c\\u1ea5p danh s\\u00e1ch c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u ho\\u1eb7c t\\u1ed5ng h\\u1ee3p s\\u1ea3n ph\\u1ea9m m\\u00e0 kh\\u00f4ng \\u0111i s\\u00e2u v\\u00e0o chi ti\\u1ebft (ACFC, Vua H\\u00e0ng Hi\\u1ec7u, c\\u00e1c b\\u00e0i \\"Top 15\\").\\n*   **\\u0110\\u1ecbnh v\\u1ecb chung chung:** S\\u1eed d\\u1ee5ng c\\u00e1c t\\u1eeb kh\\u00f3a \\"l\\u1ecbch l\\u00e3m\\", \\"sang tr\\u1ecdng\\", \\"\\u0111\\u1eb3ng c\\u1ea5p\\" nh\\u01b0ng \\u00edt khi gi\\u1ea3i th\\u00edch *t\\u1ea1i sao* s\\u1ea3n ph\\u1ea9m c\\u1ee7a h\\u1ecd ho\\u1eb7c m\\u1ed9t phong c\\u00e1ch c\\u1ee5 th\\u1ec3 l\\u1ea1i \\u0111\\u1ea1t \\u0111\\u01b0\\u1ee3c \\u0111i\\u1ec1u \\u0111\\u00f3.\\n\\n**Nh\\u1eefng m\\u1ea3ng n\\u1ed9i dung/insight m\\u00e0 \\u0111\\u1ed1i th\\u1ee7 \\u0111ang b\\u1ecf tr\\u1ed1ng ho\\u1eb7c l\\u00e0m h\\u1eddi h\\u1ee3t:**\\n\\n*   **Chuy\\u00ean s\\u00e2u v\\u1ec1 ch\\u1ea5t li\\u1ec7u & k\\u1ef9 thu\\u1eadt:** Kh\\u00f4ng c\\u00f3 b\\u00e0i vi\\u1ebft n\\u00e0o th\\u1ef1c s\\u1ef1 \\u0111i s\\u00e2u v\\u00e0o ph\\u00e2n t\\u00edch c\\u00e1c lo\\u1ea1i v\\u1ea3i cao c\\u1ea5p (len cashmere, l\\u1ee5a, cotton Ai C\\u1eadp, da th\\u1eadt...), k\\u1ef9 thu\\u1eadt may \\u0111o (bespoke, made-to-measure), quy tr\\u00ecnh s\\u1ea3n xu\\u1ea5t t\\u1ea1o n\\u00ean s\\u1ef1 kh\\u00e1c bi\\u1ec7t c\\u1ee7a \\"cao c\\u1ea5p\\" so v\\u1edbi \\"ph\\u1ed5 th\\u00f4ng\\". \\u0110\\u00e2y l\\u00e0 \\"Information Gain\\" c\\u1ef1c l\\u1edbn.\\n*   **H\\u01b0\\u1edbng d\\u1eabn phong c\\u00e1ch c\\u00e1 nh\\u00e2n h\\u00f3a:** Thi\\u1ebfu c\\u00e1c b\\u00e0i vi\\u1ebft t\\u01b0 v\\u1ea5n c\\u1ee5 th\\u1ec3 cho t\\u1eebng d\\u00e1ng ng\\u01b0\\u1eddi, \\u0111\\u1ed9 tu\\u1ed5i, ngh\\u1ec1 nghi\\u1ec7p ho\\u1eb7c s\\u1ef1 ki\\u1ec7n c\\u1ee5 th\\u1ec3. V\\u00ed d\\u1ee5: \\"Ch\\u1ecdn vest cao c\\u1ea5p cho ng\\u01b0\\u1eddi c\\u00f3 vai r\\u1ed9ng\\", \\"Phong c\\u00e1ch smart casual cao c\\u1ea5p cho bu\\u1ed5i h\\u1eb9n cu\\u1ed1i tu\\u1ea7n\\".\\n*   **B\\u00ed quy\\u1ebft \\u0111\\u1ea7u t\\u01b0 t\\u1ee7 \\u0111\\u1ed3 th\\u00f4ng minh:** Kh\\u00f4ng c\\u00f3 n\\u1ed9i dung v\\u1ec1 c\\u00e1ch x\\u00e2y d\\u1ef1ng m\\u1ed9t t\\u1ee7 \\u0111\\u1ed3 capsule (t\\u1ed1i gi\\u1ea3n nh\\u01b0ng \\u0111\\u1ee7 d\\u00f9ng), c\\u00e1c m\\u00f3n \\u0111\\u1ed3 \\"must-have\\" \\u0111\\u00e1ng \\u0111\\u1ec3 \\u0111\\u1ea7u t\\u01b0 l\\u00e2u d\\u00e0i, ho\\u1eb7c c\\u00e1ch b\\u1ea3o qu\\u1ea3n trang ph\\u1ee5c cao c\\u1ea5p \\u0111\\u1ec3 t\\u0103ng tu\\u1ed5i th\\u1ecd.\\n*   **So s\\u00e1nh & \\u0111\\u00e1nh gi\\u00e1 kh\\u00e1ch quan:** Thi\\u1ebfu c\\u00e1c b\\u00e0i so s\\u00e1nh chi ti\\u1ebft gi\\u1eefa c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u cao c\\u1ea5p (v\\u00ed d\\u1ee5: Aristino vs. Adam Store v\\u1ec1 ch\\u1ea5t l\\u01b0\\u1ee3ng v\\u1ea3i, \\u0111\\u01b0\\u1eddng may, \\u0111\\u1ed9 b\\u1ec1n) ho\\u1eb7c gi\\u1eefa th\\u01b0\\u01a1ng hi\\u1ec7u n\\u1ed9i \\u0111\\u1ecba v\\u00e0 qu\\u1ed1c t\\u1ebf v\\u1ec1 gi\\u00e1 tr\\u1ecb nh\\u1eadn \\u0111\\u01b0\\u1ee3c so v\\u1edbi chi ph\\u00ed.\\n*   **C\\u00e2u chuy\\u1ec7n th\\u01b0\\u01a1ng hi\\u1ec7u & gi\\u00e1 tr\\u1ecb c\\u1ed1t l\\u00f5i:** Ngo\\u00e0i slogan, \\u00edt th\\u01b0\\u01a1ng hi\\u1ec7u k\\u1ec3 c\\u00e2u chuy\\u1ec7n s\\u00e2u s\\u1eafc v\\u1ec1 tri\\u1ebft l\\u00fd thi\\u1ebft k\\u1ebf, ngu\\u1ed3n c\\u1ea3m h\\u1ee9ng, ho\\u1eb7c cam k\\u1ebft v\\u1ec1 \\u0111\\u1ea1o \\u0111\\u1ee9c/b\\u1ec1n v\\u1eefng (n\\u1ebfu c\\u00f3) trong ng\\u00e0nh th\\u1eddi trang cao c\\u1ea5p.\\n*   **Kh\\u00e1m ph\\u00e1 xu h\\u01b0\\u1edbng & d\\u1ef1 b\\u00e1o:** C\\u00e1c b\\u00e0i vi\\u1ebft th\\u01b0\\u1eddng ch\\u1ec9 c\\u1eadp nh\\u1eadt s\\u1ea3n ph\\u1ea9m m\\u1edbi, \\u00edt \\u0111i s\\u00e2u v\\u00e0o ph\\u00e2n t\\u00edch xu h\\u01b0\\u1edbng th\\u1eddi trang nam cao c\\u1ea5p to\\u00e0n c\\u1ea7u v\\u00e0 c\\u00e1ch \\u00e1p d\\u1ee5ng t\\u1ea1i Vi\\u1ec7t Nam.\\n\\n### 3. Elite Execution Roadmap (C\\u00f4ng Th\\u1ee9c \\u0110\\u1ec3 \\u0110\\u1ea1t Information Gain V\\u01b0\\u1ee3t Top 1)\\n\\n\\u0110\\u1ec3 t\\u1ea1o ra n\\u1ed9i dung c\\u00f3 \\"Information Gain\\" cao nh\\u1ea5t v\\u00e0 v\\u01b0\\u1ee3t xa c\\u00e1c \\u0111\\u1ed1i th\\u1ee7, XoHi Intelligence c\\u1ea7n t\\u1eadp trung v\\u00e0o s\\u1ef1 chuy\\u00ean s\\u00e2u, c\\u00e1 nh\\u00e2n h\\u00f3a v\\u00e0 gi\\u00e1 tr\\u1ecb th\\u1ef1c s\\u1ef1 cho ng\\u01b0\\u1eddi d\\u00f9ng:\\n\\n1.  **\\"Ultimate Guide\\" v\\u1ec1 Ch\\u1ea5t Li\\u1ec7u & K\\u1ef9 Thu\\u1eadt May \\u0110o:**\\n    *   **N\\u1ed9i dung:** B\\u00e0i vi\\u1ebft chuy\\u00ean s\\u00e2u v\\u1ec1 c\\u00e1c lo\\u1ea1i v\\u1ea3i (cotton Pima, len merino, l\\u1ee5a t\\u01a1 t\\u1eb1m, linen cao c\\u1ea5p, v.v.), c\\u00f4ng ngh\\u1ec7 d\\u1ec7t, quy tr\\u00ecnh may th\\u1ee7 c\\u00f4ng (hand-stitched details), v\\u00e0 s\\u1ef1 kh\\u00e1c bi\\u1ec7t v\\u1ec1 form d\\u00e1ng, \\u0111\\u1ed9 b\\u1ec1n. \\u0110i k\\u00e8m h\\u00ecnh \\u1ea3nh/video minh h\\u1ecda c\\u1eadn c\\u1ea3nh.\\n    *   **M\\u1ee5c ti\\u00eau:** \\u0110\\u1ecbnh v\\u1ecb l\\u00e0 ngu\\u1ed3n th\\u00f4ng tin uy t\\u00edn, chi ti\\u1ebft nh\\u1ea5t, gi\\u1ea3i quy\\u1ebft tri\\u1ec7t \\u0111\\u1ec3 n\\u1ed7i \\u0111au v\\u1ec1 ch\\u1ea5t l\\u01b0\\u1ee3ng v\\u00e0 s\\u1ef1 am hi\\u1ec3u.\\n\\n2.  **\\"Masterclass\\" Phong C\\u00e1ch C\\u00e1 Nh\\u00e2n H\\u00f3a:**\\n    *   **N\\u1ed9i dung:** Chu\\u1ed7i b\\u00e0i vi\\u1ebft/video h\\u01b0\\u1edbng d\\u1eabn c\\u00e1ch ch\\u1ecdn v\\u00e0 ph\\u1ed1i \\u0111\\u1ed3 cao c\\u1ea5p cho t\\u1eebng d\\u00e1ng ng\\u01b0\\u1eddi (d\\u00e1ng V, ch\\u1eef nh\\u1eadt, qu\\u1ea3 l\\u00ea), t\\u1eebng \\u0111\\u1ed9 tu\\u1ed5i (25-35, 35-45, 45+), v\\u00e0 c\\u00e1c s\\u1ef1 ki\\u1ec7n c\\u1ee5 th\\u1ec3 (business casual, black-tie, ti\\u1ec7c t\\u00f9ng, du l\\u1ecbch cao c\\u1ea5p). \\u0110\\u1ec1 xu\\u1ea5t c\\u00e1c m\\u00f3n \\u0111\\u1ed3 \\"linh h\\u1ed3n\\" cho t\\u1eebng phong c\\u00e1ch.\\n    *   **M\\u1ee5c ti\\u00eau:** Cung c\\u1ea5p gi\\u00e1 tr\\u1ecb th\\u1ef1c ti\\u1ec5n, gi\\u00fap ng\\u01b0\\u1eddi d\\u00f9ng t\\u1ef1 tin h\\u01a1n trong vi\\u1ec7c \\u0111\\u1ecbnh h\\u00ecnh phong c\\u00e1ch ri\\u00eang.\\n\\n3.  **\\"T\\u1ee7 \\u0110\\u1ed3 Qu\\u00fd \\u00d4ng Th\\u00f4ng Th\\u00e1i\\" \\u2013 H\\u01b0\\u1edbng D\\u1eabn \\u0110\\u1ea7u T\\u01b0 & B\\u1ea3o Qu\\u1ea3n:**\\n    *   **N\\u1ed9i dung:** B\\u00e0i vi\\u1ebft chi\\u1ebfn l\\u01b0\\u1ee3c v\\u1ec1 c\\u00e1ch x\\u00e2y d\\u1ef1ng t\\u1ee7 \\u0111\\u1ed3 \\"capsule\\" th\\u1eddi trang nam cao c\\u1ea5p (5-7 m\\u00f3n \\u0111\\u1ed3 c\\u1ed1t l\\u00f5i c\\u00f3 th\\u1ec3 ph\\u1ed1i th\\u00e0nh 20+ outfit). H\\u01b0\\u1edbng d\\u1eabn ch\\u1ecdn c\\u00e1c m\\u00f3n \\u0111\\u1ed3 v\\u01b0\\u1ee3t th\\u1eddi gian, m\\u1eb9o b\\u1ea3o qu\\u1ea3n (gi\\u1eb7t \\u1ee7i, c\\u1ea5t gi\\u1eef, s\\u1eeda ch\\u1eefa) \\u0111\\u1ec3 k\\u00e9o d\\u00e0i tu\\u1ed5i th\\u1ecd s\\u1ea3n ph\\u1ea9m cao c\\u1ea5p.\\n    *   **M\\u1ee5c ti\\u00eau:** Gi\\u1ea3i quy\\u1ebft n\\u1ed7i lo v\\u1ec1 chi ph\\u00ed v\\u00e0 gi\\u00fap ng\\u01b0\\u1eddi d\\u00f9ng t\\u1ed1i \\u01b0u h\\u00f3a kho\\u1ea3n \\u0111\\u1ea7u t\\u01b0 v\\u00e0o th\\u1eddi trang.\\n\\n4.  **\\"B\\u00f3c T\\u00e1ch S\\u1ef1 Th\\u1eadt\\": So S\\u00e1nh Th\\u01b0\\u01a1ng Hi\\u1ec7u & Ti\\u00eau Ch\\u00ed \\u0110\\u00e1nh Gi\\u00e1 Th\\u1ef1c T\\u1ebf:**\\n    *   **N\\u1ed9i dung:** Ph\\u00e2n t\\u00edch kh\\u00e1ch quan c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u (v\\u00ed d\\u1ee5: ARISTINO vs. Owen \\u2013 \\u0111i\\u1ec3m m\\u1ea1nh v\\u1ec1 vest, \\u0111i\\u1ec3m y\\u1ebfu v\\u1ec1 ph\\u1ee5 ki\\u1ec7n; May10 vs. An Ph\\u01b0\\u1edbc \\u2013 kh\\u00e1c bi\\u1ec7t v\\u1ec1 ph\\u00e2n kh\\u00fac c\\u00f4ng s\\u1edf) d\\u1ef1a tr\\u00ean ti\\u00eau ch\\u00ed: ch\\u1ea5t li\\u1ec7u, \\u0111\\u01b0\\u1eddng may, \\u0111\\u1ed9 b\\u1ec1n, d\\u1ecbch v\\u1ee5 kh\\u00e1ch h\\u00e0ng, gi\\u00e1 tr\\u1ecb th\\u01b0\\u01a1ng hi\\u1ec7u. C\\u00f3 th\\u1ec3 m\\u1edf r\\u1ed9ng so s\\u00e1nh v\\u1edbi c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u qu\\u1ed1c t\\u1ebf.\\n    *   **M\\u1ee5c ti\\u00eau:** Cung c\\u1ea5p th\\u00f4ng tin minh b\\u1ea1ch, gi\\u00fap ng\\u01b0\\u1eddi d\\u00f9ng \\u0111\\u01b0a ra quy\\u1ebft \\u0111\\u1ecbnh mua s\\u1eafm th\\u00f4ng th\\u00e1i, tr\\u00e1nh nh\\u1eefng l\\u1eddi qu\\u1ea3ng c\\u00e1o chung chung.\\n\\n5.  **C\\u00e2u Chuy\\u1ec7n \\u0110\\u1eb1ng Sau \\"\\u0110\\u1eb3ng C\\u1ea5p\\":**\\n    *   **N\\u1ed9i dung:** Ph\\u1ecfng v\\u1ea5n nh\\u00e0 thi\\u1ebft k\\u1ebf, th\\u1ee3 may l\\u00e0nh ngh\\u1ec1, ho\\u1eb7c k\\u1ec3 c\\u00e2u chuy\\u1ec7n v\\u1ec1 ngu\\u1ed3n g\\u1ed1c ch\\u1ea5t li\\u1ec7u, qu\\u00e1 tr\\u00ecnh t\\u1ea1o ra m\\u1ed9t s\\u1ea3n ph\\u1ea9m cao c\\u1ea5p. L\\u1ed3ng gh\\u00e9p y\\u1ebfu t\\u1ed1 b\\u1ec1n v\\u1eefng, tr\\u00e1ch nhi\\u1ec7m x\\u00e3 h\\u1ed9i n\\u1ebfu c\\u00f3.\\n    *   **M\\u1ee5c ti\\u00eau:** T\\u1ea1o chi\\u1ec1u s\\u00e2u c\\u1ea3m x\\u00fac, k\\u1ebft n\\u1ed1i ng\\u01b0\\u1eddi d\\u00f9ng v\\u1edbi gi\\u00e1 tr\\u1ecb c\\u1ed1t l\\u00f5i c\\u1ee7a th\\u1eddi trang cao c\\u1ea5p, kh\\u00f4ng ch\\u1ec9 l\\u00e0 v\\u1ebb b\\u1ec1 ngo\\u00e0i.\\n\\n**Ch\\u1ec9 s\\u1ed1 Th\\u00e0nh c\\u00f4ng (KPIs):** T\\u0103ng th\\u1eddi gian \\u1edf l\\u1ea1i trang, gi\\u1ea3m t\\u1ef7 l\\u1ec7 tho\\u00e1t, t\\u0103ng l\\u01b0\\u1ee3ng chia s\\u1ebb n\\u1ed9i dung, t\\u0103ng t\\u1ef7 l\\u1ec7 chuy\\u1ec3n \\u0111\\u1ed5i t\\u1eeb b\\u00e0i vi\\u1ebft th\\u00f4ng tin sang trang s\\u1ea3n ph\\u1ea9m (n\\u1ebfu c\\u00f3), c\\u1ea3i thi\\u1ec7n v\\u1ecb tr\\u00ed x\\u1ebfp h\\u1ea1ng cho c\\u00e1c t\\u1eeb kh\\u00f3a ng\\u00e1ch v\\u00e0 t\\u1ed5ng th\\u1ec3.\\n\\n### 4. Ground Truth Summary (T\\u00f3m T\\u1eaft B\\u1ed1i C\\u1ea3nh Trinh S\\u00e1t)\\n\\nTh\\u1ecb tr\\u01b0\\u1eddng \\"th\\u1eddi trang nam cao c\\u1ea5p\\" t\\u1ea1i Vi\\u1ec7t Nam \\u0111ang s\\u00f4i \\u0111\\u1ed9ng v\\u1edbi s\\u1ef1 g\\u00f3p m\\u1eb7t c\\u1ee7a c\\u1ea3 c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u n\\u1ed9i \\u0111\\u1ecba c\\u00f3 v\\u1ecb th\\u1ebf v\\u1eefng ch\\u1eafc (Aristino, Adam Store, May10, Owen, An Ph\\u01b0\\u1edbc) v\\u00e0 c\\u00e1c nh\\u00e0 ph\\u00e2n ph\\u1ed1i th\\u01b0\\u01a1ng hi\\u1ec7u qu\\u1ed1c t\\u1ebf (ACFC, Vua H\\u00e0ng Hi\\u1ec7u). C\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u t\\u1eadp trung v\\u00e0o \\u0111\\u1ecbnh v\\u1ecb \\"qu\\u00fd \\u00f4ng\\", \\"l\\u1ecbch l\\u00e3m\\", \\"sang tr\\u1ecdng\\", \\"\\u0111\\u1eb3ng c\\u1ea5p\\" v\\u1edbi \\"ch\\u1ea5t li\\u1ec7u cao c\\u1ea5p\\" v\\u00e0 \\"thi\\u1ebft k\\u1ebf tinh t\\u1ebf\\". Tuy nhi\\u00ean, h\\u1ea7u h\\u1ebft n\\u1ed9i dung hi\\u1ec7n t\\u1ea1i d\\u1eebng l\\u1ea1i \\u1edf vi\\u1ec7c gi\\u1edbi thi\\u1ec7u s\\u1ea3n ph\\u1ea9m, li\\u1ec7t k\\u00ea th\\u01b0\\u01a1ng hi\\u1ec7u ho\\u1eb7c qu\\u1ea3ng b\\u00e1 chung chung, b\\u1ecf qua c\\u01a1 h\\u1ed9i cung c\\u1ea5p th\\u00f4ng tin chuy\\u00ean s\\u00e2u, c\\u00e1 nh\\u00e2n h\\u00f3a v\\u00e0 gi\\u1ea3i quy\\u1ebft tri\\u1ec7t \\u0111\\u1ec3 c\\u00e1c \\"n\\u1ed7i \\u0111au\\" ti\\u1ec1m \\u1ea9n c\\u1ee7a ng\\u01b0\\u1eddi d\\u00f9ng v\\u1ec1 s\\u1ef1 am hi\\u1ec3u ch\\u1ea5t l\\u01b0\\u1ee3ng, c\\u00e1ch th\\u1ee9c x\\u00e2y d\\u1ef1ng phong c\\u00e1ch v\\u00e0 \\u0111\\u1ea7u t\\u01b0 th\\u00f4ng minh. \\u0110\\u00e2y l\\u00e0 c\\u01a1 h\\u1ed9i l\\u1edbn \\u0111\\u1ec3 XoHi Intelligence t\\u1ea1o ra n\\u1ed9i dung v\\u01b0\\u1ee3t tr\\u1ed9i v\\u1edbi \\"Information Gain\\" cao.))throw_tool_code_error(FinalResultHeadlines, [", "ground_truth_summary": "Th\\u1ecb tr\\u01b0\\u1eddng \\"th\\u1eddi trang nam cao c\\u1ea5p\\" t\\u1ea1i Vi\\u1ec7t Nam \\u0111ang s\\u00f4i \\u0111\\u1ed9ng v\\u1edbi s\\u1ef1 g\\u00f3p m\\u1eb7t c\\u1ee7a c\\u1ea3 c\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u n\\u1ed9i \\u0111\\u1ecba c\\u00f3 v\\u1ecb th\\u1ebf v\\u1eefng ch\\u1eafc (Aristino, Adam Store, May10, Owen, An Ph\\u01b0\\u1edbc) v\\u00e0 c\\u00e1c nh\\u00e0 ph\\u00e2n ph\\u1ed1i th\\u01b0\\u01a1ng hi\\u1ec7u qu\\u1ed1c t\\u1ebf (ACFC, Vua H\\u00e0ng Hi\\u1ec7u). C\\u00e1c th\\u01b0\\u01a1ng hi\\u1ec7u t\\u1eadp trung v\\u00e0o \\u0111\\u1ecbnh v\\u1ecb \\"qu\\u00fd \\u00f4ng\\", \\"l\\u1ecbch l\\u00e3m\\", \\"sang tr\\u1ecdng\\", \\"\\u0111\\u1eb3ng c\\u1ea5p\\" v\\u1edbi \\"ch\\u1ea5t li\\u1ec7u cao c\\u1ea5p\\" v\\u00e0 \\"thi\\u1ebft k\\u1ebf tinh t\\u1ebf\\". Tuy nhi\\u00ean, h\\u1ea7u h\\u1ebft n\\u1ed9i dung hi\\u1ec7n t\\u1ea1i d\\u1eebng l\\u1ea1i \\u1edf vi\\u1ec7c gi\\u1edbi thi\\u1ec7u s\\u1ea3n ph\\u1ea9m, li\\u1ec7t k\\u00ea th\\u01b0\\u01a1ng hi\\u1ec7u ho\\u1eb7c qu\\u1ea3ng b\\u00e1 chung chung, b\\u1ecf qua c\\u01a1 h\\u1ed9i cung c\\u1ea5p th\\u00f4ng tin chuy\\u00ean s\\u00e2u, c\\u00e1 nh\\u00e2n h\\u00f3a v\\u00e0 gi\\u1ea3i quy\\u1ebft tri\\u1ec7t \\u0111\\u1ec3 c\\u00e1c \\"n\\u1ed7i \\u0111au\\" ti\\u1ec1m \\u1ea9n c\\u1ee7a ng\\u01b0\\u1eddi d\\u00f9ng v\\u1ec1 s\\u1ef1 am hi\\u1ec3u ch\\u1ea5t l\\u01b0\\u1ee3ng, c\\u00e1ch th\\u1ee9c x\\u00e2y d\\u1ef1ng phong c\\u00e1ch v\\u00e0 \\u0111\\u1ea7u t\\u01b0 th\\u00f4ng minh. \\u0110\\u00e2y l\\u00e0 c\\u01a1 h\\u1ed9i l\\u1edbn \\u0111\\u1ec3 XoHi Intelligence t\\u1ea1o ra n\\u1ed9i dung v\\u01b0\\u1ee3t tr\\u1ed9i v\\u1edbi \\"Information Gain\\" cao.", "logs": []}	2026-03-26 05:32:18.430695+00	2026-03-25 05:32:18.432769+00	2026-03-25 05:32:18.432775+00	\N	default
\.


--
-- Data for Name: drafts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.drafts (id, proposed_by, target_model, target_id, action, payload, status, reviewer_id, created_at, updated_at, deleted_at, tenant_id) FROM stdin;
\.


--
-- Data for Name: media_registry; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.media_registry (id, filename, file_path, file_size, mime_type, dimensions, blurhash, alt_text, campaign_id, owner_id, media_metadata, provider, created_at, updated_at, deleted_at, tenant_id, is_public, linked_post_id, linked_post_type) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notifications (id, user_id, type, message, is_read, created_at, deleted_at, tenant_id, updated_at) FROM stdin;
7cbb468c-899d-4306-a5ef-63b88d8dedbc	user_admin	SECURITY	Đăng nhập thành công: admin@smartshop.test	f	2026-03-25 05:30:39.915909+00	\N	default	2026-03-25 05:30:39.915915+00
4f08a213-39b0-4dc0-8c92-1b3c371a6aaa	user_admin	SECURITY	Đăng nhập thành công: admin@smartshop.test	f	2026-03-25 05:50:02.884334+00	\N	default	2026-03-25 05:50:02.88434+00
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.orders (id, user_id, total_amount, status, items, created_at, updated_at, deleted_at, tenant_id, cancellation_reason, history, is_spam, spam_score, fingerprint, spam_reason) FROM stdin;
8ca880aa-95b9-42c5-bf7f-1ebb0528b7a5	user_admin	5220000	COMPLETED	[{"sku": "SKU-0001", "name": "\\u00c1o Polo Classic V1", "quantity": 2, "price": 1970000, "total": 3940000}, {"sku": "SKU-0002", "name": "\\u0110\\u1ea7m Cocktail V2", "quantity": 1, "price": 1280000, "total": 1280000}]	2026-03-02 05:18:14.609581+00	2026-03-25 05:18:14.611381+00	\N	smartshop	\N	[]	f	0	\N	\N
7e43a1e0-ec78-44e0-b216-116841b02494	user_admin	1970000	COMPLETED	[{"sku": "SKU-0001", "name": "\\u00c1o Polo Classic V1", "quantity": 1, "price": 1970000, "total": 1970000}]	2026-03-04 05:18:14.60976+00	2026-03-25 05:18:14.611385+00	\N	smartshop	\N	[]	f	0	\N	\N
bac180f0-d5db-4dc0-8a08-62f4ef20e6ea	user_admin	1970000	COMPLETED	[{"sku": "SKU-0001", "name": "\\u00c1o Polo Classic V1", "quantity": 1, "price": 1970000, "total": 1970000}]	2026-03-14 05:18:14.609836+00	2026-03-25 05:18:14.611386+00	\N	smartshop	\N	[]	f	0	\N	\N
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.permissions (id, name, code, description, created_at, updated_at, deleted_at) FROM stdin;
perm_system_all	Full Access	system:all	\N	2026-03-25 05:18:14.009367+00	2026-03-25 05:18:14.009374+00	\N
perm_product_read	Product Read	product:read	\N	2026-03-25 05:18:14.01231+00	2026-03-25 05:18:14.012315+00	\N
perm_product_write	Product Write	product:write	\N	2026-03-25 05:18:14.014297+00	2026-03-25 05:18:14.014302+00	\N
perm_order_read	Order Read	order:read	\N	2026-03-25 05:18:14.016257+00	2026-03-25 05:18:14.016261+00	\N
perm_order_write	Order Write	order:write	\N	2026-03-25 05:18:14.017927+00	2026-03-25 05:18:14.017931+00	\N
\.


--
-- Data for Name: product_bases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.product_bases (id, name, description, sku, price, stock, status, type, category_id, created_at, updated_at, deleted_at, tenant_id, slug, seo_title, seo_description, images, attributes, seo_keywords, tier_variations) FROM stdin;
prod_001	Áo Polo Classic V1	\N	SKU-0001	1970000	129	ACTIVE	RETAIL	cat_quan_jean	2026-03-25 05:18:14.601241+00	2026-03-25 05:18:14.601245+00	\N	smartshop	p-1-5e3e	\N	\N	[]	{}	\N	[]
prod_002	Đầm Cocktail V2	\N	SKU-0002	1280000	428	ACTIVE	RETAIL	cat_dam_vay	2026-03-25 05:18:14.601247+00	2026-03-25 05:18:14.601248+00	\N	smartshop	p-2-c2c7	\N	\N	[]	{}	\N	[]
prod_003	Váy Bodycon V3	\N	SKU-0003	1200000	49	ACTIVE	RETAIL	cat_dam_vay	2026-03-25 05:18:14.60125+00	2026-03-25 05:18:14.601251+00	\N	smartshop	p-3-1e69	\N	\N	[]	{}	\N	[]
\.


--
-- Data for Name: product_embeddings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.product_embeddings (id, product_base_id, created_at, updated_at, embedding) FROM stdin;
\.


--
-- Data for Name: product_variants; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.product_variants (id, product_base_id, sku, price, stock, created_at, updated_at, deleted_at, tier_index) FROM stdin;
\.


--
-- Data for Name: rental_contracts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rental_contracts (id, product_base_id, start_date, end_date, status, terms, created_at, updated_at, deleted_at) FROM stdin;
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.role_permissions (role_id, permission_id) FROM stdin;
role_superadmin	perm_system_all
role_superadmin	perm_product_write
role_superadmin	perm_order_read
role_customer	perm_order_read
role_superadmin	perm_order_write
role_superadmin	perm_product_read
role_customer	perm_product_read
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (id, name, code, description, created_at, updated_at, deleted_at, tenant_id) FROM stdin;
role_superadmin	Super Admin	SUPER_ADMIN	\N	2026-03-25 05:18:14.021162+00	2026-03-25 05:18:14.021167+00	\N	smartshop
role_customer	Customer	CUSTOMER	\N	2026-03-25 05:18:14.021168+00	2026-03-25 05:18:14.021169+00	\N	smartshop
\.


--
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.system_settings (key, value, created_at, updated_at) FROM stdin;
primary_config	{"basic_info": {"site_name": "SmartShop Xohi", "description": "H\\u1ec7 th\\u1ed1ng b\\u00e1n h\\u00e0ng AI th\\u1ebf h\\u1ec7 m\\u1edbi 2026", "logo_desktop": null, "logo_mobile": null, "favicon": null}, "contact_info": {"phone": "0901234567", "hotline": "1800-XOHI", "email": "contact@smartshop.test", "address": "Bitexco Financial Tower, Qu\\u1eadn 1, TP.HCM", "working_hours": "8:00 - 22:00"}, "social_media": [{"platform": "Facebook", "url": "https://facebook.com/xohi", "icon_url": null}, {"platform": "Zalo", "url": "https://zalo.me/xohi", "icon_url": null}, {"platform": "TikTok", "url": "https://tiktok.com/@xohi", "icon_url": null}], "seo_analytics": {"meta_title": "SmartShop - Mua s\\u1eafm th\\u00f4ng minh c\\u00f9ng AI", "meta_description": "Tr\\u1ea3i nghi\\u1ec7m mua s\\u1eafm c\\u00e1 nh\\u00e2n h\\u00f3a v\\u1edbi tr\\u1ee3 l\\u00fd \\u1ea3o Xohi.", "meta_keywords": "AI, shopping, smartshop, xohi", "google_analytics_id": "G-XXXXXXXXXX", "facebook_pixel_id": "XXXXXXXXXXXXXXX"}, "google_maps": {"map_iframe": "", "api_key": ""}, "maintenance": {"is_enabled": false, "message": "H\\u1ec7 th\\u1ed1ng \\u0111ang b\\u1ea3o tr\\u00ec \\u0111\\u1ec3 n\\u00e2ng c\\u1ea5p Core AI. Vui l\\u00f2ng quay l\\u1ea1i sau."}}	2026-03-25 05:18:14.622495	2026-03-25 05:18:14.622501
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_roles (user_id, role_id) FROM stdin;
user_admin	role_superadmin
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, name, password, status, created_at, updated_at, deleted_at, tenant_id, username) FROM stdin;
user_admin	admin@smartshop.test	Xohi	$2b$12$TnO3bnWJqfE5NiEYe0guFOq5W73B.DiFca1kfYcSnf5Ctfey4iAfu	ACTIVE	2026-03-25 05:18:14.58658+00	2026-03-25 05:18:14.586585+00	\N	smartshop	mlap
\.


--
-- Data for Name: voice_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.voice_profiles (id, user_id, wake_words, sleep_words, greeting_template, capabilities, created_at, updated_at, farewell_template, chat_settings, stt_anchors, mic_sensitivity, gemini_keys_enc, ai_models, primary_model, discovered_models) FROM stdin;
67c004ec-1e7f-45f2-9957-1d97a0238890	user_admin	["hey so hi"]	["c\\u00fat"]	Bố đây.	{"READ": true, "COUNT": true, "MUTATE": true, "ANALYZE": true}	2026-03-25 05:18:14.591774+00	2026-03-25 05:18:14.591777+00	Hẹn gặp lại.	{"selective_persistence": true, "save_ai_responses": false, "auto_purge_days": 30, "cache_limit": 10}	[]	0.6	OfdRaUZOraDbJ_Dgcjr6DU4dio9NEhDGj8mwWg8RACYnOoCe33bNW6_nVAcJsJXj_KpMJJvRrnaY-rk8sswcmvOa20_GND3cafek5Gg853NVFF53HcfZl4aY45Sn38dmFp6_tLrExV-DoH2RNhOBKa7QyBWuiVfqWcMGHoA3-g7Tti-00KloNr7ROwWGkxEGHIXKVZ1VOOwpN6dUGniqUguEKBp8rt9Dw8lMyw91ddE4Q-ajptnbYgQh3xXP7Gw19MUbrOjFOUQw4YjfPFExxVjjUwnzzVrLox7rZvh-AUyiIZW7xCPPtcPvhL5RGnxsHmYdMmUfre5rJXlUVffhWecAToRhjQu6CYcDoyNQ3PhZj-S-O4_17D6beF8yY03tgMa0k5Lv0cpBdjbBzthGM_GD-Q==	["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]	gemini-2.5-flash	[]
\.


--
-- Name: agent_telemetry_logs agent_telemetry_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agent_telemetry_logs
    ADD CONSTRAINT agent_telemetry_logs_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: appointments appointments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_pkey PRIMARY KEY (id);


--
-- Name: article_embeddings article_embeddings_article_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_embeddings
    ADD CONSTRAINT article_embeddings_article_id_key UNIQUE (article_id);


--
-- Name: article_embeddings article_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_embeddings
    ADD CONSTRAINT article_embeddings_pkey PRIMARY KEY (id);


--
-- Name: articles articles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_pkey PRIMARY KEY (id);


--
-- Name: banners banners_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.banners
    ADD CONSTRAINT banners_pkey PRIMARY KEY (id);


--
-- Name: campaign_events campaign_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campaign_events
    ADD CONSTRAINT campaign_events_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: content_campaigns content_campaigns_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_campaigns
    ADD CONSTRAINT content_campaigns_pkey PRIMARY KEY (id);


--
-- Name: content_scouts content_scouts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_scouts
    ADD CONSTRAINT content_scouts_pkey PRIMARY KEY (id);


--
-- Name: drafts drafts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drafts
    ADD CONSTRAINT drafts_pkey PRIMARY KEY (id);


--
-- Name: media_registry media_registry_file_path_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.media_registry
    ADD CONSTRAINT media_registry_file_path_key UNIQUE (file_path);


--
-- Name: media_registry media_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.media_registry
    ADD CONSTRAINT media_registry_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_code_key UNIQUE (code);


--
-- Name: permissions permissions_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_name_key UNIQUE (name);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: product_bases product_bases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_bases
    ADD CONSTRAINT product_bases_pkey PRIMARY KEY (id);


--
-- Name: product_embeddings product_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_embeddings
    ADD CONSTRAINT product_embeddings_pkey PRIMARY KEY (id);


--
-- Name: product_embeddings product_embeddings_product_base_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_embeddings
    ADD CONSTRAINT product_embeddings_product_base_id_key UNIQUE (product_base_id);


--
-- Name: product_variants product_variants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_variants
    ADD CONSTRAINT product_variants_pkey PRIMARY KEY (id);


--
-- Name: product_variants product_variants_sku_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_variants
    ADD CONSTRAINT product_variants_sku_key UNIQUE (sku);


--
-- Name: rental_contracts rental_contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rental_contracts
    ADD CONSTRAINT rental_contracts_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (key);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: voice_profiles voice_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voice_profiles
    ADD CONSTRAINT voice_profiles_pkey PRIMARY KEY (id);


--
-- Name: voice_profiles voice_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voice_profiles
    ADD CONSTRAINT voice_profiles_user_id_key UNIQUE (user_id);


--
-- Name: ix_agent_telemetry_logs_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_agent_telemetry_logs_tenant_id ON public.agent_telemetry_logs USING btree (tenant_id);


--
-- Name: ix_appointments_campaign_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_appointments_campaign_id ON public.appointments USING btree (campaign_id);


--
-- Name: ix_appointments_start_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_appointments_start_time ON public.appointments USING btree (start_time);


--
-- Name: ix_appointments_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_appointments_tenant_deleted ON public.appointments USING btree (tenant_id, deleted_at);


--
-- Name: ix_appointments_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_appointments_tenant_id ON public.appointments USING btree (tenant_id);


--
-- Name: ix_appointments_time_range; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_appointments_time_range ON public.appointments USING btree (start_time, end_time);


--
-- Name: ix_articles_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_articles_created_at ON public.articles USING btree (created_at);


--
-- Name: ix_articles_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_articles_tenant_deleted ON public.articles USING btree (tenant_id, deleted_at);


--
-- Name: ix_articles_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_articles_tenant_id ON public.articles USING btree (tenant_id);


--
-- Name: ix_banners_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_banners_tenant_id ON public.banners USING btree (tenant_id);


--
-- Name: ix_campaign_events_campaign_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_campaign_events_campaign_id ON public.campaign_events USING btree (campaign_id);


--
-- Name: ix_campaign_events_event_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_campaign_events_event_type ON public.campaign_events USING btree (event_type);


--
-- Name: ix_campaign_events_tenant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_campaign_events_tenant ON public.campaign_events USING btree (tenant_id);


--
-- Name: ix_campaign_events_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_campaign_events_tenant_id ON public.campaign_events USING btree (tenant_id);


--
-- Name: ix_campaigns_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_campaigns_status ON public.content_campaigns USING btree (status);


--
-- Name: ix_campaigns_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_campaigns_tenant_deleted ON public.content_campaigns USING btree (tenant_id, deleted_at);


--
-- Name: ix_categories_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_categories_tenant_deleted ON public.categories USING btree (tenant_id, deleted_at);


--
-- Name: ix_categories_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_categories_tenant_id ON public.categories USING btree (tenant_id);


--
-- Name: ix_chat_messages_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_chat_messages_tenant_id ON public.chat_messages USING btree (tenant_id);


--
-- Name: ix_content_campaigns_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_content_campaigns_category ON public.content_campaigns USING btree (category);


--
-- Name: ix_content_campaigns_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_content_campaigns_tenant_id ON public.content_campaigns USING btree (tenant_id);


--
-- Name: ix_content_scouts_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_content_scouts_expires_at ON public.content_scouts USING btree (expires_at);


--
-- Name: ix_content_scouts_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_content_scouts_tenant_id ON public.content_scouts USING btree (tenant_id);


--
-- Name: ix_content_scouts_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_content_scouts_topic ON public.content_scouts USING btree (topic);


--
-- Name: ix_drafts_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_drafts_tenant_id ON public.drafts USING btree (tenant_id);


--
-- Name: ix_media_campaign_provider; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_campaign_provider ON public.media_registry USING btree (campaign_id, provider);


--
-- Name: ix_media_linked_post; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_linked_post ON public.media_registry USING btree (linked_post_type, linked_post_id);


--
-- Name: ix_media_registry_campaign_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_registry_campaign_id ON public.media_registry USING btree (campaign_id);


--
-- Name: ix_media_registry_filename; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_registry_filename ON public.media_registry USING btree (filename);


--
-- Name: ix_media_registry_linked_post_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_registry_linked_post_id ON public.media_registry USING btree (linked_post_id);


--
-- Name: ix_media_registry_linked_post_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_registry_linked_post_type ON public.media_registry USING btree (linked_post_type);


--
-- Name: ix_media_registry_owner_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_registry_owner_id ON public.media_registry USING btree (owner_id);


--
-- Name: ix_media_registry_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_registry_tenant_id ON public.media_registry USING btree (tenant_id);


--
-- Name: ix_media_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_media_tenant_deleted ON public.media_registry USING btree (tenant_id, deleted_at);


--
-- Name: ix_notifications_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_notifications_tenant_id ON public.notifications USING btree (tenant_id);


--
-- Name: ix_orders_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_orders_created_at ON public.orders USING btree (created_at);


--
-- Name: ix_orders_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_orders_tenant_deleted ON public.orders USING btree (tenant_id, deleted_at);


--
-- Name: ix_orders_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_orders_tenant_id ON public.orders USING btree (tenant_id);


--
-- Name: ix_product_bases_slug; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_product_bases_slug ON public.product_bases USING btree (slug);


--
-- Name: ix_product_bases_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_product_bases_tenant_id ON public.product_bases USING btree (tenant_id);


--
-- Name: ix_products_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_products_created_at ON public.product_bases USING btree (created_at);


--
-- Name: ix_products_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_products_tenant_deleted ON public.product_bases USING btree (tenant_id, deleted_at);


--
-- Name: ix_roles_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_roles_tenant_deleted ON public.roles USING btree (tenant_id, deleted_at);


--
-- Name: ix_roles_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_roles_tenant_id ON public.roles USING btree (tenant_id);


--
-- Name: ix_scouts_tenant_topic; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scouts_tenant_topic ON public.content_scouts USING btree (tenant_id, topic);


--
-- Name: ix_users_tenant_deleted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_tenant_deleted ON public.users USING btree (tenant_id, deleted_at);


--
-- Name: ix_users_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_tenant_id ON public.users USING btree (tenant_id);


--
-- Name: appointments appointments_campaign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.appointments
    ADD CONSTRAINT appointments_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES public.content_campaigns(id) ON DELETE SET NULL;


--
-- Name: article_embeddings article_embeddings_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_embeddings
    ADD CONSTRAINT article_embeddings_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id);


--
-- Name: articles articles_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: campaign_events campaign_events_campaign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campaign_events
    ADD CONSTRAINT campaign_events_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES public.content_campaigns(id) ON DELETE CASCADE;


--
-- Name: categories categories_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.categories(id);


--
-- Name: chat_messages chat_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: drafts drafts_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drafts
    ADD CONSTRAINT drafts_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.users(id);


--
-- Name: content_campaigns fk_campaigns_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.content_campaigns
    ADD CONSTRAINT fk_campaigns_user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: media_registry media_registry_campaign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.media_registry
    ADD CONSTRAINT media_registry_campaign_id_fkey FOREIGN KEY (campaign_id) REFERENCES public.content_campaigns(id) ON DELETE SET NULL;


--
-- Name: media_registry media_registry_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.media_registry
    ADD CONSTRAINT media_registry_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: product_bases product_bases_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_bases
    ADD CONSTRAINT product_bases_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: product_embeddings product_embeddings_product_base_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_embeddings
    ADD CONSTRAINT product_embeddings_product_base_id_fkey FOREIGN KEY (product_base_id) REFERENCES public.product_bases(id);


--
-- Name: product_variants product_variants_product_base_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_variants
    ADD CONSTRAINT product_variants_product_base_id_fkey FOREIGN KEY (product_base_id) REFERENCES public.product_bases(id);


--
-- Name: rental_contracts rental_contracts_product_base_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rental_contracts
    ADD CONSTRAINT rental_contracts_product_base_id_fkey FOREIGN KEY (product_base_id) REFERENCES public.product_bases(id);


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: voice_profiles voice_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voice_profiles
    ADD CONSTRAINT voice_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Uax6iozAoYyb6DKENBnkMT12mbw17dsgOaIu5vtOmaRYScUzi7dvUsMMOkOKBTY

