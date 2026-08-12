from fastapi import APIRouter, BackgroundTasks
import app.services.crawler_service as crawler_service

router = APIRouter(prefix="/crawler", tags=["Crawler"])

@router.post("/trigger")
async def trigger_crawler(background_tasks: BackgroundTasks):
    if crawler_service.is_checking:
        return {"status": "busy", "message": "监控检查正在运行中，请稍候..."}
    
    background_tasks.add_task(crawler_service.run_stock_check_cycle)
    return {"status": "started", "message": "已触发库存与价格全量检测任务！"}

@router.get("/status")
async def get_crawler_status():
    return {
        "is_checking": crawler_service.is_checking,
        "last_check_time": crawler_service.last_check_time,
        "last_result": crawler_service.last_check_result
    }
