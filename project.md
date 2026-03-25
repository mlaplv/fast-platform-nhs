# PROJECT STRUCTURE: FAST-PLATFORM (ELITE V2.2)

```diff
.
|-- backend
|   |-- alembic.ini
|   |-- app_logging.py
|   |-- body_limit.py
|   |-- constants
|   |   |-- action_vi.py
|   |   |-- agentic.py
|   |   |-- voice.py
|   |-- controllers
|   |   |-- ai_management.py
|   |   |-- article.py
|   |   |-- auditor.py
|   |   |-- auth.py
|   |   |-- banner.py
|   |   |-- category.py
|   |   |-- chat.py
|   |   |-- health.py
|   |   |-- notifications.py
|   |   |-- order.py
|   |   |-- product.py
|   |   |-- settings.py
|   |   |-- tts_handler.py
|   |   |-- user.py
-   |   |-- client/                 <-- [ELITE: GOM NHÓM CONTROLLER CLIENT]
-   |   |   |-- shop_core.py        <-- [NOTE: CHỈ XỬ LÝ READ-ONLY & PUBLIC DATA]
-   |   |   |-- checkout.py         <-- [NOTE: TẠO ĐƠN HÀNG, KHÔNG SỬA ĐƠN]
|   |-- core
|   |   |-- database.py
|   |-- database
|   |   |-- alchemy_config.py
|   |   |-- dependencies.py
|   |   |-- __init__.py
|   |   |-- models
|   |   |-- repositories.py
|   |-- Dockerfile.dev
|   |-- entrypoint.sh
|   |-- exceptions.py
|   |-- guards.py
|   |-- __init__.py
|   |-- lifespan.py
|   |-- main.py
|   |-- mcp
|   |   |-- __init__.py
|   |   |-- protocol.py
|   |   |-- tools.py
|   |-- middleware.py
-   |   |-- domain_guard.py         <-- [ELITE: CHẶN CROSS-DOMAIN ADMIN/CLIENT]
|   |-- migrations
|   |   |-- env.py
|   |   |-- script.py.mako
|   |   |-- versions
|   |-- models
|   |   |-- __init__.py
|   |   |-- schemas.py
|   |-- resources
|   |   |-- noise_dictionary.json
|   |-- result_attrs.txt
|   |-- routers
|   |   |-- content_router.py
|   |   |-- content_stream.py
|   |   |-- intent_core.py
|   |   |-- intent_map.py
|   |   |-- intent.py
|   |   |-- intent_stream.py
|   |   |-- intent_utils.py
|   |   |-- mcp
|   |   |-- media_router.py
|   |   |-- pulse_stream.py
|   |   |-- scheduler_router.py
|   |   |-- voice_core.py
|   |   |-- voice_stream.py
|   |   |-- voice_utils.py
-   |   |-- client/                 <-- [ELITE: ROUTER CHO SMART_SHOP.TEST]
|   |-- schemas
|   |   |-- ai.py
|   |   |-- article.py
|   |   |-- auditor.py
|   |   |-- auth.py
|   |   |-- banner.py
|   |   |-- category.py
|   |   |-- chat.py
|   |   |-- common.py
|   |   |-- health.py
|   |   |-- intent.py
|   |   |-- notification.py
|   |   |-- order.py
|   |   |-- product.py
|   |   |-- scheduler.py
|   |   |-- signal.py
|   |   |-- system_settings.py
|   |   |-- user.py
|   |   |-- voice.py
-   |   |-- client/                 <-- [ELITE: SCHEMAS RÚT GỌN CHO CLIENT]
-   |   |   |-- product_public.py   <-- [NOTE: KHÔNG CHỨA GIÁ NHẬP/LOG]
-   |   |   |-- order_public.py     <-- [NOTE: CHỈ CHỨA TRẠNG THÁI GIAO HÀNG]
|   |-- scripts
|   |   |-- audit_scouting_active.py
|   |   |-- index_articles.py
|   |   |-- index_products.py
|   |   |-- seed_data.py
|   |   |-- seed.py
|   |   |-- test_atomic_scout.py
|   |   |-- tmp_check_scout.py
|   |   |-- verify_admin.py
|   |-- services
|   |   |-- ai_engine
|   |   |-- ai_service.py
|   |   |-- anomaly_detector.py
|   |   |-- anti_spam.py
|   |   |-- article_service.py
|   |   |-- article_vector_service.py
|   |   |-- auditor_service.py
|   |   |-- auth_service.py
|   |   |-- banner_service.py
|   |   |-- capability_registry.py
|   |   |-- category_service.py
|   |   |-- chat_service.py
|   |   |-- data_injector.py
|   |   |-- embedding_indexer.py
|   |   |-- event_bus.py
|   |   |-- health_service.py
|   |   |-- __init__.py
|   |   |-- media
|   |   |-- memory_stt.py
|   |   |-- memory_sys.py
|   |   |-- notification_service.py
|   |   |-- order_service.py
|   |   |-- product_service.py
|   |   |-- product_vector_service.py
|   |   |-- routing
|   |   |-- settings_service.py
|   |   |-- signal_center.py
|   |   |-- storage
|   |   |-- tts_engine.py
|   |   |-- user_service.py
-   |   |-- client_service.py       <-- [ELITE: SERVICE TẬP TRUNG CHO CLIENT]
|   |   |-- xohi
|   |   |-- xohi_memory.py
|   |   |-- xohi_responder.py
|   |-- tests
|   |   |-- test_health.py
|   |   |-- test_media_smart_crop.py
|   |   |-- verify_rotator_v70.py
|   |   |-- verify_scout_elite.py
|   |-- utils
|   |   |-- cache.py
|   |   |-- data_stripper.py
|   |   |-- http_client.py
|   |   |-- __init__.py
|   |   |-- noise_cleaner.py
|   |   |-- pii_redactor.py
|   |   |-- security.py
|   |   |-- spell_checker.py
|   |   |-- sql.py
|   |   |-- text.py
|   |-- version_info.txt
|-- bulk_fix
|-- Caddyfile
|-- certs
|   |-- caddy
|   |-- caddy-root-ca.crt
|-- CHANGELOG.md
|-- check_annotations.py
|-- check_db.py
|-- check_gemini.sh
|-- checkKeyGSA.sh
|-- CLAUDE.md
|-- deploy.sh
|-- django_docker_manager.sh
|-- docker-compose.yml
|-- docs
|   |-- GITHUB_PROTECTION_GUIDE.md
|-- frontend
|   |-- Dockerfile.dev
|   |-- package.json
|   |-- pnpm-lock.yaml
|   |-- src
|   |   |-- app.d.ts
|   |   |-- app.html
|   |   |-- App.test.ts
|   |   |-- hooks.server.ts
|   |   |-- lib
|   |   |   |-- assets
-   |   |   |   |-- client/         <-- [ELITE: VITE OPTIMIZED ASSETS CHO SHOP]
|   |   |   |-- components
-   |   |   |   |-- client/         <-- [ELITE: UI COMPONENTS CHO SHOP]
|   |   |   |-- state
-   |   |   |   |-- shop.svelte.ts  <-- [ELITE: NANOBOT STORE CHO GIỎ HÀNG]
|   |   |-- routes
-   |   |   |-- (client)/           <-- [ELITE: ROUTE GROUP CHO SMART_SHOP.TEST]
-   |   |   |   |-- +layout.svelte  <-- [NOTE: LAYOUT RIÊNG KHÔNG CHỨA ADMIN UI]
-   |   |   |   |-- +layout.ts      <-- [NOTE: CONFIG CSR/SSR CHO CLIENT]
|   |-- static
|   |   |-- favicon.svg
|   |   |-- hamster-core-backup.png
|   |   |-- hamster-core.png
|   |   |-- hamster-core.svg
|   |   |-- hamster-icon.png
|   |   |-- manifest.json
|   |   |-- sw.js
|   |   |-- uploads
|   |   |-- v65_assets
|   |-- svelte.config.js
|   |-- vite.config.js
|-- infrastructure_test.sh
|-- logs_debug.txt
|-- pyproject.toml
|-- resources
|   |-- noise_dictionary.json
|-- scripts
|   |-- check_sse.py
|   |-- diagnose-rotation.py
|   |-- setup-ssl.sh
|-- task.md
|-- temp_restore
|-- temp_venv
|-- tests
|   |-- test_media_smart_crop.py
|-- text.key
|-- uv.lock
|-- walkthrough.md
|-- XOHI_CAPABILITIES.md
|-- xohi.sh
|-- z_index_compliance_report.md
```
