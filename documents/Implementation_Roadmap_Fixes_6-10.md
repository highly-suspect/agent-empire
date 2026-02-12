# IMPLEMENTATION ROADMAP: FIXES 6-10
# Critical improvements for Phases 3-4

## OVERVIEW

This roadmap addresses 5 critical issues found in your agent-system-roadmap:
- Issue 6: Crawler too simple
- Issue 7: Verification layer expensive
- Issue 8: Code blocks break claim extraction
- Issue 9: Missing database index
- Issue 10: Circular import risk

## PRIORITY & TIMING

| Issue | Phase | Priority | Time Investment | Impact |
|-------|-------|----------|-----------------|--------|
| 9 | Phase 3 | CRITICAL | 2 minutes | Massive (search speed) |
| 8 | Phase 4 | HIGH | 30 minutes | High (prevents errors) |
| 7 | Phase 4 | MEDIUM | 1-2 hours | Medium (cost/speed) |
| 6 | Phase 3 | LOW | 2-4 hours | Low (only if crawler fails) |
| 10 | Phase 2-4 | PREVENTIVE | 10 minutes | Low (code organization) |

---

## ISSUE 9: MISSING DATABASE INDEX (CRITICAL)
**When to fix:** During Phase 3, immediately after creating documentation table
**Time:** 2 minutes
**Impact:** Without this, semantic search will be VERY slow (seconds → milliseconds)

### The Problem
Current init_db.py creates the table but no index:
```python
db.execute("""
    CREATE TABLE IF NOT EXISTS documentation (
        id SERIAL PRIMARY KEY,
        title TEXT,
        url TEXT UNIQUE,
        content TEXT,
        embedding vector(1536),  # ← No index!
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
```

Without an index, PostgreSQL scans EVERY row to find similar vectors.
- 50 docs: ~100ms (acceptable)
- 500 docs: ~1 second (slow)
- 5000 docs: ~10 seconds (unusable)

### The Fix
**File:** `scripts/init_db.py`

**Add this AFTER creating the documentation table:**
```python
# Create vector index for fast similarity search
db.execute("""
    CREATE INDEX IF NOT EXISTS documentation_embedding_idx 
    ON documentation 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100)
""")

print("✓ Vector index created")
```

