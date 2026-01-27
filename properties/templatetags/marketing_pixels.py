from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def facebook_pixel_script():
    pixel_id = getattr(settings, 'FACEBOOK_PIXEL_ID', '')
    if not pixel_id:
        return ''
    # Return the standard Facebook Pixel script
    return (
        f"""
<!-- Facebook Pixel Code -->
<script>
  !function(f,b,e,v,n,t,s)
  {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
  n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '{pixel_id}');
  fbq('track', 'PageView');
</script>
<noscript><img height=\"1\" width=\"1\" style=\"display:none\" src=\"https://www.facebook.com/tr?id={pixel_id}&ev=PageView&noscript=1\"/></noscript>
<!-- End Facebook Pixel Code -->
"""
    )

@register.simple_tag
def facebook_track(event_name='Lead', **kwargs):
    pixel_id = getattr(settings, 'FACEBOOK_PIXEL_ID', '')
    if not pixel_id:
        return ''
    # Build parameters object for fbq
    params = ', '.join([f"'{k}': '{v}'" for k, v in kwargs.items()])
    params_js = '{' + params + '}' if params else '{}'
    return f"<script>fbq('track', '{event_name}', {params_js});</script>"
