"""Middleware per tracciare metriche di performance e costi Cloud Run."""
import time
import psutil
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Traccia tempo, memoria, CPU per ogni richiesta."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Metriche pre-request
        start_time = time.time()
        process = psutil.Process(os.getpid())
        
        # Memoria iniziale
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        cpu_before = process.cpu_percent()
        
        # Esegui request
        response = await call_next(request)
        
        # Metriche post-request
        duration = time.time() - start_time
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        cpu_after = process.cpu_percent()
        
        # Calcola costi Cloud Run (pricing europe-west1)
        # CPU: €0.00002400 per vCPU-second
        # Memory: €0.00000250 per GiB-second
        # Request: €0.40 per million requests
        
        cpu_count = os.cpu_count() or 1
        mem_gb = 2.0  # 2 GiB configurati
        
        cpu_cost = (duration * cpu_count * 0.00002400)  # €
        mem_cost = (duration * mem_gb * 0.00000250)     # €
        request_cost = 0.40 / 1_000_000                  # €
        total_cost = cpu_cost + mem_cost + request_cost
        
        # Log metriche
        logger.info(
            f"[METRICS] "
            f"Path: {request.url.path} | "
            f"Duration: {duration:.2f}s | "
            f"Memory: {mem_before:.0f}->{mem_after:.0f} MB (Delta {mem_after-mem_before:+.0f}) | "
            f"CPU: {cpu_after:.1f}% | "
            f"Cost: EUR {total_cost:.6f} (CPU: EUR {cpu_cost:.6f}, MEM: EUR {mem_cost:.6f}, REQ: EUR {request_cost:.6f})"
        )
        
        # Aggiungi header custom per debug
        response.headers["X-Response-Time"] = f"{duration:.2f}s"
        response.headers["X-Memory-Usage"] = f"{mem_after:.0f}MB"
        response.headers["X-Request-Cost-EUR"] = f"{total_cost:.6f}"
        
        return response
