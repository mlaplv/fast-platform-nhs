from lxml import html
html_str = "<p><div>Hello</div></p>"
fragment = html.fragment_fromstring(html_str)
div = fragment.find('div')
div.drop_tag()
print("After drop_tag:", html.tostring(fragment))
print("P text:", repr(fragment.text))
