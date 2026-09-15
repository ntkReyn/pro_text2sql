Vietnamese NL
      ↓
Vietnamese Normalizer
      ↓
Value Grounding
      ↓
Answerability / Ambiguity Detector
  │              │             │
clear         ambiguous     out-of-scope
  │              │             │
  │           Clarify         Abstain
  ↓
Datus Agent Orchestration
  ├── Episodic Memory
  ├── Approved Examples
  └── Non-canonical Business Documents
      ↓
Preliminary Intent Sketch
      ↓
Wren Semantic Context Retrieval
      ↓
Approved Relationship Graph Expansion
      ↓
Semantic-DAIL
  ├── Vietnamese question similarity
  ├── intent/plan-skeleton similarity
  ├── metric-version compatibility
  └── verified-success score
      ↓
Reviewed Examples
      ↓
LLM Planner
      ↓
Typed SemanticQueryPlan
      ↓
Deterministic Plan Validator
      ↓
Datus ↔ Wren Adapter
      ↓
Wren MDL
  ├── Canonical metrics
  ├── Dimensions
  ├── Business definitions
  └── Approved relationships
      ↓
Wren Core Dry-plan / Compile
      ↓
SQL AST + Security Validator
      ↓
Read-only Database Execution
      ↓
Runtime + Semantic Result Validation
  │             │               │
PASS          REPAIRABLE      UNCERTAIN
  │             │               │
Answer      Bounded Datus     Clarify/
             Repair           Re-plan