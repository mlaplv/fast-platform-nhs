from .composer import composer
from .core.constitution import register_core
from .agents.rewriter import register_rewriter
from .agents.copyright import register_copyright
from .agents.seo import register_seo
from .agents.inspector import register_inspector
from .agents.pen import register_pen
from .agents.booster import register_booster
from .agents.vision import register_vision
from .agents.review_booster import register_review_booster
from .shields.adapters import register_adapters
from .niches.cosmetics import register_cosmetics
from .niches.pharmaceuticals import register_pharma
from .agents.support import register_support
from .agents.routing import register_routing
from .agents.security import register_security

# Initialize and Register all components
register_core(composer)
register_rewriter(composer)
register_copyright(composer)
register_seo(composer)
register_inspector(composer)
register_pen(composer)
register_booster(composer)
register_vision(composer)
register_review_booster(composer)
register_adapters(composer)
register_cosmetics(composer)
register_pharma(composer)
register_support(composer)
register_routing(composer)
register_security(composer)

# Register Templates
from .schema import PromptTemplate

# Rewriter Templates
composer.register_template(PromptTemplate(
    name="rewriter_product",
    components=["core_constitution", "agent_rewriter_base", "niche_product_instructions"]
))

composer.register_template(PromptTemplate(
    name="rewriter_article",
    components=["core_constitution", "agent_rewriter_base", "niche_article_instructions"]
))

# Copyright Templates
composer.register_template(PromptTemplate(
    name="copyright_analysis",
    components=["core_constitution", "agent_copyright_analyst"]
))

composer.register_template(PromptTemplate(
    name="copyright_refiner",
    components=["core_constitution", "agent_copyright_refiner"]
))

# SEO Templates
composer.register_template(PromptTemplate(
    name="seo_analysis",
    components=["core_constitution", "agent_seo_strategist"]
))

composer.register_template(PromptTemplate(
    name="seo_refiner",
    components=["core_constitution", "agent_seo_refiner"]
))

# Inspector Templates
composer.register_template(PromptTemplate(
    name="inspector_analysis",
    components=["core_constitution", "agent_chief_strategist"]
))

composer.register_template(PromptTemplate(
    name="inspector_refiner",
    components=["core_constitution", "agent_viral_refiner"]
))

# Creative Pen Templates
composer.register_template(PromptTemplate(
    name="pen_outline_article",
    components=["core_constitution", "agent_editor_in_chief", "niche_article_instructions"]
))

composer.register_template(PromptTemplate(
    name="pen_draft_article",
    components=["core_constitution", "agent_neural_journalist", "niche_article_instructions"]
))

composer.register_template(PromptTemplate(
    name="pen_outline_product",
    components=["core_constitution", "agent_editor_in_chief", "niche_product_instructions"]
))

composer.register_template(PromptTemplate(
    name="pen_draft_product",
    components=["core_constitution", "agent_copywriter_master", "niche_product_instructions"]
))

# Booster Templates
composer.register_template(PromptTemplate(
    name="booster_enrich",
    components=["core_constitution", "agent_content_enricher"]
))

composer.register_template(PromptTemplate(
    name="booster_refiner",
    components=["core_constitution", "agent_refiner_booster"]
))

# Vision & Insight Templates
composer.register_template(PromptTemplate(
    name="media_analysis",
    components=["core_constitution", "agent_media_analyst"]
))

composer.register_template(PromptTemplate(
    name="insight_discovery",
    components=["core_constitution", "agent_insight_strategist"]
))

# Review Templates
composer.register_template(PromptTemplate(
    name="review_rewrite",
    components=["core_constitution", "agent_review_booster"]
))

# Micsmo Core Commerce Templates
composer.register_template(PromptTemplate(
    name="helen_support_premium",
    components=["helen_support_persona"]
))

composer.register_template(PromptTemplate(
    name="helen_intent_classifier",
    components=["helen_intent_classifier"]
))

composer.register_template(PromptTemplate(
    name="helen_consultant_premium",
    components=["helen_sales_assassin"]
))

composer.register_template(PromptTemplate(
    name="helen_consultant_skin_barrier",
    components=["helen_skin_barrier_inquiry"]
))

composer.register_template(PromptTemplate(
    name="helen_consultant_skin_barrier_analysis",
    components=["helen_skin_barrier_analysis"]
))

composer.register_template(PromptTemplate(
    name="helen_system_consultation",
    components=["helen_system_consultation"]
))

# Micsmo Routing & STT Templates
composer.register_template(PromptTemplate(
    name="stt_corrector_premium",
    components=["stt_corrector_prompt"]
))

composer.register_template(PromptTemplate(
    name="t2_dispatcher_premium",
    components=["t2_dispatcher_prompt"]
))

composer.register_template(PromptTemplate(
    name="t3_assistant_premium",
    components=["t3_assistant_prompt"]
))

# Micsmo Security Templates
composer.register_template(PromptTemplate(
    name="security_guard_premium",
    components=["security_guard_prompt"]
))

composer.register_template(PromptTemplate(
    name="antispam_fraud_premium",
    components=["antispam_fraud_prompt"]
))

