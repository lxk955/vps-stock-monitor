from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, delete
from typing import Optional, List
import json

from app.core.database import get_db
from app.models.product import Product, PriceHistory
from app.models.setting import Setting
from app.core.security import verify_admin_token
from app.services.aff_service import inject_affiliate_code

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("")
async def get_products(
    q: Optional[str] = None,
    ids: Optional[str] = None,
    provider: Optional[str] = None,
    region: Optional[str] = None,
    line: Optional[str] = None,
    stock: Optional[str] = None,
    cycle: Optional[str] = None,
    currency: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    cpu_min: Optional[int] = None,
    ram_min: Optional[int] = None,
    disk_min: Optional[int] = None,
    traffic_min: Optional[int] = None,
    port_min: Optional[int] = None,
    recommended: Optional[bool] = None,
    sort: Optional[str] = "value",
    page: int = Query(0, ge=0),
    size: int = Query(40, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Product).where(Product.is_active == True)

    # Specific IDs filter (e.g. for user's watched products across all pages)
    if ids:
        id_list = []
        for i in ids.split(","):
            i_str = i.strip()
            if i_str.isdigit():
                id_list.append(int(i_str))
        if id_list:
            query = query.where(Product.id.in_(id_list))

    if stock:
        query = query.where(Product.status == stock)
    if recommended:
        query = query.where(Product.recommended == True)
    if provider:
        providers = [p.strip() for p in provider.split(",") if p.strip()]
        if providers:
            query = query.where(Product.provider.in_(providers))
    if cycle:
        cycles = [c.strip() for c in cycle.split(",") if c.strip()]
        if cycles:
            query = query.where(Product.price_cycle.in_(cycles))
    if currency:
        currencies = [c.strip() for c in currency.split(",") if c.strip()]
        if currencies:
            query = query.where(Product.currency.in_(currencies))
    
    if price_min is not None:
        query = query.where(Product.price >= price_min)
    if price_max is not None:
        query = query.where(Product.price <= price_max)
    if cpu_min is not None:
        query = query.where(Product.cpu_cores >= cpu_min)
    if ram_min is not None:
        query = query.where(Product.ram_mb >= ram_min)
    if disk_min is not None:
        query = query.where(Product.disk_gb >= disk_min)
    if traffic_min is not None:
        query = query.where(Product.transfer_gb >= traffic_min)
    if port_min is not None:
        query = query.where(Product.port_mbps >= port_min)

    if q and q.strip():
        search_kw = f"%{q.strip()}%"
        query = query.where(
            (Product.name.ilike(search_kw)) |
            (Product.provider.ilike(search_kw)) |
            (Product.group.ilike(search_kw)) |
            (Product.regions_json.ilike(search_kw)) |
            (Product.lines_json.ilike(search_kw)) |
            (Product.cpu.ilike(search_kw)) |
            (Product.ram.ilike(search_kw))
        )

    result = await db.execute(query)
    all_filtered = result.scalars().all()

    final_list = []
    for prod in all_filtered:
        if region:
            req_regions = [r.strip().lower() for r in region.split(",") if r.strip()]
            prod_regions = [r.lower() for r in prod.regions]
            if not any(req in " ".join(prod_regions) for req in req_regions):
                continue
        if line:
            req_lines = [l.strip().lower() for l in line.split(",") if l.strip()]
            prod_lines = [l.lower() for l in prod.lines]
            if not any(req in " ".join(prod_lines) for req in req_lines):
                continue
        final_list.append(prod)

    total = len(final_list)

    if sort == "price":
        final_list.sort(key=lambda p: (p.price or 0))
    elif sort == "-price":
        final_list.sort(key=lambda p: (p.price or 0), reverse=True)
    elif sort == "cpu":
        final_list.sort(key=lambda p: (p.cpu_cores or 0), reverse=True)
    elif sort == "ram":
        final_list.sort(key=lambda p: (p.ram_mb or 0), reverse=True)
    elif sort == "clicks":
        final_list.sort(key=lambda p: (p.clicks or 0), reverse=True)
    else: # "value"
        def calc_value_score(p: Product):
            p_price = p.price if p.price and p.price > 0 else 10.0
            if p.price_cycle == "monthly": annual_est = p_price * 12
            elif p.price_cycle == "quarterly": annual_est = p_price * 4
            elif p.price_cycle == "semiannually": annual_est = p_price * 2
            else: annual_est = p_price
            score = (p.cpu_cores * 1.5 + (p.ram_mb / 1024.0) * 2.0 + (p.disk_gb / 20.0) + (p.transfer_gb / 500.0) * 0.5) * 100
            if p.recommended: score *= 1.3
            return score / (annual_est + 1.0)

        final_list.sort(key=calc_value_score, reverse=True)

    # Load settings for dynamic AFF injection
    settings_res = await db.execute(select(Setting))
    settings_dict = {s.key: s.value for s in settings_res.scalars().all()}

    start_idx = page * size
    paginated = final_list[start_idx : start_idx + size]

    output_products = []
    for p in paginated:
        d = p.to_dict()
        if d.get("affiliate_url"):
            d["affiliate_url"] = inject_affiliate_code(d["affiliate_url"], p.provider, settings_dict)
        output_products.append(d)

    return {
        "total": total,
        "page": page,
        "size": size,
        "products": output_products
    }

@router.get("/facets")
async def get_facets(db: AsyncSession = Depends(get_db)):
    """Return aggregations for filtering facets"""
    result = await db.execute(select(Product).where(Product.is_active == True))
    products = result.scalars().all()

    region_counts = {}
    line_counts = {}
    provider_counts = {}
    cycle_counts = {}
    currency_counts = {}

    for p in products:
        provider_counts[p.provider] = provider_counts.get(p.provider, 0) + 1
        if p.price_cycle:
            cycle_counts[p.price_cycle] = cycle_counts.get(p.price_cycle, 0) + 1
        if p.currency:
            currency_counts[p.currency] = currency_counts.get(p.currency, 0) + 1
        for r in p.regions:
            region_counts[r] = region_counts.get(r, 0) + 1
        for l in p.lines:
            line_counts[l] = line_counts.get(l, 0) + 1

    format_facet = lambda d: [{"value": k, "count": v} for k, v in sorted(d.items(), key=lambda x: x[1], reverse=True)]

    return {
        "provider": format_facet(provider_counts),
        "region": format_facet(region_counts),
        "line": format_facet(line_counts),
        "cycle": format_facet(cycle_counts),
        "currency": format_facet(currency_counts)
    }

@router.get("/{id}")
async def get_product(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    settings_res = await db.execute(select(Setting))
    settings_dict = {s.key: s.value for s in settings_res.scalars().all()}
    
    d = product.to_dict()
    if d.get("affiliate_url"):
        d["affiliate_url"] = inject_affiliate_code(d["affiliate_url"], product.provider, settings_dict)
    return d

@router.get("/{id}/price-history")
async def get_price_history(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == id)
        .order_by(asc(PriceHistory.recorded_at))
    )
    histories = result.scalars().all()
    return [h.to_dict() for h in histories]

@router.post("/{id}/click")
async def record_click(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalar_one_or_none()
    if product:
        product.clicks = (product.clicks or 0) + 1
        await db.commit()
    return {"status": "ok"}

@router.post("")
async def create_product(
    data: dict,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Protected: create product (requires admin token)"""
    product = Product(
        provider=data.get("provider", "自定义厂商"),
        name=data.get("name", "新 VPS 产品"),
        group=data.get("group", ""),
        cpu=data.get("cpu", "1 vCPU"),
        ram=data.get("ram", "1024 MB"),
        disk=data.get("disk", "20 GB SSD"),
        transfer=data.get("transfer", "1000 GB/月"),
        port_speed=data.get("port_speed", "1 Gbps"),
        cpu_cores=int(data.get("cpu_cores", 1)),
        ram_mb=int(data.get("ram_mb", 1024)),
        disk_gb=int(data.get("disk_gb", 20)),
        transfer_gb=int(data.get("transfer_gb", 1000)),
        port_mbps=int(data.get("port_mbps", 1000)),
        regions_json=json.dumps(data.get("regions", []), ensure_ascii=False),
        lines_json=json.dumps(data.get("lines", []), ensure_ascii=False),
        status=data.get("status", "in_stock"),
        stock_qty=data.get("stock_qty"),
        price=float(data.get("price", 10.0)),
        original_price=data.get("original_price"),
        currency=data.get("currency", "USD"),
        price_cycle=data.get("price_cycle", "annually"),
        affiliate_url=data.get("affiliate_url", ""),
        stock_check_url=data.get("stock_check_url", ""),
        stock_check_type=data.get("stock_check_type", "manual"),
        out_of_stock_keyword=data.get("out_of_stock_keyword", "Out of Stock"),
        recommended=bool(data.get("recommended", False))
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    history = PriceHistory(
        product_id=product.id,
        price=product.price,
        currency=product.currency,
        status=product.status,
        stock_qty=product.stock_qty
    )
    db.add(history)
    await db.commit()

    return product.to_dict()

@router.put("/{id}")
async def update_product(
    id: int,
    data: dict,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Protected: update product (requires admin token)"""
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    old_price = product.price
    new_price = float(data["price"]) if "price" in data and data["price"] is not None else old_price

    if "provider" in data: product.provider = data["provider"]
    if "name" in data: product.name = data["name"]
    if "group" in data: product.group = data["group"]
    if "cpu" in data: product.cpu = data["cpu"]
    if "ram" in data: product.ram = data["ram"]
    if "disk" in data: product.disk = data["disk"]
    if "transfer" in data: product.transfer = data["transfer"]
    if "port_speed" in data: product.port_speed = data["port_speed"]
    if "cpu_cores" in data: product.cpu_cores = int(data["cpu_cores"])
    if "ram_mb" in data: product.ram_mb = int(data["ram_mb"])
    if "disk_gb" in data: product.disk_gb = int(data["disk_gb"])
    if "transfer_gb" in data: product.transfer_gb = int(data["transfer_gb"])
    if "port_mbps" in data: product.port_mbps = int(data["port_mbps"])
    if "regions" in data: product.regions = data["regions"]
    if "lines" in data: product.lines = data["lines"]
    if "status" in data: product.status = data["status"]
    if "stock_qty" in data: product.stock_qty = data["stock_qty"]
    if "original_price" in data: product.original_price = data["original_price"]
    if "currency" in data: product.currency = data["currency"]
    if "price_cycle" in data: product.price_cycle = data["price_cycle"]
    if "affiliate_url" in data: product.affiliate_url = data["affiliate_url"]
    if "stock_check_url" in data: product.stock_check_url = data["stock_check_url"]
    if "stock_check_type" in data: product.stock_check_type = data["stock_check_type"]
    if "out_of_stock_keyword" in data: product.out_of_stock_keyword = data["out_of_stock_keyword"]
    if "recommended" in data: product.recommended = bool(data["recommended"])
    if "is_active" in data: product.is_active = bool(data["is_active"])

    if new_price != old_price:
        product.previous_price = old_price
        product.price = new_price
        history = PriceHistory(
            product_id=product.id,
            price=new_price,
            currency=product.currency,
            status=product.status,
            stock_qty=product.stock_qty
        )
        db.add(history)

    await db.commit()
    await db.refresh(product)
    return product.to_dict()

@router.delete("/{id}")
async def delete_product(
    id: int,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Protected: delete product (requires admin token)"""
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    await db.delete(product)
    await db.commit()
    return {"status": "deleted"}

@router.post("/sync-presets")
async def sync_preset_products(
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Protected: Synchronize / upsert preset products from code into database"""
    from app.services.presets import PRESET_PRODUCTS
    updated_count = 0
    created_count = 0

    for item in PRESET_PRODUCTS:
        result = await db.execute(
            select(Product).where(
                Product.provider == item["provider"],
                Product.name == item["name"]
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.group = item.get("group", "")
            existing.cpu = item.get("cpu")
            existing.ram = item.get("ram")
            existing.disk = item.get("disk")
            existing.transfer = item.get("transfer")
            existing.port_speed = item.get("port_speed")
            existing.cpu_cores = item.get("cpu_cores", 1)
            existing.ram_mb = item.get("ram_mb", 1024)
            existing.disk_gb = item.get("disk_gb", 20)
            existing.transfer_gb = item.get("transfer_gb", 1000)
            existing.port_mbps = item.get("port_mbps", 1000)
            existing.regions_json = json.dumps(item.get("regions", []), ensure_ascii=False)
            existing.lines_json = json.dumps(item.get("lines", []), ensure_ascii=False)
            existing.price = item.get("price", 0.0)
            existing.original_price = item.get("original_price")
            existing.currency = item.get("currency", "USD")
            existing.price_cycle = item.get("price_cycle", "annually")
            existing.affiliate_url = item.get("affiliate_url", "")
            existing.stock_check_url = item.get("stock_check_url", "")
            existing.stock_check_type = item.get("stock_check_type", "whmcs")
            existing.out_of_stock_keyword = item.get("out_of_stock_keyword", "Out of Stock")
            existing.recommended = bool(item.get("recommended", False))
            updated_count += 1
        else:
            prod = Product(
                provider=item["provider"],
                name=item["name"],
                group=item.get("group", ""),
                cpu=item.get("cpu"),
                ram=item.get("ram"),
                disk=item.get("disk"),
                transfer=item.get("transfer"),
                port_speed=item.get("port_speed"),
                cpu_cores=item.get("cpu_cores", 1),
                ram_mb=item.get("ram_mb", 1024),
                disk_gb=item.get("disk_gb", 20),
                transfer_gb=item.get("transfer_gb", 1000),
                port_mbps=item.get("port_mbps", 1000),
                regions_json=json.dumps(item.get("regions", []), ensure_ascii=False),
                lines_json=json.dumps(item.get("lines", []), ensure_ascii=False),
                status=item.get("status", "in_stock"),
                stock_qty=item.get("stock_qty"),
                price=item.get("price", 0.0),
                original_price=item.get("original_price"),
                currency=item.get("currency", "USD"),
                price_cycle=item.get("price_cycle", "annually"),
                affiliate_url=item.get("affiliate_url", ""),
                stock_check_url=item.get("stock_check_url", ""),
                stock_check_type=item.get("stock_check_type", "whmcs"),
                out_of_stock_keyword=item.get("out_of_stock_keyword", "Out of Stock"),
                recommended=item.get("recommended", False),
                clicks=item.get("clicks", 0),
                is_active=True
            )
            db.add(prod)
            created_count += 1

    await db.commit()
    return {"message": f"成功同步预设数据：更新 {updated_count} 个产品，新增 {created_count} 个产品！"}
