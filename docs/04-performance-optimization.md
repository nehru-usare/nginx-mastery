# Level 4: Performance & Caching

## 1. worker_processes and worker_connections
To maximize NGINX performance, you must tune how it utilizes CPU and network resources.

```nginx
# Automatically spawn a worker process for each CPU core.
worker_processes auto;

events {
    # Number of connections each worker can handle simultaneously.
    # Max clients = worker_processes * worker_connections
    worker_connections 4096;
    
    # Accept as many connections as possible per event loop
    multi_accept on;
}
```

## 2. Keepalive Connections
Keepalive prevents the overhead of creating new TCP connections for every single HTTP request.

**Keepalive towards the Client:**
```nginx
http {
    # Time an inactive keep-alive connection remains open
    keepalive_timeout 65;
    
    # Max requests a single client can make over one keep-alive connection
    keepalive_requests 1000;
}
```

**Keepalive towards Upstream (Backend):**
```nginx
upstream backend_pool {
    server backend:8080;
    
    # Maintain up to 64 idle connections to the upstream servers
    keepalive 64;
}

server {
    location / {
        proxy_pass http://backend_pool;
        # HTTP/1.1 is required for keepalive to work
        proxy_http_version 1.1;
        # Clear the "Connection: close" header sent by default
        proxy_set_header Connection "";
    }
}
```

## 3. Gzip Compression
Compressing data before sending it over the network reduces transfer time and bandwidth.

```nginx
http {
    gzip on;
    gzip_comp_level 5; # 1-9 (5 is a good balance of CPU vs size)
    gzip_min_length 256; # Don't compress very small files
    gzip_proxied any; # Compress even for proxied requests
    gzip_vary on; # Send Vary header to proxies
    
    # What file types to compress
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

## 4. Brotli Compression
Brotli is a newer compression algorithm by Google that outperforms Gzip, especially for text-based assets. (Requires an NGINX module or using Docker images compiled with Brotli).

```nginx
http {
    brotli on;
    brotli_comp_level 6;
    brotli_types text/plain text/css application/javascript application/json image/svg+xml;
}
```
*Best Practice:* Enable both. Browsers that support Brotli will negotiate for it, falling back to Gzip.

## 5. NGINX Caching (`proxy_cache`)
Caching responses directly at the NGINX layer offloads immense pressure from your backend servers.

Step 1: Define the cache zone.
```nginx
http {
    # path: /var/cache/nginx
    # levels: directory structure (1:2)
    # keys_zone: memory space for keys named 'my_cache' (10MB)
    # max_size: disk space limit (1GB)
    # inactive: remove cache if not accessed in 60 minutes
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m use_temp_path=off;
}
```

Step 2: Apply the cache to a location.
```nginx
server {
    location /api/data {
        proxy_cache my_cache;
        proxy_pass http://backend;
        
        # Cache 200 and 302 responses for 10 minutes
        proxy_cache_valid 200 302 10m;
        # Cache 404s for 1 minute
        proxy_cache_valid 404 1m;
        
        # Add a header so clients can see if it was a cache HIT or MISS
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

## 6. Microcaching
Microcaching refers to caching dynamic, unpersonalized content for very short periods (e.g., 1 second). This protects the backend from sudden traffic spikes (slashdot effect) while ensuring content remains sufficiently fresh.

```nginx
location /api/trending {
    proxy_cache my_cache;
    proxy_cache_valid 200 1s; # Cache for only 1 second!
    
    # If multiple clients request the exact same expired item, 
    # only one request goes to the backend, others wait for the cache to update
    proxy_cache_lock on; 
    
    # Serve stale cache while the new one is updating
    proxy_cache_use_stale updating;
    
    proxy_pass http://backend;
}
```

## 7. Cache Invalidation
Open Source NGINX handles cache invalidation implicitly based on the `proxy_cache_valid` expiration. For explicit invalidation (purging), you typically need NGINX Plus (`proxy_cache_purge`), or you can use a community module like `ngx_cache_purge`. Another trick is cache busting by altering the URL (e.g., `style.v2.css`).

## 8. HTTP/2 Overview
HTTP/2 provides multiplexing (multiple requests over a single TCP connection), header compression, and server push. It drastically improves performance for secure connections.

```nginx
server {
    # Simply add 'http2' to the listen directive
    # Note: Browsers require SSL/TLS for HTTP/2
    listen 443 ssl http2;
    server_name example.com;
    # ... ssl configuration ...
}
```

## 9. Benchmark Comparison
To truly understand performance, you must test. Tools like `wrk` or `Apache Bench (ab)` are standard.

**Testing without Keepalive:**
```bash
ab -n 1000 -c 100 http://localhost/
```

**Testing with Keepalive (Notice the `-k` flag):**
```bash
ab -k -n 1000 -c 100 http://localhost/
```
*Expected Result:* Keepalive drastically increases Requests per Second (RPS) and lowers latency across the board.

## 10. Interview Preparation (Level 4)

1. **What is Microcaching and when would you use it?**
   *Answer:* It's the practice of caching dynamic content for an extremely short duration (e.g., 1 second). It's used to protect databases and backend applications from sudden massive spikes in read traffic, while ensuring the data served is barely out of date.

2. **Explain `worker_processes` vs `worker_connections`.**
   *Answer:* `worker_processes` defines how many distinct OS processes NGINX spins up (usually scaled to CPU cores). `worker_connections` dictates how many concurrent connections a single worker process can handle at any given moment.

3. **How does NGINX proxy caching differ from Browser caching?**
   *Answer:* Browser caching stores assets locally on the user's computer (controlled via `Cache-Control` headers). NGINX proxy caching stores responses on the proxy server itself, allowing it to fulfill requests from *multiple different clients* without hitting the backend application.

4. **Why do we need `proxy_http_version 1.1` and `proxy_set_header Connection ""` when setting up Keepalives to upstream servers?**
   *Answer:* Because NGINX proxies using HTTP/1.0 by default, which does not support keep-alive connections. HTTP/1.1 must be enforced, and the default "Connection: close" header must be cleared so the upstream knows to keep the socket open.
