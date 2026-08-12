import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Dict

DEFAULT_VENDOR_AFF_KEYS = {
    "搬瓦工 BandwagonHost": "aff_bwh",
    "RackNerd": "aff_racknerd",
    "DMIT": "aff_dmit",
    "ClawCloud": "aff_clawcloud",
    "V.PS": "aff_vps",
    "斯巴达 SpartanHost": "aff_spartan",
    "Netcup": "aff_netcup",
    "Hetzner": "aff_hetzner",
    "BuyVM (Frantech)": "aff_buyvm",
    "AkileCloud": "aff_akile",
    "WikiHost 微基主机": "aff_wikihost",
    "Kurun 库润": "aff_kurun",
    "CloudCone": "aff_cloudcone",
}

def inject_affiliate_code(original_url: str, provider: str, aff_config: Dict[str, str]) -> str:
    """Dynamically inject user's affiliate referral parameter into a product URL"""
    if not original_url or not original_url.startswith("http"):
        return original_url

    # Find the corresponding vendor AFF key
    matched_key = None
    for prov_name, key in DEFAULT_VENDOR_AFF_KEYS.items():
        if prov_name.lower() in provider.lower() or provider.lower() in prov_name.lower():
            matched_key = key
            break

    if not matched_key:
        # Fallback to provider slug
        matched_key = f"aff_{provider.lower().replace(' ', '_')}"

    aff_code = aff_config.get(matched_key, "").strip()
    if not aff_code:
        return original_url

    try:
        parsed = urlparse(original_url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)

        # Decide parameter name based on provider
        param_name = "aff"
        if "cloudcone" in provider.lower() or "netcup" in provider.lower():
            param_name = "ref"
        elif "akile" in provider.lower():
            param_name = "aff_sub"

        query_params[param_name] = [aff_code]

        # Reconstruct query string with flat list values
        flat_query = []
        for k, v_list in query_params.items():
            for v in v_list:
                flat_query.append((k, v))
        new_query = urlencode(flat_query)

        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    except Exception:
        # If parsing fails, do safe string append
        delimiter = "&" if "?" in original_url else "?"
        return f"{original_url}{delimiter}aff={aff_code}"
