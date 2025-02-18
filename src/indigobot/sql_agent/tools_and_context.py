"""Tools and context for the SQL agent program"""

import hashlib
import logging
import os
import re
import secrets
import stat
import time
import uuid
from functools import wraps
from logging.handlers import RotatingFileHandler
from typing import Optional

from langchain import hub
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain_core.tools import InjectedToolArg, tool
from langgraph.store.base import BaseStore
from typing_extensions import Annotated

from indigobot.config import vectorstore
from .places_tool import places_tool, PlacesLookupTool

retriever = vectorstore.as_retriever()
places_lookup = PlacesLookupTool()

@tool
def lookup_and_store_place_info(
    query: str,
    *,
    store: Annotated[BaseStore, InjectedToolArg],
) -> str:
    """
    Look up place information and store it in the vectorstore.
    
    Args:
        query: Search query for the place
        store: The store where the place info will be stored
        
    Returns:
        Formatted string with place details and confirmation of storage
    """
    # Look up place information
    place_info = places_lookup.lookup_place(query)
    
    if place_info.startswith("Error"):
        return place_info
        
    # Create a unique ID for the place
    place_id = str(uuid.uuid4())
    
    # Store the information
    store.put(
        ("places", "details"),
        key=place_id,
        value={
            "text": place_info,
            "query": query,
            "retrieved_at": time.time(),
            "source": "google_places"
        },
    )
    
    # Add to vectorstore for future retrieval
    vectorstore.add_texts(
        texts=[place_info],
        metadatas=[{
            "place_id": place_id,
            "query": query,
            "source": "google_places"
        }]
    )
    
    return f"{place_info}\n\nInformation has been stored for future reference."

@tool
def check_stored_place_info(
    query: str,
    *,
    store: Annotated[BaseStore, InjectedToolArg],
) -> Optional[str]:
    """
    Check if we have stored information about a place before making an API call.
    
    Args:
        query: Search query for the place
        store: The store to check for existing information
        
    Returns:
        Stored place information if found, None otherwise
    """
    # Search vectorstore first
    docs = vectorstore.similarity_search(
        query,
        k=1,
        filter={"source": "google_places"}
    )
    
    if docs and docs[0].page_content:
        # Check if the information is recent (less than 24 hours old)
        metadata = docs[0].metadata
        if metadata.get("retrieved_at", 0) > time.time() - 86400:
            return docs[0].page_content
            
    return None


# Get the SQL agent prompt
prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
assert len(prompt_template.messages) == 1

sql_message = prompt_template.format(dialect="SQLite", top_k=5)

# Enhanced system message
system_message = f"""
{sql_message}

IMPORTANT: When users ask about places, locations, businesses, or venues:

1. ALWAYS check for stored information first using check_stored_place_info when users ask about:
   - Business hours or opening times
   - Current status (open/closed)
   - Address or location details
   - Contact information
   - Website

2. If no recent information is found (or if check_stored_place_info returns None), ALWAYS use lookup_and_store_place_info to:
   - Get current, accurate information
   - Store it for future reference
   - Provide the user with up-to-date details

Example triggers that require place lookup:
- Questions about hours: "when does X open/close", "what time does X open", "is X open now"
- Location queries: "where is X", "address for X", "X near Y"
- Contact info: "phone number for X", "website for X"
- Status checks: "is X open", "is X closed"

Examples:
User: "What time does Starbucks close?"
Assistant: *uses check_stored_place_info first, then lookup_and_store_place_info if needed*

User: "Is the library open right now?"
Assistant: *uses check_stored_place_info first, then lookup_and_store_place_info if needed*

For all place-related queries, prefer getting current information over saying "I don't know" or suggesting the user check elsewhere.
"""

@tool
def upsert_memory(
    content: str,
    *,
    memory_id: Optional[uuid.UUID] = None,
    store: Annotated[BaseStore, InjectedToolArg],
):
    """
    Insert/update a memory in the database.

    :param content: The content to store in memory.
    :type content: str
    :param memory_id: Optional UUID for the memory. If not provided, a new UUID is generated.
    :type memory_id: Optional[uuid.UUID]
    :param store: The store where the memory will be inserted.
    :type store: Annotated[BaseStore, InjectedToolArg]
    :return: A message indicating the stored memory ID.
    :rtype: str
    """
    mem_id = memory_id or uuid.uuid4()
    store.put(
        ("user_123", "memories"),
        key=str(mem_id),
        value={"text": content},
    )
    return f"Stored memory {mem_id}"


def generate_request_id():
    """
    Generate a secure random request ID.

    :return: A secure random request ID.
    :rtype: str
    """
    return secrets.token_hex(16)