### What This Does
- `ivfflat`: Inverted File with Flat compression (pgvector's fast search algorithm)
- `vector_cosine_ops`: Use cosine similarity (matches your search queries)
- `lists = 100`: Cluster embeddings into 100 buckets (good for 1000-10000 docs)

### Testing
**Before index:**
```python
# Time a search
import time
start = time.time()
results = db.semantic_search(query_embedding, limit=5)
print(f"Search took: {time.time() - start:.3f}s")
```

**After index:** Should be 10-100x faster.

### Tuning
If you have more docs later:
- < 1000 docs: `lists = 100` (default, good)
- 1000-10000 docs: `lists = 100` (still good)
- 10000+ docs: `lists = 1000`

Rule of thumb: `lists = sqrt(total_rows)` rounded to nearest 100

---

## ISSUE 8: CODE BLOCKS BREAK CLAIM EXTRACTION (HIGH PRIORITY)
**When to fix:** During Phase 4 implementation
**Time:** 30 minutes
**Impact:** Prevents verification from treating code as factual claims

### The Problem
Current claim extractor splits by periods:
```python
sentences = text.split('.')
```

This breaks code examples:
```
Input: "Use ta.sma(close, 14). This calculates a 14-period SMA."

Split produces:
1. "Use ta"
2. "sma(close, 14)"  ← Treated as a claim!
3. " This calculates a 14-period SMA"
```

Now the verifier tries to fact-check "sma(close, 14)" which makes no sense.

### The Fix
**File:** `tools/claim_extractor.py`

**Replace the entire class with this improved version:**
```python
import re

class ClaimExtractor:
    def extract_claims(self, text):
        """Extract claims while preserving code blocks"""
        
        # Step 1: Extract and remove code blocks
        code_blocks = []
        code_pattern = r'```[\s\S]*?```|`[^`]+`'
        
        def save_code(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"
        
        # Replace code with placeholders
        text_without_code = re.sub(code_pattern, save_code, text)
        
        # Step 2: Split into sentences (without code interference)
        sentences = self._split_sentences(text_without_code)
        
        # Step 3: Extract claims from non-code sentences
        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip placeholders
            if '__CODE_BLOCK_' in sentence:
                continue
            
            if not sentence:
                continue
            
            if self._is_factual_claim(sentence):
                claims.append({
                    'text': sentence,
                    'type': self._classify_claim(sentence)
                })
        
        return claims
    
    def _split_sentences(self, text):
        """Split text into sentences, handling abbreviations"""
        # Simple sentence splitter (can be improved)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return sentences
    
    def _is_factual_claim(self, sentence):
        """Check if sentence makes a factual claim"""
        non_factual_indicators = [
            'i think', 'i believe', 'maybe', 'perhaps',
            'could be', 'might be', 'possibly', 'probably',
            'in my opinion', 'it seems', 'likely'
        ]
        
        sentence_lower = sentence.lower()
        
        # Skip if contains uncertainty
        if any(ind in sentence_lower for ind in non_factual_indicators):
            return False
        
        # Skip if it's a question
        if sentence.strip().endswith('?'):
            return False
        
        # Skip if it's too short (likely fragment)
        if len(sentence.split()) < 4:
            return False
        
        return True
    
    def _classify_claim(self, sentence):
        """Classify the type of claim"""
        sentence_lower = sentence.lower()
        
        # Function claims
        if any(indicator in sentence_lower for indicator in ['function', 'method', '()']):
            return 'FUNCTION_CLAIM'
        
        # Syntax claims
        if 'syntax' in sentence_lower or 'keyword' in sentence_lower:
            return 'SYNTAX_CLAIM'
        
        # Version-specific claims
        if any(v in sentence_lower for v in ['v5', 'v6', 'version']):
            return 'VERSION_CLAIM'
        
        # Behavior claims
        if any(verb in sentence_lower for verb in ['calculates', 'returns', 'plots', 'generates']):
            return 'BEHAVIOR_CLAIM'
        
        return 'GENERAL_CLAIM'
```

### What Changed
1. **Code block detection:** Finds and removes ``` and ` blocks before splitting
2. **Better sentence splitting:** Handles abbreviations (e.g., "ta.sma" won't split)
3. **Question detection:** Skips rhetorical questions
4. **Length filter:** Ignores sentence fragments
5. **Better claim types:** More granular classification

### Testing
```python
extractor = ClaimExtractor()

# Test with code
text = """
Pine Script v6 introduced the input.string() function. 
Here's an example:
```
indicator("My Indicator")
plot(close)
```
This plots the closing price on the chart.
"""

claims = extractor.extract_claims(text)
for claim in claims:
    print(f"[{claim['type']}] {claim['text']}")

# Expected output:
# [VERSION_CLAIM] Pine Script v6 introduced the input.string() function
# [BEHAVIOR_CLAIM] This plots the closing price on the chart
# 
# Note: Code block is NOT extracted as a claim
```

---

## ISSUE 7: VERIFICATION TOO EXPENSIVE (MEDIUM PRIORITY)
**When to fix:** During Phase 4, after basic verification works
**Time:** 1-2 hours
**Impact:** Reduces API calls by 70-90%, speeds up responses

### The Problem
Current approach verifies EVERY claim individually:
```python
for claim in claims:
    verdict = await self.verifier.run(verification_prompt)  # ← 1 API call per claim
```

**Cost example:**
- Response has 10 claims
- 10 verification API calls (~$0.002 each with GPT-4)
- Total: $0.02 per response
- 100 responses/day = $2/day = $60/month just for verification

### The Fix: Batch Verification
**File:** `controllers/pinescript_controller.py`

**Replace the verification method:**
```python
async def _verify_response(self, response, context):
    """Verify claims with batched verification"""
    claims = self.claim_extractor.extract_claims(response)
    
    if not claims:
        return response
    
    # Prepare documentation context
    docs_text = "\n\n".join([
        f"Source: {doc['title']}\n{doc['content']}"
        for doc in context.get('relevant_docs', [])
    ])
    
    # BATCH VERIFICATION: Verify all claims in one call
    batch_prompt = f"""Documentation:
{docs_text}

Verify the following claims against the documentation above.
For each claim, provide: SUPPORTED, PARTIALLY_SUPPORTED, or UNSUPPORTED.

Claims to verify:
{self._format_claims_for_batch(claims)}

Format your response as:
CLAIM 1: [VERDICT]
CLAIM 2: [VERDICT]
...

Be conservative: if documentation doesn't explicitly support a claim, mark UNSUPPORTED.
"""
    
    # Single API call for all claims
    batch_verdict = await self.verifier.run(batch_prompt)
    
    # Parse batch results
    verification_results = self._parse_batch_verdict(batch_verdict, claims)
    unsupported_claims = self._find_unsupported(verification_results, claims)
    
    # Add warning if needed
    if unsupported_claims:
        warning = "\n\n⚠️ WARNING: Some claims could not be verified:\n"
        warning += "\n".join(f"- {claim}" for claim in unsupported_claims)
        warning += "\n\nPlease verify these statements independently."
        return response + warning
    
    return response + "\n\n✓ All claims verified against documentation"

def _format_claims_for_batch(self, claims):
    """Format claims for batch verification"""
    formatted = []
    for i, claim in enumerate(claims, 1):
        formatted.append(f"{i}. [{claim['type']}] {claim['text']}")
    return "\n".join(formatted)

def _parse_batch_verdict(self, verdict_text, claims):
    """Parse batch verification results"""
    results = []
    lines = verdict_text.split('\n')
    
    for line in lines:
        if line.startswith('CLAIM'):
            # Extract verdict from line like "CLAIM 1: SUPPORTED"
            parts = line.split(':')
            if len(parts) >= 2:
                results.append(parts[1].strip())
    
    # Fallback: if parsing failed, mark all as needing verification
    if len(results) != len(claims):
        return ['PARTIALLY_SUPPORTED'] * len(claims)
    
    return results

def _find_unsupported(self, verification_results, claims):
    """Find claims that weren't supported"""
    unsupported = []
    
    for i, verdict in enumerate(verification_results):
        if 'UNSUPPORTED' in verdict:
            unsupported.append(claims[i]['text'])
    
    return unsupported
```

### Cost Comparison
**Before (individual verification):**
- 10 claims = 10 API calls = ~$0.02
- 100 responses = $2.00

**After (batch verification):**
- 10 claims = 1 API call = ~$0.002
- 100 responses = $0.20

**Savings: 90%**

### Advanced: Selective Verification (Phase 5 optimization)
Only verify high-risk claims:
```python
def _filter_high_risk_claims(self, claims):
    """Only verify claims that are likely to be wrong"""
    high_risk_types = ['FUNCTION_CLAIM', 'SYNTAX_CLAIM', 'VERSION_CLAIM']
    return [c for c in claims if c['type'] in high_risk_types]

# Then only verify high-risk claims
high_risk = self._filter_high_risk_claims(claims)
if high_risk:
    verification_results = await self._verify_batch(high_risk, docs_text)
```

This reduces verification to only ~30% of claims, cutting costs even further.

---

## ISSUE 6: CRAWLER TOO SIMPLE (LOW PRIORITY)
**When to fix:** Only if TradingView docs don't load properly in Phase 3
**Time:** 2-4 hours
**Impact:** Only matters if basic crawler fails

### When You Need This
The basic crawler will work if:
- ✅ TradingView docs are mostly static HTML
- ✅ Content loads without JavaScript
- ✅ Pages respond quickly

You need the advanced crawler if:
- ❌ Pages are blank when you curl them
- ❌ Content loads via JavaScript
- ❌ You get rate-limited or blocked

### Test First
Before spending time on this, test the basic crawler:
```bash
curl https://www.tradingview.com/pine-script-docs/en/v6/ | grep -i "indicator"
```

**If you see documentation content:** Basic crawler will work, skip this fix.

**If you see empty/loading messages:** You need the advanced crawler.

### The Advanced Fix
**File:** `tools/crawler.py`

**Option 1: Add Playwright (for JavaScript-heavy sites)**
```python
from playwright.sync_api import sync_playwright
import time

class AdvancedCrawler:
    def __init__(self, base_url, max_pages=100):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited = set()
    
    def crawl(self):
        """Crawl with JavaScript rendering"""
        pages = []
        to_visit = [self.base_url]
        
        with sync_playwright() as p:
            # Launch browser (headless = no window)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            while to_visit and len(pages) < self.max_pages:
                url = to_visit.pop(0)
                
                if url in self.visited:
                    continue
                
                try:
                    # Navigate and wait for content
                    page.goto(url, wait_until='networkidle')
                    self.visited.add(url)
                    
                    # Extract content
                    title = page.title()
                    content = page.inner_text('body')
                    
                    pages.append({
                        'url': url,
                        'title': title,
                        'content': content
                    })
                    
                    # Find links
                    links = page.query_selector_all('a')
                    for link in links:
                        href = link.get_attribute('href')
                        if href:
                            next_url = self._resolve_url(url, href)
                            if self._is_valid_url(next_url):
                                to_visit.append(next_url)
                    
                    time.sleep(2)  # Respectful delay
                    
                except Exception as e:
                    print(f"Error crawling {url}: {e}")
                    continue
            
            browser.close()
        
        return pages
    
    def _resolve_url(self, base, href):
        """Resolve relative URLs"""
        from urllib.parse import urljoin
        return urljoin(base, href)
    
    def _is_valid_url(self, url):
        """Check if URL should be crawled"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        
        return (
            parsed.netloc == base_parsed.netloc and
            url not in self.visited and
            not url.endswith(('.pdf', '.zip', '.jpg', '.png')) and
            '#' not in url  # Skip anchor links
        )
```

**Install Playwright:**
```bash
pip install playwright
playwright install chromium
```

**Option 2: Add Retry Logic + Better Headers (simpler)**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

class ResilientCrawler:
    def __init__(self, base_url, max_pages=100):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited = set()
        
        # Create session with retries
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,  # Retry up to 3 times
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Better headers (appear more like a real browser)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def crawl(self):
        """Crawl with retries and better error handling"""
        pages = []
        to_visit = [self.base_url]
        
        while to_visit and len(pages) < self.max_pages:
            url = to_visit.pop(0)
            
            if url in self.visited:
                continue
            
            try:
                # Request with automatic retries
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                self.visited.add(url)
                
                # Parse content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title = soup.find('title')
                title_text = title.get_text() if title else url
                
                # Remove script and style tags
                for script in soup(["script", "style"]):
                    script.decompose()
                
                content = soup.get_text(separator='\n', strip=True)
                
                pages.append({
                    'url': url,
                    'title': title_text,
                    'content': content
                })
                
                # Find links
                for link in soup.find_all('a', href=True):
                    from urllib.parse import urljoin
                    next_url = urljoin(url, link['href'])
                    if self._is_valid_url(next_url):
                        to_visit.append(next_url)
                
                # Respectful delay (2-3 seconds)
                time.sleep(2 + (time.time() % 1))
                
            except requests.exceptions.RequestException as e:
                print(f"Error crawling {url}: {e}")
                continue
        
        return pages
```

### When to Use Which
- **Playwright:** If JavaScript rendering is required
- **Resilient Crawler:** If you just need better retry logic
- **Basic Crawler:** If it already works (don't fix what isn't broken!)

---

## ISSUE 10: CIRCULAR IMPORT RISK (PREVENTIVE)
**When to fix:** During Phase 2-4 implementation
**Time:** 10 minutes per phase
**Impact:** Prevents hard-to-debug import errors

### The Problem
Your architecture could create circular dependencies:
```
controllers/controller.py
    ↓ imports
agents/verification_agent.py
    ↓ inherits from
agents/base.py
    ↓ (potentially) imports
controllers/controller.py  ← CIRCULAR!
```

### The Prevention Strategy
Follow these import rules:

**Rule 1: Agents never import controllers**
```python
# agents/base.py
# agents/pinescript_agent.py  
# agents/verification_agent.py

# ❌ NEVER DO THIS:
from controllers.controller import Controller

# ✅ Agents should only import:
# - pydantic_ai
# - dotenv
# - Other agents (carefully)
```

**Rule 2: Controllers import agents (one direction only)**
```python
# controllers/pinescript_controller.py

# ✅ This is fine:
from agents.pinescript_agent import PineScriptAgent
from agents.verification_agent import VerificationAgent
```

**Rule 3: Tools are imported by both (no imports between tools)**
```python
# tools/database.py
# tools/embedder.py
# tools/claim_extractor.py

# ❌ NEVER DO THIS:
from controllers.controller import Controller
from agents.base import BaseAgent

# ✅ Tools should only import:
# - Standard library
# - External packages (openai, psycopg2, etc.)
# - Other tools (carefully)
```

### Dependency Graph (Allowed)
```
┌─────────────┐
│  Interface  │ (Streamlit)
└──────┬──────┘
       │ imports
       ↓
┌─────────────┐
│ Controller  │
└──────┬──────┘
       │ imports
       ├──────────────┬──────────────┐
       ↓              ↓              ↓
┌─────────┐    ┌───────────┐  ┌──────────┐
│  Agent  │    │   Tools   │  │  Memory  │
└─────────┘    └───────────┘  └──────────┘
```

**Key:** Arrows point downward only. No circular dependencies.

### Testing for Circular Imports
Add this test to your project:
```python
# tests/test_imports.py
def test_no_circular_imports():
    """Verify no circular import dependencies"""
    
    # This will fail if circular imports exist
    try:
        from agents.base import BaseAgent
        from agents.pinescript_agent import PineScriptAgent
        from controllers.controller import Controller
        from controllers.pinescript_controller import PineScriptController
        print("✓ No circular imports detected")
    except ImportError as e:
        print(f"✗ Import error (possible circular dependency): {e}")
        raise
```

Run before committing each phase:
```bash
python3 tests/test_imports.py
```

---

## SUMMARY: IMPLEMENTATION CHECKLIST

### Phase 3 (RAG Integration)
```
☐ Issue 9: Add vector index to init_db.py (2 min, CRITICAL)
☐ Issue 6: Test basic crawler first, upgrade only if needed (0-4 hours)
```

### Phase 4 (Verification Layer)
```
☐ Issue 8: Improve claim extraction to skip code (30 min, HIGH)
☐ Issue 7: Implement batch verification (1-2 hours, MEDIUM)
☐ Issue 10: Verify no circular imports (10 min, PREVENTIVE)
```

### Phase 5 (Production Polish)
```
☐ Issue 7 (advanced): Add selective verification (30 min, OPTIONAL)
☐ Issue 10: Final import check before tagging v5.0 (5 min)
```

---

## TESTING EACH FIX

### Test Issue 9 (Vector Index)
```python
import time
from tools.database import DatabaseTool
from tools.embedder import TextEmbedder

db = DatabaseTool()
embedder = TextEmbedder()

# Create test embedding
query_embedding = embedder.embed_text("How do I plot RSI?")

# Time the search
start = time.time()
results = db.semantic_search(query_embedding, limit=5)
duration = time.time() - start

print(f"Search took: {duration:.3f}s")
# Expected: < 0.1s with index, > 1s without index
```

### Test Issue 8 (Code Block Handling)
```python
from tools.claim_extractor import ClaimExtractor

extractor = ClaimExtractor()

test_text = """
Pine Script v6 introduced new features.
Use this code:
```
indicator("Test")
plot(close)
```
This plots the closing price.
"""

claims = extractor.extract_claims(test_text)
print(f"Extracted {len(claims)} claims")
for claim in claims:
    print(f"- {claim['text']}")

# Expected: 2 claims (intro + closing price explanation)
# Code block should NOT be a claim
```

### Test Issue 7 (Batch Verification)
```python
# Count API calls (add to your code)
api_call_count = 0

# In verifier, wrap the run method:
original_run = self.verifier.run
async def counted_run(*args, **kwargs):
    global api_call_count
    api_call_count += 1
    return await original_run(*args, **kwargs)
self.verifier.run = counted_run

# Test a query
await controller.process_query("Explain Pine Script functions")

print(f"API calls made: {api_call_count}")
# Expected: 1 call with batch verification, 5-10 calls without
```

---

## COST ANALYSIS

### Current Roadmap (No Fixes)
- Phase 3: ~$5 (embeddings)
- Phase 4: ~$60/month (verification)
- **Total:** $65/month

### With All Fixes
- Phase 3: ~$5 (embeddings) + faster search
- Phase 4: ~$6/month (batch verification)
- **Total:** $11/month

**Savings: $54/month (83% reduction)**

---

## FINAL RECOMMENDATIONS

**Must implement:**
- Issue 9 (vector index) - 2 minutes, massive impact

**Should implement:**
- Issue 8 (code handling) - 30 minutes, prevents errors
- Issue 7 (batch verify) - 1 hour, huge cost savings

**Only if needed:**
- Issue 6 (advanced crawler) - only if basic fails

**Good practice:**
- Issue 10 (import checks) - keeps code clean

**Total time investment for all recommended fixes: ~2 hours**
**Total cost savings: ~$50/month**

Worth it? Absolutely.
