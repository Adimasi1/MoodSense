"""
Cloud Run Cost Calculator for MoodSense - Free Tier Budget Analysis

Google Cloud Free Tier (always free):
- 2 million requests/month
- 360,000 vCPU-seconds/month (100 CPU hours)
- 180,000 GiB-seconds/month (50 hours with 1GB RAM)

Cloud Run Pricing (europe-west1):
- CPU: €0.00002400 per vCPU-second
- Memory: €0.00000250 per GiB-second  
- Requests: €0.40 per million requests
"""

# CONSTANTS
COLD_START_RATIO = 0.1  # 10% of requests have cold starts
WARM_REQUEST_RATIO = 0.9  # 90% of requests are warm
DAYS_PER_MONTH = 30  # Standard month length
PRICING_CPU_PER_VCPU_SEC = 0.00002400  # EUR
PRICING_MEM_PER_GIB_SEC = 0.00000250  # EUR
PRICING_REQ_PER_MILLION = 0.40  # EUR
HOURS_PER_SECOND = 3600  # Conversion factor

# CLOUD RUN CONFIGURATION
CPU_CORES = 2  # vCPU allocated
MEMORY_GB = 2.0  # GiB allocated
MIN_INSTANCES = 0  # No fixed cost (scale-to-zero)
MAX_INSTANCES = 1  # Limits concurrency

# PERFORMANCE ESTIMATES (after optimizations)
AVG_DURATION_SECONDS = 60  # ~60 sec per 2000 messages (with 2 CPU + optimizations)
COLD_START_SECONDS = 30  # First request after inactivity

# USAGE SCENARIOS
scenarios = {
    "Development (5 tests/day)": {
        "requests_per_day": 5,
        "days_per_month": DAYS_PER_MONTH,
    },
    "Beta testing (20 analyses/day)": {
        "requests_per_day": 20,
        "days_per_month": DAYS_PER_MONTH,
    },
    "Light production (50/day)": {
        "requests_per_day": 50,
        "days_per_month": DAYS_PER_MONTH,
    },
    "Medium production (200/day)": {
        "requests_per_day": 200,
        "days_per_month": DAYS_PER_MONTH,
    },
}

# FREE TIER MONTHLY LIMITS
FREE_REQUESTS = 2_000_000
FREE_CPU_SECONDS = 360_000
FREE_MEM_GB_SECONDS = 180_000

def calculate_monthly_cost(requests_per_day: int, days: int):
    """Calculates monthly costs for a usage scenario."""
    
    total_requests = requests_per_day * days
    
    # Assume 10% cold starts
    warm_requests = int(total_requests * WARM_REQUEST_RATIO)
    cold_requests = int(total_requests * COLD_START_RATIO)
    
    # Total execution time
    total_duration = (warm_requests * AVG_DURATION_SECONDS) + (cold_requests * (AVG_DURATION_SECONDS + COLD_START_SECONDS))
    
    # Resources consumed
    total_cpu_seconds = total_duration * CPU_CORES
    total_mem_gb_seconds = total_duration * MEMORY_GB
    
    # Subtract Free Tier
    billable_requests = max(0, total_requests - FREE_REQUESTS)
    billable_cpu_seconds = max(0, total_cpu_seconds - FREE_CPU_SECONDS)
    billable_mem_gb_seconds = max(0, total_mem_gb_seconds - FREE_MEM_GB_SECONDS)
    
    # Calculate costs
    request_cost = (billable_requests / 1_000_000) * PRICING_REQ_PER_MILLION
    cpu_cost = billable_cpu_seconds * PRICING_CPU_PER_VCPU_SEC
    mem_cost = billable_mem_gb_seconds * PRICING_MEM_PER_GIB_SEC
    
    total_cost = request_cost + cpu_cost + mem_cost
    
    return {
        "requests": total_requests,
        "cpu_seconds": total_cpu_seconds,
        "mem_gb_seconds": total_mem_gb_seconds,
        "within_free_tier": total_requests < FREE_REQUESTS and total_cpu_seconds < FREE_CPU_SECONDS and total_mem_gb_seconds < FREE_MEM_GB_SECONDS,
        "request_cost": request_cost,
        "cpu_cost": cpu_cost,
        "mem_cost": mem_cost,
        "total_monthly_cost": total_cost,
        "cost_per_request": total_cost / total_requests if total_requests > 0 else 0,
    }

