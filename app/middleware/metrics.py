"""Middleware to track performance metrics and Cloud Run costs."""
import time
import psutil
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Cloud Run pricing constants (europe-west1)
CPU_COST_PER_VCPU_SECOND = 0.00002400  # EUR per vCPU-second
MEMORY_COST_PER_GIB_SECOND = 0.00000250  # EUR per GiB-second
REQUEST_COST_PER_MILLION = 0.40  # EUR per million requests
CONFIGURED_MEMORY_GB = 2.0  # GiB allocated in Cloud Run
MB_TO_MIB_DIVISOR = 1024  # Conversion factor for memory units

class MetricsMiddleware(BaseHTTPMiddleware):
    """Tracks time, memory, and CPU usage for each request."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Pre-request metrics
        start_time = time.time()
        process = psutil.Process(os.getpid())
        
        # Initial memory
        mem_before = process.memory_info().rss / MB_TO_MIB_DIVISOR / MB_TO_MIB_DIVISOR  # MB
        cpu_before = process.cpu_percent()
        
        # Execute request
        response = await call_next(request)
        
        # Post-request metrics
        duration = time.time() - start_time
        mem_after = process.memory_info().rss / MB_TO_MIB_DIVISOR / MB_TO_MIB_DIVISOR  # MB
        cpu_after = process.cpu_percent()
        
        # Calculate Cloud Run costs (europe-west1 pricing)
        cpu_count = os.cpu_count() or 1
        
        cpu_cost = duration * cpu_count * CPU_COST_PER_VCPU_SECOND
        mem_cost = duration * CONFIGURED_MEMORY_GB * MEMORY_COST_PER_GIB_SECOND
        request_cost = REQUEST_COST_PER_MILLION / 1_000_000
        total_cost = cpu_cost + mem_cost + request_cost
        
        # Log metrics
        logger.info(
            f"[METRICS] "
            f"Path: {request.url.path} | "
            f"Duration: {duration:.2f}s | "
            f"Memory: {mem_before:.0f}->{mem_after:.0f} MB (Delta {mem_after-mem_before:+.0f}) | "
            f"CPU: {cpu_after:.1f}% | "
            f"Cost: EUR {total_cost:.6f} (CPU: EUR {cpu_cost:.6f}, MEM: EUR {mem_cost:.6f}, REQ: EUR {request_cost:.6f})"
        )
        
        # Add custom headers for debugging
        response.headers["X-Response-Time"] = f"{duration:.2f}s"
        response.headers["X-Memory-Usage"] = f"{mem_after:.0f}MB"
        response.headers["X-Request-Cost-EUR"] = f"{total_cost:.6f}"
        
        return response