@tool
async def sanitize_input(user_input: str) -> tuple[str, dict]:
    """
    Sanitize user input and return parameters for prepared statements.

    :param user_input: The user's input query to sanitize.
    :type user_input: str
    :return: A tuple containing the sanitized query and a dictionary of parameters.
    :rtype: tuple[str, dict]
    :raises ValueError: If input is not a string or contains disallowed operations.
    """
    if not isinstance(user_input, str) or not user_input.strip():
        raise ValueError("Input must be a non-empty string")

    # Stricter input length limit
    if len(user_input) > 500:
        raise ValueError("Input exceeds maximum length")

    # Whitelist of allowed SQL operations and keywords
    ALLOWED_OPERATIONS = {
        "SELECT",
        "FROM",
        "WHERE",
        "AND",
        "OR",
        "LIKE",
        "ORDER",
        "BY",
        "LIMIT",
        "JOIN",
        "GROUP",
        "HAVING",
        "ID",
        "DOCUMENTS",
        "TITLE",
        "ASC",
        "DESC",
        "INNER",
        "LEFT",
        "RIGHT",
        "OUTER",
        "ON",
        "AS",
        "IN",
        "BETWEEN",
        "IS",
        "NULL",
        "NOT",
        "CONTENT",
        "*",
        "=",
        ">",
        "<",
        ">=",
        "<=",
        "!=",
        "%",  # Common operators
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "0",  # Numbers
        # Add common SQL functions
        "COUNT",
        "SUM",
        "AVG",
        "MIN",
        "MAX",
        "DISTINCT",
        # Add common data types
        "INTEGER",
        "TEXT",
        "REAL",
        "BOOLEAN",
    }

    # Generate request ID for logging
    request_id = generate_request_id()

    # Create logging context with more details
    log_context = {
        "request_id": request_id,
        "input_length": len(user_input),
        "timestamp": time.time(),
    }
    logging.info("Processing input sanitization", extra=log_context)

    # Extract parameters for prepared statement
    params = {}
    param_count = 0

    def replace_with_param(match):
        nonlocal param_count
        param_count += 1
        param_name = f"param_{param_count}"
        # Strip quotes from string literals
        value = match.group(0)
        if value.startswith(("'", '"')) and value.endswith(("'", '"')):
            value = value[1:-1]
        params[param_name] = value
        return f":{param_name}"

    # Replace literals with named parameters
    user_input = re.sub(r"'[^']*'|\"[^\"]*\"|\d+", replace_with_param, user_input)

    # Validate operations - ignore parameters in the validation
    cleaned_input = re.sub(r":[a-zA-Z0-9_]+", "", user_input)
    tokens = set(re.findall(r"\b\w+\b", cleaned_input.upper()))
    disallowed = tokens - ALLOWED_OPERATIONS
    if disallowed:
        raise ValueError(f"Query contains disallowed operations: {disallowed}")

    # Extended list of dangerous SQL keywords
    dangerous_keywords = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "UNION",
        "EXEC",
        "EXECUTE",
        "LOAD_FILE",
        "INTO OUTFILE",
        "INFORMATION_SCHEMA",
        "SLEEP",
        "BENCHMARK",
        "WAITFOR",
        "DELAY",
        "XP_",
        "SP_",
    ]
    pattern = r"\b(" + "|".join(map(re.escape, dangerous_keywords)) + r")\b"
    user_input = re.sub(pattern, "", user_input, flags=re.IGNORECASE)

    # Additional checks for common SQL injection patterns
    sql_injection_patterns = [
        r"@@",
        r"\bchar\s*\(",
        r"\bconvert\s*\(",
        r"\bcast\s*\(",
        r";(?!\s*$)",
        r"--(?!\s*$)",
        r"/\*",
        r"\*/",
        r"xp_",
        r"\bunion\b(?!\s+select\b)",
        r"\bdrop\b",
        r"\bdelete\b",
        r"update.*set",
        r"insert.*into",
        r"\bor\s+\d*\s*=\s*\d*\b",  # Catch any OR = pattern
        r"\band\s+\d*\s*=\s*\d*\b",  # Catch any AND = pattern
        r";\s*--\s*$",  # Catch malicious comment injections
        r"'\s*or\s+'.*?'\s*=\s*'.*?'",  # Catch any string-based OR injections
        r"'\s*or\s*true\b",  # Catch OR TRUE injections
        r"\bor\s+true\b",  # Catch OR TRUE without quotes
        r"\bor\s+[0-9]+\s*=\s*[0-9]+\b",  # Catch OR 1=1 explicitly with any numbers
        r"\band\s+[0-9]+\s*=\s*[0-9]+\b",  # Catch AND 1=1 explicitly with any numbers
        r"'\s*;\s*",  # Catch semicolon in strings
        r"\bdrop\s+table\b",  # Explicit DROP TABLE
        r"\bdelete\s+from\b",  # Explicit DELETE FROM
        r"\btruncate\s+table\b",  # TRUNCATE attempts
        r"--\s*$",  # Comment at end of line
        r"/\*.*?\*/",  # Multi-line comments
        r"\bexec\b",  # EXEC statements
        r"\bxp_cmdshell\b",  # Command shell attempts
    ]

    input_lower = user_input.lower()
    for pattern in sql_injection_patterns:
        if re.search(pattern, input_lower, re.IGNORECASE):
            raise ValueError("Potentially malicious input detected")

    # Check for multiple statements
    if ";" in user_input:
        raise ValueError("Multiple SQL statements are not allowed")

    # Hash the sanitized input for logging
    input_hash = hashlib.sha256(user_input.encode()).hexdigest()[:16]
    logging.info(f"Input processed, hash: {input_hash}", extra=log_context)

    return user_input.strip(), params


