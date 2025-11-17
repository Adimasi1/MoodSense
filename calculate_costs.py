"""
Calcolo costi Cloud Run MoodSense - Budget Free Tier e oltre

Google Cloud Free Tier (sempre gratis):
- 2 million requests/month
- 360,000 vCPU-seconds/month (100 ore CPU)
- 180,000 GiB-seconds/month (50 ore con 1GB RAM)

Pricing Cloud Run (europa-west1):
- CPU: €0.00002400 per vCPU-second
- Memory: €0.00000250 per GiB-second  
- Requests: €0.40 per million requests
"""

# CONFIGURAZIONE CLOUD RUN
CPU_CORES = 2  # vCPU allocate
MEMORY_GB = 2.0  # GiB allocate
MIN_INSTANCES = 0  # No costo fisso
MAX_INSTANCES = 1  # Limita concorrenza

# STIMA PERFORMANCE (dopo ottimizzazioni)
AVG_DURATION_SECONDS = 60  # ~60 sec per 2000 messaggi (con 2 CPU + ottimizzazioni)
COLD_START_SECONDS = 30     # Prima richiesta dopo inattività

# SCENARI DI UTILIZZO
scenarios = {
    "Sviluppo (5 test/giorno)": {
        "requests_per_day": 5,
        "days_per_month": 30,
    },
    "Beta test (20 analisi/giorno)": {
        "requests_per_day": 20,
        "days_per_month": 30,
    },
    "Produzione leggera (50/giorno)": {
        "requests_per_day": 50,
        "days_per_month": 30,
    },
    "Produzione media (200/giorno)": {
        "requests_per_day": 200,
        "days_per_month": 30,
    },
}

# FREE TIER MENSILE
FREE_REQUESTS = 2_000_000
FREE_CPU_SECONDS = 360_000
FREE_MEM_GB_SECONDS = 180_000

def calculate_monthly_cost(requests_per_day: int, days: int):
    """Calcola costi mensili per uno scenario."""
    
    total_requests = requests_per_day * days
    
    # Assumi 10% cold start
    warm_requests = int(total_requests * 0.9)
    cold_requests = int(total_requests * 0.1)
    
    # Tempo totale
    total_duration = (warm_requests * AVG_DURATION_SECONDS) + (cold_requests * (AVG_DURATION_SECONDS + COLD_START_SECONDS))
    
    # Risorse consumate
    total_cpu_seconds = total_duration * CPU_CORES
    total_mem_gb_seconds = total_duration * MEMORY_GB
    
    # Sottrai Free Tier
    billable_requests = max(0, total_requests - FREE_REQUESTS)
    billable_cpu_seconds = max(0, total_cpu_seconds - FREE_CPU_SECONDS)
    billable_mem_gb_seconds = max(0, total_mem_gb_seconds - FREE_MEM_GB_SECONDS)
    
    # Calcola costi
    request_cost = (billable_requests / 1_000_000) * 0.40
    cpu_cost = billable_cpu_seconds * 0.00002400
    mem_cost = billable_mem_gb_seconds * 0.00000250
    
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
print("💰 CALCOLO COSTI CLOUD RUN - MoodSense")
print("=" * 80)
print(f"\n📊 Configurazione:")
print(f"  - CPU: {CPU_CORES} vCPU")
print(f"  - Memory: {MEMORY_GB} GiB")
print(f"  - Min instances: {MIN_INSTANCES} (scale-to-zero)")
print(f"  - Max instances: {MAX_INSTANCES}")
print(f"  - Tempo medio: {AVG_DURATION_SECONDS}s per richiesta")
print(f"  - Cold start: +{COLD_START_SECONDS}s")

print(f"\n🎁 Free Tier mensile:")
print(f"  - Requests: {FREE_REQUESTS:,}")
print(f"  - CPU: {FREE_CPU_SECONDS:,} vCPU-seconds ({FREE_CPU_SECONDS/3600:.1f} ore)")
print(f"  - Memory: {FREE_MEM_GB_SECONDS:,} GiB-seconds ({FREE_MEM_GB_SECONDS/3600:.1f} ore @ 1GB)")

print("\n" + "=" * 80)
print("💸 SCENARI DI COSTO")
print("=" * 80)

for name, config in scenarios.items():
    result = calculate_monthly_cost(config["requests_per_day"], config["days_per_month"])
    
    print(f"\n📱 {name}")
    print(f"  └─ Richieste/mese: {result['requests']:,}")
    print(f"  └─ CPU consumata: {result['cpu_seconds']:,.0f} vCPU-sec ({result['cpu_seconds']/3600:.1f} ore)")
    print(f"  └─ Memory consumata: {result['mem_gb_seconds']:,.0f} GiB-sec ({result['mem_gb_seconds']/3600:.1f} ore)")
    
    if result["within_free_tier"]:
        print(f"  ✅ TUTTO GRATIS (dentro Free Tier)")
        print(f"  └─ Costo: €0.00/mese")
    else:
        print(f"  ⚠️  Fuori Free Tier")
        print(f"  └─ Costo requests: €{result['request_cost']:.2f}")
        print(f"  └─ Costo CPU: €{result['cpu_cost']:.2f}")
        print(f"  └─ Costo Memory: €{result['mem_cost']:.2f}")
        print(f"  └─ TOTALE: €{result['total_monthly_cost']:.2f}/mese")
        print(f"  └─ Costo per analisi: €{result['cost_per_request']:.4f}")

print("\n" + "=" * 80)
print("🎯 LIMITI PER RESTARE NEL FREE TIER")
print("=" * 80)

# Calcola limite richieste giornaliere
max_daily_requests_cpu = FREE_CPU_SECONDS / (AVG_DURATION_SECONDS * CPU_CORES) / 30
max_daily_requests_mem = FREE_MEM_GB_SECONDS / (AVG_DURATION_SECONDS * MEMORY_GB) / 30
max_daily_requests = min(max_daily_requests_cpu, max_daily_requests_mem)

print(f"\n📈 Con configurazione attuale ({CPU_CORES} CPU, {MEMORY_GB} GB, {AVG_DURATION_SECONDS}s/req):")
print(f"  - Limite CPU: ~{max_daily_requests_cpu:.0f} richieste/giorno")
print(f"  - Limite Memory: ~{max_daily_requests_mem:.0f} richieste/giorno")
print(f"  - Limite effettivo: ~{max_daily_requests:.0f} richieste/giorno")
print(f"  - Ovvero: ~{max_daily_requests * 30:.0f} richieste/mese GRATIS")

print("\n" + "=" * 80)
print("💡 RACCOMANDAZIONI")
print("=" * 80)
print("""
1. ✅ Sviluppo/Test (5-20/giorno): COMPLETAMENTE GRATIS
2. ✅ Beta (50/giorno): COMPLETAMENTE GRATIS  
3. ⚠️  Produzione (200+/giorno): ~€5-10/mese

4. Per ZERO costi con più utenti:
   - Riduci CPU a 1 vCPU (più lento ma gratis più a lungo)
   - Limita a 100 analisi/mese con quota utente
   - Usa caching risultati per chat già analizzate

5. Budget Google Cloud:
   - Vai su Billing → Budgets & Alerts
   - Crea budget €5/mese con alert al 50%, 80%, 100%
   - Riceverai email se superi soglia
""")

print("=" * 80)
