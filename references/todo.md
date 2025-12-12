consistent movement rules

track gold add gold per year 

spell track in handbook 

track changes in characteristics. 

skills don't persist  across adding experience

keep track skill points you can allocate 

switch tracks 

keep track of experience / available skill point 

Angar is king of the mainland and claims proveance over all the splintering 

cost of daggers vs other things like great swords

pack weight 

adventure logs 


---
  Code Review Summary

  CRITICAL (Fix Now)

  1. Hardcoded SECRET_KEY fallback - settings.py:24-27 - should fail if not set in production
  2. Git subprocess on every request - context_processors.py - should cache at startup

  HIGH (Fix Soon)

  3. DEBUG defaults to True - dangerous for production
  4. Path traversal check is weak - views.py:1410-1412 - use pathlib.resolve() instead
  5. Race condition in auto-save - character count isn't atomic
  6. No models registered in admin

  MEDIUM (Technical Debt)

  7. index() view is 343 lines - needs to be split up
  8. Duplicate consolidate_skills() - imported AND redefined locally
  9. Inconsistent error handling - mix of JsonResponse, messages.error, Http404
  10. No database indexes on frequently queried fields
  11. Session data has no size limits
  12. Missing CSRF verification on JSON endpoints

  LOW (Cleanup)

  13. Unused imports - Counter never used
  14. Magic numbers - hardcoded 4, 1.5, 2 without constants
  15. 80+ lines of JS in templates - should be external files
  16. No logging
  17. Missing docstrings on many functions
  18. CSS duplication across templates

  Security Gaps

  - No rate limiting
  - No Content Security Policy
  - Markdown rendered without sanitization

  Testing Gaps

  - build_final_str_repr() untested
  - Edge cases in skill consolidation
  - Race conditions in auto-save

---