class RateLimiter:
    def __init__(self, max_requests=50, time_window=3600):
        """
        Initialize the RateLimiter with specified limits and tracking configurations.

        :param max_requests: Maximum number of requests allowed within the time window.
        :type max_requests: int
        :param time_window: The time window in seconds for rate limiting.
        :type time_window: int
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
        self.blocked_ips = set()
        self.violation_counts = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = 300
        self.suspicious_patterns = {}
        self.ip_request_patterns = {}

    def is_rate_limited(self, key: str, ip: str = None) -> bool:
        """
        Check if the request is rate-limited and log any suspicious activity.

        :param key: The key for tracking requests.
        :type key: str
        :param ip: The IP address of the requestor.
        :type ip: str, optional
        :return: True if the request is rate-limited, False otherwise.
        :rtype: bool
        """
        now = time.time()

        # Periodic cleanup
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_data(now)

        # Enhanced IP blocking check
        if ip:
            if ip in self.blocked_ips:
                logging.warning(
                    f"Blocked IP attempted access: {ip}", extra={"ip": ip, "key": key}
                )
                return True

            # Track request patterns
            if ip not in self.ip_request_patterns:
                self.ip_request_patterns[ip] = []
            self.ip_request_patterns[ip].append(now)

            # Detect suspicious patterns
            if self._detect_suspicious_activity(ip, now):
                self.blocked_ips.add(ip)
                logging.warning(f"IP blocked due to suspicious activity: {ip}")
                return True

        # Clean old requests
        self.requests = {
            k: v for k, v in self.requests.items() if now - v[-1] < self.time_window
        }

        if key not in self.requests:
            self.requests[key] = []

        # Add new request
        self.requests[key] = [
            t for t in self.requests[key] if now - t < self.time_window
        ]

        # Check rate limit
        if len(self.requests[key]) >= self.max_requests:
            if ip:
                self.violation_counts[ip] = self.violation_counts.get(ip, 0) + 1
                if self.violation_counts[ip] >= 3:  # Block after 3 violations
                    self.blocked_ips.add(ip)
                    logging.warning(f"IP blocked due to repeated violations: {ip}")
            return True

        self.requests[key].append(now)
        return False

    def _detect_suspicious_activity(self, ip: str, now: float) -> bool:
        """
        Detect suspicious patterns in requests that may indicate automated attacks.

        Checks for:
        - High frequency requests (>30 per minute)
        - Regular intervals between requests (potential bot behavior)

        :param ip: IP address to check
        :type ip: str
        :param now: Current timestamp
        :type now: float
        :return: True if suspicious activity detected, False otherwise
        :rtype: bool
        """
        # Get requests from last minute only
        recent_requests = [t for t in self.ip_request_patterns[ip] if now - t < 60]

        # Check for high frequency requests
        if len(recent_requests) > 30:  # More than 30 requests per minute
            return True

        # Check for regular intervals (bot detection)
        if len(recent_requests) > 5:
            intervals = [
                recent_requests[i] - recent_requests[i - 1]
                for i in range(1, len(recent_requests))
            ]
            # If all intervals are identical (rounded to 2 decimal places)
            if len(set(round(i, 2) for i in intervals)) == 1:
                return True

        return False

    def reset_violations(self, ip: str):
        """
        Reset violation count for an IP.

        :param ip: The IP address whose violations are to be reset.
        :type ip: str
        """
        if ip in self.violation_counts:
            del self.violation_counts[ip]
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)


rate_limiter = RateLimiter()


@tool
def rate_limit(func):
    """
    Decorator to implement rate limiting on a function.

    :param func: The function to apply rate limiting to.
    :type func: callable
    :return: The wrapped function with rate limiting applied.
    :rtype: callable
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        request_id = generate_request_id()
        if rate_limiter.is_rate_limited(request_id):
            logging.warning(f"Rate limit exceeded for request {request_id}")
            raise Exception("Rate limit exceeded. Please wait.")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            raise

    return wrapper


"""Logging"""
log_file = "sql_agent.log"
log_handler = RotatingFileHandler(
    log_file, maxBytes=10 * 1024 * 1024, backupCount=5, mode="a"  # 10MB
)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)
# Secure log file permissions
os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR)  # 0o600 - user read/write only

prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
assert len(prompt_template.messages) == 1

system_message = prompt_template.format(dialect="SQLite", top_k=5)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
description = """
    Use to look up values to filter on. Input is an approximate spelling 
    of the proper noun, output is valid proper nouns. Use the noun most 
    similar to the search. You can also use your sqlmap tool for security evaluation.
    """
retriever_tool = create_retriever_tool(
    retriever,
    name="search_proper_nouns",
    description=description,
)

# Add tools to the existing retriever tool
tools = [
    retriever_tool,
    lookup_and_store_place_info,
    check_stored_place_info,
    upsert_memory,
    sanitize_input,
]