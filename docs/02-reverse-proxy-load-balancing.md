# Level 2: Reverse Proxy & Load Balancing

## 1. What is a Reverse Proxy?
A reverse proxy is a server that sits in front of backend web servers and forwards client requests to those web servers. Unlike a forward proxy (which hides the client from the server), a reverse proxy hides the servers from the client.

**Benefits of a Reverse Proxy:**
- **Security**: The backend servers never reveal their IP addresses to the outside world.
- **Scalability**: Traffic can be distributed across multiple backend servers.
- **SSL Termination**: The reverse proxy can decode incoming HTTPS traffic, saving backend servers the computation cost.
- **Caching**: Frequently accessed static content can be cached at the proxy layer.

## 2. In-Depth: `proxy_pass`
The `proxy_pass` directive is the core of NGINX reverse proxy capabilities. It maps a location block to an upstream server.

```nginx
server {
    listen 80;
    server_name example.com;

    location /api/ {
        # The trailing slash in proxy_pass matters!
        proxy_pass http://backend_server:3000/;
    }
}
```

*Important Note on Trailing Slashes:*
- `proxy_pass http://backend/`: Strips the matching `location` prefix (`/api/`) before forwarding. A request to `/api/users` becomes `/users`.
- `proxy_pass http://backend`: Appends the full URI. A request to `/api/users` becomes `/api/users`.

## 3. The `upstream` Block
To route traffic to multiple servers, NGINX uses the `upstream` block. It defines a pool of servers that can be referenced by `proxy_pass`.

```nginx
upstream my_backend {
    server backend_node_1:8080;
    server backend_node_2:8080;
}

server {
    listen 80;
    location / {
        proxy_pass http://my_backend;
    }
}
```

## 4. Load Balancing Algorithms
By default, NGINX distributes requests using **Round Robin** (sequentially). You can modify this inside the `upstream` block.

- **Round Robin (Default)**: Requests are distributed sequentially.
- **Least Connections (`least_conn;`)**: Sends requests to the server with the fewest active connections. Great when requests take varying amounts of time.
- **IP Hash (`ip_hash;`)**: Routes requests from the same client IP to the same backend server. Useful for stateful applications (session persistence).
- **Weighted**:
    ```nginx
    upstream weighted_backend {
        server node_1:8080 weight=3; # Receives 3/4 of the traffic
        server node_2:8080 weight=1; # Receives 1/4 of the traffic
    }
    ```

## 5. Health Checks
**Passive Health Checks (Open Source NGINX)**:
NGINX automatically monitors failed connections. If a server fails, it is temporarily marked down.
```nginx
upstream backend {
    server node_1:8080 max_fails=3 fail_timeout=30s;
    server node_2:8080 max_fails=3 fail_timeout=30s;
}
```
If `node_1` fails 3 times within 30 seconds, it will be skipped for the next 30 seconds.

*(Note: Active Health Checks using `health_check` are only natively available in NGINX Plus).*

## 6. Headers Handling
When proxying, the backend server sees the NGINX server's IP rather than the client's. We must forward crucial headers manually.

```nginx
location / {
    proxy_pass http://my_backend;
    
    # Forward the real client IP to the backend
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 7. Proxy Buffering
Proxy buffering controls how NGINX handles the response from the backend.
- **Buffering ON (Default)**: NGINX downloads the entire backend response into memory/disk before sending it to the client. This frees up the backend connection immediately.
- **Buffering OFF**: NGINX synchronously sends the response to the client as it receives it. 

```nginx
location / {
    proxy_pass http://my_backend;
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k; # 8 buffers of 4k each
}
```
*When to disable buffering?* For long-polling or Server-Sent Events (SSE).

## 8. Timeout Tuning
To prevent NGINX or backend workers from hanging indefinitely on stalled requests, explicitly set timeouts.

```nginx
location / {
    proxy_pass http://my_backend;
    
    proxy_connect_timeout 5s;   # Max time to establish connection to upstream
    proxy_send_timeout 10s;     # Max time between two successive write operations to upstream
    proxy_read_timeout 10s;     # Max time between two successive read operations from upstream
}
```

## 9. Full Docker Compose Setup (2 Backend Services)

### Structure
```text
docker/
├── docker-compose.yml
└── nginx/
    └── nginx.conf
```

### `docker-compose.yml`
```yaml
version: '3.8'

services:
  lb:
    image: nginx:1.25-alpine
    container_name: nginx_lb
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - web1
      - web2

  web1:
    image: hashicorp/http-echo
    container_name: web1
    command: -text="Hello from Web Server 1" -listen=:8080

  web2:
    image: hashicorp/http-echo
    container_name: web2
    command: -text="Hello from Web Server 2" -listen=:8080
```

### `nginx.conf`
```nginx
events { worker_connections 1024; }

http {
    upstream backend_pool {
        # Docker internal DNS resolves these service names
        server web1:8080;
        server web2:8080;
    }

    server {
        listen 80;
        
        location / {
            proxy_pass http://backend_pool;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## 10. Traffic Simulation
Run the stack:
```bash
docker-compose up -d
```
Hit the load balancer multiple times using `curl`:
```bash
for i in {1..4}; do curl http://localhost; done
```
*Expected Output (Round Robin):*
```text
Hello from Web Server 1
Hello from Web Server 2
Hello from Web Server 1
Hello from Web Server 2
```

## 11. Mini Project: Setup Load Balancer with Failover
**Goal**: Create an active-backup topology.

**Steps**:
1. Create `projects/level-2-load-balancer/`.
2. Add the `docker-compose.yml` and `nginx.conf`.
3. In `nginx.conf`, inside the `upstream` block, mark `web2` as a backup server:
   ```nginx
   upstream backend_pool {
       server web1:8080;
       server web2:8080 backup;
   }
   ```
4. Start the stack. Traffic will only go to `web1`.
5. Run `docker stop web1`.
6. Run `curl http://localhost` and observe traffic failing over to `web2`.

## 12. Interview Preparation (Level 2)

1. **What is the difference between a Reverse Proxy and a Forward Proxy?**
   *Answer:* A forward proxy sits in front of the client (hiding the client from the internet). A reverse proxy sits in front of the server (hiding the server infrastructure from the client).

2. **How does NGINX handle backend server failures by default?**
   *Answer:* Using passive health checks. If a request to an upstream server times out or fails (based on `max_fails` and `fail_timeout`), NGINX temporarily marks the server as down and stops sending traffic to it.

3. **Why do we need to set `X-Forwarded-For` and `X-Real-IP` headers?**
   *Answer:* Because the backend server only sees the connection coming from NGINX's IP address. By explicitly setting these headers, the backend application can log or apply logic based on the actual user's IP address.

4. **When should you disable proxy buffering?**
   *Answer:* When building real-time applications using long-polling, Server-Sent Events (SSE), or WebSockets, so that data flows immediately to the client without waiting for chunks to fill up in NGINX memory.
