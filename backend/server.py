from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Models for BPMN Process Management
class ProcessBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProcessCreate(ProcessBase):
    bpmn_xml: Optional[str] = None

class ProcessUpdate(ProcessBase):
    bpmn_xml: Optional[str] = None

class Process(ProcessBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bpmn_xml: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Legacy models for status checks
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str


# BPMN Process endpoints
@api_router.get("/processes", response_model=List[Process])
async def get_processes():
    """Get all BPMN processes"""
    try:
        processes = await db.bpmn_processes.find().to_list(1000)
        return [Process(**process) for process in processes]
    except Exception as e:
        logger.error(f"Error fetching processes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch processes")

@api_router.get("/processes/{process_id}", response_model=Process)
async def get_process(process_id: str):
    """Get a specific BPMN process"""
    try:
        process = await db.bpmn_processes.find_one({"id": process_id})
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        return Process(**process)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching process {process_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch process")

@api_router.post("/processes", response_model=Process)
async def create_process(input: ProcessCreate):
    """Create a new BPMN process"""
    try:
        process_dict = input.dict()
        process_obj = Process(**process_dict)
        await db.bpmn_processes.insert_one(process_obj.dict())
        logger.info(f"Created new process: {process_obj.id}")
        return process_obj
    except Exception as e:
        logger.error(f"Error creating process: {e}")
        raise HTTPException(status_code=500, detail="Failed to create process")

@api_router.put("/processes/{process_id}", response_model=Process)
async def update_process(process_id: str, input: ProcessUpdate):
    """Update an existing BPMN process"""
    try:
        # Check if process exists
        existing_process = await db.bpmn_processes.find_one({"id": process_id})
        if not existing_process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        # Update process
        update_data = input.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await db.bpmn_processes.update_one(
            {"id": process_id},
            {"$set": update_data}
        )
        
        # Return updated process
        updated_process = await db.bpmn_processes.find_one({"id": process_id})
        logger.info(f"Updated process: {process_id}")
        return Process(**updated_process)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating process {process_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update process")

@api_router.delete("/processes/{process_id}")
async def delete_process(process_id: str):
    """Delete a BPMN process"""
    try:
        result = await db.bpmn_processes.delete_one({"id": process_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Process not found")
        
        logger.info(f"Deleted process: {process_id}")
        return {"message": "Process deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting process {process_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete process")

@api_router.get("/processes/{process_id}/export")
async def export_process_bpmn(process_id: str):
    """Export BPMN XML for a specific process"""
    try:
        process = await db.bpmn_processes.find_one({"id": process_id})
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        if not process.get("bpmn_xml"):
            raise HTTPException(status_code=404, detail="No BPMN XML found for this process")
        
        from fastapi.responses import Response
        return Response(
            content=process["bpmn_xml"],
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={process['name']}.bpmn"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting process {process_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export process")


# Legacy endpoints for status checks
@api_router.get("/")
async def root():
    return {"message": "BPMN Flow Editor API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()