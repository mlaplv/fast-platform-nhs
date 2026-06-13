"""Quick test for _inject_link_into_html logic."""
import re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.seo_contextual_linker import SeoContextualLinker

linker = SeoContextualLinker()
inject = linker._inject_link_into_html

# ── Test 1: Fast path (no inline tags) ──
content = '<p>Collagen là một protein quan trọng cho làn da.</p>'
result, ok = inject(content, 'Collagen là một protein quan trọng cho làn da.', 'Collagen', '/collagen.html', '')
assert ok, "Test 1 FAILED: should match"
assert '<a href="/collagen.html">Collagen</a>' in result, f"Test 1 FAILED: {result}"
print(f"✅ Test 1 PASSED: {result}")

# ── Test 2: Slow path (inline <strong> tag) ──
content = '<p><strong>Collagen</strong> là một protein quan trọng cho làn da.</p>'
result, ok = inject(content, 'Collagen là một protein quan trọng cho làn da.', 'protein quan trọng', '/protein.html', '')
assert ok, "Test 2 FAILED: should match via regex"
assert '<a href="/protein.html">protein quan trọng</a>' in result, f"Test 2 FAILED: {result}"
print(f"✅ Test 2 PASSED: {result}")

# ── Test 3: Slow path (whitespace differences) ──
content = '<p>Collagen  là\n  một protein quan trọng.</p>'
result, ok = inject(content, 'Collagen là một protein quan trọng.', 'protein quan trọng', '/x.html', '')
assert ok, "Test 3 FAILED: should match with whitespace diff"
assert '<a href="/x.html">protein quan trọng</a>' in result, f"Test 3 FAILED: {result}"
print(f"✅ Test 3 PASSED: {result}")

# ── Test 4: Anchor text with inline tag inside ──
content = '<p>Sử dụng <em>collagen peptide</em> giúp da căng mịn mỗi ngày.</p>'
result, ok = inject(content, 'Sử dụng collagen peptide giúp da căng mịn mỗi ngày.', 'collagen peptide', '/cp.html', ' rel="nofollow"')
assert ok, "Test 4 FAILED: anchor across inline tag"
assert '<a href="/cp.html" rel="nofollow">collagen peptide</a>' in result, f"Test 4 FAILED: {result}"
print(f"✅ Test 4 PASSED: {result}")

# ── Test 5: No match (sentence not in content) ──
content = '<p>Something completely different.</p>'
result, ok = inject(content, 'Collagen là protein.', 'Collagen', '/x.html', '')
assert not ok, "Test 5 FAILED: should NOT match"
print(f"✅ Test 5 PASSED: correctly rejected")

print("\n🎉 All 5 tests passed!")
