# Level 5: Advanced Routing & Architecture

## 1. Path-Based Routing
Path-based routing directs traffic to different backend services depending on the request URI.

```nginx
server {
    listen 80;
    server_name example.com;

    # Matches /api/ exactly, or anything starting with /api/
    location /api/ {
        proxy_pass http://api_backend;
    }

    # Matches /blog/
    location /blog/ {
        proxy_pass http://wordpress_backend;
    }

    # Default matching for everything else
    location / {
        proxy_pass http://frontend_app;
    }
}
```

## 2. Subdomain Routing
Subdomain routing uses the `server_name` directive to route traffic based on the requested host.

```nginx
# API Subdomain
server {
    listen 80;
    server_name api.example.com;
    location / {
        proxy_pass http://api_backend;
    }
}

# App Subdomain
server {
    listen 80;
    server_name app.example.com;
    location / {
        proxy_pass http://frontend_app;
    }
}
```

## 3. The API Gateway Pattern
NGINX is incredibly powerful as an API Gateway, an entry point that aggregates and routes calls to various microservices, enforces authentication, and applies rate limiting.

### Conceptual Architecture Diagram
```text
+-------------------+
|      Client       |
+-------------------+
          |
    [HTTPS: 443]
          v
+-------------------+      --> Authentication/Rate Limiting
|   NGINX Gateway   |
+-------------------+
   |      |      |
   v      v      v
[Auth] [Users] [Orders]    --> Microservices
```

### Configuration
```nginx
server {
    listen 443 ssl;
    server_name gateway.api.com;
    
    # Global Rate Limiting
    limit_req zone=api_limit burst=20 nodelay;

    # Microservice: Users
    location /v1/users/ {
        proxy_pass http://users_service:3000/;
    }

    # Microservice: Orders
    location /v1/orders/ {
        proxy_pass http://orders_service:4000/;
    }
}
```

## 4. WebSocket Proxy
WebSockets establish a persistent, bidirectional connection. To proxy WebSockets, you must explicitly pass the `Upgrade` and `Connection` headers.

```nginx
location /chat/ {
    proxy_pass http://chat_backend;
    
    # Required for WebSockets
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    
    # Optional: Increase timeout so idle connections don't drop
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

## 5. gRPC Proxy
gRPC relies on HTTP/2. Because NGINX supports HTTP/2, it can route gRPC traffic.

```nginx
server {
    listen 443 ssl http2; # HTTP/2 is mandatory for gRPC
    server_name grpc.example.com;
    
    # ssl configs...

    location / {
        # Note the use of grpc:// instead of http://
        grpc_pass grpc://grpc_backend:50051;
    }
}
```

## 6. Stream Proxy (TCP / UDP)
NGINX isn't limited to HTTP; it can proxy raw TCP and UDP traffic (like databases, DNS, or raw sockets) using the `stream` block.

*Note: The `stream` block goes alongside `http` in the root `nginx.conf`, not inside it.*

```nginx
stream {
    # Load balancing a MySQL cluster (TCP)
    upstream mysql_read {
        server db_replica1:3306;
        server db_replica2:3306;
    }

    server {
        listen 3306;
        proxy_pass mysql_read;
    }

    # Proxying a DNS server (UDP)
    server {
        listen 53 udp;
        proxy_pass 192.168.1.100:53;
    }
}
```

## 7. Microservices with Docker Compose
Putting path routing, WebSockets, and subdomains together.

### `docker-compose.yml`
```yaml
version: '3.8'

services:
  gateway:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
  
  frontend:
    image: hashicorp/http-echo
    command: -text="Frontend UI" -listen=:8080

  api_users:
    image: hashicorp/http-echo
    command: -text="Users Microservice" -listen=:8080

  ws_chat:
    image: hashicorp/http-echo
    command: -text="Chat WebSocket Service" -listen=:8080
```

### `nginx.conf`
```nginx
events {}

http {
    server {
        listen 80;
        
        # 1. Path-based routing
        location /api/users/ {
            proxy_pass http://api_users:8080/;
        }

        # 2. WebSocket routing
        location /chat/ {
            proxy_pass http://ws_chat:8080/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
        }

        # 3. Default fallback to frontend
        location / {
            proxy_pass http://frontend:8080/;
        }
    }
}
```

## 8. Interview Preparation (Level 5)

1. **How does NGINX proxy WebSockets?**
   *Answer:* WebSockets begin as an HTTP request with an `Upgrade` header. To keep the connection open and bidirectional, NGINX must be configured to pass the `Upgrade` and `Connection: Upgrade` headers to the backend upstream.
   
2. **Where does the `stream` context live in an `nginx.conf` file?**
   *Answer:* It lives at the root level, entirely separate from and outside of the `http {}` context, because it deals with layer 4 OSI (TCP/UDP) protocols rather than layer 7 (HTTP).

3. **What is the difference between `proxy_pass` and `grpc_pass`?**
   *Answer:* `proxy_pass` is used for standard HTTP/1.x or HTTP/2 rest traffic, whereas `grpc_pass` instructs NGINX to handle the specific framing and HTTP/2 multiplexing required by the gRPC protocol natively. 

4. **In path-based routing, what happens if both `location /api/` and `location /api/users/` exist?**
   *Answer:* NGINX matches the most specific (longest) prefix first. So a request to `/api/users/123` will hit the `/api/users/` block, while `/api/products` will hit the `/api/` block.
