# Level 1: NGINX Fundamentals

## 1. What is NGINX?
NGINX (pronounced "engine-ex") is a powerful, open-source web server that also functions as an impressive reverse proxy, load balancer, mail proxy, and HTTP cache. Known for its high performance, stability, rich feature set, simple configuration, and low resource consumption. In modern production environments, it is the standard for handling high-traffic websites.

## 2. History and Architecture
Created by Igor Sysoev in 2004, NGINX was specifically designed to solve the **C10K problem** — the challenge of handling 10,000 concurrent client connections on a single server.

Unlike traditional servers that create a new thread or process for each request, NGINX uses a highly optimized, asynchronous event-driven architecture. This design means that NGINX can handle tens of thousands of concurrent connections with a very small and predictable memory footprint.

## 3. The Event-Driven Model
In an event-driven architecture, a single worker process handles multiple connections concurrently using an event loop. Wait blocks are avoided. If a connection needs to wait (e.g., for a background networking task), the worker process doesn't block; instead, it registers an event and moves on to serve other requests. When the waiting task is complete, an event is fired in the queue, and NGINX processes the next steps.

```ascii
+-----------------------------------------------------------+
|                          NGINX                            |
|                                                           |
|   +---------------------------------------------------+   |
|   |                 Event Loop                        |   |
|   |                                                   |   |
|   |  Req 1 -> [Wait] -> Event Queue -> Process Req 1  |   |
|   |  Req 2 -> [Wait] -> Event Queue -> Process Req 2  |   |
|   |  Req 3 -> [Wait] -> Event Queue -> Process Req 3  |   |
|   |                                                   |   |
|   +---------------------------------------------------+   |
+-----------------------------------------------------------+
```

## 4. Master & Worker Processes
NGINX operates using a multi-process architecture consisting of one **Master Process** and multiple **Worker Processes**.

- **Master Process**: Runs as root. It reads and evaluates configuration files, manages worker processes, and handles administrative tasks like binding to privileged ports (e.g., 80, 443).
- **Worker Processes**: Do the actual heavy lifting. They handle incoming network connections, read/write to the disk, and communicate with upstream servers. 
- **Production Best Practice:** By default, set `worker_processes auto;` in `nginx.conf` so NGINX automatically spawns one worker per CPU core.

## 5. NGINX vs Apache
| Feature | NGINX | Apache HTTP Server |
|---------|-------|--------------------|
| **Architecture** | Event-driven, asynchronous. | Process/thread-based (mpm_prefork, mpm_worker). |
| **Concurrency** | Handles immense concurrent requests with low memory. | Memory footprint grows heavily under high concurrency. |
| **Static Files** | Extremely fast at serving static content directly. | Slower, overhead of reading files through conventional handlers. |
| **Configuration** | Centralized in `nginx.conf`, no `.htaccess` support. | Decentralized `.htaccess` support (adds overhead). |
| **Use Case** | Best for reverse proxy, load balancer, API gateway. | Good for PHP applications, shared hosting. |

## 6. Basic Configuration Breakdown
The core configuration file is generally found at `/etc/nginx/nginx.conf`. The config is structured using contexts (blocks) and directives.

```nginx
# Global Context

user nginx;
worker_processes auto; # One per CPU core
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    # Events Block
    worker_connections 1024; # Max connections per worker
}

http {
    # HTTP Block
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    sendfile on; # Optimize static file delivery
    keepalive_timeout 65;

    # Server Block
    server {
        listen 80;
        server_name example.com www.example.com;

        # Location Block
        location / {
            root /usr/share/nginx/html;
            index index.html;
        }

        # Another Location Block
        location /images/ {
            root /data;
        }
    }
}
```

### Directive Explanations
1. **nginx.conf**: The root entrypoint. Everything cascades from here.
2. **events block**: Controls network connection processing. `worker_connections` multiplied by `worker_processes` equals max theoretical concurrent connections.
3. **http block**: Contains all HTTP-related directives (routing, MIME types, overarching server rules).
4. **server block**: Defines a virtual server. `listen` binds a port. `server_name` checks the Host header to route traffic.
5. **location block**: Matches specific URI patterns. `root` specifies where files live on the filesystem.

## 7. Serving Static Files with Docker
In modern infrastructure, we run NGINX in containers. Let's create a minimal static site delivery container.

### Project Structure Diagram
```text
docker/
├── docker-compose.yml
└── nginx/
    ├── html/
    │   └── index.html
    └── nginx.conf
```

### `nginx.conf`
Create `docker/nginx/nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    server {
        listen 80;
        server_name localhost;

        location / {
            root /usr/share/nginx/html;
            index index.html;
        }
    }
}
```

### `index.html`
Create `docker/nginx/html/index.html`:
```html
<!DOCTYPE html>
<html>
<head><title>NGINX Mastery</title></head>
<body><h1>Hello NGINX! It works.</h1></body>
</html>
```

### `docker-compose.yml`
Create `docker/docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    image: nginx:1.25-alpine
    container_name: nginx-static-web
    ports:
      - "8080:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/html:/usr/share/nginx/html:ro
    restart: unless-stopped
```

**Real-world Production Note:** Notice the `:ro` flag in volumes. Mounting configurations as Read-Only ensures compromised containers cannot mutate their own reverse proxy rules.

## 8. Testing with `curl`
Spin up the container:
```bash
docker-compose up -d
```

Test it:
```bash
curl -I http://localhost:8080/
```

*Expected Output:*
```http
HTTP/1.1 200 OK
Server: nginx/1.25.x
Date: Mon, 01 Jan 2024 10:00:00 GMT
Content-Type: text/html
Content-Length: 104
Last-Modified: Mon, 01 Jan 2024 09:00:00 GMT
Connection: keep-alive
Accept-Ranges: bytes
```

## 9. Mini Project: Static Portfolio Site
**Goal:** Practice creating a static site served purely through Docker and NGINX. 

**Steps:**
1. Create `projects/level-1-static-site`.
2. Replicate the docker-compose topology from step 7.
3. Replace the `html` folder contents with a real HTML/CSS template (e.g., personal portfolio).
4. Add a `location /assets/` block specifically to serve css files and turn `sendfile on;` inside your `http { ... }` block to optimize kernel-space file serving.

**Common Mistake Debugging:** 
- *403 Forbidden*: Usually means the `index.html` file isn't present in the `root` defined in the `location` block, or NGINX lacks read permissions to the directory.
- *404 Not Found*: The URL requested doesn't match the `location` or files don't correspond to the URL path.
- *Container keeps exiting*: Check logs using `docker logs nginx-static-web`. This is often a syntax error in `nginx.conf` (`;` missing, or curly braces mismatch).

## 10. Interview Preparation (Level 1)

1. **What is the C10K problem, and how did NGINX solve it?**
   *Answer:* It's the challenge of serving 10,000 concurrent clients on a single server. NGINX solved it by replacing the traditional "thread-per-process" model with an asynchronous, event-driven, non-blocking architecture.

2. **Explain the difference between Master and Worker NGINX processes.**
   *Answer:* The master process reads configuration and binds ports under root privileges. Worker processes are child processes spawned by the master to handle actual network connections and I/O. 

3. **In `nginx.conf`, what is the hierarchy of blocks from top to bottom?**
   *Answer:* Global directives -> Events context -> HTTP context -> Server context (virtual hosts) -> Location context (URL matching).

4. **Why do we use Alpine images (`nginx:1.25-alpine`) in Docker?**
   *Answer:* Alpine linux dramatically reduces the image size (often under 25MB) which speeds up deployments, saves network bandwidth, and reduces the attack surface for security vulnerabilities.
