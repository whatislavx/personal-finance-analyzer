from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)
# LifespanContext is not required by this module; import it only if available.
# Some FastAPI/Starlette versions may not provide it inside the image. We
# define a lightweight fallback to avoid import errors when the symbol is
# unused.
try:
    from fastapi.lifespan import LifespanContext  # type: ignore
except Exception:
    try:
        from starlette.lifespan import LifespanContext  # type: ignore
    except Exception:
        # Minimal fallback placeholder (no-op). Not used by this module but
        # prevents import-time failures on mismatched dependency versions.
        class LifespanContext:  # type: ignore
            def __init__(self, app=None):
                self.app = app

            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                return False

            async def __aenter__(self):
                return None

            async def __aexit__(self, exc_type, exc, tb):
                return False

from typing import List, Dict
import uuid
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from enum import Enum

from app.db.deps import get_db
from app.db.models.jobs import Job
from app.db.schemas.jobs import JobCreate, JobRead, JobUpdate
from app.core.auth import get_current_user, get_user_from_token
from app.core.rabbit import send_job_message
from app.core.config import settings

router = APIRouter(prefix="/jobs", tags=["jobs"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        self.active_connections[job_id].remove(websocket)
        if not self.active_connections[job_id]:
            del self.active_connections[job_id]

    async def send_personal_message(self, message: str, job_id: str):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                await connection.send_text(message)


manager = ConnectionManager()


# --- RabbitMQ Event Consumer ---
async def consume_job_events():  # pragma: no cover - infrastructure/Rabbit integration
    try:
        import aio_pika
    except ImportError:
        return

    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "job_events", aio_pika.ExchangeType.FANOUT
            )
            queue = await channel.declare_queue("", exclusive=True)
            await queue.bind(exchange)

            async with queue.iterator() as qiterator:
                async for message in qiterator:
                    async with message.process():
                        try:
                            payload = json.loads(message.body.decode())
                            job_id = payload.get("job_id")
                            if job_id:
                                await manager.send_personal_message(
                                    json.dumps(payload), str(job_id)
                                )
                        except Exception:
                            pass
    except Exception:
        pass

@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = Job(**job_in.model_dump())
    job.user_id = current_user.id
    db.add(job)

    await db.commit()
    await db.refresh(job)

    # Publish message to RabbitMQ (fire-and-forget)
    try:
        asyncio.create_task(
            send_job_message({"job_id": str(job.id), "user_id": str(current_user.id)})
        )
    except Exception:
        # non-fatal if RabbitMQ not configured
        pass

    return job


@router.get("/", response_model=List[JobRead])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = select(Job).where(Job.user_id == current_user.id).offset(skip).limit(limit)
    result = await db.execute(q)
    items = result.scalars().all()

    return items


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await db.get(Job, job_id)

    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="The job you are trying to access does not exist or is not associated with your account.")

    return job


@router.put("/{job_id}", response_model=JobRead)
async def update_job(
    job_id: uuid.UUID,
    job_in: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await db.get(Job, job_id)

    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="The job you are trying to access does not exist or is not associated with your account.")

    update_data = job_in.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(job, k, v)

    db.add(job)
    await db.commit()
    await db.refresh(job)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await db.get(Job, job_id)

    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="The job you are trying to access does not exist or is not associated with your account.")

    await db.delete(job)
    await db.commit()

    return None


