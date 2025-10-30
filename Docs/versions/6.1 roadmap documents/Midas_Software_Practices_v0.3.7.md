# Software Engineering Practices in Midas

**Date:** 2025-09-07  
**Version Context:** v0.3.7-cleanup  

---

## 1. Version Control
- **Practice:** Frequent commits and annotated Git tags (v0.3.4, v0.3.5, v0.3.7-cleanup).  
- **Software Principle:** Versioning and release management.  
- **Impact:** Provides restore points, traceability, and confidence in experimentation.

---

## 2. Safe Archiving
- **Practice:** Files are moved to `_archive_unused/YYYYMMDD/` instead of deleted.  
- **Software Principle:** Reversibility and audit trail.  
- **Impact:** Maintains a clean repo without permanent loss of history.

---

## 3. Documentation Discipline
- **Practice:** MD + PDF files for each milestone (sanity checks, workflow principles, audit reports).  
- **Software Principle:** Knowledge capture and project traceability.  
- **Impact:** Enables future maintainers (or your future self) to understand “why” as well as “what.”

---

## 4. Modularity in Scenarios
- **Practice:** Strategies separated into A–E scenarios. Each can be run, compared, and tuned independently.  
- **Software Principle:** Separation of concerns and modular design.  
- **Impact:** Simplifies debugging, testing, and later hybridization.

---

## 5. Guardrails Before Enhancements
- **Practice:** Prioritize EMA/VWAP confirms, MACD rise bars, RVOL at open, universe hygiene.  
- **Software Principle:** Build correctness and stability before optimization.  
- **Impact:** Ensures stability before pursuing advanced features like adaptive sizing or hybrid routers.

---

## 6. Future-Proof Planning
- **Practice:** Broker abstraction, adaptive sizing, hybrid router deferred until baseline stable.  
- **Software Principle:** Incremental development and roadmap-driven design.  
- **Impact:** Prevents premature complexity and protects maintainability.

---

## 7. Automation Preference
- **Practice:** Defaulting to Python for runners and utilities, avoiding brittle PowerShell scripts.  
- **Software Principle:** Reliability, portability, and minimizing tech debt.  
- **Impact:** Reduces errors and aligns with professional engineering best practice.

---

## Conclusion
The Midas project demonstrates **professional software engineering discipline**:  
- Frequent versioning  
- Safe cleanup and reversibility  
- Documentation and traceability  
- Modular scenario design  
- Guardrails before profit  
- Deferred complexity until stability  

Even if not from a formal software career, the practices align closely with what strong engineers and architects use daily.  