print("=" * 80)
print("💰 CLOUD RUN COST CALCULATOR - MoodSense")
print("=" * 80)
print(f"\n📊 Configuration:")
print(f"  - CPU: {CPU_CORES} vCPU")
print(f"  - Memory: {MEMORY_GB} GiB")
print(f"  - Min instances: {MIN_INSTANCES} (scale-to-zero)")
print(f"  - Max instances: {MAX_INSTANCES}")
print(f"  - Average time: {AVG_DURATION_SECONDS}s per request")
print(f"  - Cold start: +{COLD_START_SECONDS}s")

print(f"\n🎁 Monthly Free Tier:")
print(f"  - Requests: {FREE_REQUESTS:,}")
print(f"  - CPU: {FREE_CPU_SECONDS:,} vCPU-seconds ({FREE_CPU_SECONDS/HOURS_PER_SECOND:.1f} hours)")
print(f"  - Memory: {FREE_MEM_GB_SECONDS:,} GiB-seconds ({FREE_MEM_GB_SECONDS/HOURS_PER_SECOND:.1f} hours @ 1GB)")

print("\n" + "=" * 80)
print("💸 COST SCENARIOS")
print("=" * 80)

for name, config in scenarios.items():
    result = calculate_monthly_cost(config["requests_per_day"], config["days_per_month"])
    
    print(f"\n📱 {name}")
    print(f"  └─ Requests/month: {result['requests']:,}")
    print(f"  └─ CPU consumed: {result['cpu_seconds']:,.0f} vCPU-sec ({result['cpu_seconds']/HOURS_PER_SECOND:.1f} hours)")
    print(f"  └─ Memory consumed: {result['mem_gb_seconds']:,.0f} GiB-sec ({result['mem_gb_seconds']/HOURS_PER_SECOND:.1f} hours)")
    
    if result["within_free_tier"]:
        print(f"  ✅ COMPLETELY FREE (within Free Tier)")
        print(f"  └─ Cost: €0.00/month")
    else:
        print(f"  ⚠️  Outside Free Tier")
        print(f"  └─ Request cost: €{result['request_cost']:.2f}")
        print(f"  └─ CPU cost: €{result['cpu_cost']:.2f}")
        print(f"  └─ Memory cost: €{result['mem_cost']:.2f}")
        print(f"  └─ TOTAL: €{result['total_monthly_cost']:.2f}/month")
        print(f"  └─ Cost per analysis: €{result['cost_per_request']:.4f}")

print("\n" + "=" * 80)
print("🎯 LIMITS TO STAY IN FREE TIER")
print("=" * 80)

# Calculate daily request limits
max_daily_requests_cpu = FREE_CPU_SECONDS / (AVG_DURATION_SECONDS * CPU_CORES) / DAYS_PER_MONTH
max_daily_requests_mem = FREE_MEM_GB_SECONDS / (AVG_DURATION_SECONDS * MEMORY_GB) / DAYS_PER_MONTH
max_daily_requests = min(max_daily_requests_cpu, max_daily_requests_mem)

print(f"\n📈 With current configuration ({CPU_CORES} CPU, {MEMORY_GB} GB, {AVG_DURATION_SECONDS}s/req):")
print(f"  - CPU limit: ~{max_daily_requests_cpu:.0f} requests/day")
print(f"  - Memory limit: ~{max_daily_requests_mem:.0f} requests/day")
print(f"  - Effective limit: ~{max_daily_requests:.0f} requests/day")
print(f"  - That is: ~{max_daily_requests * DAYS_PER_MONTH:.0f} requests/month FREE")

print("\n" + "=" * 80)
print("💡 RECOMMENDATIONS")
print("=" * 80)
print("""
1. ✅ Development/Testing (5-20/day): COMPLETELY FREE
2. ✅ Beta (50/day): COMPLETELY FREE  
3. ⚠️  Production (200+/day): ~€5-10/month

4. For ZERO costs with more users:
   - Reduce CPU to 1 vCPU (slower but free longer)
   - Limit to 100 analyses/month with user quota
   - Use result caching for already analyzed chats

5. Google Cloud Budget:
   - Go to Billing → Budgets & Alerts
   - Create €5/month budget with alerts at 50%, 80%, 100%
   - You'll receive emails if threshold exceeded
""")

print("=" * 80)
