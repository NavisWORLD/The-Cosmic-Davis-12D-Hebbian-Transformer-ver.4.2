"""Cosmos System Integrity Check"""
import sys, os
sys.path.insert(0, r'd:\Cosmos')
os.environ['COSMOS_SKIP_TORCH'] = '1'

checks = {}

# 1. CNS Core
try:
    from Cosmos.web.cosmosynapse.engine import cns_core
    checks['CNS Core (cns_core)'] = 'OK - Module importable'
except Exception as e:
    checks['CNS Core (cns_core)'] = f'FAIL - {e}'

# 2. RSM Engine
try:
    from Cosmos.web.cosmosynapse.engine.rsm_engine import RSMEngine
    engine = RSMEngine()
    status = engine.get_status()
    mods = status.get("modules_in_scope", "?")
    hermes = status.get("hermes_assisted", "?")
    checks['RSM Engine'] = f'OK - {mods} modules in scope, hermes={hermes}'
except Exception as e:
    checks['RSM Engine'] = f'FAIL - {e}'

# 3. Archival Memory
try:
    from Cosmos.memory.archival_memory import ArchivalMemory
    checks['Archival Memory'] = 'OK - Module importable'
except Exception as e:
    checks['Archival Memory'] = f'FAIL - {e}'

# 4. Token Saver (OrderedDict fix)
try:
    from Cosmos.core.token_saver import TokenSaver
    checks['Token Saver (OrderedDict)'] = 'OK - Import clean'
except Exception as e:
    checks['Token Saver (OrderedDict)'] = f'FAIL - {e}'

# 5. Orchestrator Router
try:
    from Cosmos.web.routes.orchestrator import router
    route_paths = [r.path for r in router.routes]
    checks['Orchestrator Router'] = f'OK - routes: {route_paths}'
except Exception as e:
    checks['Orchestrator Router'] = f'FAIL - {e}'

# 6. Hermes Bridge
try:
    from Cosmos.integration.hermes_bridge import HermesBridge
    checks['Hermes Bridge'] = 'OK - Module importable'
except Exception as e:
    checks['Hermes Bridge'] = f'FAIL - {e}'

# 7. Quantum Bridge
try:
    from Cosmos.integration.quantum_bridge import QuantumBridge
    checks['Quantum Bridge'] = 'OK - Module importable'
except Exception as e:
    checks['Quantum Bridge'] = f'FAIL - {e}'

# 8. Cosmos Swarm Orchestrator
try:
    from Cosmos.web.cosmosynapse.engine.cosmos_swarm_orchestrator import CosmosSwarmOrchestrator
    checks['Swarm Orchestrator'] = 'OK - Module importable'
except Exception as e:
    checks['Swarm Orchestrator'] = f'FAIL - {e}'

# 9. Synaptic Field
try:
    from Cosmos.web.cosmosynapse.engine.synaptic_field import SynapticField
    checks['Synaptic Field (12D)'] = 'OK - Module importable'
except Exception as e:
    checks['Synaptic Field (12D)'] = f'FAIL - {e}'

# 10. Evolution Engine (Life Loop)
try:
    from Cosmos.core.collective.evolution_engine import EvolutionEngine
    checks['Evolution Engine (Life Loop)'] = 'OK - Module importable'
except Exception as e:
    checks['Evolution Engine (Life Loop)'] = f'FAIL - {e}'

# 11. Collective Organism
try:
    from Cosmos.core.collective.organism import CollectiveOrganism
    checks['Collective Organism'] = 'OK - Module importable'
except Exception as e:
    checks['Collective Organism'] = f'FAIL - {e}'

# 12. Swarm Plasticity
try:
    from Cosmos.web.cosmosynapse.engine.swarm_plasticity import SwarmPlasticity
    checks['Swarm Plasticity (Hebbian)'] = 'OK - Module importable'
except Exception as e:
    checks['Swarm Plasticity (Hebbian)'] = f'FAIL - {e}'

# Print results
print('=' * 60)
print('  COSMOS SYSTEM INTEGRITY CHECK')
print('=' * 60)
for name, status in checks.items():
    icon = 'PASS' if 'OK' in status else 'FAIL'
    print(f'  [{icon}] {name}')
    print(f'         {status}')
print('=' * 60)
passed = sum(1 for s in checks.values() if 'OK' in s)
total = len(checks)
print(f'  RESULT: {passed}/{total} systems OK')
print('=' * 60)
