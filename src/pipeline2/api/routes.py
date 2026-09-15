"""FastAPI routes for the Text-to-SQL system."""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from .schemas import QueryRequest, QueryResponse, TrainRequest, TrainResponse, ModelInfo, HealthResponse
from .dependencies import AuthDependency, RateLimiter, ModelManager, DatabaseManager
from ..inference.llama_engine import LlamaEngine
from ..sql.validator import SQLValidator
from ..sql.executor import SQLExecutor
from ..visualization.vega_generator import VegaLiteGenerator

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Text-to-SQL API",
    version="1.0.0",
    description="Convert natural language to SQL with automatic visualization"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencies
auth = AuthDependency()
rate_limiter = RateLimiter()
model_manager = ModelManager()
db_manager = DatabaseManager()


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from .health import health_check as check
    return await check()


@app.post("/api/v1/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    auth_result: dict = Depends(auth),
    rate_limit: bool = Depends(rate_limiter)
):
    """
    Submit a natural language query.
    
    Args:
        request: QueryRequest with user query and parameters
        
    Returns:
        QueryResponse with SQL, data, and visualization
    """
    try:
        query_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Processing query {query_id}: {request.query[:100]}...")
        
        # Get model
        model = await model_manager.get_model(request.model_id)
        engine = LlamaEngine(model.path, model.config)
        
        # Build prompt
        schema = await db_manager.get_schema()
        business_rules = await db_manager.get_business_rules()
        
        prompt = engine.build_prompt(
            user_query=request.query,
            schema=schema,
            business_rules=business_rules,
            current_date=datetime.utcnow()
        )
        
        # Generate SQL and intent
        result = engine.generate(prompt)
        sql = result.get('sql')
        intent = result.get('intent', {})
        
        # Validate SQL
        validator = SQLValidator(schema)
        is_valid, errors = validator.validate(sql)
        
        if not is_valid and request.max_retries > 0:
            # Attempt repair
            for attempt in range(request.max_retries):
                sql = validator.repair_sql(sql, errors)
                is_valid, errors = validator.validate(sql)
                if is_valid:
                    break
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid SQL generated: {', '.join(errors)}"
            )
        
        # Execute SQL
        executor = SQLExecutor(db_manager.connection_pool)
        data = executor.execute(sql)
        
        # Generate visualization
        viz = None
        if request.include_viz:
            viz_generator = VegaLiteGenerator()
            viz = viz_generator.generate(data, intent)
        
        # Log query
        background_tasks.add_task(
            log_query,
            query_id=query_id,
            user_query=request.query,
            sql=sql,
            row_count=len(data),
            execution_time=(datetime.utcnow() - start_time).total_seconds()
        )
        
        return QueryResponse(
            query_id=query_id,
            sql=sql,
            data=data,
            visualization=viz,
            intent=intent,
            metadata={
                'execution_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                'row_count': len(data),
                'model_version': model.version
            }
        )
        
    except Exception as e:
        logger.error(f"Query {query_id} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/train", response_model=TrainResponse)
async def train_endpoint(
    request: TrainRequest,
    background_tasks: BackgroundTasks,
    auth_result: dict = Depends(auth)
):
    """
    Start training pipeline.
    
    Args:
        request: TrainRequest with database URL and business docs
        
    Returns:
        TrainResponse with model ID and status
    """
    try:
        job_id = str(uuid.uuid4())
        logger.info(f"Starting training job {job_id}")
        
        # Start training in background
        background_tasks.add_task(
            run_training,
            job_id=job_id,
            database_url=request.database_url,
            business_docs=request.business_docs,
            model_name=request.model_name,
            config=request.config
        )
        
        return TrainResponse(
            model_id=job_id,
            status="started",
            metrics={}
        )
        
    except Exception as e:
        logger.error(f"Training job failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/models", response_model=List[ModelInfo])
async def list_models(
    auth_result: dict = Depends(auth)
):
    """List available models."""
    try:
        models = await model_manager.list_models()
        return models
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/models/{model_id}/load")
async def load_model(
    model_id: str,
    auth_result: dict = Depends(auth)
):
    """Load a specific model for inference."""
    try:
        await model_manager.load_model(model_id)
        return {"status": "loaded", "model_id": model_id}
    except Exception as e:
        logger.error(f"Failed to load model {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def log_query(query_id: str, user_query: str, sql: str, row_count: int, execution_time: float):
    """Background task to log query."""
    logger.info(f"Query {query_id} completed: {row_count} rows, {execution_time:.2f}s")


async def run_training(job_id: str, database_url: str, business_docs: List[str], model_name: str, config: dict):
    """Background task for training."""
    logger.info(f"Training job {job_id} started")
    try:
        from src.pipeline1.schema_extractor.extractor import SchemaExtractor
        from src.pipeline1.business_rules.parser import BusinessRuleParser
        from src.pipeline1.dataset.generator import DatasetGenerator
        from src.pipeline1.training.trainer import QLoRATrainer
        
        # Extract schema
        extractor = SchemaExtractor(database_url)
        schema = extractor.extract_full_schema()
        
        # Parse business rules
        parser = BusinessRuleParser()
        rules = parser.parse_documents(business_docs)
        
        # Generate dataset
        generator = DatasetGenerator(schema, rules)
        dataset = generator.generate_examples()
        
        # Train model
        trainer = QLoRATrainer(model_name, config)
        model_path = trainer.train(dataset)
        
        # Register model
        await model_manager.register_model(job_id, model_path)
        
        logger.info(f"Training job {job_id} completed")
    except Exception as e:
        logger.error(f"Training job {job_id} failed: {str(e)}")