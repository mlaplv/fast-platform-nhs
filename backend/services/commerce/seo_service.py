import json
from backend.schemas.product import ProductResponse, SeoMetaSchema

class SeoService:
    @staticmethod
    def generate_seo_meta(product: ProductResponse) -> SeoMetaSchema:
        """
        Generates fallback metadata and JSON-LD schema for a product.
        Complies with Elite V2.2 RAM/Latency protocols by pre-serializing JSON-LD.
        Requires strict typing 'product: ProductResponse' and returns 'SeoMetaSchema'.
        """
        # Fallback Metadata Rules (Title: 50-60, Desc: 150-160)
        title = product.seoTitle or product.name
        if title and len(title) > 60:
            title = title[:57] + "..."
            
        desc = product.seoDescription or product.shortDescription or (str(product.description)[:150] if product.description else f"Mua {product.name} chính gốc ưu đãi.")
        if desc and len(desc) > 160:
            desc = desc[:157] + "..."
            
        keywords = product.seoKeywords or f"{product.name}, {product.category}, ưu đãi, 2026"
        
        # SvelteKit and API should run natively on smartshop.test domain matching environment
        canonical_url = f"https://smartshop.test/{product.slug}"

        # JSON-LD Schema Build
        schema = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": product.name,
            "description": desc,
            "image": product.images if product.images else [],
            "sku": product.sku or product.id,
            "offers": {
                "@type": "Offer",
                "url": canonical_url,
                "priceCurrency": "VND",
                "price": product.discountPrice if product.discountPrice else product.price,
                "availability": "https://schema.org/InStock" if product.stock > 0 else "https://schema.org/OutOfStock",
                "itemCondition": "https://schema.org/NewCondition"
            }
        }
        
        if product.metadata and getattr(product.metadata, 'reviews', None):
            reviews_list = []
            total_rating = 0.0
            count = 0
            for r in product.metadata.reviews:
                rating = float(r.get('rating', 5))
                total_rating += rating
                count += 1
                if len(reviews_list) < 3: # Keep the schema small, max 3 reviews
                    reviews_list.append({
                        "@type": "Review",
                        "reviewRating": {
                            "@type": "Rating",
                            "ratingValue": str(rating),
                            "bestRating": "5"
                        },
                        "author": {
                            "@type": "Person",
                            "name": r.get('author_name', 'Verified Buyer')
                        },
                        "reviewBody": r.get('content', '')
                    })
            if reviews_list:
                schema["review"] = reviews_list
                # Format to string with 1 decimal place using float interpolation instead of round()
                schema["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": f"{total_rating / count:.1f}",
                    "reviewCount": str(count)
                }
        
        # Serialize logic manually to prevent deep dictionary cloning impact on RAM
        # Using json.dumps removes whitespace to save space on client DOM
        schema_json = json.dumps(schema, separators=(',', ':'), ensure_ascii=False)

        return SeoMetaSchema(
            title=title,
            description=desc,
            keywords=keywords,
            canonical_url=canonical_url,
            json_ld_string=schema_json
        )