@router.websocket("/ws/{job_id}")
async def websocket_job_events(websocket: WebSocket, job_id: str):  # pragma: no cover - websocket integration path
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    from app.db.engine import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        user = await get_user_from_token(token, db)
        job = await db.get(Job, job_id)
        if user is None or not job or not hasattr(user, "id") or str(job.user_id) != str(user.id):
            await websocket.close(code=1008)
            return

    await manager.connect(websocket, job_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Heavy ML imports are performed lazily inside perform_job to avoid
# crashing the entire application if the optional ML dependencies are
# missing in the runtime environment (they can be large and optional).
# If they are absent, the job will be marked with an error result.
#
# Updated perform_job to import ML libs on demand
async def perform_job(job_id: str, db: AsyncSession):  # pragma: no cover - heavy optional ML runtime path
    try:
        job = await db.get(Job, job_id)
        if not job:
            return

        job.status = JobStatus.IN_PROGRESS
        db.add(job)
        await db.commit()

        # Lazy import of heavy ML libraries
        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression
            from sklearn.preprocessing import PolynomialFeatures
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.impute import SimpleImputer
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            from xgboost import XGBRegressor
            from sklearn.decomposition import PCA
            from sklearn.cluster import KMeans
            import matplotlib.pyplot as plt
            import io
            import base64
        except Exception as imp_err:
            # Mark job as failed due to missing optional dependencies so the
            # API can start even if ML libs are not installed.
            err_msg = f"Missing ML dependencies: {imp_err}"
            job.status = JobStatus.COMPLETED
            job.result = {"error": err_msg}
            db.add(job)
            await db.commit()
            return

        # Simulate detailed analysis with advanced predictive modeling
        data = np.random.rand(200, 10)  # Example data with 10 features
        target = (
            3 * data[:, 0] ** 2 + 2 * data[:, 1] + 1.5 * data[:, 2] - 0.5 * data[:, 3]
            + np.random.randn(200) * 0.1
        )

        # Define pipelines for multiple models
        models = {
            "RandomForest": Pipeline([
                ("imputer", SimpleImputer(strategy="mean")),
                ("scaler", StandardScaler()),
                ("model", RandomForestRegressor(n_estimators=100, random_state=42)),
            ]),
            "GradientBoosting": Pipeline([
                ("imputer", SimpleImputer(strategy="mean")),
                ("scaler", StandardScaler()),
                ("model", GradientBoostingRegressor(n_estimators=100, random_state=42)),
            ]),
            "XGBoost": Pipeline([
                ("imputer", SimpleImputer(strategy="mean")),
                ("scaler", StandardScaler()),
                ("model", XGBRegressor(n_estimators=100, random_state=42)),
            ]),
        }

        results = {}
        for model_name, pipeline in models.items():
            pipeline.fit(data, target)
            predictions = pipeline.predict(data)

            # Evaluate model
            mae = mean_absolute_error(target, predictions)
            mse = mean_squared_error(target, predictions)
            r2 = r2_score(target, predictions)

            results[model_name] = {
                "MAE": mae,
                "MSE": mse,
                "R2": r2,
                "Feature Importances": pipeline.named_steps["model"].feature_importances_.tolist()
                if hasattr(pipeline.named_steps["model"], "feature_importances_") else None,
            }

        # Perform PCA for dimensionality reduction
        pca = PCA(n_components=2)
        reduced_data = pca.fit_transform(data)

        # Perform clustering
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(reduced_data)

        # Generate a scatter plot for PCA and clustering
        plt.figure(figsize=(8, 6))
        for cluster_id in range(3):
            cluster_points = reduced_data[clusters == cluster_id]
            plt.scatter(cluster_points[:, 0], cluster_points[:, 1], label=f"Cluster {cluster_id}")
        plt.title("PCA and Clustering")
        plt.xlabel("Principal Component 1")
        plt.ylabel("Principal Component 2")
        plt.legend()

        # Save the plot to a base64 string
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plot_base64 = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()

        # Generate advice based on the best model
        best_model = max(results, key=lambda x: results[x]["R2"])
        advice = [
            f"The best model is {best_model} with R2 score of {results[best_model]['R2']:.2f}.",
            "Focus on the most important features for better results.",
            "Clusters identified in the data can help segment your analysis.",
        ]

        # Update job progress and store results
        for step in range(1, 6):
            await asyncio.sleep(2)  # Simulate computation
            job.progress = step * 20  # Update progress
            db.add(job)
            await db.commit()

        job.status = JobStatus.COMPLETED
        job.result = {
            "model_results": results,
            "advice": advice,
            "pca_plot": plot_base64,
        }
        db.add(job)
        await db.commit()
    except Exception as e:
        raise RuntimeError(f"An error occurred during job execution: {str(e)}")
