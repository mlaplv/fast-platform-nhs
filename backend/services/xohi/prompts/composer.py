import logging
from typing import List, Dict, Optional
from .schema import PromptComponent, PromptCategory, PromptTemplate

logger = logging.getLogger("api-gateway")

class PromptComposer:
    """
    Elite V2.2 Prompt Orchestration System (POS).
    Assembles atomic prompt components into a final system prompt.
    """
    def __init__(self):
        self._components: Dict[str, PromptComponent] = {}
        self._templates: Dict[str, PromptTemplate] = {}

    def register_component(self, component: PromptComponent) -> None:
        self._components[component.id] = component
        logger.debug(f"[POS] Registered component: {component.id} ({component.category})")

    def register_template(self, template: PromptTemplate) -> None:
        self._templates[template.name] = template
        logger.debug(f"[POS] Registered template: {template.name}")

    def compose(self, template_name: str, context: Optional[Dict[str, object]] = None, extra_components: Optional[List[str]] = None) -> str:
        """Assembles the final prompt string with dynamic mixins."""
        template = self._templates.get(template_name)
        if not template:
            logger.warning(f"[POS] Template not found: {template_name}")
            return ""

        component_ids = list(template.components)
        if extra_components:
            for ec in extra_components:
                if ec not in component_ids:
                    component_ids.append(ec)

        parts = []
        for comp_id in component_ids:
            comp = self._components.get(comp_id)
            if comp:
                content = comp.content
                # Context injection
                if context:
                    try:
                        content = content.format(**context)
                    except (KeyError, IndexError):
                        # Gracefully skip if context keys don't match
                        pass
                parts.append(content)
            else:
                logger.error(f"[POS] Component {comp_id} not found")

        return "\n\n".join(parts)

# Singleton Instance
composer = PromptComposer()
